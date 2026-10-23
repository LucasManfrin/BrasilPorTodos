"""Synthetic fiscal observations in the isolated PostgreSQL test transaction."""

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.integrations.treasury import SOURCE_URL, TREASURY_SERIES, period_fingerprint
from app.modules.indicators.models import Indicator, IndicatorValue
from app.modules.sources.models import Source
from app.modules.users.models import User
from app.seed_indicators import seed

from .test_admin_indicators import administrator
from .test_plans import create_plan
from .test_policies import draft, headers

pytestmark = pytest.mark.database


def seed_month(session, user, when, revenue="1000.10", expenditure="750.01"):
    values = {
        "rtn-receita-liquida": Decimal(revenue),
        "rtn-despesa-primaria": Decimal(expenditure),
        "rtn-resultado-primario": Decimal(revenue) - Decimal(expenditure),
    }
    provenance = {
        "collector": "tesouro-rtn-v1",
        "accounting_basis": "cash",
        "price_basis": "nominal",
        "currency": "BRL",
        "original_unit": "R$ milhões",
        "scale": "1000000",
        "period_fingerprint": period_fingerprint(when, values),
    }
    for code, value in values.items():
        seed(
            session,
            user,
            code,
            [(when, value)],
            "https://apiapex.tesouro.gov.br/test-only",
            provenance_extra=provenance,
        )


def seed_closed_year(client, session):
    actor = administrator(client, session)
    user = session.get(User, UUID(actor["user"]["id"]))
    year = datetime.now(UTC).year - 1
    for month in range(1, 13):
        seed_month(session, user, date(year, month, 1))
    return actor, user, year


def test_fiscal_baseline_is_public_and_repeated_import_is_idempotent(auth_client, db_session):
    _, user, year = seed_closed_year(auth_client, db_session)
    response = auth_client.get("/api/v1/indicators/baseline/current")
    assert response.status_code == 200
    before = response.json()["data"]
    assert before["kind"] == "CONTEXT_WITH_FISCAL"
    assert before["fiscal"]["status"] == "AVAILABLE" and before["fiscal"]["year"] == year
    assert before["fiscal"]["amounts"]["calculated_primary_balance"] == "3001.08"
    assert len(before["fiscal"]["months"]) == 12
    assert all(
        row["provenance"]["definition"]["unit"] == "R$"
        for month in before["fiscal"]["months"]
        for row in month["observations"]
    )
    assert "email" not in response.text and "password_hash" not in response.text
    seed_month(db_session, user, date(year, 1, 1))
    after = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert after["id"] == before["id"] and after["fiscal"] == before["fiscal"]
    records = db_session.scalars(
        select(IndicatorValue)
        .join(Indicator, IndicatorValue.indicator_id == Indicator.id)
        .where(Indicator.code.in_(TREASURY_SERIES))
    ).all()
    assert len(records) == 36 and all(record.revision == 1 for record in records)


def test_fiscal_revision_does_not_rewrite_published_policy_plan_or_execution(
    auth_client, db_session
):
    actor, user, year = seed_closed_year(auth_client, db_session)
    policy, _ = draft(auth_client, actor)
    frozen = policy["version"]["baseline_snapshot"]
    policy = auth_client.post(
        f"/api/v1/policies/{policy['id']}/publish", headers=headers(actor)
    ).json()["data"]
    plan = create_plan(auth_client, actor, [policy])
    published_response = auth_client.post(
        f"/api/v1/plans/{plan['id']}/publish", headers=headers(actor)
    )
    assert published_response.status_code == 200, published_response.text
    published = published_response.json()["data"]
    original_execution = published["version"]["simulation"]
    assert original_execution["cumulative_impact"] == "-100.10"
    seed_month(db_session, user, date(year, 1, 1), revenue="1100.10")
    revised = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert revised["id"] != frozen["id"]
    assert revised["fiscal"]["amounts"]["calculated_primary_balance"] == "3101.08"
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
    assert repeated["input_hash"] == original_execution["input_hash"]
    assert repeated["cumulative_impact"] == "-100.10"
    assert repeated["input_snapshot"]["baseline_snapshot"]["fiscal"] == frozen["fiscal"]
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(
            text("UPDATE plan_versions SET baseline_snapshot='{}'::jsonb WHERE id=:id"),
            {"id": published["version"]["id"]},
        )


def test_fiscal_refresh_requires_explicit_draft_action_and_incremental_result_is_unchanged(
    auth_client, db_session
):
    actor, user, year = seed_closed_year(auth_client, db_session)
    policy, _ = draft(auth_client, actor)
    policy = auth_client.post(
        f"/api/v1/policies/{policy['id']}/publish", headers=headers(actor)
    ).json()["data"]
    plan = create_plan(auth_client, actor, [policy])
    before = plan["version"]["baseline_snapshot"]
    initial_result = auth_client.post(
        f"/api/v1/plans/{plan['id']}/simulate", headers=headers(actor)
    ).json()["data"]
    seed_month(db_session, user, date(year, 1, 1), revenue="1100.10")
    updated = auth_client.patch(
        f"/api/v1/plans/{plan['id']}",
        json={"title": "Texto alterado sem trocar a referência"},
        headers=headers(actor),
    ).json()["data"]
    assert updated["version"]["baseline_snapshot"] == before
    refreshed = auth_client.patch(
        f"/api/v1/plans/{plan['id']}",
        json={"refresh_baseline": True},
        headers=headers(actor),
    ).json()["data"]
    assert refreshed["version"]["baseline_snapshot"]["id"] != before["id"]
    result = auth_client.post(
        f"/api/v1/plans/{plan['id']}/simulate", headers=headers(actor)
    ).json()["data"]
    assert result["input_hash"] != initial_result["input_hash"]
    assert result["cumulative_impact"] == initial_result["cumulative_impact"] == "-100.10"
    assert result["years"] == initial_result["years"]
    assert "BASELINE_DIFFERS" in {warning["code"] for warning in result["warnings"]}


def test_examples_are_excluded_from_fiscal_reference_even_with_official_identifiers(
    auth_client, db_session
):
    seed_closed_year(auth_client, db_session)
    source = db_session.scalar(select(Source).where(Source.url == SOURCE_URL))
    source.is_example = True
    db_session.commit()
    result = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert result["fiscal"]["status"] == "INCOMPLETE"
    assert result["fiscal"]["amounts"] is None
    assert not result["observations"]
