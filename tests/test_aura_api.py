
import io

import pandas as pd
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend import aura_inference, auth_service
from backend.database import Base, get_db
from backend.main import app
from backend.models import Administrator


@pytest.fixture
def client(monkeypatch):
    """
    Authenticated AURA API test client using
    an isolated in-memory SQLite database.
    """

    monkeypatch.setattr(
        auth_service,
        "JWT_SECRET_KEY",
        "machinedoctor-test-secret-2026-long-enough-for-hs256",
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

    try:
        with Session(engine) as db:
            administrator = Administrator(
                username="aura_test_admin",
                password_hash=auth_service.hash_password(
                    "TestPassword123!"
                ),
                is_active=True,
            )

            db.add(administrator)
            db.commit()

            administrator_id = administrator.id

        token = auth_service.create_access_token(
            administrator_id
        )

        with TestClient(app) as test_client:
            test_client.headers.update({
                "Authorization": f"Bearer {token}"
            })

            # Confirm authentication is working.
            auth_response = test_client.get("/api/auth/me")

            assert auth_response.status_code == 200, (
                auth_response.text
            )

            yield test_client

    finally:
        app.dependency_overrides.pop(get_db, None)
        engine.dispose()


def sample_features():
    return pd.DataFrame({
        "run_id": ["motor_01"] * 5,
        "time_start": [0, 0.5, 1.0, 1.5, 2.0],
        "time_end": [0.5, 1.0, 1.5, 2.0, 2.5],
        "rms": [0.2, 0.21, 0.22, 0.25, 0.3],
        "crest_factor": [2.1, 2.2, 2.3, 2.4, 2.5],
        "kurtosis": [3.0, 3.1, 3.2, 3.4, 3.6],
        "rpm": [1500, 1510, 1520, 1530, 1540],
        "rpm_acceleration": [20] * 5,
    })


def upload(client, data, filename="features.csv"):
    return client.post(
        "/api/aura/diagnose",
        files={
            "file": (
                filename,
                io.BytesIO(data),
                "text/csv",
            )
        },
    )


def test_diagnostic_endpoint(client, monkeypatch):
    class FakeModel:
        def predict_sequence(self, data):
            return pd.DataFrame({
                "state": [
                    "UNKNOWN",
                    "UNKNOWN",
                    "NORMAL",
                    "NORMAL",
                    "WARNING",
                ],
                "reason": ["test"] * len(data),
                "persistent_score": [0.1] * len(data),
                "instantaneous_score": [0.2] * len(data),
                "uncertainty_distance": [0.3] * len(data),
                "memory_size": [1, 2, 3, 4, 5],
            })

    metadata = {
        "model_name": "test_model",
        "model_version": "aura-v0.1",
        "feature_columns": [
            "rms",
            "crest_factor",
            "kurtosis",
        ],
        "condition_columns": [
            "rpm",
            "rpm_acceleration",
        ],
        "uncertainty_threshold": 2.5,
        "persistence_threshold": 1.2,
    }

    monkeypatch.setattr(
        aura_inference,
        "get_aura_model",
        lambda: (FakeModel(), metadata),
    )

    data = sample_features().to_csv(
        index=False
    ).encode()

    response = upload(client, data)

    assert response.status_code == 200, response.text

    result = response.json()

    assert result["total_windows"] == 5
    assert result["state_counts"]["WARNING"] == 1


def test_missing_columns(client):
    data = pd.DataFrame({
        "time_start": [0, 1, 2],
        "time_end": [1, 2, 3],
    }).to_csv(index=False).encode()

    response = upload(client, data)

    assert response.status_code == 422, response.text


def test_invalid_extension(client):
    response = upload(
        client,
        b"invalid",
        filename="features.txt",
    )

    assert response.status_code == 415, response.text


def test_multiple_runs_rejected(client):
    data = sample_features()

    data.loc[4, "run_id"] = "another_motor"

    response = upload(
        client,
        data.to_csv(index=False).encode(),
    )

    assert response.status_code == 422, response.text


def test_aura_requires_authentication():
    """
    Unauthenticated inference must be rejected.
    """

    with TestClient(app) as test_client:
        response = test_client.post(
            "/api/aura/diagnose",
            files={
                "file": (
                    "features.csv",
                    b"invalid",
                    "text/csv",
                )
            },
        )

    assert response.status_code == 401, response.text
