import logging

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import StatementError

from app.core.config import Settings
from app.database.session import get_session
from app.main import create_app
from app.modules.guidance.settings import GuidanceSettings
from app.modules.ideas.settings import IdeaSettings


@pytest.mark.parametrize("environment", ["production", "staging", "Development", "unknown"])
def test_insecure_cookie_configuration_fails_closed_outside_development(environment):
    with pytest.raises(ValidationError, match="COOKIE_SECURE"):
        Settings(_env_file=None, environment=environment, cookie_secure=False)


@pytest.mark.parametrize("environment", ["production", "development", "staging"])
def test_secure_cookies_work_in_all_environments(environment):
    settings = Settings(_env_file=None, environment=environment, cookie_secure=True)
    assert settings.cookie_secure is True


def test_http_development_remains_explicitly_supported():
    settings = Settings(_env_file=None, environment="development", cookie_secure=False)
    assert settings.cookie_secure is False


def test_whitespace_signing_key_is_rejected():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None, environment="production", cookie_secure=True, jwt_secret=" " * 40)


def test_private_sql_errors_are_not_exposed_in_responses_or_logs(monkeypatch, caplog):
    private = "private-fixture-password-draft-content"
    app = create_app()

    def unavailable_database():
        raise StatementError(
            f"driver-error-with-{private}",
            "INSERT INTO private_table (payload) VALUES (:payload)",
            {"payload": private},
            Exception(private),
        )

    app.dependency_overrides[get_session] = unavailable_database
    logger = logging.getLogger("brasil_portodos.http")
    monkeypatch.setattr(logger, "propagate", True)
    with caplog.at_level(logging.INFO, logger="brasil_portodos.http"), TestClient(app) as client:
        response = client.get("/api/v1/ready")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "DATABASE_ERROR"
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Request-ID"] in caplog.text
    assert "StatementError" in caplog.text
    assert private not in response.text + caplog.text
    assert "INSERT INTO" not in caplog.text


@pytest.mark.parametrize("kind", ["core", "guidance", "ideas"])
def test_configuration_errors_do_not_echo_private_input(kind):
    private = "private-fixture-value-never-log"
    constructors = {
        "core": (
            Settings,
            {
                "environment": "production",
                "cookie_secure": False,
                "jwt_secret": private + "-long-enough",
                "database_url": f"postgresql+psycopg://fixture:{private}@localhost/example",
            },
        ),
        "guidance": (
            GuidanceSettings,
            {
                "gemini_api_key": private,
                "guidance_model": private,
            },
        ),
        "ideas": (IdeaSettings, {"ideas_daily_limit": private}),
    }
    settings_type, payload = constructors[kind]
    with pytest.raises(ValidationError) as caught:
        settings_type(_env_file=None, **payload)
    assert private not in str(caught.value)
    assert "input_value" not in str(caught.value)
