"""Synthetic real-income data; local revisions and price references only."""

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select

from app.integrations import ibge
from app.modules.indicators import collection
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.users.models import User
from app.seed_indicators import seed

from .test_admin_indicators import administrator

pytestmark = pytest.mark.database


def reference(when, anchor="1234", fingerprint="synthetic-release-a"):
    return {
        "income_price_reference": when.isoformat(),
        "income_price_period": f"Synthetic rolling quarter ending {when.isoformat()}",
        "income_price_anchor_value": anchor,
        "income_price_reference_url": ibge.INCOME_REFERENCE_URL,
        "income_price_method_url": ibge.INCOME_PRICE_METHOD_URL,
        "income_source_modified": when.isoformat(),
        "income_periods_url": ibge.INCOME_PERIODS_URL,
        "income_periods_fingerprint": fingerprint,
        "price_basis": "real_latest_rolling_quarter",
    }


def rows(session):
    return session.scalars(
        select(IndicatorValue)
        .join(Indicator, IndicatorValue.indicator_id == Indicator.id)
        .where(Indicator.code == ibge.INCOME_CODE)
        .order_by(IndicatorValue.reference_date, IndicatorValue.revision)
    ).all()


def actor(auth_client, db_session):
    account = administrator(auth_client, db_session)
    return db_session.get(User, UUID(account["user"]["id"]))


def mock_source(monkeypatch, ref, values):
    calls = []
    monkeypatch.setattr(ibge, "income_price_reference", lambda: dict(ref))

    def fetch(code, start, end):
        assert code == ibge.INCOME_CODE
        calls.append((start, end))
        return (
            [(when, value) for when, value in sorted(values.items()) if start <= when <= end],
            f"https://servicodados.ibge.gov.br/synthetic/{start.isoformat()}",
        )

    monkeypatch.setattr(ibge, "fetch_series", fetch)
    return calls


def test_income_repeated_collection_is_idempotent_and_preserves_own_price_base(
    auth_client, db_session, monkeypatch
):
    user = actor(auth_client, db_session)
    end = datetime.now(UTC).date()
    latest = end.replace(day=1)
    old = date(end.year - 1, 1, 1)
    ref = reference(latest)
    mock_source(monkeypatch, ref, {old: Decimal("1100"), latest: Decimal("1234")})
    first = collection.collect_income(db_session, user, end)
    assert first[ibge.INCOME_CODE] == {"status": "SUCCESS", "observations": 2}
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    ids = {row.id for row in rows(db_session)}
    assert collection.collect_income(db_session, user, end) == first
    assert {row.id for row in rows(db_session)} == ids
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert after["id"] == before["id"]
    assert all(
        row.provenance["income_price_reference"] == latest.isoformat() for row in rows(db_session)
    )


def test_income_rebase_refreshes_stored_history_older_than_three_years_without_rewriting_revisions(
    auth_client, db_session, monkeypatch
):
    user = actor(auth_client, db_session)
    end = datetime.now(UTC).date()
    latest = end.replace(day=1)
    prior_base = (latest - timedelta(days=1)).replace(day=1)
    old = date(end.year - 5, 1, 1)
    provenance = {"collector": "ibge-pnad-income-v1", **reference(prior_base)}
    seed(
        db_session,
        user,
        ibge.INCOME_CODE,
        [(old, Decimal("1000"))],
        "https://servicodados.ibge.gov.br/synthetic-old-income",
        provenance_extra=provenance,
    )
    original = rows(db_session)[0]
    original_id = original.id
    original_provenance = dict(original.provenance)
    calls = mock_source(
        monkeypatch,
        reference(latest, "1234", "synthetic-release-b"),
        {old: Decimal("1100"), latest: Decimal("1234")},
    )
    result = collection.collect_income(db_session, user, end)
    assert result[ibge.INCOME_CODE]["status"] == "SUCCESS"
    assert calls[0][0] == old
    saved = rows(db_session)
    assert len(saved) == 3
    assert db_session.get(IndicatorValue, original_id).value == Decimal("1000")
    assert db_session.get(IndicatorValue, original_id).provenance == original_provenance
    revised = [row for row in saved if row.reference_date == old and row.revision == 2][0]
    assert revised.value == Decimal("1100")
    assert revised.provenance["income_price_reference"] == latest.isoformat()
    assert revised.provenance["income_price_reference"] != old.isoformat()


def test_source_price_anchor_change_during_collection_preserves_previous_income(
    auth_client, db_session, monkeypatch
):
    user = actor(auth_client, db_session)
    end = datetime.now(UTC).date()
    latest = end.replace(day=1)
    ref = reference(latest)
    mock_source(monkeypatch, ref, {latest: Decimal("1234")})
    assert collection.collect_income(db_session, user, end)[ibge.INCOME_CODE]["status"] == "SUCCESS"
    ids = {row.id for row in rows(db_session)}
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    sequence = iter([ref, {**ref, "income_periods_fingerprint": "changed-historical-release"}])
    monkeypatch.setattr(ibge, "income_price_reference", lambda: next(sequence))
    result = collection.collect_income(db_session, user, end)
    assert result[ibge.INCOME_CODE]["status"] == "FAILED"
    assert {row.id for row in rows(db_session)} == ids
    assert (
        auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["id"] == before["id"]
    )


def test_source_omitting_old_stored_month_cannot_mix_income_price_bases(
    auth_client, db_session, monkeypatch
):
    user = actor(auth_client, db_session)
    end = datetime.now(UTC).date()
    latest = end.replace(day=1)
    old = date(end.year - 5, 1, 1)
    seed(
        db_session,
        user,
        ibge.INCOME_CODE,
        [(old, Decimal("1100"))],
        "https://servicodados.ibge.gov.br/synthetic-old-income",
        provenance_extra={"collector": "ibge-pnad-income-v1", **reference(latest)},
    )
    mock_source(monkeypatch, reference(latest), {old: Decimal("1100"), latest: Decimal("1234")})
    assert collection.collect_income(db_session, user, end)[ibge.INCOME_CODE]["status"] == "SUCCESS"
    ids = {row.id for row in rows(db_session)}
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    mock_source(
        monkeypatch,
        reference(latest, "1500", "synthetic-new-release"),
        {latest: Decimal("1500")},
    )
    result = collection.collect_income(db_session, user, end)
    assert result[ibge.INCOME_CODE]["status"] == "FAILED"
    assert {row.id for row in rows(db_session)} == ids
    assert (
        auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["id"] == before["id"]
    )


def test_income_write_failure_rolls_back_all_new_windows(auth_client, db_session, monkeypatch):
    user = actor(auth_client, db_session)
    end = datetime.now(UTC).date()
    latest = end.replace(day=1)
    prior = date(end.year - 1, 1, 1)
    mock_source(monkeypatch, reference(latest), {prior: Decimal("1100"), latest: Decimal("1234")})
    real_seed = collection.seed
    writes = []

    def fail_on_second_window(*args, **kwargs):
        writes.append(args[4])
        if len(writes) == 2:
            raise RuntimeError("Synthetic database failure")
        return real_seed(*args, **kwargs)

    monkeypatch.setattr(collection, "seed", fail_on_second_window)
    result = collection.collect_income(db_session, user, end)
    assert result[ibge.INCOME_CODE]["status"] == "FAILED"
    assert len(writes) == 2 and rows(db_session) == []
