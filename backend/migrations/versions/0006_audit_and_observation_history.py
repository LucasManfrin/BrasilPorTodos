"""Append-only audit trail and indicator revisions.

Revision ID: 0006
Revises: 0005
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("actor_id", sa.UUID(), nullable=False),
        sa.Column("entity_kind", sa.String(30), nullable=False),
        sa.Column("entity_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], name="fk_audit_events_actor_id_users"),
    )
    op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.execute("""
        CREATE FUNCTION bpt_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Historical entries cannot be rewritten; add a revision' USING ERRCODE='23514';
        END;
        $$;
        CREATE TRIGGER frozen_audit BEFORE UPDATE OR DELETE ON audit_events
        FOR EACH ROW EXECUTE FUNCTION bpt_append_only();
        CREATE TRIGGER frozen_indicator_value BEFORE UPDATE OR DELETE ON indicator_values
        FOR EACH ROW EXECUTE FUNCTION bpt_append_only();
    """)


def downgrade():
    op.execute("DROP TRIGGER frozen_indicator_value ON indicator_values")
    op.execute("DROP TRIGGER frozen_audit ON audit_events")
    op.execute("DROP FUNCTION bpt_append_only()")
    op.drop_table("audit_events")
