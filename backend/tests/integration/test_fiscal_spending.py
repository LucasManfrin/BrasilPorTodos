"""Invented functional spending in the exclusive PostgreSQL rollback transaction."""

from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.integrations import federal_spending as provider
from app.modules.indicators import collection, fiscal_baseline, fiscal_spending
from app.modules.indicators.models import FiscalSpendingCohort, Indicator, IndicatorValue
from app.modules.sources.models import Source
from app.modules.users.models import User
from tests.federal_spending_fixture import payload

from .test_auth import signup
from .test_fiscal_baseline import seed_closed_year, seed_month
from .test_plans import create_plan
from .test_policies import draft, headers

pytestmark = pytest.mark.database
ENDPOINT = "/api/v1/indicators/spending/functions"


def collect(session, user, year, monkeypatch, **values):
    data = payload(year, **values)
    monkeypatch.setattr(provider, "fetch_year", lambda requested, end: deepcopy(data))
    result = collection.collect_spending(session, user, datetime.now(UTC).date())
    assert result["federal-spending"]["status"] == "SUCCESS", result
    return result


def rows(session):
    return list(
        session.scalars(select(FiscalSpendingCohort).order_by(FiscalSpendingCohort.revision))
    )


def test_public_read_idempotence_and_separate_persistence_preserve_context_catalog_and_motor(
    auth_client, db_session, monkeypatch
):
    actor, user, year = seed_closed_year(auth_client, db_session)
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    fiscal = auth_client.get("/api/v1/indicators/baseline/fiscal").json()["data"]
    catalog = auth_client.get("/api/v1/indicators?page_size=100").json()
    counts = [
        db_session.scalar(select(func.count()).select_from(model))
        for model in (Indicator, IndicatorValue)
    ]
    policy, _ = draft(auth_client, actor)
    policy = auth_client.post(
        f"/api/v1/policies/{policy['id']}/publish", headers=headers(actor)
    ).json()["data"]
    plan = create_plan(auth_client, actor, [policy])
    plan = auth_client.post(f"/api/v1/plans/{plan['id']}/publish", headers=headers(actor)).json()[
        "data"
    ]
    assert plan["version"]["simulation"]["cumulative_impact"] == "-100.10"
    collect(db_session, user, year, monkeypatch)
    response = auth_client.get(ENDPOINT)
    data = response.json()["data"]
    assert response.status_code == 200 and data["status"] == "AVAILABLE"
    assert data["year"] == year and data["revision"] == 1
    assert data["payload"]["totals"] == {
        "PAID": "1201.20",
        "RAP_PAID": "120.12",
        "TOTAL_PAID": "1321.32",
    }
    assert len(data["payload"]["months"]) == 12
    for private in ("password_hash", "email", "created_by", "source_id", str(user.id)):
        assert private not in response.text
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert {key: value for key, value in after.items() if key != "captured_at"} == {
        key: value for key, value in before.items() if key != "captured_at"
    }
    assert auth_client.get("/api/v1/indicators/baseline/fiscal").json()["data"] == fiscal
    assert auth_client.get("/api/v1/indicators?page_size=100").json() == catalog
    assert [
        db_session.scalar(select(func.count()).select_from(model))
        for model in (Indicator, IndicatorValue)
    ] == counts
    assert auth_client.get(f"/api/v1/policies/{policy['slug']}").json()["data"] == policy
    assert auth_client.get(f"/api/v1/plans/{plan['slug']}").json()["data"] == plan
    saved = rows(db_session)[0]
    saved_identity = (saved.id, saved.retrieved_at, saved.payload, saved.source_snapshot)
    collect(db_session, user, year, monkeypatch)
    assert len(rows(db_session)) == 1
    assert (saved.id, saved.retrieved_at, saved.payload, saved.source_snapshot) == saved_identity
    assert auth_client.get(ENDPOINT).json()["data"] == data


def test_new_file_revision_is_whole_cohort_and_old_file_cannot_revert_latest(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    first = deepcopy(rows(db_session)[0].payload)
    first_source = rows(db_session)[0].source_id
    collect(db_session, user, year, monkeypatch, paid="-100.10", tag="new-file")
    data = auth_client.get(ENDPOINT).json()["data"]
    assert data["status"] == "AVAILABLE" and data["revision"] == 2
    assert data["payload"]["totals"]["PAID"] == "-1201.20"
    assert rows(db_session)[0].payload == first and rows(db_session)[1].source_id == first_source
    monkeypatch.setattr(provider, "fetch_year", lambda *args: first)
    result = collection.collect_spending(db_session, user, datetime.now(UTC).date())
    assert result["federal-spending"]["status"] == "FAILED" and len(rows(db_session)) == 2
    assert auth_client.get(ENDPOINT).json()["data"] == data


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_cohort_immutable_in_postgresql_even_for_direct_sql(
    auth_client, db_session, monkeypatch, operation
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    row = rows(db_session)[0]
    command = (
        "UPDATE fiscal_spending_cohorts SET revision=2 WHERE id=:id"
        if operation == "UPDATE"
        else "DELETE FROM fiscal_spending_cohorts WHERE id=:id"
    )
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(text(command), {"id": row.id})
    assert auth_client.get(ENDPOINT).json()["data"]["revision"] == 1


@pytest.mark.parametrize("failure", ["hash", "reconciliation", "precision"])
def test_latest_incompatible_revision_never_falls_back_to_older_valid_cohort(
    auth_client, db_session, monkeypatch, failure
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    first = rows(db_session)[0]
    data = deepcopy(first.payload)
    data["resource"]["sha256"] = "f" * 64
    if failure == "reconciliation":
        data["months"][0]["groups"][0]["amounts"]["PAID"] = "123.00"
    if failure == "precision":
        data["precision_version"] = "unsupported"
    data["fingerprint"] = provider.fingerprint(data)
    new = FiscalSpendingCohort(
        year=year,
        revision=2,
        source_id=first.source_id,
        created_by=user.id,
        retrieved_at=datetime.now(UTC),
        source_hash=data["resource"]["sha256"],
        parser_version=data["parser_version"],
        precision_version=data["precision_version"],
        cohort_fingerprint="a" * 64 if failure == "hash" else data["fingerprint"],
        source_snapshot=deepcopy(first.source_snapshot),
        payload=data,
    )
    db_session.add(new)
    db_session.commit()
    result = auth_client.get(ENDPOINT).json()["data"]
    assert result["status"] == "INCOMPLETE" and result["year"] == year
    assert result["payload"] is None and result["source"] is None
    assert result["revision"] is None and len(rows(db_session)) == 2
    source = auth_client.get(f"/api/v1/sources/{first.source_id}")
    assert source.status_code == 200
    assert "collection_code" not in source.json()["data"]


@pytest.mark.parametrize("failure", ["outage", "truncated", "write", "year_changed", "wrong_year"])
def test_failed_collection_rolls_back_all_new_rows_and_preserves_previous_snapshot(
    auth_client, db_session, monkeypatch, failure
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    before = auth_client.get(ENDPOINT).json()["data"]
    source_count = db_session.scalar(select(func.count()).select_from(Source))
    saved = {row.id for row in rows(db_session)}
    data = payload(year if failure != "wrong_year" else year - 1, paid="200.10", tag="second-file")
    if failure == "truncated":
        data["months"].pop()
        data["fingerprint"] = provider.fingerprint(data)

    def fetch(*args):
        if failure == "outage":
            raise TimeoutError("Invented source failure")
        return data

    monkeypatch.setattr(provider, "fetch_year", fetch)
    if failure == "write":

        def record(*args, **kwargs):
            raise RuntimeError("Invented failure after source/cohort flush")

        monkeypatch.setattr(fiscal_spending, "record", record)
    original = fiscal_baseline.current
    calls = []

    def selected(session):
        calls.append(True)
        if len(calls) > 1:
            return {"status": "AVAILABLE", "year": year - 1}
        return original(session)

    if failure == "year_changed":
        monkeypatch.setattr(fiscal_baseline, "current", selected)
    result = collection.collect_spending(db_session, user, datetime.now(UTC).date())
    monkeypatch.setattr(fiscal_baseline, "current", original)
    assert result["federal-spending"]["status"] == "FAILED"
    assert {row.id for row in rows(db_session)} == saved
    assert db_session.scalar(select(func.count()).select_from(Source)) == source_count
    assert auth_client.get(ENDPOINT).json()["data"] == before


def test_missing_or_changed_selected_year_never_falls_back_or_calls_provider(
    auth_client, db_session, monkeypatch
):
    def no_fetch(*args):
        raise AssertionError("No reviewed year available; must not fetch.")

    monkeypatch.setattr(provider, "fetch_year", no_fetch)
    assert auth_client.get(ENDPOINT).json()["data"]["status"] == "EMPTY"
    assert (
        collection.collect_spending(db_session, None, datetime.now(UTC).date())["federal-spending"][
            "status"
        ]
        == "NO_DATA"
    )
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    monkeypatch.setattr(
        fiscal_spending,
        "current_fiscal",
        lambda session: {
            "status": "AVAILABLE",
            "year": year - 1,
        },
    )
    result = auth_client.get(ENDPOINT).json()["data"]
    assert result["status"] == "EMPTY" and result["year"] == year - 1 and result["payload"] is None


def test_private_same_url_never_promotes_source_or_copies_private_metadata(
    auth_client, db_session, monkeypatch
):
    actor, user, year = seed_closed_year(auth_client, db_session)
    other, _ = signup(auth_client)
    owner = db_session.get(User, UUID(other["user"]["id"]))
    private = Source(
        created_by=owner.id,
        title="Private functional source",
        institution="Private",
        url=provider.SOURCE_URL,
        source_type="OFFICIAL",
        is_example=False,
        description="Private notes never public",
        accessed_at=datetime.now(UTC).date(),
    )
    db_session.add(private)
    db_session.commit()
    collect(db_session, user, year, monkeypatch)
    row = rows(db_session)[0]
    assert row.source_id != private.id
    assert auth_client.get(f"/api/v1/sources/{private.id}").status_code == 404
    response = auth_client.get("/api/v1/sources?page_size=100")
    assert str(private.id) not in response.text and "Private notes" not in response.text
    verified = next(item for item in response.json()["data"] if item["id"] == str(row.source_id))
    assert verified["collection_code"] == "federal-spending"
    assert verified["license"] == provider.SOURCE["license"]
    assert verified["license_url"] == provider.SOURCE["license_url"]
    assert auth_client.get(f"/api/v1/sources/{row.source_id}").json()["data"] == verified
    manual = auth_client.post(
        "/api/v1/sources",
        headers=headers(actor),
        json={
            "title": "Manual same URL",
            "institution": provider.SOURCE["institution"],
            "url": provider.SOURCE_URL,
            "source_type": "OFFICIAL",
            "accessed_at": "2025-01-01",
        },
    ).json()["data"]
    own = auth_client.get("/api/v1/sources/mine?page_size=100", headers=headers(actor)).json()[
        "data"
    ]
    assert "collection_code" not in next(item for item in own if item["id"] == manual["id"])
    assert (
        auth_client.post(
            "/api/v1/sources",
            headers=headers(actor),
            json={
                "title": "Forged marker",
                "institution": provider.SOURCE["institution"],
                "url": provider.SOURCE_URL,
                "accessed_at": "2025-01-01",
                "collection_code": "federal-spending",
            },
        ).status_code
        == 422
    )


def test_source_mutation_invalidates_metadata_and_unlinked_public_visibility(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    row = rows(db_session)[0]
    original = deepcopy(row.source_snapshot)
    source = db_session.get(Source, row.source_id)
    source.title = "Changed metadata"
    db_session.commit()
    assert row.source_snapshot == original
    assert auth_client.get(ENDPOINT).json()["data"]["status"] == "INCOMPLETE"
    assert auth_client.get(f"/api/v1/sources/{source.id}").status_code == 404


def test_reference_amount_revision_does_not_change_independent_spending_cohort(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    before = auth_client.get(ENDPOINT).json()["data"]
    seed_month(db_session, user, datetime(year, 1, 1).date(), revenue="1100.10")
    assert auth_client.get(ENDPOINT).json()["data"] == before


def test_first_collection_failure_after_flush_rolls_back_new_source_and_cohort(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    sources_before = db_session.scalar(select(func.count()).select_from(Source))
    data = payload(year)
    monkeypatch.setattr(provider, "fetch_year", lambda *args: data)

    def fail_after_flush(*args, **kwargs):
        assert len(rows(db_session)) == 1
        assert db_session.scalar(select(func.count()).select_from(Source)) == sources_before + 1
        raise RuntimeError("Invented first-import failure after complete persistence")

    monkeypatch.setattr(fiscal_spending, "record", fail_after_flush)
    result = collection.collect_spending(db_session, user, datetime.now(UTC).date())
    assert result["federal-spending"]["status"] == "FAILED"
    assert rows(db_session) == []
    assert db_session.scalar(select(func.count()).select_from(Source)) == sources_before
    assert auth_client.get(ENDPOINT).json()["data"]["status"] == "EMPTY"
