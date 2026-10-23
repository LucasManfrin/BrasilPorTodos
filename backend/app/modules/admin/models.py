from uuid import UUID

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import CreatedAt, UUIDPrimaryKey


class AuditEvent(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    entity_kind: Mapped[str] = mapped_column(String(30))
    entity_id: Mapped[UUID] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(50))
    reason: Mapped[str] = mapped_column(Text)
    details: Mapped[dict] = mapped_column(JSONB)


def record(session, actor, kind, entity_id, action, reason, details=None):
    session.add(
        AuditEvent(
            actor_id=actor.id,
            entity_kind=kind,
            entity_id=entity_id,
            action=action,
            reason=reason,
            details=details or {},
        )
    )
