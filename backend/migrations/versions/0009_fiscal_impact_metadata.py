"""Add declared fiscal metadata without inferring metadata in historical publications."""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

CONSTRAINTS = {
    "fiscal_scope": "fiscal_scope IN ('CENTRAL_GOVERNMENT','GENERAL_GOVERNMENT','STATE','MUNICIPAL','OTHER','UNSPECIFIED')",
    "accounting_basis": "accounting_basis IN ('CASH','ACCRUAL','UNSPECIFIED')",
    "price_basis": "price_basis IN ('NOMINAL','CONSTANT','UNSPECIFIED')",
    "component": "component IN ('PRIMARY','INTEREST','UNSPECIFIED')",
    "period_basis": "period_basis IN ('FULL_YEAR','PARTIAL_YEAR','UNSPECIFIED')",
    "price_reference": "(price_basis = 'CONSTANT' AND price_base_year IS NOT NULL AND price_base_year BETWEEN 1900 AND 2200) OR (price_basis <> 'CONSTANT' AND price_base_year IS NULL)",
}


def upgrade():
    for field, length in (
        ("fiscal_scope", 20),
        ("accounting_basis", 12),
        ("price_basis", 12),
        ("component", 12),
        ("period_basis", 12),
    ):
        op.add_column(
            "financial_impacts",
            sa.Column(field, sa.String(length), nullable=False, server_default="UNSPECIFIED"),
        )
    op.add_column("financial_impacts", sa.Column("price_base_year", sa.Integer(), nullable=True))
    for name, condition in CONSTRAINTS.items():
        op.create_check_constraint(
            op.f(f"ck_financial_impacts_{name}"), "financial_impacts", condition
        )


def downgrade():
    for name in reversed(CONSTRAINTS):
        op.drop_constraint(op.f(f"ck_financial_impacts_{name}"), "financial_impacts", type_="check")
    for field in (
        "price_base_year",
        "period_basis",
        "component",
        "price_basis",
        "accounting_basis",
        "fiscal_scope",
    ):
        op.drop_column("financial_impacts", field)
