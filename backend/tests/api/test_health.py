from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.database.session import get_session
from app.main import create_app


def test_health_is_public_and_does_not_need_a_database():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"data": {"status": "ok"}}
        assert response.headers["X-Request-ID"]


def test_ready_requires_database_connectivity():
    class UnavailableSession:
        def execute(self, statement):
            raise OperationalError("SELECT 1", {}, Exception("private-db-details"))

    app = create_app()
    app.dependency_overrides[get_session] = lambda: UnavailableSession()
    with TestClient(app) as client:
        response = client.get("/api/v1/ready")
        assert response.status_code == 503
        assert response.json()["error"]["code"] == "DATABASE_UNAVAILABLE"
        assert "private-db-details" not in response.text


def test_ready_contract_when_database_is_available():
    class AvailableSession:
        def execute(self, statement):
            assert str(statement) == "SELECT 1"

    app = create_app()
    app.dependency_overrides[get_session] = lambda: AvailableSession()
    with TestClient(app) as client:
        response = client.get("/api/v1/ready")
        assert response.status_code == 200
        assert response.json() == {"data": {"status": "ready"}}


def test_missing_route_uses_error_envelope():
    with TestClient(create_app()) as client:
        response = client.get("/api/v1/missing")
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "HTTP_404"
