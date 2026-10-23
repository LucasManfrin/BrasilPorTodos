"""Freeze contextual Brazil baseline on versions; persist official collection outcomes."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("policy_versions", "plan_versions"):
        op.add_column(table, sa.Column("baseline_snapshot", JSONB(), nullable=True))
    op.create_table(
        "indicator_collection_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("results", JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_indicator_collection_runs"),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["users.id"], name="fk_indicator_collection_runs_actor_id_users"
        ),
    )


def downgrade():
    op.drop_table("indicator_collection_runs")
    for table in ("policy_versions", "plan_versions"):
        op.drop_column(table, "baseline_snapshot")
