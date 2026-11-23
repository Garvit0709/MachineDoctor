
from fastapi.testclient import TestClient

from backend.main import app


def test_motor_registry_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/motors")

    assert response.status_code == 401


def test_diagnostic_history_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/diagnostic-sessions")

    assert response.status_code == 401


def test_health_endpoint_remains_public():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
