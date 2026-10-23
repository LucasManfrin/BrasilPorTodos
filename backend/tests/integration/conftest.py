import os

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.database.session import get_session
from app.main import create_app


@pytest.fixture(autouse=True)
def isolated_test_settings(monkeypatch):
    # Integration security assertions must not inherit the local development .env.
    # DATABASE_URL remains the explicit isolated database chosen by the test runner.
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("COOKIE_SECURE", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def db_session():
    if os.getenv("RUN_DATABASE_TESTS") != "1":
        pytest.skip("Requires PostgreSQL; set RUN_DATABASE_TESTS=1")
    engine = create_engine(get_settings().database_url, connect_args={"options": "-c timezone=UTC"})
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


@pytest.fixture
def auth_client(db_session):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db_session
    app.dependency_overrides[get_settings] = lambda: Settings(
        jwt_secret=SecretStr("test-only-signing-key-with-at-least-32-characters")
    )
    with TestClient(app, base_url="https://testserver") as client:
        yield client
