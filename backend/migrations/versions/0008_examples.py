"""Explicit demonstration flags; production excludes them."""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade():
    for table in ("policies", "plans", "sources"):
        op.add_column(
            table,
            sa.Column("is_example", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        )


def downgrade():
    for table in ("policies", "plans", "sources"):
        op.drop_column(table, "is_example")
