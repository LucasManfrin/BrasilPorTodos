from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import CreatedAt, UUIDPrimaryKey


class GuidanceCall(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "guidance_calls"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','SUCCEEDED','REJECTED','FAILED')", name="status"),
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    step_id: Mapped[str] = mapped_column(String(40))
    script_version: Mapped[str] = mapped_column(String(20))
    prompt_version: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str] = mapped_column(String(20))
    model: Mapped[str] = mapped_column(String(100))
    prompt: Mapped[dict] = mapped_column(JSONB)
    response: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(12))
    error_code: Mapped[str | None] = mapped_column(Text)
    cleared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
