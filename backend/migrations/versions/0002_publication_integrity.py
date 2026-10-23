"""Protect published versions and their dependent content.

Revision ID: 0002
Revises: 0001
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cyclic pointers must be created after their target version tables exist.
    for parent, version, parent_id in (
        ("policies", "policy_versions", "policy_id"),
        ("plans", "plan_versions", "plan_id"),
    ):
        singular = "policy" if parent == "policies" else "plan"
        op.create_foreign_key(
            f"fk_{singular}_current_version",
            parent,
            version,
            ["id", "current_version_id", "current_version_status"],
            [parent_id, "id", "status"],
            deferrable=True,
            initially="DEFERRED",
        )
    op.execute("""
    CREATE FUNCTION bpt_frozen_version() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF TG_OP = 'INSERT' THEN
            IF NEW.status <> 'DRAFT' THEN
                RAISE EXCEPTION 'Create a draft before publishing' USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END IF;
        IF OLD.status = 'PUBLISHED' THEN
            RAISE EXCEPTION 'Published versions are immutable' USING ERRCODE = '23514';
        END IF;
        IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
        IF NEW.id <> OLD.id THEN
            RAISE EXCEPTION 'Version identity is immutable' USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    END;
    $$;
    CREATE FUNCTION bpt_draft_child() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE
        old_id uuid;
        new_id uuid;
        version_state text;
    BEGIN
        IF TG_OP <> 'INSERT' THEN
            old_id := (to_jsonb(OLD)->>TG_ARGV[1])::uuid;
            EXECUTE format('SELECT status FROM %I WHERE id=$1 FOR UPDATE', TG_ARGV[0])
                INTO version_state USING old_id;
            IF version_state = 'PUBLISHED' THEN
                RAISE EXCEPTION 'Published version content is immutable' USING ERRCODE='23514';
            END IF;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            new_id := (to_jsonb(NEW)->>TG_ARGV[1])::uuid;
            EXECUTE format('SELECT status FROM %I WHERE id=$1 FOR UPDATE', TG_ARGV[0])
                INTO version_state USING new_id;
            IF version_state = 'PUBLISHED' THEN
                RAISE EXCEPTION 'Published version content is immutable' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END IF;
        RETURN OLD;
    END;
    $$;
    CREATE FUNCTION bpt_publication_checks() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF NEW.status='PUBLISHED' AND TG_TABLE_NAME='policy_versions' THEN
            IF EXISTS (SELECT 1 FROM policy_sources
                       WHERE policy_version_id=NEW.id AND source_snapshot IS NULL) THEN
                RAISE EXCEPTION 'Publication requires source snapshots' USING ERRCODE='23514';
            END IF;
            IF NEW.financial_impact_status <> 'ESTIMATED' AND EXISTS (
                SELECT 1 FROM financial_impacts WHERE policy_version_id=NEW.id
            ) THEN
                RAISE EXCEPTION 'Nonestimated versions cannot have amounts' USING ERRCODE='23514';
            END IF;
        END IF;
        RETURN NEW;
    END;
    $$;
    """)
    for table in ("policy_versions", "plan_versions"):
        op.execute(
            f"CREATE TRIGGER frozen_version BEFORE INSERT OR UPDATE OR DELETE ON {table} "
            "FOR EACH ROW EXECUTE FUNCTION bpt_frozen_version()"
        )
    op.execute(
        "CREATE TRIGGER publication_checks BEFORE UPDATE ON policy_versions "
        "FOR EACH ROW EXECUTE FUNCTION bpt_publication_checks()"
    )
    for table, version_table, column in (
        ("policy_sources", "policy_versions", "policy_version_id"),
        ("financial_impacts", "policy_versions", "policy_version_id"),
        ("policy_fundings", "policy_versions", "policy_version_id"),
        ("plan_policies", "plan_versions", "plan_version_id"),
    ):
        op.execute(
            f"CREATE TRIGGER frozen_child BEFORE INSERT OR UPDATE OR DELETE ON {table} "
            f"FOR EACH ROW EXECUTE FUNCTION bpt_draft_child('{version_table}', '{column}')"
        )


def downgrade() -> None:
    for table in ("policy_sources", "financial_impacts", "policy_fundings", "plan_policies"):
        op.execute(f"DROP TRIGGER frozen_child ON {table}")
    op.execute("DROP TRIGGER publication_checks ON policy_versions")
    for table in ("policy_versions", "plan_versions"):
        op.execute(f"DROP TRIGGER frozen_version ON {table}")
    for function in ("bpt_publication_checks", "bpt_draft_child", "bpt_frozen_version"):
        op.execute(f"DROP FUNCTION {function}()")
    op.drop_constraint("fk_policy_current_version", "policies", type_="foreignkey")
    op.drop_constraint("fk_plan_current_version", "plans", type_="foreignkey")
