
from fastapi.testclient import TestClient

from backend.main import app
from backend.auth_router import limiter


def test_login_rate_limit():
    # Reset in-memory counters for test isolation.
    limiter._storage.reset()

    try:
        with TestClient(app) as client:
            responses = []

            for _ in range(6):
                response = client.post(
                    "/api/auth/login",
                    json={
                        "username": "nonexistent_admin",
                        "password": "IncorrectPassword123!",
                    },
                )
                responses.append(response.status_code)

        assert responses[:5] == [401] * 5
        assert responses[5] == 429

    finally:
        limiter._storage.reset()


def test_health_endpoint_not_rate_limited():
    with TestClient(app) as client:
        for _ in range(6):
            response = client.get("/api/health")
            assert response.status_code == 200
