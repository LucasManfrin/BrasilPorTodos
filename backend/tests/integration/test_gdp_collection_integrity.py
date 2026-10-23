"""Regression tests for truncated GDP responses using synthetic isolated data."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.integrations.gdp import GDP_CODE
from app.modules.indicators import collection
from app.modules.indicators.models import Indicator, IndicatorValue

from .test_fiscal_baseline import seed_closed_year
from .test_gdp_baseline import seed_gdp_year

pytestmark = pytest.mark.database


def bundle(year, months):
    return {
        "observations": [(date(year, month, 1), Decimal("260000.00")) for month in months],
        "request_url": "https://apisidra.ibge.gov.br/synthetic-gdp-test",
    }


def observation_ids(session):
    return set(
        session.scalars(
            select(IndicatorValue.id)
            .join(Indicator, Indicator.id == IndicatorValue.indicator_id)
            .where(Indicator.code == GDP_CODE)
        )
    )


def test_truncated_closed_year_response_preserves_previously_available_gdp_and_all_batch_data(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    seed_gdp_year(db_session, user, year)
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    ids_before = observation_ids(db_session)
    end = datetime.now(UTC).date()
    calls = []

    def fetch(requested_year, until):
        calls.append(requested_year)
        if requested_year == year:
            return bundle(year, (1, 4, 7))
        if requested_year == year - 1:
            return bundle(year - 1, (1, 4, 7, 10))
        if requested_year == end.year:
            return bundle(end.year, (1,))
        return bundle(requested_year, ())

    seeded = []
    real_seed = collection.seed

    def tracked_seed(*args, **kwargs):
        seeded.append(args[2])
        return real_seed(*args, **kwargs)

    monkeypatch.setattr(collection.gdp, "fetch_year", fetch)
    monkeypatch.setattr(collection, "seed", tracked_seed)
    result = collection.collect_gdp(db_session, user, end)
    assert result[GDP_CODE]["status"] == "FAILED"
    assert len(calls) == 6 and not seeded
    assert observation_ids(db_session) == ids_before
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert after["id"] == before["id"] and after["fiscal"] == before["fiscal"]
    assert after["fiscal"]["gdp"]["status"] == "AVAILABLE"


def test_initial_partial_closed_year_and_current_year_remain_observations_without_denominator(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    end = datetime.now(UTC).date()

    def fetch(requested_year, until):
        if requested_year == year:
            return bundle(year, (1, 4, 7))
        if requested_year == end.year:
            return bundle(end.year, (1,))
        return bundle(requested_year, ())

    monkeypatch.setattr(collection.gdp, "fetch_year", fetch)
    result = collection.collect_gdp(db_session, user, end)
    assert result[GDP_CODE] == {"status": "SUCCESS", "observations": 4}
    assert len(observation_ids(db_session)) == 4
    fiscal = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["fiscal"]
    assert fiscal["status"] == "AVAILABLE"
    assert fiscal["gdp"]["status"] == "INCOMPLETE"
    assert fiscal["gdp"]["nominal_gdp"] is None and fiscal["ratios"] is None
    indicator = db_session.scalar(select(Indicator).where(Indicator.code == GDP_CODE))
    records = db_session.scalars(
        select(IndicatorValue).where(IndicatorValue.indicator_id == indicator.id)
    ).all()
    assert all(row.value == Decimal("260000.00") for row in records)
    assert {row.reference_date for row in records} == {
        date(year, 1, 1),
        date(year, 4, 1),
        date(year, 7, 1),
        date(end.year, 1, 1),
    }


def test_empty_response_preserves_cached_full_year_without_fabricating_observations(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    seed_gdp_year(db_session, user, year)
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    ids_before = observation_ids(db_session)
    monkeypatch.setattr(collection.gdp, "fetch_year", lambda year, end: bundle(year, ()))
    result = collection.collect_gdp(db_session, user, datetime.now(UTC).date())
    assert result[GDP_CODE]["status"] == "NO_DATA"
    assert observation_ids(db_session) == ids_before
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert after["id"] == before["id"] and after["fiscal"] == before["fiscal"]
