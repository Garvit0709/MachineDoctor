
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
    monkeypatch.setattr(
        auth_service,
        "JWT_SECRET_KEY",
        "unit-test-secret-not-for-production-use",
    )

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

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def test_login_success(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testadmin",
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "testadmin",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401


def test_profile_requires_token(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401


def test_profile_with_valid_token(client):
    login = client.post(
        "/api/auth/login",
        json={
            "username": "testadmin",
            "password": "TestPassword123!",
        },
    )

    token = login.json()["access_token"]

    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200
    assert response.json()["username"] == "testadmin"


def test_profile_rejects_invalid_token(client):
    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": "Bearer invalid.token.value"
        },
    )

    assert response.status_code == 401
