
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.main import app


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    def override_get_db():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(engine)
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

    assert response.status_code == 201
    assert response.json()["motor_code"] == "MTR-001"


def test_list_motors(client):
    client.post("/api/motors", json=sample_motor())

    response = client.get("/api/motors")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_duplicate_motor_code(client):
    client.post("/api/motors", json=sample_motor())

    response = client.post(
        "/api/motors",
        json=sample_motor(),
    )

    assert response.status_code == 409


def test_update_motor(client):
    created = client.post(
        "/api/motors",
        json=sample_motor(),
    ).json()

    response = client.patch(
        f"/api/motors/{created['id']}",
        json={"name": "Updated Motor"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Motor"


def test_create_bearing(client):
    motor = client.post(
        "/api/motors",
        json=sample_motor(),
    ).json()

    response = client.post(
        f"/api/motors/{motor['id']}/bearings",
        json={
            "bearing_code": "BRG-DE-001",
            "position": "DRIVE_END",
            "bearing_type": "Ball Bearing",
        },
    )

    assert response.status_code == 201
    assert response.json()["motor_id"] == motor["id"]


def test_delete_motor(client):
    motor = client.post(
        "/api/motors",
        json=sample_motor(),
    ).json()

    response = client.delete(
        f"/api/motors/{motor['id']}"
    )

    assert response.status_code == 204

    response = client.get(
        f"/api/motors/{motor['id']}"
    )

    assert response.status_code == 404


def test_invalid_rpm(client):
    payload = sample_motor()
    payload["rated_rpm"] = -100

    response = client.post(
        "/api/motors",
        json=payload,
    )

    assert response.status_code == 422
