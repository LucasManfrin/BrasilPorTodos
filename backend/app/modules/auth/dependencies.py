from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import DomainError
from app.database.session import get_session
from app.modules.auth.models import AuthSession
from app.modules.auth.security import decode_access
from app.modules.users.models import User

bearer = HTTPBearer(auto_error=False)


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[Session, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> User:
    if credentials is None:
        raise DomainError(401, "AUTH_REQUIRED", "Entre para continuar.")
    user_id, session_id = decode_access(credentials.credentials, settings)
    grant = session.get(AuthSession, session_id)
    user = session.get(User, user_id)
    if (
        grant is None
        or grant.user_id != user_id
        or grant.revoked_at is not None
        or grant.expires_at <= datetime.now(UTC)
        or user is None
        or not user.is_active
    ):
        raise DomainError(401, "INVALID_SESSION", "Sessão inválida ou expirada.")
    return user


def require_owner(user: User, author_id: UUID) -> None:
    if user.id != author_id and user.role != "ADMIN":
        raise DomainError(403, "FORBIDDEN", "Você não pode alterar este conteúdo.")
