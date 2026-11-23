
import io

import pytest

from fastapi.testclient import TestClient

from backend.main import app
from backend.auth_dependencies import get_current_admin


@pytest.fixture
def client():
    """
    Test client with isolated authentication overrides.
    No real administrator credentials are required.
    """
    app.dependency_overrides[get_current_admin] = (
        lambda: object()
    )

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(
            get_current_admin,
            None,
        )


def upload(client, content, filename="test.csv"):
    return client.post(
        "/api/aura/diagnose",
        files={
            "file": (
                filename,
                io.BytesIO(content),
                "text/csv",
            )
        },
    )


def test_reject_invalid_extension(client):
    response = upload(
        client,
        b"invalid",
        filename="test.txt",
    )

    assert response.status_code == 415


def test_reject_empty_csv(client):
    response = upload(client, b"")

    assert response.status_code == 400


def test_reject_oversized_csv(client):
    content = b"a" * (2 * 1024 * 1024 + 1)

    response = upload(client, content)

    assert response.status_code == 413


def test_reject_null_bytes(client):
    response = upload(
        client,
        b"run_id,rms\nmotor\x00,0.2",
    )

    assert response.status_code == 400


def test_reject_missing_features(client):
    response = upload(
        client,
        b"run_id,time_start,time_end,rms\n"
        b"test,0,1,0.2\n",
    )

    assert response.status_code == 422


def test_public_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200


def test_motor_registry_requires_authentication():
    with TestClient(app) as client:
        response = client.get("/api/motors")

    assert response.status_code == 401


def test_aura_requires_authentication():
    with TestClient(app) as client:
        response = upload(
            client,
            b"run_id,rms\nmotor,0.2",
        )

    assert response.status_code == 401
