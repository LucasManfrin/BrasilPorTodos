"""Nominal GDP compatibility and publication snapshots in isolated PostgreSQL."""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.integrations.gdp import GDP_CODE, year_fingerprint
from app.modules.indicators.models import Indicator, IndicatorValue
from app.seed_indicators import seed

from .test_fiscal_baseline import seed_closed_year, seed_month
from .test_plans import create_plan
from .test_policies import draft, headers

pytestmark = pytest.mark.database


def seed_gdp_year(session, user, year, quarter_values=None, months=(1, 4, 7, 10)):
    values = {
        date(year, month, 1): Decimal(value)
        for month, value in zip(
            months,
            quarter_values or ("250000.00",) * len(months),
            strict=True,
        )
    }
    provenance = {
        "collector": "ibge-cnt-gdp-v1",
        "original_unit": "Milhões de Reais",
        "scale": "1000000",
        "series": "585",
        "aggregation": "sum_four_quarters_cnt",
        "source_precision": "0.01_million_brl",
        "annual_fingerprint": year_fingerprint(year, values),
    }
    seed(
        session,
        user,
        GDP_CODE,
        list(values.items()),
        "https://apisidra.ibge.gov.br/test-only",
        provenance_extra=provenance,
        commit=False,
    )
    session.commit()


def test_same_year_nominal_gdp_produces_exact_fiscal_percentages(auth_client, db_session):
    _, user, year = seed_closed_year(auth_client, db_session)
    seed_gdp_year(db_session, user, year)
    response = auth_client.get("/api/v1/indicators/baseline/current")
    assert response.status_code == 200
    fiscal = response.json()["data"]["fiscal"]
    assert fiscal["year"] == fiscal["gdp"]["year"] == year
    assert fiscal["gdp"]["status"] == "AVAILABLE"
    assert fiscal["gdp"]["nominal_gdp"] == "1000000.00"
    assert fiscal["ratios"] == {
        "net_revenue_pct_gdp": "1.2001",
        "primary_expenditure_pct_gdp": "0.9000",
        "primary_balance_pct_gdp": "0.3001",
    }
    assert len(fiscal["gdp"]["quarters"]) == 4
    assert "Governo Central" in fiscal["scope"]
    assert any("nacional" in item for item in fiscal["gdp"]["limitations"])


def test_negative_observed_primary_balance_keeps_its_sign_as_percent_of_gdp(
    auth_client, db_session
):
    _, user, year = seed_closed_year(auth_client, db_session)
    for month in range(1, 13):
        seed_month(db_session, user, date(year, month, 1), revenue="100.00")
    seed_gdp_year(db_session, user, year)
    fiscal = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["fiscal"]
    assert fiscal["amounts"]["published_primary_balance"] == "-7800.12"
    assert fiscal["ratios"]["primary_balance_pct_gdp"] == "-0.7800"
    assert fiscal["ratios"]["net_revenue_pct_gdp"] == "0.1200"


def test_older_or_current_year_to_date_gdp_is_not_used_for_closed_fiscal_year(
    auth_client, db_session
):
    _, user, year = seed_closed_year(auth_client, db_session)
    seed_gdp_year(db_session, user, year - 1)
    seed_gdp_year(db_session, user, year + 1, months=(1,))
    fiscal = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["fiscal"]
    assert fiscal["status"] == "AVAILABLE" and fiscal["year"] == year
    assert fiscal["gdp"]["status"] == "EMPTY"
    assert fiscal["gdp"]["nominal_gdp"] is None and fiscal["ratios"] is None


def test_three_quarters_do_not_become_an_annual_denominator(auth_client, db_session):
    _, user, year = seed_closed_year(auth_client, db_session)
    seed_gdp_year(db_session, user, year, months=(1, 4, 7))
    fiscal = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["fiscal"]
    assert fiscal["status"] == "AVAILABLE"
    assert fiscal["gdp"]["status"] == "INCOMPLETE"
    assert fiscal["gdp"]["nominal_gdp"] is None and fiscal["ratios"] is None


def test_atomic_gdp_release_changes_current_hash_but_preserves_published_snapshots(
    auth_client, db_session
):
    actor, user, year = seed_closed_year(auth_client, db_session)
    seed_gdp_year(db_session, user, year)
    policy, _ = draft(auth_client, actor)
    frozen = policy["version"]["baseline_snapshot"]
    policy = auth_client.post(
        f"/api/v1/policies/{policy['id']}/publish", headers=headers(actor)
    ).json()["data"]
    plan = create_plan(auth_client, actor, [policy])
    published = auth_client.post(
        f"/api/v1/plans/{plan['id']}/publish", headers=headers(actor)
    ).json()["data"]
    original_result = published["version"]["simulation"]
    seed_gdp_year(
        db_session,
        user,
        year,
        quarter_values=("260000.00", "250000.00", "250000.00", "250000.00"),
    )
    current = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert current["id"] != frozen["id"]
    assert current["fiscal"]["gdp"]["nominal_gdp"] == "1010000.00"
    assert current["fiscal"]["ratios"]["primary_balance_pct_gdp"] == "0.2971"
    assert (
        auth_client.get(f"/api/v1/policies/{policy['slug']}").json()["data"]["version"][
            "baseline_snapshot"
        ]
        == frozen
    )
    assert auth_client.get(f"/api/v1/plans/{plan['slug']}").json()["data"] == published
    repeated = auth_client.post(
        f"/api/v1/plans/{plan['id']}/simulate", headers=headers(actor)
    ).json()["data"]
    assert repeated["input_hash"] == original_result["input_hash"]
    assert repeated["cumulative_impact"] == original_result["cumulative_impact"] == "-100.10"
    assert (
        repeated["input_snapshot"]["baseline_snapshot"]["fiscal"]["gdp"] == frozen["fiscal"]["gdp"]
    )
    indicator = db_session.scalar(select(Indicator).where(Indicator.code == GDP_CODE))
    rows = db_session.scalars(
        select(IndicatorValue).where(IndicatorValue.indicator_id == indicator.id)
    ).all()
    assert len(rows) == 8
    assert sum(row.revision == 2 for row in rows) == 4
