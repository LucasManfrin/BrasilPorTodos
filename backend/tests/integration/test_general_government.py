"""Invented annual statistics; all database writes use the isolated rollback fixture."""

from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError

from app.integrations import general_government as provider
from app.modules.indicators import collection, fiscal_baseline, general_government
from app.modules.indicators.models import GeneralGovernmentCohort, Indicator, IndicatorValue
from app.modules.sources.models import Source
from app.modules.users.models import User
from tests.general_government_fixture import payload

from .test_auth import signup
from .test_fiscal_baseline import seed_closed_year, seed_month
from .test_plans import create_plan
from .test_policies import draft, headers

pytestmark = pytest.mark.database
ENDPOINT = "/api/v1/indicators/government/general"


def collect(session, user, year, monkeypatch, tag="synthetic-file-one", revenue="1000.10"):
    data = payload(year, tag=tag, revenue=revenue)
    monkeypatch.setattr(provider, "fetch_year", lambda requested, end: deepcopy(data))
    result = collection.collect_general_government(session, user, datetime.now(UTC).date())
    assert result["general-government"]["status"] == "SUCCESS", result
    assert result["general-government"]["observations"] == 64
    return result


def rows(session):
    return list(
        session.scalars(select(GeneralGovernmentCohort).order_by(GeneralGovernmentCohort.revision))
    )


def test_public_read_and_idempotence_preserve_context_catalog_and_published_simulations(
    auth_client, db_session, monkeypatch
):
    actor, user, year = seed_closed_year(auth_client, db_session)
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    fiscal = auth_client.get("/api/v1/indicators/baseline/fiscal").json()["data"]
    catalog = auth_client.get("/api/v1/indicators?page_size=100").json()
    counts = [
        db_session.scalar(select(func.count()).select_from(m)) for m in (Indicator, IndicatorValue)
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
    assert (
        len(data["payload"]["sectors"]) == 8
        and data["payload"]["coverage"]["municipal_extrapolated"]
    )
    assert data["period_start"] == f"{year}-01-01" and data["period_end"] == f"{year}-12-31"
    for private in ("password_hash", "email", "created_by", "source_id", str(user.id)):
        assert private not in response.text
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert {k: v for k, v in after.items() if k != "captured_at"} == {
        k: v for k, v in before.items() if k != "captured_at"
    }
    assert auth_client.get("/api/v1/indicators/baseline/fiscal").json()["data"] == fiscal
    assert auth_client.get("/api/v1/indicators?page_size=100").json() == catalog
    assert [
        db_session.scalar(select(func.count()).select_from(m)) for m in (Indicator, IndicatorValue)
    ] == counts
    assert auth_client.get(f"/api/v1/policies/{policy['slug']}").json()["data"] == policy
    assert auth_client.get(f"/api/v1/plans/{plan['slug']}").json()["data"] == plan
    saved = rows(db_session)[0]
    identity = (
        saved.id,
        saved.retrieved_at,
        deepcopy(saved.payload),
        deepcopy(saved.source_snapshot),
    )
    collect(db_session, user, year, monkeypatch)
    assert len(rows(db_session)) == 1
    assert (saved.id, saved.retrieved_at, saved.payload, saved.source_snapshot) == identity
    assert auth_client.get(ENDPOINT).json()["data"] == data


def test_whole_publication_revision_does_not_overwrite_or_revert_a_newer_file(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    first = deepcopy(rows(db_session)[0].payload)
    first_source = rows(db_session)[0].source_id
    collect(db_session, user, year, monkeypatch, tag="new-file", revenue="2000.10")
    data = auth_client.get(ENDPOINT).json()["data"]
    assert data["status"] == "AVAILABLE" and data["revision"] == 2
    assert data["payload"]["sectors"] != first["sectors"]
    assert rows(db_session)[0].payload == first and rows(db_session)[1].source_id == first_source
    monkeypatch.setattr(provider, "fetch_year", lambda *args: first)
    result = collection.collect_general_government(db_session, user, datetime.now(UTC).date())
    assert result["general-government"]["status"] == "FAILED" and len(rows(db_session)) == 2
    assert auth_client.get(ENDPOINT).json()["data"] == data


def test_same_file_changed_semantics_requires_new_method_version(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    before = auth_client.get(ENDPOINT).json()["data"]
    modified = payload(year, tag="synthetic-file-one", revenue="2000.10")
    assert modified["resource"]["sha256"] == rows(db_session)[0].source_hash
    provider.validate_payload(modified)
    monkeypatch.setattr(provider, "fetch_year", lambda *args: modified)
    result = collection.collect_general_government(db_session, user, datetime.now(UTC).date())
    assert result["general-government"]["status"] == "FAILED"
    assert len(rows(db_session)) == 1
    assert auth_client.get(ENDPOINT).json()["data"] == before


@pytest.mark.parametrize("operation", ["UPDATE", "DELETE"])
def test_publication_immutable_even_for_direct_sql(auth_client, db_session, monkeypatch, operation):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    row = rows(db_session)[0]
    sql = (
        "UPDATE general_government_cohorts SET revision=2 WHERE id=:id"
        if operation == "UPDATE"
        else "DELETE FROM general_government_cohorts WHERE id=:id"
    )
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(text(sql), {"id": row.id})
    assert auth_client.get(ENDPOINT).json()["data"]["revision"] == 1


@pytest.mark.parametrize("failure", ["hash", "identity", "precision"])
def test_invalid_latest_revision_never_falls_back(auth_client, db_session, monkeypatch, failure):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    first = rows(db_session)[0]
    data = deepcopy(first.payload)
    data["resource"]["sha256"] = "f" * 64
    if failure == "identity":
        data["sectors"][0]["amounts"]["revenue"] = "999999.00"
    if failure == "precision":
        data["precision_version"] = "unsupported"
    data["fingerprint"] = provider.fingerprint(data)
    db_session.add(
        GeneralGovernmentCohort(
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
    )
    db_session.commit()
    result = auth_client.get(ENDPOINT).json()["data"]
    assert result["status"] == "INCOMPLETE" and result["year"] == year
    assert result["payload"] is None and result["source"] is None and result["revision"] is None
    source = auth_client.get(f"/api/v1/sources/{first.source_id}")
    assert source.status_code == 200 and "collection_code" not in source.json()["data"]


@pytest.mark.parametrize("failure", ["outage", "truncated", "write", "year_changed", "wrong_year"])
def test_failed_collection_rolls_back_entire_new_cohort_and_preserves_previous(
    auth_client, db_session, monkeypatch, failure
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    before = auth_client.get(ENDPOINT).json()["data"]
    source_count = db_session.scalar(select(func.count()).select_from(Source))
    saved = {row.id for row in rows(db_session)}
    data = payload(year if failure != "wrong_year" else year - 1, tag="second-file")
    if failure == "truncated":
        data["sectors"].pop()
        data["fingerprint"] = provider.fingerprint(data)

    def fetch(*args):
        if failure == "outage":
            raise TimeoutError("private-secret-url")
        return data

    monkeypatch.setattr(provider, "fetch_year", fetch)
    if failure == "write":

        def failed_record(*args, **kwargs):
            raise RuntimeError("Invented audit failure after flush")

        monkeypatch.setattr(general_government, "record", failed_record)
    original = fiscal_baseline.current
    calls = []

    def selected(session):
        calls.append(True)
        return {"status": "AVAILABLE", "year": year - 1} if len(calls) > 1 else original(session)

    if failure == "year_changed":
        monkeypatch.setattr(fiscal_baseline, "current", selected)
    result = collection.collect_general_government(db_session, user, datetime.now(UTC).date())
    monkeypatch.setattr(fiscal_baseline, "current", original)
    assert result["general-government"]["status"] == "FAILED"
    assert "private-secret" not in str(result)
    assert {row.id for row in rows(db_session)} == saved
    assert db_session.scalar(select(func.count()).select_from(Source)) == source_count
    assert auth_client.get(ENDPOINT).json()["data"] == before


def test_missing_reference_skips_fetch_and_other_year_never_falls_back(
    auth_client, db_session, monkeypatch
):
    def no_fetch(*args):
        raise AssertionError("No reference year; no fetch")

    monkeypatch.setattr(provider, "fetch_year", no_fetch)
    assert auth_client.get(ENDPOINT).json()["data"]["status"] == "EMPTY"
    assert (
        collection.collect_general_government(db_session, None, datetime.now(UTC).date())[
            "general-government"
        ]["status"]
        == "NO_DATA"
    )
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    monkeypatch.setattr(
        general_government,
        "current_fiscal",
        lambda session: {"status": "AVAILABLE", "year": year - 1},
    )
    result = auth_client.get(ENDPOINT).json()["data"]
    assert result["status"] == "EMPTY" and result["year"] == year - 1 and result["payload"] is None


def test_private_matching_url_is_never_promoted_and_manual_marker_is_rejected(
    auth_client, db_session, monkeypatch
):
    actor, user, year = seed_closed_year(auth_client, db_session)
    other, _ = signup(auth_client)
    owner = db_session.get(User, UUID(other["user"]["id"]))
    private = Source(
        created_by=owner.id,
        title="Private title",
        institution="Private institution",
        url=provider.SOURCE_URL,
        source_type="OFFICIAL",
        is_example=False,
        description="Private notes",
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
    assert verified["collection_code"] == "general-government"
    assert (
        verified["license"] == provider.SOURCE["license"]
        and verified["license_url"] == provider.SOURCE["license_url"]
    )
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
                "collection_code": "general-government",
            },
        ).status_code
        == 422
    )


def test_source_mutation_invalidates_frozen_metadata_and_public_visibility(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    row = rows(db_session)[0]
    original = deepcopy(row.source_snapshot)
    source = db_session.get(Source, row.source_id)
    source.title = "Changed title"
    db_session.commit()
    assert row.source_snapshot == original
    assert auth_client.get(ENDPOINT).json()["data"]["status"] == "INCOMPLETE"
    assert auth_client.get(f"/api/v1/sources/{source.id}").status_code == 404


def test_reference_amount_revision_does_not_change_independent_annual_statistics(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    before = auth_client.get(ENDPOINT).json()["data"]
    seed_month(db_session, user, datetime(year, 1, 1).date(), revenue="1100.10")
    assert auth_client.get(ENDPOINT).json()["data"] == before


def test_first_collection_failure_after_flush_rolls_back_source_and_cohort(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    count = db_session.scalar(select(func.count()).select_from(Source))
    monkeypatch.setattr(provider, "fetch_year", lambda *args: payload(year))

    def fail_after_flush(*args, **kwargs):
        assert len(rows(db_session)) == 1
        assert db_session.scalar(select(func.count()).select_from(Source)) == count + 1
        raise RuntimeError("Invented first-import failure")

    monkeypatch.setattr(general_government, "record", fail_after_flush)
    result = collection.collect_general_government(db_session, user, datetime.now(UTC).date())
    assert result["general-government"]["status"] == "FAILED"
    assert (
        rows(db_session) == []
        and db_session.scalar(select(func.count()).select_from(Source)) == count
    )
    assert auth_client.get(ENDPOINT).json()["data"]["status"] == "EMPTY"
