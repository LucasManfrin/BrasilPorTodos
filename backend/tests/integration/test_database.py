import os

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.mark.database
@pytest.mark.skipif(os.getenv("RUN_DATABASE_TESTS") != "1", reason="Requires PostgreSQL")
def test_postgres_readiness():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "ready"
