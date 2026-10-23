"""Invented RTN values and isolated PostgreSQL rollback; never call the provider."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select

from app.integrations import treasury
from app.integrations import treasury_composition as provider
from app.modules.indicators import collection
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.sources.models import Source

from .test_auth import signup
from .test_fiscal_baseline import seed_closed_year, seed_month
from .test_plans import create_plan
from .test_policies import draft, headers

pytestmark = pytest.mark.database


def bundle(year, change=False):
    values = dict(
        zip(
            provider.ALL_SERIES,
            map(
                Decimal,
                (
                    "1000.10",
                    "750.01",
                    "250.09",
                    "1100.10",
                    "100.00",
                    "800.00",
                    "-1.00",
                    "200.00",
                    "101.10",
                    "300.00",
                    "200.00",
                    "100.00",
                    "150.01",
                ),
            ),
            strict=True,
        )
    )
    rows = {}
    for code, value in values.items():
        rows[code] = {
            "observations": [
                (
                    date(year, month, 1),
                    value
                    + (
                        Decimal("1.00")
                        if change and month == 1 and code == "rtn-receita-rfb"
                        else Decimal("-1.00")
                        if change and month == 1 and code == "rtn-receitas-nao-administradas"
                        else Decimal("0.00")
                    ),
                )
                for month in range(1, 13)
            ],
            "request_url": "https://apiapex.tesouro.gov.br/test-only-composition",
        }
    return rows


def import_composition(session, user, year, monkeypatch, *, change=False):
    monkeypatch.setattr(provider, "fetch_year", lambda requested, end: bundle(year, change))
    return collection.collect_composition(session, user, datetime.now(UTC).date())


def ids(session):
    return set(
        session.scalars(
            select(IndicatorValue.id)
            .join(Indicator)
            .where(Indicator.code.in_(provider.COMPOSITION_SERIES))
        )
    )


def test_separate_composition_preserves_catalog_context_published_snapshots_and_incremental_result(
    auth_client, db_session, monkeypatch
):
    actor, user, year = seed_closed_year(auth_client, db_session)
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    catalog_before = auth_client.get("/api/v1/indicators?page_size=100").json()
    proposal, _ = draft(auth_client, actor)
    proposal = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/publish", headers=headers(actor)
    ).json()["data"]
    plan = create_plan(auth_client, actor, [proposal])
    plan = auth_client.post(f"/api/v1/plans/{plan['id']}/publish", headers=headers(actor)).json()[
        "data"
    ]
    assert (
        import_composition(db_session, user, year, monkeypatch)["rtn-composition"]["status"]
        == "SUCCESS"
    )
    response = auth_client.get("/api/v1/indicators/baseline/composition")
    assert response.status_code == 200
    composition = response.json()["data"]
    assert composition["status"] == "AVAILABLE" and composition["year"] == year
    assert composition["totals"]["gross_revenue"] == "13201.20"
    assert len(composition["months"]) == 12 and len(ids(db_session)) == 120
    assert "email" not in response.text and "password_hash" not in response.text
    assert auth_client.get("/api/v1/indicators?page_size=100").json() == catalog_before
    admin_codes = {
        row["code"]
        for row in auth_client.get(
            "/api/v1/admin/indicators?page_size=100", headers=headers(actor)
        ).json()["data"]
    }
    assert set(provider.COMPOSITION_SERIES).issubset(admin_codes)
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert before["id"] == after["id"] and before["fiscal"] == after["fiscal"]
    assert auth_client.get(f"/api/v1/policies/{proposal['slug']}").json()["data"] == proposal
    assert auth_client.get(f"/api/v1/plans/{plan['slug']}").json()["data"] == plan
    saved_ids = ids(db_session)
    import_composition(db_session, user, year, monkeypatch)
    assert ids(db_session) == saved_ids
    assert auth_client.get("/api/v1/indicators/baseline/composition").json()["data"] == composition


def test_component_only_revision_updates_cohort_without_altering_historical_triple_or_hash(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    import_composition(db_session, user, year, monkeypatch)
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    original = auth_client.get("/api/v1/indicators/baseline/composition").json()["data"]
    assert (
        import_composition(db_session, user, year, monkeypatch, change=True)["rtn-composition"][
            "status"
        ]
        == "SUCCESS"
    )
    revised = auth_client.get("/api/v1/indicators/baseline/composition").json()["data"]
    assert revised["status"] == "AVAILABLE"
    assert revised["totals"] == original["totals"]
    assert revised["revenue"][0]["amount"] != original["revenue"][0]["amount"]
    assert len(ids(db_session)) == 130
    assert all(row["revision"] == 2 for row in revised["months"][0]["observations"])
    assert (
        auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["id"] == before["id"]
    )


@pytest.mark.parametrize("failure", ["persistence", "truncated", "outage", "anchor_mismatch"])
def test_failed_fetch_or_partial_write_rolls_back_and_preserves_previous_composition(
    auth_client, db_session, monkeypatch, failure
):
    _, user, year = seed_closed_year(auth_client, db_session)
    import_composition(db_session, user, year, monkeypatch)
    before = auth_client.get("/api/v1/indicators/baseline/composition").json()["data"]
    baseline = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    saved_ids = ids(db_session)
    data = bundle(year, True)
    if failure == "truncated":
        for item in data.values():
            item["observations"] = item["observations"][:-1]
    if failure == "anchor_mismatch":
        data["rtn-receita-liquida"]["observations"][0] = (date(year, 1, 1), Decimal("1001.10"))
        data["rtn-resultado-primario"]["observations"][0] = (date(year, 1, 1), Decimal("251.09"))
        data["rtn-receita-bruta"]["observations"][0] = (date(year, 1, 1), Decimal("1101.10"))
        data["rtn-receita-rfb"]["observations"][0] = (date(year, 1, 1), Decimal("802.00"))

    def fetch(*args):
        if failure == "outage":
            raise TimeoutError("Synthetic provider outage")
        return data

    monkeypatch.setattr(provider, "fetch_year", fetch)
    original_seed = collection.seed
    writes = []

    def seed(*args, **kwargs):
        writes.append(args[2])
        if failure == "persistence" and len(writes) == 2:
            raise RuntimeError("Synthetic failure after first write")
        return original_seed(*args, **kwargs)

    monkeypatch.setattr(collection, "seed", seed)
    result = collection.collect_composition(db_session, user, datetime.now(UTC).date())
    assert result["rtn-composition"]["status"] == "FAILED"
    assert ids(db_session) == saved_ids
    assert auth_client.get("/api/v1/indicators/baseline/composition").json()["data"] == before
    assert (
        auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["id"]
        == baseline["id"]
    )
    if failure != "persistence":
        assert writes == []


def test_revised_historical_anchor_blocks_old_component_cohort_without_falling_back(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    import_composition(db_session, user, year, monkeypatch)
    saved_ids = ids(db_session)
    seed_month(db_session, user, date(year, 1, 1), revenue="1001.10")
    result = auth_client.get("/api/v1/indicators/baseline/composition").json()["data"]
    assert result["status"] == "INCOMPLETE" and result["totals"] is None
    assert result["reference_amounts"]["net_revenue"] == "12002.20"
    assert ids(db_session) == saved_ids


def test_same_official_url_cannot_promote_another_users_private_source(
    auth_client, db_session, monkeypatch
):
    private_actor, _ = signup(auth_client)
    source = Source(
        created_by=UUID(private_actor["user"]["id"]),
        title="Confidential private source",
        institution="Secretaria do Tesouro Nacional",
        url=treasury.SOURCE_URL,
        source_type="OFFICIAL",
        accessed_at=datetime.now(UTC).date(),
        description="Confidential draft metadata",
    )
    db_session.add(source)
    db_session.commit()
    private_id = source.id
    _, user, year = seed_closed_year(auth_client, db_session)
    assert (
        import_composition(db_session, user, year, monkeypatch)["rtn-composition"]["status"]
        == "SUCCESS"
    )
    response = auth_client.get("/api/v1/indicators/baseline/composition")
    assert response.json()["data"]["status"] == "AVAILABLE"
    assert "Confidential" not in response.text and str(private_id) not in response.text
    assert auth_client.get(f"/api/v1/sources/{private_id}").status_code == 404
    assert not db_session.scalar(
        select(IndicatorValue.id).where(IndicatorValue.source_id == private_id)
    )
