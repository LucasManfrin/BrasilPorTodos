from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import Timestamps, UUIDPrimaryKey


class Idea(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "ideas"
    __table_args__ = (
        CheckConstraint("status IN ('PRIVATE','SHARED','PROMOTED','ARCHIVED')", name="status"),
        CheckConstraint("(status = 'SHARED') = (shared_snapshot IS NOT NULL)", name="sharing"),
    )
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    summary: Mapped[str] = mapped_column(Text)
    content: Mapped[dict] = mapped_column(JSONB)
    beneficiaries: Mapped[str] = mapped_column(Text, default="")
    adversely_affected: Mapped[str] = mapped_column(Text, default="")
    risks: Mapped[str] = mapped_column(Text, default="")
    assisted_fields: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(12), default="PRIVATE", index=True)
    shared_snapshot: Mapped[dict | None] = mapped_column(JSONB(none_as_null=True))
    shared_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    origin_idea_id: Mapped[UUID | None] = mapped_column(ForeignKey("ideas.id"))
    origin_attribution: Mapped[dict | None] = mapped_column(JSONB)
    promoted_policy_version_number: Mapped[int | None]
    promoted_policy_id: Mapped[UUID | None] = mapped_column(ForeignKey("policies.id"), unique=True)


class IdeaSuggestion(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "idea_suggestions"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','ACCEPTED','DISMISSED')", name="status"),
    )
    idea_id: Mapped[UUID] = mapped_column(ForeignKey("ideas.id"), index=True)
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(Text)
    note: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), default="PENDING")


class IdeaReport(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "idea_reports"
    __table_args__ = (
        CheckConstraint("status IN ('PENDING','DISMISSED','ARCHIVED')", name="status"),
    )
    idea_id: Mapped[UUID] = mapped_column(ForeignKey("ideas.id"), index=True)
    idea_snapshot: Mapped[dict] = mapped_column(JSONB)
    reporter_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12), default="PENDING")
    resolved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"))
    resolution_note: Mapped[str | None] = mapped_column(Text)
