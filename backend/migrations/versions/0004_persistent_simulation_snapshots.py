"""Add frozen simulation references and execution lifecycle.

Revision ID: 0004
Revises: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "simulations", sa.Column("status", sa.String(12), server_default="DRAFT", nullable=False)
    )
    op.add_column(
        "simulations", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_check_constraint(
        "ck_simulations_status", "simulations", "status IN ('DRAFT','COMPLETED')"
    )
    op.create_check_constraint(
        "ck_simulations_completion_time",
        "simulations",
        "(status='DRAFT' AND completed_at IS NULL) OR (status='COMPLETED' AND completed_at IS NOT NULL)",
    )
    op.create_unique_constraint(
        "uq_simulation_plan_status", "simulations", ["plan_version_id", "id", "status"]
    )
    op.add_column("plan_versions", sa.Column("simulation_id", sa.Uuid(), nullable=True))
    op.add_column(
        "plan_versions",
        sa.Column("simulation_status", sa.String(12), server_default="COMPLETED", nullable=False),
    )
    op.create_check_constraint(
        "ck_plan_versions_simulation_status", "plan_versions", "simulation_status='COMPLETED'"
    )
    op.create_foreign_key(
        "fk_plan_published_simulation",
        "plan_versions",
        "simulations",
        ["id", "simulation_id", "simulation_status"],
        ["plan_version_id", "id", "status"],
        initially="DEFERRED",
        deferrable=True,
    )


def downgrade() -> None:
    op.drop_constraint("fk_plan_published_simulation", "plan_versions", type_="foreignkey")
    op.drop_constraint("ck_plan_versions_simulation_status", "plan_versions", type_="check")
    op.drop_column("plan_versions", "simulation_status")
    op.drop_column("plan_versions", "simulation_id")
    op.drop_constraint("uq_simulation_plan_status", "simulations", type_="unique")
    op.drop_constraint("ck_simulations_completion_time", "simulations", type_="check")
    op.drop_constraint("ck_simulations_status", "simulations", type_="check")
    op.drop_column("simulations", "completed_at")
    op.drop_column("simulations", "status")
