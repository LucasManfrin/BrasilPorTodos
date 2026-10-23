"""Synthetic below-line values in exclusive PostgreSQL rollback transactions."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select

from app.integrations import treasury
from app.integrations import treasury_interest as provider
from app.modules.indicators import collection
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.sources.models import Source

from .test_auth import signup
from .test_fiscal_baseline import seed_closed_year, seed_month
from .test_plans import create_plan
from .test_policies import draft, headers

pytestmark = pytest.mark.database


def bundle(year, interest="-70.01"):
    money = {
        "rtn-primario-abaixo-linha": Decimal("100.10"),
        "rtn-juros-nominais": Decimal(interest),
        "rtn-resultado-nominal": Decimal("100.10") + Decimal(interest),
    }
    return {
        code: {
            "observations": [(date(year, month, 1), value) for month in range(1, 13)],
            "request_url": "https://apiapex.tesouro.gov.br/test-only-below-line",
        }
        for code, value in money.items()
    }


def collect(session, user, year, monkeypatch, interest="-70.01"):
    monkeypatch.setattr(provider, "fetch_year", lambda requested, end: bundle(year, interest))
    return collection.collect_interest(session, user, datetime.now(UTC).date())


def ids(session):
    return set(
        session.scalars(
            select(IndicatorValue.id)
            .join(Indicator)
            .where(Indicator.code.in_(provider.INTEREST_SERIES))
        )
    )


def test_interest_read_is_public_separate_idempotent_and_preserves_publications_context_and_catalog(
    auth_client, db_session, monkeypatch
):
    actor, user, year = seed_closed_year(auth_client, db_session)
    before = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    catalog = auth_client.get("/api/v1/indicators?page_size=100").json()
    policy, _ = draft(auth_client, actor)
    policy = auth_client.post(
        f"/api/v1/policies/{policy['id']}/publish", headers=headers(actor)
    ).json()["data"]
    plan = create_plan(auth_client, actor, [policy])
    plan = auth_client.post(f"/api/v1/plans/{plan['id']}/publish", headers=headers(actor)).json()[
        "data"
    ]
    result = collect(db_session, user, year, monkeypatch)
    assert result["rtn-interest"]["status"] == "SUCCESS"
    response = auth_client.get("/api/v1/indicators/baseline/interest")
    assert (
        response.status_code == 200
        and "password_hash" not in response.text
        and "email" not in response.text
    )
    interest = response.json()["data"]
    assert interest["status"] == "AVAILABLE" and interest["totals"] == {
        "primary_balance": "1201.20",
        "interest": "-840.12",
        "nominal_balance": "361.08",
    }
    assert (
        interest["totals"]["primary_balance"]
        != before["fiscal"]["amounts"]["published_primary_balance"]
    )
    assert interest["accounting_basis"] == "mixed" and len(interest["months"]) == 12
    assert auth_client.get("/api/v1/indicators?page_size=100").json() == catalog
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert after["id"] == before["id"] and after["fiscal"] == before["fiscal"]
    assert auth_client.get(f"/api/v1/policies/{policy['slug']}").json()["data"] == policy
    assert auth_client.get(f"/api/v1/plans/{plan['slug']}").json()["data"] == plan
    admin_codes = {
        row["code"]
        for row in auth_client.get(
            "/api/v1/admin/indicators?page_size=100", headers=headers(actor)
        ).json()["data"]
    }
    assert set(provider.INTEREST_SERIES).issubset(admin_codes)
    saved = ids(db_session)
    assert len(saved) == 36
    collect(db_session, user, year, monkeypatch)
    assert (
        ids(db_session) == saved
        and auth_client.get("/api/v1/indicators/baseline/interest").json()["data"] == interest
    )


def test_above_line_revision_does_not_invalidate_same_year_independent_below_line_cohort(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    before = auth_client.get("/api/v1/indicators/baseline/interest").json()["data"]
    seed_month(db_session, user, date(year, 1, 1), revenue="1100.10")
    assert auth_client.get("/api/v1/indicators/baseline/interest").json()["data"] == before


def test_positive_interest_revision_preserves_signed_value_and_revises_whole_month_cohort(
    auth_client, db_session, monkeypatch
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    context = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["id"]
    assert (
        collect(db_session, user, year, monkeypatch, "70.01")["rtn-interest"]["status"] == "SUCCESS"
    )
    result = auth_client.get("/api/v1/indicators/baseline/interest").json()["data"]
    assert result["status"] == "AVAILABLE" and result["totals"]["interest"] == "840.12"
    assert result["totals"]["nominal_balance"] == "2041.32"
    assert len(ids(db_session)) == 72
    assert all(row["revision"] == 2 for month in result["months"] for row in month["observations"])
    assert auth_client.get("/api/v1/indicators/baseline/current").json()["data"]["id"] == context


@pytest.mark.parametrize(
    "failure", ["persistence", "truncated", "outage", "wrong_nominal", "wrong_year"]
)
def test_failed_cohort_or_write_preserves_previous_below_line_data(
    auth_client, db_session, monkeypatch, failure
):
    _, user, year = seed_closed_year(auth_client, db_session)
    collect(db_session, user, year, monkeypatch)
    before = auth_client.get("/api/v1/indicators/baseline/interest").json()["data"]
    saved = ids(db_session)
    data = bundle(year if failure != "wrong_year" else year - 1, "70.01")
    if failure == "truncated":
        for item in data.values():
            item["observations"] = item["observations"][:-1]
    if failure == "wrong_nominal":
        data["rtn-resultado-nominal"]["observations"][0] = (date(year, 1, 1), Decimal("1.00"))

    def fetch(*args):
        if failure == "outage":
            raise TimeoutError("Synthetic outage")
        return data

    monkeypatch.setattr(provider, "fetch_year", fetch)
    original_seed, writes = collection.seed, []

    def seed(*args, **kwargs):
        writes.append(args[2])
        if failure == "persistence" and len(writes) == 2:
            raise RuntimeError("Synthetic persistence failure")
        return original_seed(*args, **kwargs)

    monkeypatch.setattr(collection, "seed", seed)
    assert (
        collection.collect_interest(db_session, user, datetime.now(UTC).date())["rtn-interest"][
            "status"
        ]
        == "FAILED"
    )
    assert (
        ids(db_session) == saved
        and auth_client.get("/api/v1/indicators/baseline/interest").json()["data"] == before
    )
    if failure != "persistence":
        assert writes == []


def test_interest_requires_reference_year_and_never_fetches_without_it(
    auth_client, db_session, monkeypatch
):
    from app.modules.users.models import User

    from .test_admin_indicators import administrator

    actor = administrator(auth_client, db_session)
    user = db_session.get(User, UUID(actor["user"]["id"]))

    def forbidden(*args):
        raise AssertionError("No fetch without an observed closed reference year")

    monkeypatch.setattr(provider, "fetch_year", forbidden)
    assert (
        collection.collect_interest(db_session, user, datetime.now(UTC).date())["rtn-interest"][
            "status"
        ]
        == "NO_DATA"
    )
    result = auth_client.get("/api/v1/indicators/baseline/interest").json()["data"]
    assert result["status"] == "EMPTY" and result["year"] is None and result["totals"] is None


def test_private_same_url_source_does_not_become_public_below_line_evidence(
    auth_client, db_session, monkeypatch
):
    actor, _ = signup(auth_client)
    private = Source(
        created_by=UUID(actor["user"]["id"]),
        title="Private confidential title",
        institution="Secretaria do Tesouro Nacional",
        url=treasury.SOURCE_URL,
        source_type="OFFICIAL",
        accessed_at=datetime.now(UTC).date(),
        description="Private confidential metadata",
    )
    db_session.add(private)
    db_session.commit()
    private_id = private.id
    _, user, year = seed_closed_year(auth_client, db_session)
    assert collect(db_session, user, year, monkeypatch)["rtn-interest"]["status"] == "SUCCESS"
    response = auth_client.get("/api/v1/indicators/baseline/interest")
    assert response.json()["data"]["status"] == "AVAILABLE"
    assert "confidential" not in response.text and str(private_id) not in response.text
    assert auth_client.get(f"/api/v1/sources/{private_id}").status_code == 404
