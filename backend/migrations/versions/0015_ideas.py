"""Accessible private ideas, explicit shared snapshots and abuse controls."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def common():
    return [
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    ]


def upgrade():
    op.add_column(
        "policies",
        sa.Column(
            "accessible_creation", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.add_column("policy_versions", sa.Column("proposal_details", JSONB(), nullable=True))
    op.create_table(
        "ideas",
        *common(),
        sa.Column("author_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("content", JSONB(), nullable=False),
        sa.Column("beneficiaries", sa.Text(), nullable=False),
        sa.Column("adversely_affected", sa.Text(), nullable=False),
        sa.Column("risks", sa.Text(), nullable=False),
        sa.Column("assisted_fields", JSONB(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("shared_snapshot", JSONB(), nullable=True),
        sa.Column("shared_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("origin_idea_id", sa.UUID(), sa.ForeignKey("ideas.id"), nullable=True),
        sa.Column("origin_attribution", JSONB(), nullable=True),
        sa.Column("promoted_policy_version_number", sa.Integer(), nullable=True),
        sa.Column(
            "promoted_policy_id",
            sa.UUID(),
            sa.ForeignKey("policies.id"),
            nullable=True,
            unique=True,
        ),
        sa.CheckConstraint("status IN ('PRIVATE','SHARED','PROMOTED','ARCHIVED')", name="status"),
        sa.CheckConstraint("(status = 'SHARED') = (shared_snapshot IS NOT NULL)", name="sharing"),
    )
    op.create_index("ix_ideas_author_id", "ideas", ["author_id"])
    op.create_index("ix_ideas_status", "ideas", ["status"])
    op.create_table(
        "idea_suggestions",
        *common(),
        sa.Column("idea_id", sa.UUID(), sa.ForeignKey("ideas.id"), nullable=False),
        sa.Column("author_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.CheckConstraint("status IN ('PENDING','ACCEPTED','DISMISSED')", name="status"),
    )
    op.create_index("ix_idea_suggestions_idea_id", "idea_suggestions", ["idea_id"])
    op.create_index("ix_idea_suggestions_author_id", "idea_suggestions", ["author_id"])
    op.create_table(
        "idea_reports",
        *common(),
        sa.Column("idea_id", sa.UUID(), sa.ForeignKey("ideas.id"), nullable=False),
        sa.Column("reporter_id", sa.UUID(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("idea_snapshot", JSONB(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column("resolved_by", sa.UUID(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.CheckConstraint("status IN ('PENDING','DISMISSED','ARCHIVED')", name="status"),
    )
    op.create_index("ix_idea_reports_idea_id", "idea_reports", ["idea_id"])
    op.create_index("ix_idea_reports_reporter_id", "idea_reports", ["reporter_id"])


def downgrade():
    op.drop_table("idea_reports")
    op.drop_table("idea_suggestions")
    op.drop_table("ideas")
    op.drop_column("policy_versions", "proposal_details")
    op.drop_column("policies", "accessible_creation")
