from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select, update

from app.core.dependencies import DB, CurrentUser
from app.core.errors import DomainError
from app.modules.admin.models import AuditEvent, record
from app.modules.auth.models import AuthSession
from app.modules.indicators import service as indicators
from app.modules.indicators.schemas import IndicatorInput, ObservationInput
from app.modules.users.models import User


def admin(user: CurrentUser):
    if user.role != "ADMIN":
        raise DomainError(403, "ADMIN_REQUIRED", "Esta ação exige administração.")
    return user


Admin = Annotated[User, Depends(admin)]
router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/indicators/collect")
def collect_official(session: DB, actor: Admin, tasks: BackgroundTasks):
    from app.modules.indicators.collection import request_collection

    return {"data": request_collection(session, actor, tasks)}


class UserState(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    is_active: bool
    reason: str = Field(min_length=1, max_length=2000)


@router.get("/users")
def users(
    session: DB,
    actor: Admin,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(max_length=120)] = None,
):
    statement = select(User)
    if q:
        statement = statement.where(User.username.ilike(f"%{q}%"))
    total = session.scalar(select(func.count()).select_from(statement.subquery()))
    rows = session.scalars(
        statement.order_by(User.username).offset((page - 1) * page_size).limit(page_size)
    )
    return {
        "data": [
            {
                "id": str(row.id),
                "name": row.name,
                "username": row.username,
                "role": row.role,
                "is_active": row.is_active,
            }
            for row in rows
        ],
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }


@router.patch("/users/{user_id}")
def user_state(user_id: UUID, data: UserState, session: DB, actor: Admin):
    row = session.scalar(select(User).where(User.id == user_id).with_for_update())
    if row is None:
        raise DomainError(404, "USER_NOT_FOUND", "Usuário não encontrado.")
    if row.role == "ADMIN":
        raise DomainError(
            409,
            "ADMIN_STATE_PROTECTED",
            "Administradores são mantidos pelo procedimento operacional local.",
        )
    before = row.is_active
    row.is_active = data.is_active
    if not data.is_active:
        # Reactivating the account must never resurrect credentials from before its suspension.
        session.execute(
            update(AuthSession)
            .where(AuthSession.user_id == row.id, AuthSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )
    record(
        session,
        actor,
        "user",
        row.id,
        "ACTIVATE" if data.is_active else "DEACTIVATE",
        data.reason,
        {"before": before, "after": data.is_active},
    )
    session.commit()
    return {"data": {"id": str(row.id), "is_active": row.is_active}}


@router.get("/audit")
def audit(
    session: DB,
    actor: Admin,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    total = session.scalar(select(func.count()).select_from(AuditEvent))
    rows = session.scalars(
        select(AuditEvent)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return {
        "data": [
            {
                "id": str(row.id),
                "actor_id": str(row.actor_id),
                "entity_kind": row.entity_kind,
                "entity_id": str(row.entity_id),
                "action": row.action,
                "reason": row.reason,
                "created_at": row.created_at.isoformat(),
                "details": row.details,
            }
            for row in rows
        ],
        "pagination": {"page": page, "page_size": page_size, "total": total},
    }


@router.get("/indicators")
def list_indicators(
    session: DB,
    actor: Admin,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return indicators.catalog(session, page, page_size, include_inactive=True)


@router.post("/indicators", status_code=201)
def create_indicator(data: IndicatorInput, session: DB, actor: Admin):
    return {"data": indicators.save(session, data, actor)}


@router.put("/indicators/{indicator_id}")
def edit_indicator(indicator_id: UUID, data: IndicatorInput, session: DB, actor: Admin):
    return {"data": indicators.save(session, data, actor, indicator_id)}


@router.post("/indicators/{indicator_id}/values", status_code=201)
def create_value(indicator_id: UUID, data: ObservationInput, session: DB, actor: Admin):
    return {"data": indicators.add_observation(session, indicator_id, data, actor)}
