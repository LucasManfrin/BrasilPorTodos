import copy
from datetime import UTC, datetime
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.modules.plans.models import PlanVersion
from app.modules.simulations.models import Simulation
from app.simulation.compatibility import EXPECTED

from .test_auth import signup
from .test_fiscal_compatibility import frozen_base as frozen_base
from .test_fiscal_compatibility import publish
from .test_plans import plan_input
from .test_policies import headers

pytestmark = pytest.mark.database


def config():
    return {
        "title": "Cenário futuro fictício",
        "explanation": "Premissas manuais de teste, sem previsão oficial.",
        "reference_baseline_id": "frozen-reviewed-2025",
        "years": [
            {
                "year": 2027,
                "net_revenue": "1000.00",
                "primary_expenditure": "1100.00",
                "justification": "Premissa explícita",
                "source_urls": ["https://example.test/method"],
            },
            {
                "year": 2028,
                "net_revenue": "2000.00",
                "primary_expenditure": "1800.00",
                "justification": "Outra premissa",
                "source_urls": [],
            },
        ],
    }


def make_plan(client, user, proposals, premise=None):
    data = plan_input(proposals)
    if premise is not None:
        data["fiscal_scenario"] = premise
    response = client.post("/api/v1/plans", headers=headers(user), json=data)
    assert response.status_code == 201, response.text
    return response.json()["data"]


def confirm(client, user, item, hash_value=None):
    current = client.get(f"/api/v1/plans/{item['id']}/draft", headers=headers(user)).json()["data"]
    return client.post(
        f"/api/v1/plans/{item['id']}/fiscal-scenario/confirm",
        headers=headers(user),
        json={
            "expected_input_hash": hash_value
            or current["version"]["fiscal_scenario"]["review_input_hash"]
        },
    )


def run(client, user, item):
    response = client.post(f"/api/v1/plans/{item['id']}/simulate", headers=headers(user))
    assert response.status_code == 200, response.text
    return response.json()["data"]


def patch(client, user, item, data):
    response = client.patch(f"/api/v1/plans/{item['id']}", headers=headers(user), json=data)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_draft_partial_null_removal_and_no_silent_incremental_fallback(auth_client, frozen_base):
    user, _ = signup(auth_client)
    proposal = publish(auth_client, user, EXPECTED, year=2027)
    item = make_plan(auth_client, user, [proposal], {})
    assert item["version"]["fiscal_scenario"]["years"] == []
    partial = patch(
        auth_client,
        user,
        item,
        {
            "fiscal_scenario": {
                "years": [{"year": 2027, "net_revenue": None, "primary_expenditure": "0"}]
            }
        },
    )
    assert partial["version"]["fiscal_scenario"]["years"][0]["net_revenue"] is None
    for action in ("simulate", "publish"):
        response = auth_client.post(f"/api/v1/plans/{item['id']}/{action}", headers=headers(user))
        assert (
            response.status_code == 422
            and response.json()["error"]["code"] == "SCENARIO_INCOMPLETE"
        )
    response = confirm(auth_client, user, item)
    assert response.status_code == 422
    removed = patch(auth_client, user, item, {"fiscal_scenario": None})
    assert removed["version"]["fiscal_scenario"] is None
    result = run(auth_client, user, item)
    assert (
        "fiscal_scenario" not in result["input_snapshot"]
        and "fiscal_scenario" not in result["assumptions"]
    )
    assert result["cumulative_impact"] == "-100.10"


def test_confirmed_future_scenario_roundtrip_with_historical_assessment_separate(
    auth_client, frozen_base
):
    user, _ = signup(auth_client)
    item = make_plan(auth_client, user, [publish(auth_client, user, EXPECTED, year=2027)], config())
    saved = item["version"]["fiscal_scenario"]
    assert saved["excludes_plan_impacts"] is False and saved["reviewed_at"] is None
    blocked = run(auth_client, user, item)
    assert blocked["assumptions"]["fiscal_scenario"]["years"][0]["combined"] is None
    assert "DOUBLE_COUNTING_UNCHECKED" in {warning["code"] for warning in blocked["warnings"]}
    response = confirm(auth_client, user, item)
    assert response.status_code == 200, response.text
    reviewed = response.json()["data"]["version"]["fiscal_scenario"]
    assert reviewed["excludes_plan_impacts"] is True
    assert reviewed["review_input_hash"] == reviewed["reviewed_input_hash"]
    assert (
        datetime.fromisoformat(reviewed["reviewed_at"]).utcoffset() == datetime.now(UTC).utcoffset()
    )
    result = run(auth_client, user, item)
    future = result["assumptions"]["fiscal_scenario"]
    assert future["status"] == "COMPATIBLE"
    assert future["years"][0]["declared"]["primary_balance"] == "-100.00"
    assert future["years"][0]["combined"]["primary_expenditure"] == "1200.10"
    assert future["years"][0]["combined"]["primary_balance"] == "-200.10"
    assert result["years"][0]["net_impact"] == "-100.10"
    assert result["assumptions"]["fiscal_compatibility"]["status"] == "NOT_COMPARABLE"
    assert (
        result["input_snapshot"]["fiscal_scenario"]["reviewed_input_hash"]
        == reviewed["reviewed_input_hash"]
    )
    assert result["input_snapshot"]["fiscal_scenario"]["scenario_method_version"] == "1.0.0"
    assert run(auth_client, user, item)["input_hash"] == result["input_hash"]


def test_review_hash_stale_confirmation_and_real_changes_reset_review(auth_client, frozen_base):
    user, _ = signup(auth_client)
    proposal = publish(auth_client, user, EXPECTED, year=2027)
    item = make_plan(auth_client, user, [proposal], config())
    assert confirm(auth_client, user, item).status_code == 200
    current = auth_client.get(f"/api/v1/plans/{item['id']}/draft", headers=headers(user)).json()[
        "data"
    ]
    original = current["version"]["fiscal_scenario"]
    current = patch(
        auth_client,
        user,
        item,
        {
            "title": "Título alterado",
            "summary": "Outro resumo",
            "vision": "Outra visão",
            "fiscal_scenario": config(),
        },
    )
    assert current["version"]["fiscal_scenario"] == original
    identical = config()
    identical["years"][0]["net_revenue"] = "1000"
    assert (
        patch(auth_client, user, item, {"fiscal_scenario": identical})["version"]["fiscal_scenario"]
        == original
    )
    for changes in (
        {"policies": [{"policy_version_id": proposal["version"]["id"], "is_enabled": False}]},
        {"start_year": 2028},
        {"refresh_baseline": True},
        {"fiscal_scenario": {**config(), "title": "Nova premissa"}},
    ):
        current = patch(auth_client, user, item, changes)
        after = current["version"]["fiscal_scenario"]
        assert (
            after["excludes_plan_impacts"] is False
            and after["reviewed_input_hash"] is None
            and after["reviewed_at"] is None
        )
    response = confirm(auth_client, user, item, original["review_input_hash"])
    assert response.status_code == 409 and response.json()["error"]["code"] == "SCENARIO_CHANGED"


def test_confirmation_auth_owner_admin_and_private_draft(auth_client, db_session, frozen_base):
    user, _ = signup(auth_client)
    item = make_plan(auth_client, user, [publish(auth_client, user, EXPECTED, year=2027)], config())
    endpoint = f"/api/v1/plans/{item['id']}/fiscal-scenario/confirm"
    body = {"expected_input_hash": item["version"]["fiscal_scenario"]["review_input_hash"]}
    assert auth_client.post(endpoint, json=body).status_code == 401
    other, _ = signup(auth_client)
    assert auth_client.post(endpoint, json=body, headers=headers(other)).status_code == 403
    assert auth_client.get(f"/api/v1/plans/{item['slug']}").status_code == 404
    assert (
        auth_client.get(f"/api/v1/plans/{item['id']}/draft", headers=headers(other)).status_code
        == 403
    )
    assert auth_client.get("/api/v1/plans").json()["data"] == []
    db_session.execute(
        text("UPDATE users SET role='ADMIN' WHERE id=:id"), {"id": other["user"]["id"]}
    )
    db_session.flush()
    assert auth_client.post(endpoint, json=body, headers=headers(other)).status_code == 200


def test_readonly_fields_injection_is_rejected(auth_client, frozen_base):
    user, _ = signup(auth_client)
    item = make_plan(auth_client, user, [publish(auth_client, user, EXPECTED, year=2027)], config())
    for field, value in (
        ("excludes_plan_impacts", True),
        ("reviewed_at", "2026-01-01"),
        ("review_input_hash", "a" * 64),
        ("reviewed_input_hash", "a" * 64),
        ("currency", "USD"),
    ):
        response = auth_client.patch(
            f"/api/v1/plans/{item['id']}",
            headers=headers(user),
            json={"fiscal_scenario": {**config(), field: value}},
        )
        assert response.status_code == 422


@pytest.mark.parametrize(
    "change", ["wrong_id", "historical_year", "gap", "duplicate", "too_many", "null"]
)
def test_invalid_active_config_cannot_confirm_simulate_or_publish(auth_client, frozen_base, change):
    user, _ = signup(auth_client)
    data = config()
    if change == "wrong_id":
        data["reference_baseline_id"] = "another"
    elif change == "historical_year":
        data["years"][0]["year"] = 2025
    elif change == "gap":
        data["years"] = data["years"][:1]
    elif change == "duplicate":
        data["years"][1]["year"] = 2027
    elif change == "too_many":
        data["years"] = data["years"] * 16
    elif change == "null":
        data["years"][0]["net_revenue"] = None
    proposal = publish(auth_client, user, EXPECTED, year=2027)
    if change == "too_many":
        response = auth_client.post(
            "/api/v1/plans",
            headers=headers(user),
            json={**plan_input([proposal]), "fiscal_scenario": data},
        )
        assert response.status_code == 422
        return
    item = make_plan(auth_client, user, [proposal], data)
    assert confirm(auth_client, user, item).status_code == 422
    for action in ("simulate", "publish"):
        response = auth_client.post(f"/api/v1/plans/{item['id']}/{action}", headers=headers(user))
        assert response.status_code == 422 and response.json()["error"]["code"] in {
            "SCENARIO_INCOMPLETE",
            "SCENARIO_INVALID",
        }


def test_publication_immutable_scenario_json_and_new_draft_clear_review_without_rebinding(
    auth_client, db_session, frozen_base, monkeypatch
):
    user, _ = signup(auth_client)
    item = make_plan(auth_client, user, [publish(auth_client, user, EXPECTED, year=2027)], config())
    assert confirm(auth_client, user, item).status_code == 200
    response = auth_client.post(f"/api/v1/plans/{item['id']}/publish", headers=headers(user))
    assert response.status_code == 200, response.text
    original = response.json()["data"]
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(
            text("UPDATE plan_versions SET fiscal_scenario='{}'::jsonb WHERE id=:id"),
            {"id": original["version"]["id"]},
        )
    old_exec = copy.deepcopy(original["version"]["simulation"])
    response = auth_client.post(
        f"/api/v1/plans/{item['id']}/fiscal-scenario/confirm",
        headers=headers(user),
        json={"expected_input_hash": original["version"]["fiscal_scenario"]["review_input_hash"]},
    )
    assert response.status_code == 409 and response.json()["error"]["code"] == "DRAFT_REQUIRED"
    changed = copy.deepcopy(frozen_base)
    changed["id"] = "new-reference"
    monkeypatch.setattr(
        "app.modules.plans.service.current_baseline", lambda _: copy.deepcopy(changed)
    )
    response = auth_client.post(f"/api/v1/plans/{item['id']}/draft", headers=headers(user))
    assert response.status_code == 200, response.text
    cloned = response.json()["data"]
    assert cloned["version"]["fiscal_scenario"]["excludes_plan_impacts"] is False
    assert cloned["version"]["fiscal_scenario"]["reference_baseline_id"] == "frozen-reviewed-2025"
    assert cloned["version"]["baseline_snapshot"]["id"] == "new-reference"
    invalid = auth_client.post(f"/api/v1/plans/{item['id']}/simulate", headers=headers(user))
    assert invalid.status_code == 422 and invalid.json()["error"]["code"] == "SCENARIO_INVALID"
    public = auth_client.get(f"/api/v1/plans/{item['slug']}").json()["data"]
    assert public == original and public["version"]["simulation"] == old_exec
    assert db_session.get(Simulation, UUID(old_exec["id"])).input_hash == old_exec["input_hash"]


@pytest.mark.parametrize(
    "metadata,status",
    [({**EXPECTED, "fiscal_scope": "STATE"}, "NOT_COMPARABLE"), ({}, "INCOMPLETE")],
)
def test_confirmation_does_not_require_compatible_impacts_and_publication_is_allowed_blocked(
    auth_client, frozen_base, metadata, status
):
    user, _ = signup(auth_client)
    item = make_plan(auth_client, user, [publish(auth_client, user, metadata, year=2027)], config())
    assert confirm(auth_client, user, item).status_code == 200
    result = run(auth_client, user, item)
    assert result["assumptions"]["fiscal_scenario"]["status"] == status
    assert all(row["combined"] is None for row in result["assumptions"]["fiscal_scenario"]["years"])
    response = auth_client.post(f"/api/v1/plans/{item['id']}/publish", headers=headers(user))
    assert response.status_code == 200, response.text


def test_unconfirmed_scenario_can_publish_separate_declared_and_incremental_results(
    auth_client, frozen_base
):
    user, _ = signup(auth_client)
    item = make_plan(auth_client, user, [publish(auth_client, user, EXPECTED, year=2027)], config())
    response = auth_client.post(f"/api/v1/plans/{item['id']}/publish", headers=headers(user))
    assert response.status_code == 200, response.text
    published = response.json()["data"]
    assert not published["version"]["fiscal_scenario"]["excludes_plan_impacts"]
    assert (
        published["version"]["simulation"]["assumptions"]["fiscal_scenario"]["years"][0]["combined"]
        is None
    )


def test_duplicate_plan_creation_resets_review_and_corrupt_json_fails_closed(
    auth_client, db_session, frozen_base
):
    user, _ = signup(auth_client)
    proposal = publish(auth_client, user, EXPECTED, year=2027)
    item = make_plan(auth_client, user, [proposal], config())
    reviewed = confirm(auth_client, user, item).json()["data"]
    duplicate = make_plan(
        auth_client,
        user,
        [proposal],
        {key: reviewed["version"]["fiscal_scenario"][key] for key in config()},
    )
    assert duplicate["version"]["fiscal_scenario"]["excludes_plan_impacts"] is False
    version = db_session.get(PlanVersion, UUID(duplicate["version"]["id"]))
    version.fiscal_scenario = ["invalid"]
    db_session.flush()
    response = auth_client.post(f"/api/v1/plans/{duplicate['id']}/simulate", headers=headers(user))
    assert response.status_code == 422 and response.json()["error"]["code"] == "SCENARIO_INVALID"


@pytest.mark.parametrize(
    "kind",
    [
        "revenue",
        "source",
        "justification",
        "composition",
        "order",
        "horizon",
        "refresh",
        "reference",
    ],
)
def test_each_reviewed_input_change_independently_clears_confirmation(
    auth_client, frozen_base, kind
):
    user, _ = signup(auth_client)
    first = publish(auth_client, user, EXPECTED, year=2027)
    second = publish(auth_client, user, EXPECTED, year=2027)
    item = make_plan(auth_client, user, [first, second], config())
    original = confirm(auth_client, user, item).json()["data"]["version"]["fiscal_scenario"]
    changed = config()
    changes = {"fiscal_scenario": changed}
    if kind == "revenue":
        changed["years"][0]["net_revenue"] = "1001.00"
    elif kind == "source":
        changed["years"][0]["source_urls"] = ["https://example.test/new-method"]
    elif kind == "justification":
        changed["years"][0]["justification"] = "Premissa revista"
    elif kind == "reference":
        changed["reference_baseline_id"] = "different"
    elif kind == "composition":
        changes = {
            "policies": [
                {"policy_version_id": first["version"]["id"], "is_enabled": False},
                {"policy_version_id": second["version"]["id"]},
            ]
        }
    elif kind == "order":
        changes = {
            "policies": [
                {"policy_version_id": second["version"]["id"]},
                {"policy_version_id": first["version"]["id"]},
            ]
        }
    elif kind == "horizon":
        changes = {"start_year": 2028}
    elif kind == "refresh":
        changes = {"refresh_baseline": True}
    after = patch(auth_client, user, item, changes)["version"]["fiscal_scenario"]
    assert (
        not after["excludes_plan_impacts"]
        and after["reviewed_input_hash"] is None
        and after["reviewed_at"] is None
    )
    if kind != "refresh":
        assert after["review_input_hash"] != original["review_input_hash"]


@pytest.mark.parametrize("kind", ["heterogeneous", "not_estimated"])
def test_mixed_or_unestimated_selected_policies_block_all_combined_years(
    auth_client, frozen_base, kind
):
    user, _ = signup(auth_client)
    first = publish(auth_client, user, EXPECTED, year=2027)
    metadata = {**EXPECTED, "price_basis": "CONSTANT", "price_base_year": 2020}
    second = publish(auth_client, user, metadata, year=2027)
    if kind == "not_estimated":
        response = auth_client.patch(
            f"/api/v1/policies/{second['id']}",
            headers=headers(user),
            json={"financial_impact_status": "NOT_ESTIMATED", "impacts": []},
        )
        assert response.status_code == 200, response.text
        response = auth_client.post(
            f"/api/v1/policies/{second['id']}/publish", headers=headers(user)
        )
        assert response.status_code == 200, response.text
        second = response.json()["data"]
    item = make_plan(auth_client, user, [first, second], config())
    assert confirm(auth_client, user, item).status_code == 200
    result = run(auth_client, user, item)
    future = result["assumptions"]["fiscal_scenario"]
    assert all(row["combined"] is None for row in future["years"])
    if kind == "heterogeneous":
        assert future["aggregate_basis"] == future["price_basis"] == "MIXED"
        assert future["status"] == "NOT_COMPARABLE"
        assert future["cumulative_incremental"] == "-200.20"
    else:
        assert future["status"] == "INCOMPLETE" and future["incremental_is_partial"]
        assert future["cumulative_incremental"] == "-100.10"


def test_fixing_proposal_and_updating_plan_version_preserves_previous_public_scenario_execution(
    auth_client, frozen_base
):
    user, _ = signup(auth_client)
    proposal = publish(auth_client, user, {}, year=2027)
    item = make_plan(auth_client, user, [proposal], config())
    assert confirm(auth_client, user, item).status_code == 200
    response = auth_client.post(f"/api/v1/plans/{item['id']}/publish", headers=headers(user))
    assert response.status_code == 200, response.text
    original = response.json()["data"]
    assert (
        original["version"]["simulation"]["assumptions"]["fiscal_scenario"]["status"]
        == "INCOMPLETE"
    )
    impact = {
        "year": 2027,
        "impact_type": "NEW_EXPENSE",
        "amount": "100.10",
        "description": "Fictício",
        **EXPECTED,
    }
    response = auth_client.patch(
        f"/api/v1/policies/{proposal['id']}", headers=headers(user), json={"impacts": [impact]}
    )
    assert response.status_code == 200, response.text
    proposal = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user)
    ).json()["data"]
    updated = patch(
        auth_client, user, item, {"policies": [{"policy_version_id": proposal["version"]["id"]}]}
    )
    assert updated["version"]["version_number"] == 2
    assert not updated["version"]["fiscal_scenario"]["excludes_plan_impacts"]
    assert confirm(auth_client, user, item).status_code == 200
    result = run(auth_client, user, item)
    assert result["assumptions"]["fiscal_scenario"]["status"] == "COMPATIBLE"
    assert result["input_hash"] != original["version"]["simulation"]["input_hash"]
    assert auth_client.get(f"/api/v1/plans/{item['slug']}/versions/1").json()["data"] == original
