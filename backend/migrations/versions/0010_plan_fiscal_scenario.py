"""Optional fiscal scenario per plan version; no legacy snapshot/result rewriting."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("plan_versions", sa.Column("fiscal_scenario", postgresql.JSONB(), nullable=True))


def downgrade():
    op.drop_column("plan_versions", "fiscal_scenario")
