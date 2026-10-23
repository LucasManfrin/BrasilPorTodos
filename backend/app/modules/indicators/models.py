from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import CreatedAt, Timestamps, UUIDPrimaryKey


class Indicator(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "indicators"
    __table_args__ = (
        CheckConstraint(
            "category IN ('ECONOMY','FISCAL','SOCIAL','PUBLIC_SPENDING')", name="category"
        ),
        CheckConstraint(
            "frequency IN ('DAILY','MONTHLY','QUARTERLY','YEARLY','IRREGULAR')", name="frequency"
        ),
    )

    code: Mapped[str] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(20))
    unit: Mapped[str] = mapped_column(String(50))
    frequency: Mapped[str] = mapped_column(String(15))
    scope: Mapped[str] = mapped_column(Text)
    methodology: Mapped[str] = mapped_column(Text)
    base_year: Mapped[int | None]
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))


class IndicatorValue(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "indicator_values"
    __table_args__ = (
        UniqueConstraint("indicator_id", "reference_date", "source_id", "revision"),
        CheckConstraint("revision > 0", name="revision"),
        CheckConstraint(
            "value > '-Infinity'::numeric AND value < 'Infinity'::numeric", name="finite_value"
        ),
    )

    indicator_id: Mapped[UUID] = mapped_column(ForeignKey("indicators.id"), index=True)
    reference_date: Mapped[date]
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6))
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revision: Mapped[int] = mapped_column(server_default="1")
    revision_reason: Mapped[str | None] = mapped_column(Text)
    provenance: Mapped[dict] = mapped_column(JSONB)


class FiscalSpendingCohort(UUIDPrimaryKey, CreatedAt, Base):
    """One immutable reviewed file/year, all stages and classifications together."""

    __tablename__ = "fiscal_spending_cohorts"
    __table_args__ = (
        UniqueConstraint("year", "revision", name="uq_fiscal_spending_cohorts_year_revision"),
        UniqueConstraint(
            "year",
            "source_hash",
            "parser_version",
            "precision_version",
            name="uq_fiscal_spending_cohorts_year_hash_versions",
        ),
        CheckConstraint("year >= 1997 AND year <= 9999", name="year"),
        CheckConstraint("revision > 0", name="revision"),
        CheckConstraint("source_hash ~ '^[0-9a-f]{64}$'", name="source_hash"),
        CheckConstraint("cohort_fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint"),
        CheckConstraint(
            "jsonb_typeof(payload) = 'object' AND jsonb_typeof(source_snapshot) = 'object'",
            name="json_objects",
        ),
    )
    year: Mapped[int]
    revision: Mapped[int]
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_hash: Mapped[str] = mapped_column(String(64))
    parser_version: Mapped[str] = mapped_column(String(50))
    precision_version: Mapped[str] = mapped_column(String(100))
    cohort_fingerprint: Mapped[str] = mapped_column(String(64))
    source_snapshot: Mapped[dict] = mapped_column(JSONB)
    payload: Mapped[dict] = mapped_column(JSONB)


class GeneralGovernmentCohort(UUIDPrimaryKey, CreatedAt, Base):
    """One immutable official publication/year with all sectors and consolidations."""

    __tablename__ = "general_government_cohorts"
    __table_args__ = (
        UniqueConstraint("year", "revision", name="uq_general_government_cohorts_year_revision"),
        UniqueConstraint(
            "year",
            "source_hash",
            "parser_version",
            "precision_version",
            name="uq_general_government_cohorts_year_hash_versions",
        ),
        CheckConstraint("year >= 2010 AND year <= 9999", name="year"),
        CheckConstraint("revision > 0", name="revision"),
        CheckConstraint("source_hash ~ '^[0-9a-f]{64}$'", name="source_hash"),
        CheckConstraint("cohort_fingerprint ~ '^[0-9a-f]{64}$'", name="fingerprint"),
        CheckConstraint(
            "jsonb_typeof(payload) = 'object' AND jsonb_typeof(source_snapshot) = 'object'",
            name="json_objects",
        ),
    )
    year: Mapped[int]
    revision: Mapped[int]
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_hash: Mapped[str] = mapped_column(String(64))
    parser_version: Mapped[str] = mapped_column(String(50))
    precision_version: Mapped[str] = mapped_column(String(100))
    cohort_fingerprint: Mapped[str] = mapped_column(String(64))
    source_snapshot: Mapped[dict] = mapped_column(JSONB)
    payload: Mapped[dict] = mapped_column(JSONB)
