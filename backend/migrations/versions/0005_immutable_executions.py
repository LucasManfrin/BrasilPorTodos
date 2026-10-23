"""Freeze completed executions and their annual results.

Revision ID: 0005
Revises: 0004
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    CREATE FUNCTION bpt_frozen_execution() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN
        IF TG_OP='INSERT' THEN
            IF NEW.status <> 'DRAFT' THEN
                RAISE EXCEPTION 'Executions start as drafts' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END IF;
        IF OLD.status='COMPLETED' THEN
            RAISE EXCEPTION 'Completed executions are immutable' USING ERRCODE='23514';
        END IF;
        IF TG_OP='DELETE' THEN RETURN OLD; END IF;
        RETURN NEW;
    END;
    $$;
    CREATE FUNCTION bpt_frozen_result() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE execution_state text;
    BEGIN
        IF TG_OP <> 'INSERT' THEN
            SELECT status INTO execution_state FROM simulations WHERE id=OLD.simulation_id FOR UPDATE;
            IF execution_state='COMPLETED' THEN
                RAISE EXCEPTION 'Completed results are immutable' USING ERRCODE='23514';
            END IF;
        END IF;
        IF TG_OP <> 'DELETE' THEN
            SELECT status INTO execution_state FROM simulations WHERE id=NEW.simulation_id FOR UPDATE;
            IF execution_state='COMPLETED' THEN
                RAISE EXCEPTION 'Completed results are immutable' USING ERRCODE='23514';
            END IF;
            RETURN NEW;
        END IF;
        RETURN OLD;
    END;
    $$;
    CREATE TRIGGER frozen_execution BEFORE INSERT OR UPDATE OR DELETE ON simulations
    FOR EACH ROW EXECUTE FUNCTION bpt_frozen_execution();
    CREATE TRIGGER frozen_result BEFORE INSERT OR UPDATE OR DELETE ON simulation_results
    FOR EACH ROW EXECUTE FUNCTION bpt_frozen_result();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER frozen_result ON simulation_results")
    op.execute("DROP TRIGGER frozen_execution ON simulations")
    op.execute("DROP FUNCTION bpt_frozen_result()")
    op.execute("DROP FUNCTION bpt_frozen_execution()")
