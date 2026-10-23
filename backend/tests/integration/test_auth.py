from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings, get_settings
from app.database.session import get_session
from app.main import create_app
from app.modules.auth.models import RefreshToken
from app.modules.users.models import User

pytestmark = pytest.mark.database
TEST_SECRET = "test-only-signing-key-with-at-least-32-characters"


def signup(client):
    identifier = uuid4().hex
    data = {
        "name": "Pessoa Teste",
        "username": identifier,
        "email": f"{identifier}@example.com",
        "password": "password-test-only-123",
    }
    response = client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 201, response.text
    return response.json()["data"], data


def test_signup_login_me_and_password_storage(auth_client, db_session):
    result, data = signup(auth_client)
    user = db_session.scalar(select(User).where(User.email == data["email"]))
    assert user.password_hash.startswith("$argon2id$")
    assert user.password_hash != data["password"]
    assert "password" not in result["user"]
    assert result["user"]["role"] == "USER"
    me = auth_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {result['access_token']}"}
    )
    assert me.status_code == 200
    assert me.json()["data"]["email"] == data["email"]
    assert me.headers["Cache-Control"] == "no-store"
    login = auth_client.post(
        "/api/v1/auth/login", json={"email": data["email"].upper(), "password": data["password"]}
    )
    assert login.status_code == 200
    assert login.headers["Cache-Control"] == "no-store"
    cookies = login.headers.get_list("set-cookie")
    refresh_cookie = next(cookie for cookie in cookies if cookie.startswith("bpt_refresh="))
    assert "HttpOnly" in refresh_cookie and "Secure" in refresh_cookie
    assert "SameSite=strict" in refresh_cookie and "Path=/api/v1/auth" in refresh_cookie
    raw_refresh = auth_client.cookies.get("bpt_refresh")
    token = db_session.scalar(select(RefreshToken).order_by(RefreshToken.created_at.desc()))
    assert token.token_hash != raw_refresh
    assert token.csrf_hash != result["csrf_token"]


def test_refresh_rotation_replay_revokes_the_session(auth_client):
    result, _ = signup(auth_client)
    old_refresh = auth_client.cookies.get("bpt_refresh")
    renewed = auth_client.post(
        "/api/v1/auth/refresh", headers={"X-CSRF-Token": result["csrf_token"]}
    )
    assert renewed.status_code == 200
    assert auth_client.cookies.get("bpt_refresh") != old_refresh
    current_token = renewed.json()["data"]["access_token"]
    replay = auth_client.post(
        "/api/v1/auth/refresh",
        headers={"Cookie": f"bpt_refresh={old_refresh}", "X-CSRF-Token": result["csrf_token"]},
    )
    assert replay.status_code == 401
    assert replay.json()["error"]["code"] == "REFRESH_REUSED"
    assert (
        auth_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {current_token}"}
        ).status_code
        == 401
    )


def test_logout_invalidates_access_immediately(auth_client):
    result, _ = signup(auth_client)
    logout = auth_client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": result["csrf_token"]})
    assert logout.status_code == 200
    assert not auth_client.cookies.get("bpt_refresh")
    me = auth_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {result['access_token']}"}
    )
    assert me.status_code == 401


@pytest.mark.parametrize("origin", ["http://localhost:3000", "http://127.0.0.1:3000"])
def test_csrf_and_origin_rejection(auth_client, origin):
    result, _ = signup(auth_client)
    assert auth_client.post("/api/v1/auth/refresh").status_code == 403
    assert (
        auth_client.post("/api/v1/auth/refresh", headers={"X-CSRF-Token": "invalid"}).status_code
        == 403
    )
    assert (
        auth_client.post(
            "/api/v1/auth/refresh",
            headers={"X-CSRF-Token": result["csrf_token"], "Origin": "https://untrusted.example"},
        ).status_code
        == 403
    )
    assert (
        auth_client.post(
            "/api/v1/auth/refresh",
            headers={"X-CSRF-Token": result["csrf_token"], "Origin": origin},
        ).status_code
        == 200
    )


def test_unknown_account_and_wrong_password_have_same_error(auth_client):
    _, data = signup(auth_client)
    wrong = auth_client.post(
        "/api/v1/auth/login", json={"email": data["email"], "password": "wrong-password"}
    )
    unknown = auth_client.post(
        "/api/v1/auth/login", json={"email": "unknown@example.com", "password": "wrong-password"}
    )
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_login_rate_limit_counts_failed_credentials(auth_client):
    for _ in range(8):
        assert (
            auth_client.post(
                "/api/v1/auth/login",
                json={"email": "unknown@example.com", "password": "wrong-password"},
            ).status_code
            == 401
        )
    response = auth_client.post(
        "/api/v1/auth/login", json={"email": "unknown@example.com", "password": "wrong-password"}
    )
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "60"


def test_admin_assignment_and_weak_password_are_rejected(auth_client):
    _, data = signup(auth_client)
    assert (
        auth_client.post("/api/v1/auth/register", json={**data, "role": "ADMIN"}).status_code == 422
    )
    assert (
        auth_client.post("/api/v1/auth/register", json={**data, "password": "short"}).status_code
        == 422
    )
    assert auth_client.post("/api/v1/auth/register", json=data).status_code == 409


def test_inactive_account_cannot_use_access_or_refresh(auth_client, db_session):
    result, data = signup(auth_client)
    user = db_session.scalar(select(User).where(User.email == data["email"]))
    user.is_active = False
    db_session.commit()
    assert (
        auth_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {result['access_token']}"}
        ).status_code
        == 401
    )
    assert (
        auth_client.post(
            "/api/v1/auth/refresh", headers={"X-CSRF-Token": result["csrf_token"]}
        ).status_code
        == 401
    )


def test_missing_expired_or_modified_jwt_is_rejected(auth_client):
    assert auth_client.get("/api/v1/auth/me").status_code == 401
    result, _ = signup(auth_client)
    claims = jwt.decode(
        result["access_token"], TEST_SECRET, algorithms=["HS256"], audience="brasil-portodos-api"
    )
    claims["exp"] = datetime.now(UTC) - timedelta(seconds=1)
    expired = jwt.encode(claims, TEST_SECRET, algorithm="HS256")
    assert (
        auth_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {expired}"}
        ).status_code
        == 401
    )
    tampered = jwt.encode(claims, "different-key-with-32-plus-characters", algorithm="HS256")
    assert (
        auth_client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {tampered}"}
        ).status_code
        == 401
    )


def test_missing_signing_secret_fails_closed(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(jwt_secret=None)
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login", json={"email": "unknown@example.com", "password": "test-password"}
        )
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "AUTH_NOT_CONFIGURED"
