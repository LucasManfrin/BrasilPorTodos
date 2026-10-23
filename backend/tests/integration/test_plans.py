import hashlib
import json

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from .test_auth import signup
from .test_policies import draft, headers

pytestmark = pytest.mark.database


def published_policy(client, user):
    proposal, _ = draft(client, user)
    response = client.post(f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user))
    assert response.status_code == 200, response.text
    return response.json()["data"]


def plan_input(versions):
    return {
        "title": "Plano fictício",
        "summary": "Exemplo de teste",
        "vision": "Visão de teste",
        "start_year": 2027,
        "end_year": 2028,
        "policies": [{"policy_version_id": version["version"]["id"]} for version in versions],
    }


def create_plan(client, user, proposals):
    response = client.post("/api/v1/plans", json=plan_input(proposals), headers=headers(user))
    assert response.status_code == 201, response.text
    return response.json()["data"]


def test_published_plan_pins_versions_and_execution(auth_client):
    user, _ = signup(auth_client)
    proposal = published_policy(auth_client, user)
    plan = create_plan(auth_client, user, [proposal])
    assert auth_client.get("/api/v1/plans").json()["data"] == []
    assert auth_client.get(f"/api/v1/plans/{plan['slug']}").status_code == 404
    simulated = auth_client.post(f"/api/v1/plans/{plan['id']}/simulate", headers=headers(user))
    assert simulated.status_code == 200, simulated.text
    result = simulated.json()["data"]
    assert result["years"][0]["net_impact"] == "-100.10"
    assert result["years"][1]["net_impact"] == "0.00"
    assert result["cumulative_impact"] == "-100.10"
    assert not result["is_partial"]
    assert result["warnings"][0]["code"] == "UNFUNDED"
    canonical = json.dumps(
        result["input_snapshot"], sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    assert hashlib.sha256(canonical.encode()).hexdigest() == result["input_hash"]
    published = auth_client.post(f"/api/v1/plans/{plan['id']}/publish", headers=headers(user))
    assert published.status_code == 200, published.text
    original = published.json()["data"]
    auth_client.patch(
        f"/api/v1/policies/{proposal['id']}",
        json={
            "impacts": [
                {
                    "year": 2027,
                    "impact_type": "NEW_EXPENSE",
                    "amount": "900.90",
                    "description": "Nova hipótese",
                }
            ]
        },
        headers=headers(user),
    )
    assert (
        auth_client.post(
            f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user)
        ).status_code
        == 200
    )
    public = auth_client.get(f"/api/v1/plans/{plan['slug']}").json()["data"]
    assert public == original
    assert public["version"]["policies"][0]["policy_version_id"] == proposal["version"]["id"]
    repeated = auth_client.post(
        f"/api/v1/plans/{plan['id']}/simulate", headers=headers(user)
    ).json()["data"]
    assert repeated["id"] != original["version"]["simulation"]["id"]
    assert repeated["input_hash"] == original["version"]["simulation"]["input_hash"]


def test_new_plan_version_changes_items_without_altering_old_version(auth_client):
    user, _ = signup(auth_client)
    first = published_policy(auth_client, user)
    second = published_policy(auth_client, user)
    plan = create_plan(auth_client, user, [first, second])
    assert (
        auth_client.post(f"/api/v1/plans/{plan['id']}/publish", headers=headers(user)).status_code
        == 200
    )
    update = auth_client.patch(
        f"/api/v1/plans/{plan['id']}",
        json={
            "policies": [
                {"policy_version_id": second["version"]["id"], "is_enabled": False},
                {"policy_version_id": first["version"]["id"]},
            ]
        },
        headers=headers(user),
    )
    assert update.status_code == 200, update.text
    assert update.json()["data"]["version"]["version_number"] == 2
    simulation = auth_client.post(
        f"/api/v1/plans/{plan['id']}/simulate", headers=headers(user)
    ).json()["data"]
    assert simulation["cumulative_impact"] == "-100.10"
    assert auth_client.get(f"/api/v1/plans/{plan['slug']}/versions/2").status_code == 404
    assert (
        auth_client.post(f"/api/v1/plans/{plan['id']}/publish", headers=headers(user)).status_code
        == 200
    )
    old = auth_client.get(f"/api/v1/plans/{plan['slug']}/versions/1").json()["data"]
    assert old["version"]["simulation"]["cumulative_impact"] == "-200.20"
    assert "INTERACTIONS_NOT_MODELED" in {
        warning["code"] for warning in old["version"]["simulation"]["warnings"]
    }
    assert len(auth_client.get(f"/api/v1/plans/{plan['slug']}/versions").json()["data"]) == 2


def test_draft_versions_and_duplicate_proposal_identities_are_rejected(auth_client):
    user, _ = signup(auth_client)
    proposal, _ = draft(auth_client, user)
    assert (
        auth_client.post(
            "/api/v1/plans", json=plan_input([proposal]), headers=headers(user)
        ).status_code
        == 422
    )
    v1 = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user)
    ).json()["data"]
    auth_client.patch(
        f"/api/v1/policies/{proposal['id']}", json={"title": "v2"}, headers=headers(user)
    )
    v2 = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user)
    ).json()["data"]
    assert (
        auth_client.post(
            "/api/v1/plans", json=plan_input([v1, v2]), headers=headers(user)
        ).status_code
        == 422
    )


def test_plan_authorization_and_public_privacy(auth_client):
    owner, _ = signup(auth_client)
    proposal = published_policy(auth_client, owner)
    plan = create_plan(auth_client, owner, [proposal])
    assert auth_client.post(f"/api/v1/plans/{plan['id']}/simulate").status_code == 401
    other, _ = signup(auth_client)
    for action in ("simulate", "publish", "draft"):
        assert (
            auth_client.post(
                f"/api/v1/plans/{plan['id']}/{action}", headers=headers(other)
            ).status_code
            == 403
        )
    assert auth_client.get("/api/v1/plans/mine", headers=headers(other)).json()["data"] == []
    assert (
        auth_client.patch(
            f"/api/v1/plans/{plan['id']}", json={"title": "Other"}, headers=headers(other)
        ).status_code
        == 403
    )


def test_partial_result_and_outside_period_are_explicit(auth_client):
    user, _ = signup(auth_client)
    known = published_policy(auth_client, user)
    unknown, _ = draft(auth_client, user)
    auth_client.patch(
        f"/api/v1/policies/{unknown['id']}",
        json={"financial_impact_status": "NOT_ESTIMATED", "impacts": []},
        headers=headers(user),
    )
    unknown = auth_client.post(
        f"/api/v1/policies/{unknown['id']}/publish", headers=headers(user)
    ).json()["data"]
    plan = create_plan(auth_client, user, [known, unknown])
    auth_client.patch(
        f"/api/v1/plans/{plan['id']}", json={"start_year": 2028}, headers=headers(user)
    )
    response = auth_client.post(f"/api/v1/plans/{plan['id']}/simulate", headers=headers(user))
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["is_partial"] and result["cumulative_impact"] == "0.00"
    assert {"OUTSIDE_PERIOD", "NOT_ESTIMATED"}.issubset(
        {warning["code"] for warning in result["warnings"]}
    )


def test_completed_execution_and_results_cannot_be_rewritten(auth_client, db_session):
    user, _ = signup(auth_client)
    proposal = published_policy(auth_client, user)
    plan = create_plan(auth_client, user, [proposal])
    result = auth_client.post(f"/api/v1/plans/{plan['id']}/simulate", headers=headers(user)).json()[
        "data"
    ]
    for statement in (
        "UPDATE simulations SET calculation_version='changed' WHERE id=:id",
        "DELETE FROM simulations WHERE id=:id",
        "UPDATE simulation_results SET new_expenses=0, net_impact=0 WHERE simulation_id=:id",
        "DELETE FROM simulation_results WHERE simulation_id=:id",
    ):
        with pytest.raises(IntegrityError), db_session.begin_nested():
            db_session.execute(text(statement), {"id": result["id"]})


def test_archive_preserves_published_plan(auth_client):
    user, _ = signup(auth_client)
    proposal = published_policy(auth_client, user)
    plan = create_plan(auth_client, user, [proposal])
    auth_client.post(f"/api/v1/plans/{plan['id']}/publish", headers=headers(user))
    response = auth_client.post(
        f"/api/v1/plans/{plan['id']}/archive",
        json={"reason": "Teste encerrado"},
        headers=headers(user),
    )
    assert response.status_code == 200
    assert auth_client.get("/api/v1/plans").json()["data"] == []
    public = auth_client.get(f"/api/v1/plans/{plan['slug']}")
    assert public.status_code == 200 and public.json()["data"]["status"] == "ARCHIVED"
