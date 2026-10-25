import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings
from app.core.errors import DomainError

password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash("dummy-credential-never-valid")


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def signing_secret(settings: Settings) -> str:
    if settings.jwt_secret is None:
        raise DomainError(503, "AUTH_NOT_CONFIGURED", "Autenticação ainda não configurada.")
    return settings.jwt_secret.get_secret_value()


def access_token(user_id: UUID, session_id: UUID, settings: Settings) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "sid": str(session_id),
            "jti": str(uuid4()),
            "type": "access",
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(minutes=settings.jwt_access_minutes),
            "iss": settings.jwt_issuer,
            "aud": settings.jwt_audience,
        },
        signing_secret(settings),
        algorithm="HS256",
    )


def decode_access(token: str, settings: Settings) -> tuple[UUID, UUID]:
    secret = signing_secret(settings)
    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "sid", "jti", "type", "iat", "nbf", "exp", "iss", "aud"]},
        )
        if not isinstance(payload["sub"], str) or not isinstance(payload["sid"], str):
            raise ValueError("Invalid session identifiers")
        if payload["type"] != "access":
            raise ValueError("Invalid token type")
        return UUID(payload["sub"]), UUID(payload["sid"])
    except (jwt.InvalidTokenError, ValueError, TypeError) as exc:
        raise DomainError(401, "INVALID_SESSION", "Sessão inválida ou expirada.") from exc
