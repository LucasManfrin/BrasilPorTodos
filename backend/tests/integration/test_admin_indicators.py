from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.modules.users.models import User

from .test_auth import signup
from .test_policies import draft, headers
from .test_sources import source_data

pytestmark = pytest.mark.database


def administrator(client, session):
    result, _ = signup(client)
    session.get(User, UUID(result["user"]["id"])).role = "ADMIN"
    session.commit()
    return result


def definition():
    return {
        "code": "indicator-test",
        "name": "Indicador fictício de teste",
        "description": "Somente dados de teste",
        "category": "ECONOMY",
        "unit": "%",
        "frequency": "MONTHLY",
        "scope": "Teste",
        "methodology": "Método fictício",
        "reason": "Configuração de teste",
    }


def observation(source_id):
    return {
        "reference_date": "2025-01-01",
        "value": "1.234567",
        "source_id": source_id,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "revision_reason": "Importação de teste",
        "provenance": {
            "dataset_url": "https://example.com/series",
            "license": "Test-only",
            "license_url": "https://example.com/terms",
            "method": "Fictício",
            "institution": "Teste",
        },
    }


def test_indicator_history_keeps_revisions_idempotence_and_definition(auth_client, db_session):
    actor = administrator(auth_client, db_session)
    source = auth_client.post("/api/v1/sources", json=source_data(), headers=headers(actor)).json()[
        "data"
    ]
    indicator = auth_client.post(
        "/api/v1/admin/indicators", json=definition(), headers=headers(actor)
    ).json()["data"]
    assert indicator["latest"] is None and indicator["data_status"] == "NO_DATA"
    url = f"/api/v1/admin/indicators/{indicator['id']}/values"
    payload = observation(source["id"])
    first = auth_client.post(url, json=payload, headers=headers(actor))
    assert first.status_code == 201, first.text
    repeated = auth_client.post(url, json=payload, headers=headers(actor))
    assert repeated.json()["data"]["id"] == first.json()["data"]["id"]
    payload["value"] = "2.000001"
    revised = auth_client.post(url, json=payload, headers=headers(actor))
    assert revised.json()["data"]["revision"] == 2
    public = auth_client.get("/api/v1/indicators/indicator-test").json()["data"]
    assert public["latest"]["value"] == "2.000001"
    assert len(public["history"]) == 2
    changed = {**definition(), "unit": "R$"}
    assert (
        auth_client.put(
            f"/api/v1/admin/indicators/{indicator['id']}", json=changed, headers=headers(actor)
        ).status_code
        == 409
    )
    audit = auth_client.get("/api/v1/admin/audit", headers=headers(actor)).json()["data"]
    assert len(audit) == 3
    for sql, record_id in (
        ("UPDATE indicator_values SET value=9 WHERE id=:id", first.json()["data"]["id"]),
        ("DELETE FROM audit_events WHERE id=:id", audit[0]["id"]),
    ):
        with pytest.raises(IntegrityError), db_session.begin_nested():
            db_session.execute(text(sql), {"id": record_id})


def test_admin_permissions_user_deactivation_and_archiving_are_audited(auth_client, db_session):
    user, _ = signup(auth_client)
    assert auth_client.get("/api/v1/admin/users").status_code == 401
    assert auth_client.get("/api/v1/admin/users", headers=headers(user)).status_code == 403
    proposal, _ = draft(auth_client, user)
    auth_client.post(f"/api/v1/policies/{proposal['id']}/publish", headers=headers(user))
    actor = administrator(auth_client, db_session)
    archived = auth_client.post(
        f"/api/v1/policies/{proposal['id']}/archive",
        json={"reason": "Moderação de teste"},
        headers=headers(actor),
    )
    assert archived.status_code == 200
    assert (
        auth_client.get(f"/api/v1/policies/{proposal['slug']}").json()["data"]["status"]
        == "ARCHIVED"
    )
    change = auth_client.patch(
        f"/api/v1/admin/users/{user['user']['id']}",
        json={"is_active": False, "reason": "Teste"},
        headers=headers(actor),
    )
    assert change.status_code == 200
    assert auth_client.get("/api/v1/auth/me", headers=headers(user)).status_code == 401
    assert (
        auth_client.patch(
            f"/api/v1/admin/users/{actor['user']['id']}",
            json={"is_active": False, "reason": "Teste"},
            headers=headers(actor),
        ).status_code
        == 409
    )
    events = auth_client.get("/api/v1/admin/audit", headers=headers(actor)).json()["data"]
    assert {row["action"] for row in events} == {"ARCHIVE", "DEACTIVATE"}
    assert all(
        row["actor_id"] == actor["user"]["id"] and row["created_at"] and row["reason"]
        for row in events
    )
    users = auth_client.get("/api/v1/admin/users", headers=headers(actor)).json()["data"]
    assert all("email" not in row and "password_hash" not in row for row in users)


def test_future_or_unattributed_indicator_values_are_refused(auth_client, db_session):
    actor = administrator(auth_client, db_session)
    source = auth_client.post("/api/v1/sources", json=source_data(), headers=headers(actor)).json()[
        "data"
    ]
    indicator = auth_client.post(
        "/api/v1/admin/indicators", json=definition(), headers=headers(actor)
    ).json()["data"]
    url = f"/api/v1/admin/indicators/{indicator['id']}/values"
    payload = observation(source["id"])
    payload["reference_date"] = (datetime.now(UTC).date() + timedelta(days=1)).isoformat()
    assert (
        auth_client.post(url, json=payload, headers=headers(actor)).json()["error"]["code"]
        == "FUTURE_OBSERVATION"
    )
    payload = observation(source["id"])
    payload["provenance"] = {}
    assert (
        auth_client.post(url, json=payload, headers=headers(actor)).json()["error"]["code"]
        == "PROVENANCE_REQUIRED"
    )
