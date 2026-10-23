from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from app.core.errors import DomainError
from app.modules.indicators import collection
from app.modules.indicators.collection import CollectionRun
from app.modules.users.models import User

from .test_admin_indicators import administrator
from .test_plans import create_plan
from .test_policies import draft, headers

pytestmark = pytest.mark.database


def test_database_lock_cooldown_and_failed_source_preserve_previous_data(
    auth_client, db_session, monkeypatch
):
    actor = administrator(auth_client, db_session)
    user = db_session.get(User, actor["user"]["id"])
    calls = []

    def fetch(code, start, end):
        calls.append(code)
        if code == "divida-liquida-pib":
            raise ValueError("Simulated source outage")
        return [(start, "1")], "https://api.bcb.gov.br/test"

    monkeypatch.setattr(collection.bcb, "fetch_series", fetch)
    monkeypatch.setattr(collection.ibge, "fetch_series", fetch)
    monkeypatch.setattr(
        collection,
        "collect_income",
        lambda *args: {collection.ibge.INCOME_CODE: {"status": "NO_DATA"}},
    )
    monkeypatch.setattr(collection.treasury, "fetch_bundle", lambda *args: {})
    monkeypatch.setattr(
        collection.gdp,
        "fetch_year",
        lambda *args: {"observations": [], "request_url": "https://apisidra.ibge.gov.br/test"},
    )
    from decimal import Decimal

    from app.modules.indicators.models import Indicator, IndicatorValue

    collection.seed(
        db_session,
        user,
        "divida-liquida-pib",
        [(datetime.now(UTC).date().replace(day=1), "123")],
        "https://api.bcb.gov.br/test",
    )
    result = collection.collect(db_session, user, ignore_cooldown=True)
    assert result["last_run"]["status"] == "PARTIAL"
    assert result["last_run"]["series"]["divida-liquida-pib"]["status"] == "FAILED"
    definition = db_session.scalar(select(Indicator).where(Indicator.code == "divida-liquida-pib"))
    saved = db_session.scalars(
        select(IndicatorValue).where(IndicatorValue.indicator_id == definition.id)
    ).all()
    assert len(saved) == 1 and saved[0].value == Decimal("123")
    attempts = len(calls)
    assert collection.collect(db_session, user, manual=True)["skipped"]
    assert len(calls) == attempts
    with collection.get_engine().connect() as owner:
        owner.exec_driver_sql("SELECT pg_advisory_lock(82461301)")
        try:
            with pytest.raises(DomainError, match="COLLECTION_RUNNING"):
                collection.collect(db_session, user, ignore_cooldown=True)
        finally:
            owner.exec_driver_sql("SELECT pg_advisory_unlock(82461301)")
    assert len(list(db_session.scalars(select(CollectionRun)))) == 1


def test_only_admin_requests_refresh_and_request_returns_before_network(
    auth_client, db_session, monkeypatch
):
    actor = administrator(auth_client, db_session)
    calls = []
    monkeypatch.setattr(
        collection, "run_requested_collection", lambda actor_id: calls.append(actor_id)
    )
    assert auth_client.post("/api/v1/admin/indicators/collect").status_code == 401
    response = auth_client.post("/api/v1/admin/indicators/collect", headers=headers(actor))
    assert response.status_code == 200 and response.json()["data"]["accepted"]
    assert len(calls) == 1
    db_session.add(
        CollectionRun(
            actor_id=actor["user"]["id"],
            status="SUCCESS",
            results={},
            finished_at=datetime.now(UTC),
        )
    )
    db_session.commit()
    skipped = auth_client.post("/api/v1/admin/indicators/collect", headers=headers(actor)).json()[
        "data"
    ]
    assert skipped["skipped"] and not skipped["accepted"] and len(calls) == 1


def test_production_hides_examples_from_detail_history_sources_and_counts(auth_client, db_session):
    actor = administrator(auth_client, db_session)
    proposal, source = draft(auth_client, actor)
    proposal = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/publish", headers=headers(actor)
    ).json()["data"]
    plan = create_plan(auth_client, actor, [proposal])
    plan = auth_client.post(f"/api/v1/plans/{plan['id']}/publish", headers=headers(actor)).json()[
        "data"
    ]
    from app.modules.plans.models import Plan
    from app.modules.policies.models import Policy

    db_session.get(Policy, proposal["id"]).is_example = True
    db_session.get(Plan, plan["id"]).is_example = True
    db_session.commit()
    assert auth_client.get("/api/v1/policies").json()["data"] == []
    assert auth_client.get(f"/api/v1/policies/{proposal['slug']}").status_code == 404
    assert auth_client.get(f"/api/v1/policies/{proposal['slug']}/versions").status_code == 404
    assert auth_client.get("/api/v1/plans").json()["data"] == []
    assert auth_client.get(f"/api/v1/plans/{plan['slug']}").status_code == 404
    assert auth_client.get("/api/v1/sources").json()["data"] == []
