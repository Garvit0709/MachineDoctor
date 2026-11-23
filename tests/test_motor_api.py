import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend import auth_service
from backend.database import Base, get_db
from backend.main import app
from backend.models import Administrator



@pytest.fixture
def client(monkeypatch):
    # Configure a test-only JWT secret.
    monkeypatch.setattr(
        auth_service,
        "JWT_SECRET_KEY",
        "machinedoctor-test-secret-2026-long-enough-for-hs256",
    )

    # Create an isolated in-memory test database.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db

    try:
        # Create a test administrator.
        with Session(engine) as db:
            administrator = Administrator(
                username="testadmin",
                password_hash=auth_service.hash_password(
                    "TestPassword123!"
                ),
                is_active=True,
            )

            db.add(administrator)
            db.commit()
            administrator_id = administrator.id

        # Generate a valid JWT for the administrator.
        token = auth_service.create_access_token(
            administrator_id
        )

        with TestClient(app) as test_client:
            # All Motor Registry requests use this token.
            test_client.headers.update({
                "Authorization": f"Bearer {token}",
            })

            # Verify authentication before running tests.
            auth_response = test_client.get("/api/auth/me")

            assert auth_response.status_code == 200, (
                "Test administrator authentication failed: "
                f"{auth_response.status_code} "
                f"{auth_response.text}"
            )

            yield test_client

    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()

def sample_motor():
    return {
        "motor_code": "MTR-001",
        "name": "Test Motor",
        "location": "Laboratory",
        "rated_rpm": 1500,
    }


def test_create_motor(client):
    response = client.post(
        "/api/motors",
        json=sample_motor(),
    )

    assert response.status_code == 201, response.text
    assert response.json()["motor_code"] == "MTR-001"


def test_list_motors(client):
    created = client.post(
        "/api/motors",
        json=sample_motor(),
    )

    assert created.status_code == 201, created.text

    response = client.get("/api/motors")

    assert response.status_code == 200, response.text
    assert len(response.json()) == 1


def test_duplicate_motor_code(client):
    first = client.post(
        "/api/motors",
        json=sample_motor(),
    )

    assert first.status_code == 201, first.text

    response = client.post(
        "/api/motors",
        json=sample_motor(),
    )

    assert response.status_code == 409, response.text


def test_update_motor(client):
    response = client.post(
        "/api/motors",
        json=sample_motor(),
    )

    assert response.status_code == 201, response.text
    motor_id = response.json()["id"]

    updated = client.patch(
        f"/api/motors/{motor_id}",
        json={"name": "Updated Motor"},
    )

    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Updated Motor"


def test_create_bearing(client):
    response = client.post(
        "/api/motors",
        json=sample_motor(),
    )

    assert response.status_code == 201, response.text
    motor_id = response.json()["id"]

    bearing = client.post(
        f"/api/motors/{motor_id}/bearings",
        json={
            "bearing_code": "BRG-DE-001",
            "position": "DRIVE_END",
            "bearing_type": "Ball Bearing",
        },
    )

    assert bearing.status_code == 201, bearing.text
    assert bearing.json()["motor_id"] == motor_id


def test_delete_motor(client):
    response = client.post(
        "/api/motors",
        json=sample_motor(),
    )

    assert response.status_code == 201, response.text
    motor_id = response.json()["id"]

    deleted = client.delete(
        f"/api/motors/{motor_id}"
    )

    assert deleted.status_code == 204, deleted.text

    retrieved = client.get(
        f"/api/motors/{motor_id}"
    )

    assert retrieved.status_code == 404, retrieved.text


def test_invalid_rpm(client):
    payload = sample_motor()
    payload["rated_rpm"] = -100

    response = client.post(
        "/api/motors",
        json=payload,
    )

    assert response.status_code == 422, response.text
