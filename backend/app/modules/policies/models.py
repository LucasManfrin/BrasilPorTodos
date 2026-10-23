from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
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


class Policy(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "policies"
    accessible_creation: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    is_example: Mapped[bool] = mapped_column(Boolean, server_default=text("false"))
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT','PUBLISHED','ARCHIVED')", name="status"),
        CheckConstraint(
            "(status = 'DRAFT' AND current_version_id IS NULL) OR "
            "(status IN ('PUBLISHED','ARCHIVED') AND current_version_id IS NOT NULL)",
            name="public_version",
        ),
        CheckConstraint("current_version_status = 'PUBLISHED'", name="pointer_status"),
        ForeignKeyConstraint(
            ["id", "current_version_id", "current_version_status"],
            ["policy_versions.policy_id", "policy_versions.id", "policy_versions.status"],
            name="fk_policy_current_version",
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


class PolicyVersion(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "policy_versions"
    __table_args__ = (
        UniqueConstraint("policy_id", "version_number", name="uq_policy_version_number"),
        UniqueConstraint("policy_id", "id", "status", name="uq_policy_version_pointer"),
        UniqueConstraint("id", "status", name="uq_policy_version_status"),
        Index(
            "uq_policy_one_draft", "policy_id", unique=True, postgresql_where=text("status='DRAFT'")
        ),
        CheckConstraint("version_number > 0", name="version_number"),
        CheckConstraint("status IN ('DRAFT','PUBLISHED')", name="status"),
        CheckConstraint(
            "(status='DRAFT' AND published_at IS NULL) OR "
            "(status='PUBLISHED' AND published_at IS NOT NULL)",
            name="publication_timestamp",
        ),
        CheckConstraint(
            "financial_impact_status IN ('ESTIMATED','NOT_ESTIMATED','NOT_APPLICABLE')",
            name="impact_status",
        ),
        CheckConstraint(
            "implementation_start IS NULL OR implementation_start BETWEEN 1900 AND 2200",
            name="start_year",
        ),
        CheckConstraint(
            "implementation_end IS NULL OR implementation_end BETWEEN 1900 AND 2200",
            name="end_year",
        ),
        CheckConstraint("implementation_end >= implementation_start", name="period"),
        CheckConstraint(
            "category IN ('ECONOMY','TAXATION','EDUCATION','HEALTH','SECURITY','PENSION',"
            "'INFRASTRUCTURE','SOCIAL_ASSISTANCE','PUBLIC_ADMINISTRATION','SCIENCE_TECHNOLOGY',"
            "'HOUSING','ENERGY','ENVIRONMENT','OTHER')",
            name="category",
        ),
    )

    policy_id: Mapped[UUID] = mapped_column(ForeignKey("policies.id"), index=True)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    version_number: Mapped[int]
    status: Mapped[str] = mapped_column(String(12), server_default="DRAFT")
    title: Mapped[str] = mapped_column(String(200), server_default="")
    summary: Mapped[str] = mapped_column(Text, server_default="")
    problem: Mapped[str] = mapped_column(Text, server_default="")
    proposal: Mapped[str] = mapped_column(Text, server_default="")
    category: Mapped[str] = mapped_column(String(30), server_default="OTHER")
    implementation_start: Mapped[int | None]
    implementation_end: Mapped[int | None]
    financial_impact_status: Mapped[str] = mapped_column(String(20), server_default="NOT_ESTIMATED")
    impact_justification: Mapped[str | None] = mapped_column(Text)
    baseline_snapshot: Mapped[dict | None] = mapped_column(JSONB)
    proposal_details: Mapped[dict | None] = mapped_column(JSONB)
    change_summary: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PolicySource(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "policy_sources"
    __table_args__ = (UniqueConstraint("policy_version_id", "source_id"),)

    policy_version_id: Mapped[UUID] = mapped_column(ForeignKey("policy_versions.id"), index=True)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("sources.id"))
    usage_description: Mapped[str] = mapped_column(Text)
    source_snapshot: Mapped[dict | None] = mapped_column(JSONB)


class FinancialImpact(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "financial_impacts"
    __table_args__ = (
        CheckConstraint("year BETWEEN 1900 AND 2200", name="year"),
        CheckConstraint("amount >= 0 AND amount < 'Infinity'::numeric", name="amount"),
        CheckConstraint(
            "impact_type IN ('NEW_EXPENSE','EXPENSE_REDUCTION','NEW_REVENUE','REVENUE_REDUCTION')",
            name="impact_type",
        ),
        CheckConstraint(
            "fiscal_scope IN ('CENTRAL_GOVERNMENT','GENERAL_GOVERNMENT','STATE',"
            "'MUNICIPAL','OTHER','UNSPECIFIED')",
            name="fiscal_scope",
        ),
        CheckConstraint(
            "accounting_basis IN ('CASH','ACCRUAL','UNSPECIFIED')", name="accounting_basis"
        ),
        CheckConstraint("price_basis IN ('NOMINAL','CONSTANT','UNSPECIFIED')", name="price_basis"),
        CheckConstraint("component IN ('PRIMARY','INTEREST','UNSPECIFIED')", name="component"),
        CheckConstraint(
            "period_basis IN ('FULL_YEAR','PARTIAL_YEAR','UNSPECIFIED')", name="period_basis"
        ),
        CheckConstraint(
            "(price_basis = 'CONSTANT' AND price_base_year IS NOT NULL AND "
            "price_base_year BETWEEN 1900 AND 2200) OR "
            "(price_basis <> 'CONSTANT' AND price_base_year IS NULL)",
            name="price_reference",
        ),
    )

    policy_version_id: Mapped[UUID] = mapped_column(ForeignKey("policy_versions.id"), index=True)
    year: Mapped[int]
    impact_type: Mapped[str] = mapped_column(String(20))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    description: Mapped[str] = mapped_column(Text)
    fiscal_scope: Mapped[str] = mapped_column(String(20), server_default="UNSPECIFIED")
    accounting_basis: Mapped[str] = mapped_column(String(12), server_default="UNSPECIFIED")
    price_basis: Mapped[str] = mapped_column(String(12), server_default="UNSPECIFIED")
    price_base_year: Mapped[int | None]
    component: Mapped[str] = mapped_column(String(12), server_default="UNSPECIFIED")
    period_basis: Mapped[str] = mapped_column(String(12), server_default="UNSPECIFIED")


class PolicyFunding(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "policy_fundings"
    __table_args__ = (
        CheckConstraint("amount >= 0 AND amount < 'Infinity'::numeric", name="amount"),
        CheckConstraint("year IS NULL OR year BETWEEN 1900 AND 2200", name="year"),
        CheckConstraint(
            "funding_type IN ('SPENDING_CUT','NEW_REVENUE','TAX_INCREASE','DEBT',"
            "'PROGRAM_REPLACEMENT','REVENUE_GROWTH','UNFUNDED','OTHER')",
            name="funding_type",
        ),
    )

    policy_version_id: Mapped[UUID] = mapped_column(ForeignKey("policy_versions.id"), index=True)
    funding_type: Mapped[str] = mapped_column(String(25))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2))
    year: Mapped[int | None]
    description: Mapped[str] = mapped_column(Text)
