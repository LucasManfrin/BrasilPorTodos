"""Erasure marker survives completion of in-flight guidance calls."""

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "guidance_calls", sa.Column("cleared_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade():
    op.drop_column("guidance_calls", "cleared_at")
