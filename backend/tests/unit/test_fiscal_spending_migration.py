"""Compile only the new migration offline; no database connection or schema writes."""

from importlib.util import module_from_spec, spec_from_file_location
from io import StringIO
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.database.base import Base
from app.database.models import FiscalSpendingCohort


def test_offline_cohort_migration_matches_named_constraints_and_is_append_only():
    path = (
        Path(__file__).resolve().parents[2] / "migrations/versions/0011_fiscal_spending_cohort.py"
    )
    spec = spec_from_file_location("new_spending_migration", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    output = StringIO()
    context = MigrationContext.configure(
        dialect_name="postgresql",
        opts={
            "as_sql": True,
            "output_buffer": output,
            "target_metadata": Base.metadata,
        },
    )
    with Operations.context(context):
        module.upgrade()
    ddl = output.getvalue()
    for constraint in FiscalSpendingCohort.__table__.constraints:
        assert f"CONSTRAINT {constraint.name} " in ddl
    assert "ck_fiscal_spending_cohorts_ck_" not in ddl
    assert "BEFORE UPDATE OR DELETE ON fiscal_spending_cohorts" in ddl
    assert "EXECUTE FUNCTION bpt_append_only()" in ddl
    with Operations.context(context):
        module.downgrade()
    assert "DROP FUNCTION" not in output.getvalue()
