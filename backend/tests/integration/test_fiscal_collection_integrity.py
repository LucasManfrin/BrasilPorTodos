"""Synthetic sources and fiscal values; isolated PostgreSQL rollback only."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select

from app.integrations.treasury import SOURCE_URL, TREASURY_SERIES
from app.modules.indicators import collection
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.sources.models import Source
from app.modules.users.models import User

from .test_admin_indicators import administrator
from .test_auth import signup
from .test_fiscal_baseline import seed_closed_year

pytestmark = pytest.mark.database


def synthetic_bundle(year, revenue="1100.10", expenditure="750.01"):
    values = {
        "rtn-receita-liquida": Decimal(revenue),
        "rtn-despesa-primaria": Decimal(expenditure),
        "rtn-resultado-primario": Decimal(revenue) - Decimal(expenditure),
    }
    return {
        code: {
            "observations": [(date(year, month, 1), value) for month in range(1, 13)],
            "request_url": "https://apiapex.tesouro.gov.br/synthetic-unit-test",
        }
        for code, value in values.items()
    }


def mock_fiscal_window(monkeypatch, year):
    calls = []

    def fetch(start, end):
        calls.append(start.year)
        return synthetic_bundle(year) if start.year == year else {}

    monkeypatch.setattr(collection.treasury, "fetch_bundle", fetch)
    return calls


def record_ids(session):
    return set(
        session.scalars(
            select(IndicatorValue.id)
            .join(Indicator, IndicatorValue.indicator_id == Indicator.id)
            .where(Indicator.code.in_(TREASURY_SERIES))
        )
    )


@pytest.mark.parametrize("private_source_type", ["OFFICIAL", "OTHER"])
def test_collector_does_not_publish_another_users_private_source_with_same_official_url(
    auth_client, db_session, monkeypatch, private_source_type
):
    private_actor, _ = signup(auth_client)
    private_source = Source(
        created_by=UUID(private_actor["user"]["id"]),
        title="Título privado que não pode sair do rascunho",
        institution="Secretaria do Tesouro Nacional",
        url=SOURCE_URL,
        source_type=private_source_type,
        accessed_at=datetime.now(UTC).date(),
        description="Descrição confidencial não publicada pelo autor",
    )
    db_session.add(private_source)
    db_session.commit()
    private_id = private_source.id
    private_title = private_source.title
    private_description = private_source.description
    actor = administrator(auth_client, db_session)
    user = db_session.get(User, UUID(actor["user"]["id"]))
    end = datetime.now(UTC).date()
    mock_fiscal_window(monkeypatch, end.year - 1)
    results = collection.collect_fiscal(db_session, user, end)
    assert all(result["status"] == "SUCCESS" for result in results.values())
    assert not db_session.scalar(
        select(IndicatorValue.id).where(IndicatorValue.source_id == private_id).limit(1)
    )
    public = auth_client.get("/api/v1/sources")
    assert public.status_code == 200
    assert private_title not in public.text and private_description not in public.text
    assert str(private_id) not in {row["id"] for row in public.json()["data"]}
    assert auth_client.get(f"/api/v1/sources/{private_id}").status_code == 404
    baseline = auth_client.get("/api/v1/indicators/baseline/current")
    assert baseline.status_code == 200
    assert private_title not in baseline.text and private_description not in baseline.text
    assert baseline.json()["data"]["fiscal"]["status"] == "AVAILABLE"
    assert all(
        row["source"]["id"] != str(private_id)
        for month in baseline.json()["data"]["fiscal"]["months"]
        for row in month["observations"]
    )


def test_fiscal_collection_failure_after_first_series_rolls_back_new_revisions(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    ids_before = record_ids(db_session)
    calls = mock_fiscal_window(monkeypatch, year)
    real_seed = collection.seed
    seeded = []

    def fail_on_second_series(*args, **kwargs):
        seeded.append(args[2])
        if len(seeded) == 2:
            raise RuntimeError("Synthetic persistence failure after receipts")
        return real_seed(*args, **kwargs)

    monkeypatch.setattr(collection, "seed", fail_on_second_series)
    results = collection.collect_fiscal(db_session, user, datetime.now(UTC).date())
    assert all(result["status"] == "FAILED" for result in results.values())
    assert seeded == ["rtn-receita-liquida", "rtn-despesa-primaria"]
    assert len(calls) == 6
    assert record_ids(db_session) == ids_before
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert after["id"] == before["id"] and after["fiscal"] == before["fiscal"]
    assert after["fiscal"]["status"] == "AVAILABLE"


def test_repeated_fiscal_collection_keeps_observation_ids_and_context_hash(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    mock_fiscal_window(monkeypatch, year)
    end = datetime.now(UTC).date()
    first = collection.collect_fiscal(db_session, user, end)
    assert all(result["status"] == "SUCCESS" for result in first.values())
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    ids_before = record_ids(db_session)
    second = collection.collect_fiscal(db_session, user, end)
    assert second == first
    assert record_ids(db_session) == ids_before
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert after["id"] == before["id"] and after["fiscal"] == before["fiscal"]


def test_upstream_failure_after_fetched_year_preserves_observations_and_fiscal_reference(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    ids_before = record_ids(db_session)
    end = datetime.now(UTC).date()
    calls = []

    def fetch(start, until):
        calls.append(start.year)
        if len(calls) == 2:
            raise TimeoutError("Synthetic upstream outage")
        return synthetic_bundle(start.year)

    def forbidden_seed(*args, **kwargs):
        raise AssertionError("No writes before the complete fiscal window is fetched")

    monkeypatch.setattr(collection.treasury, "fetch_bundle", fetch)
    monkeypatch.setattr(collection, "seed", forbidden_seed)
    results = collection.collect_fiscal(db_session, user, end)
    assert all(result["status"] == "FAILED" for result in results.values())
    assert len(calls) == 2
    assert record_ids(db_session) == ids_before
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert after["id"] == before["id"] and after["fiscal"] == before["fiscal"]
    assert after["fiscal"]["year"] == year
