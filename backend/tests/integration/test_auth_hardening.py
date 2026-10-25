from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from sqlalchemy import select

from app.modules.auth import service
from app.modules.auth.models import AuthSession
from app.modules.users.models import User

from .test_admin_indicators import administrator
from .test_auth import TEST_SECRET, signup
from .test_policies import headers

pytestmark = pytest.mark.database


def claims_for(result):
    return jwt.decode(
        result["access_token"], TEST_SECRET, algorithms=["HS256"], audience="brasil-portodos-api"
    )


def read_me(client, claims):
    token = jwt.encode(claims, TEST_SECRET, algorithm="HS256")
    return client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})


@pytest.mark.parametrize(
    "missing", ["sub", "sid", "jti", "type", "iat", "nbf", "exp", "iss", "aud"]
)
def test_missing_required_claim_is_rejected(auth_client, missing):
    result, _ = signup(auth_client)
    claims = claims_for(result)
    del claims[missing]
    assert read_me(auth_client, claims).status_code == 401


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("iss", "foreign-issuer"),
        ("aud", "foreign-api"),
        ("type", "refresh"),
        ("sid", []),
        ("sid", 1),
        ("sid", "not-a-uuid"),
        ("sub", "not-a-uuid"),
    ],
)
def test_invalid_claims_fail_closed_without_server_error(auth_client, name, value):
    result, _ = signup(auth_client)
    claims = claims_for(result)
    claims[name] = value
    assert read_me(auth_client, claims).status_code == 401


def test_not_yet_valid_token_is_rejected(auth_client):
    result, _ = signup(auth_client)
    claims = claims_for(result)
    claims["nbf"] = datetime.now(UTC) + timedelta(minutes=10)
    assert read_me(auth_client, claims).status_code == 401


def test_session_from_another_account_cannot_be_used(auth_client):
    first, _ = signup(auth_client)
    second, _ = signup(auth_client)
    claims = claims_for(first)
    claims["sid"] = claims_for(second)["sid"]
    assert read_me(auth_client, claims).status_code == 401


def test_role_claim_cannot_override_database_role(auth_client):
    result, _ = signup(auth_client)
    claims = claims_for(result)
    claims["role"] = "ADMIN"
    token = jwt.encode(claims, TEST_SECRET, algorithm="HS256")
    response = auth_client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_admin_demotion_takes_effect_for_existing_access_token(auth_client, db_session):
    actor = administrator(auth_client, db_session)
    assert auth_client.get("/api/v1/admin/users", headers=headers(actor)).status_code == 200
    db_session.get(User, UUID(actor["user"]["id"])).role = "USER"
    db_session.commit()
    assert auth_client.get("/api/v1/admin/users", headers=headers(actor)).status_code == 403


def test_deactivation_revokes_all_sessions_even_after_reactivation(auth_client, db_session):
    first, data = signup(auth_client)
    credentials = [(first, auth_client.cookies.get("bpt_refresh"))]
    second = auth_client.post(
        "/api/v1/auth/login", json={"email": data["email"], "password": data["password"]}
    ).json()["data"]
    credentials.append((second, auth_client.cookies.get("bpt_refresh")))
    actor = administrator(auth_client, db_session)
    path = f"/api/v1/admin/users/{first['user']['id']}"
    for active in [False, True]:
        response = auth_client.patch(
            path,
            json={"is_active": active, "reason": "Isolated suspension regression"},
            headers=headers(actor),
        )
        assert response.status_code == 200
    sessions = db_session.scalars(
        select(AuthSession).where(AuthSession.user_id == UUID(first["user"]["id"]))
    ).all()
    assert len(sessions) == 2 and all(row.revoked_at for row in sessions)
    for result, refresh in credentials:
        assert auth_client.get("/api/v1/auth/me", headers=headers(result)).status_code == 401
        assert (
            auth_client.post(
                "/api/v1/auth/refresh",
                headers={"Cookie": f"bpt_refresh={refresh}", "X-CSRF-Token": result["csrf_token"]},
            ).status_code
            == 401
        )
    # A fresh login after explicit reactivation works; old credentials stay invalid.
    assert (
        auth_client.post(
            "/api/v1/auth/login", json={"email": data["email"], "password": data["password"]}
        ).status_code
        == 200
    )


def test_empty_identity_uses_ip_limit_without_accidental_eight_request_limit(db_session):
    client = "isolated-test-" + uuid4().hex
    for _ in range(30):
        service.consume_rate_limits(db_session, "refresh", client)
    from app.core.errors import DomainError

    with pytest.raises(DomainError) as error:
        service.consume_rate_limits(db_session, "refresh", client)
    assert error.value.status == 429


def test_forwarded_ip_headers_do_not_bypass_login_limit(auth_client):
    for attempt in range(9):
        response = auth_client.post(
            "/api/v1/auth/login",
            json={"email": "unknown-audit@example.com", "password": "wrong-password"},
            headers={
                "X-Forwarded-For": f"192.0.2.{attempt + 1}",
                "X-Real-IP": f"192.0.2.{attempt + 1}",
            },
        )
        assert response.status_code == (401 if attempt < 8 else 429)


def test_admin_cannot_promote_user_with_extra_role_field(auth_client, db_session):
    target, _ = signup(auth_client)
    actor = administrator(auth_client, db_session)
    response = auth_client.patch(
        f"/api/v1/admin/users/{target['user']['id']}",
        json={"is_active": True, "reason": "Test", "role": "ADMIN"},
        headers=headers(actor),
    )
    assert response.status_code == 422
    assert db_session.get(User, UUID(target["user"]["id"])).role == "USER"
