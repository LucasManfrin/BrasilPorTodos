"""Immutable general-government cohorts, independent from RTN and snapshots."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "general_government_cohorts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("parser_version", sa.String(50), nullable=False),
        sa.Column("precision_version", sa.String(100), nullable=False),
        sa.Column("cohort_fingerprint", sa.String(64), nullable=False),
        sa.Column("source_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_general_government_cohorts")),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["sources.id"],
            name=op.f("fk_general_government_cohorts_source_id_sources"),
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_general_government_cohorts_created_by_users"),
        ),
        sa.UniqueConstraint(
            "year", "revision", name=op.f("uq_general_government_cohorts_year_revision")
        ),
        sa.UniqueConstraint(
            "year",
            "source_hash",
            "parser_version",
            "precision_version",
            name=op.f("uq_general_government_cohorts_year_hash_versions"),
        ),
        sa.CheckConstraint(
            "year >= 2010 AND year <= 9999", name=op.f("ck_general_government_cohorts_year")
        ),
        sa.CheckConstraint("revision > 0", name=op.f("ck_general_government_cohorts_revision")),
        sa.CheckConstraint(
            "source_hash ~ '^[0-9a-f]{64}$'", name=op.f("ck_general_government_cohorts_source_hash")
        ),
        sa.CheckConstraint(
            "cohort_fingerprint ~ '^[0-9a-f]{64}$'",
            name=op.f("ck_general_government_cohorts_fingerprint"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(payload) = 'object' AND jsonb_typeof(source_snapshot) = 'object'",
            name=op.f("ck_general_government_cohorts_json_objects"),
        ),
    )
    op.create_index(
        "ix_general_government_cohorts_source_id", "general_government_cohorts", ["source_id"]
    )
    op.execute("""
        CREATE TRIGGER frozen_general_government_cohort
        BEFORE UPDATE OR DELETE ON general_government_cohorts
        FOR EACH ROW EXECUTE FUNCTION bpt_append_only();
    """)


def downgrade():
    op.execute("DROP TRIGGER frozen_general_government_cohort ON general_government_cohorts")
    op.drop_index(
        "ix_general_government_cohorts_source_id", table_name="general_government_cohorts"
    )
    op.drop_table("general_government_cohorts")
