
import io

import numpy as np
import pandas as pd

from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def make_csv(
    frequency=25.0,
    sampling_rate=2000,
    duration=2.0,
):
    t = np.arange(
        0,
        duration,
        1.0 / sampling_rate,
    )

    signal = np.sin(
        2 * np.pi * frequency * t
    )

    data = pd.DataFrame({
        "time_s": t,
        "vibration": signal,
    })

    return data.to_csv(
        index=False
    ).encode("utf-8")


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "operational"


def test_signal_analysis():
    response = client.post(
        "/api/signals/analyze",
        files={
            "file": (
                "healthy.csv",
                io.BytesIO(make_csv()),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["status"] == "processed"
    assert result["aura_inference_performed"] is False

    assert abs(
        result["features"]["rms"]
        - np.sqrt(0.5)
    ) < 0.01

    assert abs(
        result["features"]["dominant_frequency"]
        - 25.0
    ) < 1.0


def test_invalid_extension():
    response = client.post(
        "/api/signals/analyze",
        files={
            "file": (
                "invalid.txt",
                io.BytesIO(b"invalid"),
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_missing_columns():
    response = client.post(
        "/api/signals/analyze",
        files={
            "file": (
                "invalid.csv",
                io.BytesIO(b"x,y\n1,2\n3,4"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 422


def test_nonuniform_sampling():
    data = (
        "time_s,vibration\n"
        "0.0,0.1\n"
        "0.001,0.2\n"
        "0.003,0.3\n"
    )

    response = client.post(
        "/api/signals/analyze",
        files={
            "file": (
                "irregular.csv",
                io.BytesIO(data.encode()),
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
