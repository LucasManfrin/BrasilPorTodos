from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import CreatedAt, Timestamps, UUIDPrimaryKey


class Plan(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "plans"
    is_example: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','PUBLISHED','ARCHIVED')", name="status"),
        CheckConstraint(
            "(status='DRAFT' AND current_version_id IS NULL) OR "
            "(status IN ('PUBLISHED','ARCHIVED') AND current_version_id IS NOT NULL)",
            name="public_version",
        ),
        CheckConstraint("current_version_status = 'PUBLISHED'", name="pointer_status"),
        ForeignKeyConstraint(
            ["id", "current_version_id", "current_version_status"],
            ["plan_versions.plan_id", "plan_versions.id", "plan_versions.status"],
            name="fk_plan_current_version",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    slug: Mapped[str] = mapped_column(String(180), unique=True)
    status: Mapped[str] = mapped_column(String(12), server_default="DRAFT")
    current_version_id: Mapped[UUID | None]
    current_version_status: Mapped[str] = mapped_column(String(12), server_default="PUBLISHED")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    archive_reason: Mapped[str | None] = mapped_column(Text)


class PlanVersion(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "plan_versions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["id", "simulation_id", "simulation_status"],
            ["simulations.plan_version_id", "simulations.id", "simulations.status"],
            name="fk_plan_published_simulation",
            use_alter=True,
            deferrable=True,
            initially="DEFERRED",
        ),
        CheckConstraint("simulation_status = 'COMPLETED'", name="simulation_status"),
        UniqueConstraint("plan_id", "version_number", name="uq_plan_version_number"),
        UniqueConstraint("plan_id", "id", "status", name="uq_plan_version_pointer"),
        Index("uq_plan_one_draft", "plan_id", unique=True, postgresql_where=text("status='DRAFT'")),
        CheckConstraint("version_number > 0", name="version_number"),
        CheckConstraint("status IN ('DRAFT','PUBLISHED')", name="status"),
        CheckConstraint(
            "(status='DRAFT' AND published_at IS NULL) OR "
            "(status='PUBLISHED' AND published_at IS NOT NULL)",
            name="publication_timestamp",
        ),
        CheckConstraint("start_year BETWEEN 1900 AND 2200", name="start_year"),
        CheckConstraint("end_year BETWEEN 1900 AND 2200", name="end_year"),
        CheckConstraint("end_year >= start_year", name="period"),
    )

    simulation_id: Mapped[UUID | None]
    simulation_status: Mapped[str] = mapped_column(String(12), server_default="COMPLETED")
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("plans.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    version_number: Mapped[int]
    status: Mapped[str] = mapped_column(String(12), server_default="DRAFT")
    title: Mapped[str] = mapped_column(String(200), server_default="")
    summary: Mapped[str] = mapped_column(Text, server_default="")
    vision: Mapped[str] = mapped_column(Text, server_default="")
    start_year: Mapped[int]
    end_year: Mapped[int]
    baseline_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    fiscal_scenario: Mapped[dict | None] = mapped_column(JSONB)
    change_summary: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PlanPolicy(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "plan_policies"
    __table_args__ = (
        UniqueConstraint("plan_version_id", "policy_version_id", name="uq_plan_policy_version"),
        UniqueConstraint("plan_version_id", "position", name="uq_plan_policy_position"),
        CheckConstraint("position >= 0", name="position"),
        CheckConstraint("policy_version_status = 'PUBLISHED'", name="published_policy"),
        ForeignKeyConstraint(
            ["policy_version_id", "policy_version_status"],
            ["policy_versions.id", "policy_versions.status"],
            name="fk_plan_policy_published_version",
        ),
    )

    plan_version_id: Mapped[UUID] = mapped_column(ForeignKey("plan_versions.id"), index=True)
    policy_version_id: Mapped[UUID]
    policy_version_status: Mapped[str] = mapped_column(String(12), server_default="PUBLISHED")
    position: Mapped[int]
    is_enabled: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))
