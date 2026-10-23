import hmac
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import DomainError
from app.modules.auth.models import AuthRateLimit, AuthSession, RefreshToken
from app.modules.auth.schemas import LoginInput, RegisterInput
from app.modules.auth.security import (
    access_token,
    digest,
    dummy_hash,
    password_hasher,
    signing_secret,
)
from app.modules.users.models import User


def consume_rate_limits(session: Session, action: str, client: str, identifier: str = "") -> None:
    bucket = int(datetime.now(UTC).timestamp()) // 60
    keys = [(f"{action}:ip:{client}", 30), (f"{action}:identity:{client}:{identifier}", 8)]
    exceeded = False
    for key, limit in keys:
        statement = insert(AuthRateLimit).values(key=digest(key), bucket=bucket, hits=1)
        hits = session.scalar(
            statement.on_conflict_do_update(
                index_elements=[AuthRateLimit.key],
                set_={
                    "bucket": bucket,
                    "hits": case((AuthRateLimit.bucket == bucket, AuthRateLimit.hits + 1), else_=1),
                },
            ).returning(AuthRateLimit.hits)
        )
        exceeded = exceeded or hits > limit
    # Rejected credentials must not roll back the abuse counters.
    session.commit()
    if exceeded:
        raise DomainError(429, "AUTH_RATE_LIMIT", "Muitas tentativas. Aguarde um minuto.")


def issue_credentials(
    session: Session, user: User, settings: Settings, grant: AuthSession | None = None
):
    if grant is None:
        grant = AuthSession(
            user_id=user.id, expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_days)
        )
        session.add(grant)
        session.flush()
    refresh = secrets.token_urlsafe(48)
    csrf = secrets.token_urlsafe(32)
    session.add(
        RefreshToken(
            session_id=grant.id,
            token_hash=digest(refresh),
            csrf_hash=digest(csrf),
            expires_at=grant.expires_at,
        )
    )
    result = {
        "access_token": access_token(user.id, grant.id, settings),
        "expires_in": settings.jwt_access_minutes * 60,
        "csrf_token": csrf,
        "user": user,
    }
    session.commit()
    return result, refresh


def register(session: Session, data: RegisterInput, settings: Settings):
    signing_secret(settings)
    user = User(
        name=data.name,
        username=data.username,
        email=str(data.email).lower(),
        password_hash=password_hasher.hash(data.password.get_secret_value()),
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise DomainError(
            409, "ACCOUNT_EXISTS", "Não foi possível cadastrar com esses dados."
        ) from exc
    return issue_credentials(session, user, settings)


def login(session: Session, data: LoginInput, settings: Settings):
    signing_secret(settings)
    user = session.scalar(select(User).where(User.email == str(data.email).lower()))
    valid, updated_hash = password_hasher.verify_and_update(
        data.password.get_secret_value(), user.password_hash if user else dummy_hash
    )
    if user is None or not valid or not user.is_active:
        raise DomainError(401, "INVALID_CREDENTIALS", "E-mail ou senha inválidos.")
    if updated_hash:
        user.password_hash = updated_hash
    return issue_credentials(session, user, settings)


def find_refresh(session: Session, raw_token: str | None, csrf: str | None):
    if not raw_token or len(raw_token) > 200:
        raise DomainError(401, "INVALID_SESSION", "Sessão inválida ou expirada.")
    token = session.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == digest(raw_token)).with_for_update()
    )
    if token is None:
        raise DomainError(401, "INVALID_SESSION", "Sessão inválida ou expirada.")
    if not csrf or not hmac.compare_digest(token.csrf_hash, digest(csrf)):
        raise DomainError(403, "INVALID_CSRF", "Requisição de sessão inválida.")
    grant = session.scalar(
        select(AuthSession).where(AuthSession.id == token.session_id).with_for_update()
    )
    now = datetime.now(UTC)
    if grant.revoked_at or grant.expires_at <= now or token.expires_at <= now:
        raise DomainError(401, "INVALID_SESSION", "Sessão inválida ou expirada.")
    if token.consumed_at:
        grant.revoked_at = now
        session.commit()
        raise DomainError(401, "REFRESH_REUSED", "Sessão revogada. Entre novamente.")
    return token, grant


def refresh(session: Session, raw_token: str | None, csrf: str | None, settings: Settings):
    signing_secret(settings)
    token, grant = find_refresh(session, raw_token, csrf)
    user = session.get(User, grant.user_id)
    if not user.is_active:
        raise DomainError(401, "INVALID_SESSION", "Sessão inválida ou expirada.")
    token.consumed_at = datetime.now(UTC)
    return issue_credentials(session, user, settings, grant)


def logout(session: Session, raw_token: str | None, csrf: str | None):
    _, grant = find_refresh(session, raw_token, csrf)
    grant.revoked_at = datetime.now(UTC)
    session.commit()
