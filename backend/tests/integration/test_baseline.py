import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from .test_admin_indicators import administrator, definition, observation
from .test_plans import create_plan
from .test_policies import draft, headers, source_data

pytestmark = pytest.mark.database


def setup_series(client, session):
    actor = administrator(client, session)
    source = client.post("/api/v1/sources", json=source_data(), headers=headers(actor)).json()[
        "data"
    ]
    indicator = client.post(
        "/api/v1/admin/indicators", json=definition(), headers=headers(actor)
    ).json()["data"]
    value = observation(source["id"])
    client.post(
        f"/api/v1/admin/indicators/{indicator['id']}/values", json=value, headers=headers(actor)
    )
    return actor, indicator, value


def test_publication_and_simulation_keep_baseline_when_official_series_is_revised(
    auth_client, db_session
):
    actor, indicator, value = setup_series(auth_client, db_session)
    policy, _ = draft(auth_client, actor)
    frozen = policy["version"]["baseline_snapshot"]
    assert frozen["status"] == "PARTIAL" and len(frozen["observations"]) == 1
    policy = auth_client.post(
        f"/api/v1/policies/{policy['id']}/publish", headers=headers(actor)
    ).json()["data"]
    plan = create_plan(auth_client, actor, [policy])
    published = auth_client.post(
        f"/api/v1/plans/{plan['id']}/publish", headers=headers(actor)
    ).json()["data"]
    value["value"] = "7.000000"
    auth_client.post(
        f"/api/v1/admin/indicators/{indicator['id']}/values", json=value, headers=headers(actor)
    )
    current = auth_client.get("/api/v1/indicators/baseline/current").json()["data"]
    assert current["id"] != frozen["id"]
    assert (
        auth_client.get(f"/api/v1/policies/{policy['slug']}").json()["data"]["version"][
            "baseline_snapshot"
        ]
        == frozen
    )
    saved = auth_client.get(f"/api/v1/plans/{plan['slug']}").json()["data"]
    assert saved == published
    repeated = auth_client.post(
        f"/api/v1/plans/{plan['id']}/simulate", headers=headers(actor)
    ).json()["data"]
    assert repeated["input_hash"] == published["version"]["simulation"]["input_hash"]
    assert repeated["input_snapshot"]["baseline_snapshot"]["id"] == frozen["id"]
    with pytest.raises(IntegrityError), db_session.begin_nested():
        db_session.execute(
            text("UPDATE policy_versions SET baseline_snapshot='{}'::jsonb WHERE id=:id"),
            {"id": policy["version"]["id"]},
        )


def test_refresh_is_explicit_on_draft_and_retrieval_url_does_not_create_false_revision(
    auth_client, db_session
):
    actor, indicator, value = setup_series(auth_client, db_session)
    policy, _ = draft(auth_client, actor)
    before = policy["version"]["baseline_snapshot"]
    value["provenance"]["request_url"] = "https://example.com/different-interval"
    repeated = auth_client.post(
        f"/api/v1/admin/indicators/{indicator['id']}/values", json=value, headers=headers(actor)
    ).json()["data"]
    assert repeated["revision"] == 1
    value["value"] = "9.000000"
    auth_client.post(
        f"/api/v1/admin/indicators/{indicator['id']}/values", json=value, headers=headers(actor)
    )
    unchanged = auth_client.patch(
        f"/api/v1/policies/{policy['id']}",
        json={"title": "Alteração de texto"},
        headers=headers(actor),
    ).json()["data"]
    assert unchanged["version"]["baseline_snapshot"] == before
    refreshed = auth_client.patch(
        f"/api/v1/policies/{policy['id']}", json={"refresh_baseline": True}, headers=headers(actor)
    ).json()["data"]
    assert refreshed["version"]["baseline_snapshot"]["id"] != before["id"]
    assert len(auth_client.get("/api/v1/indicators/indicator-test").json()["data"]["series"]) == 1
