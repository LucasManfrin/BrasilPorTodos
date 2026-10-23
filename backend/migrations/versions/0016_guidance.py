"""Private, bounded Gemini guidance audit; no publication or fiscal mutation."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "guidance_calls",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("user_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("step_id", sa.String(40), nullable=False),
        sa.Column("script_version", sa.String(20), nullable=False),
        sa.Column("prompt_version", sa.String(20), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt", JSONB(), nullable=False),
        sa.Column("response", JSONB(), nullable=True),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("error_code", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('PENDING','SUCCEEDED','REJECTED','FAILED')", name="status"),
    )
    op.create_index("ix_guidance_calls_user_id", "guidance_calls", ["user_id"])
    op.create_index("ix_guidance_calls_expires_at", "guidance_calls", ["expires_at"])


def downgrade():
    op.drop_table("guidance_calls")
