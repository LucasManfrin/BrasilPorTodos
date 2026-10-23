"""Append-only context content, human review and publication records."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import CreatedAt, UUIDPrimaryKey


class Context(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "contexts"
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    is_example: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))


class ContextVersion(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "context_versions"
    __table_args__ = (
        UniqueConstraint("context_id", "version_number", name="uq_context_version_number"),
        UniqueConstraint("id", "content_hash", name="uq_context_version_hash"),
        CheckConstraint("version_number > 0", name="version_number"),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
    )
    context_id: Mapped[UUID] = mapped_column(ForeignKey("contexts.id"), index=True)
    version_number: Mapped[int]
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB)


class ContextReview(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "context_reviews"
    __table_args__ = (
        UniqueConstraint("context_version_id", "review_number", name="uq_context_review_number"),
        UniqueConstraint(
            "id", "context_version_id", "content_hash", name="uq_context_review_target"
        ),
        ForeignKeyConstraint(
            ["context_version_id", "content_hash"],
            ["context_versions.id", "context_versions.content_hash"],
            name="fk_context_review_version_hash",
        ),
        CheckConstraint("review_number > 0", name="review_number"),
        CheckConstraint("decision IN ('ACCEPT','REQUEST_CHANGES')", name="decision"),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
        CheckConstraint("jsonb_typeof(payload) = 'object'", name="payload_object"),
    )
    context_version_id: Mapped[UUID] = mapped_column(index=True)
    review_number: Mapped[int]
    reviewer_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    content_hash: Mapped[str] = mapped_column(String(64))
    decision: Mapped[str] = mapped_column(String(20))
    payload: Mapped[dict] = mapped_column(JSONB)


class ContextPublication(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "context_publications"
    __table_args__ = (
        UniqueConstraint("context_version_id", name="uq_context_publication_version"),
        ForeignKeyConstraint(
            ["context_version_id", "content_hash"],
            ["context_versions.id", "context_versions.content_hash"],
            name="fk_context_publication_version_hash",
        ),
        ForeignKeyConstraint(
            ["review_id", "context_version_id", "content_hash"],
            [
                "context_reviews.id",
                "context_reviews.context_version_id",
                "context_reviews.content_hash",
            ],
            name="fk_context_publication_review_target",
        ),
        CheckConstraint("content_hash ~ '^[0-9a-f]{64}$'", name="content_hash"),
    )
    context_version_id: Mapped[UUID]
    review_id: Mapped[UUID]
    content_hash: Mapped[str] = mapped_column(String(64))
    published_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
