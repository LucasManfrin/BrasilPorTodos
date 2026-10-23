from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import CreatedAt, UUIDPrimaryKey


class Simulation(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "simulations"
    __table_args__ = (
        UniqueConstraint("plan_version_id", "id", "status", name="uq_simulation_plan_status"),
        CheckConstraint("status IN ('DRAFT','COMPLETED')", name="status"),
        CheckConstraint(
            "(status='DRAFT' AND completed_at IS NULL) OR "
            "(status='COMPLETED' AND completed_at IS NOT NULL)",
            name="completion_time",
        ),
    )
    status: Mapped[str] = mapped_column(String(12), server_default="DRAFT")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    plan_version_id: Mapped[UUID] = mapped_column(ForeignKey("plan_versions.id"), index=True)
    calculation_version: Mapped[str] = mapped_column(String(30))
    input_snapshot: Mapped[dict] = mapped_column(JSONB)
    input_hash: Mapped[str] = mapped_column(String(64))
    assumptions: Mapped[dict] = mapped_column(JSONB)
    warnings: Mapped[list] = mapped_column(JSONB)
    is_partial: Mapped[bool]


class SimulationResult(UUIDPrimaryKey, CreatedAt, Base):
    __tablename__ = "simulation_results"
    __table_args__ = (
        UniqueConstraint("simulation_id", "year"),
        CheckConstraint("year BETWEEN 1900 AND 2200", name="year"),
        CheckConstraint(
            "new_expenses >= 0 AND expense_reductions >= 0 AND new_revenues >= 0 "
            "AND revenue_reductions >= 0 AND new_expenses < 'Infinity'::numeric "
            "AND expense_reductions < 'Infinity'::numeric AND new_revenues < 'Infinity'::numeric "
            "AND revenue_reductions < 'Infinity'::numeric",
            name="amounts",
        ),
        CheckConstraint(
            "net_impact = expense_reductions + new_revenues - new_expenses - revenue_reductions",
            name="net_impact",
        ),
    )

    simulation_id: Mapped[UUID] = mapped_column(ForeignKey("simulations.id"), index=True)
    year: Mapped[int]
    new_expenses: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    expense_reductions: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    new_revenues: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    revenue_reductions: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    net_impact: Mapped[Decimal] = mapped_column(Numeric(18, 2))
