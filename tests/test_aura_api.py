
import io

import pandas as pd

from fastapi.testclient import TestClient

from backend.main import app
from backend import aura_inference


client = TestClient(app)


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


def upload(data, filename="features.csv"):
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


def test_diagnostic_endpoint(monkeypatch):
    class FakeModel:
        def predict_sequence(self, data):
            return pd.DataFrame({
                "state": ["UNKNOWN", "UNKNOWN",
                          "NORMAL", "NORMAL", "WARNING"],
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
            "rms", "crest_factor", "kurtosis"
        ],
        "condition_columns": [
            "rpm", "rpm_acceleration"
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

    response = upload(data)

    assert response.status_code == 200

    result = response.json()

    assert result["total_windows"] == 5
    assert result["state_counts"]["WARNING"] == 1


def test_missing_columns():
    data = pd.DataFrame({
        "time_start": [0, 1, 2],
        "time_end": [1, 2, 3],
    }).to_csv(index=False).encode()

    response = upload(data)

    assert response.status_code == 422


def test_invalid_extension():
    response = upload(
        b"invalid",
        filename="features.txt",
    )

    assert response.status_code == 415


def test_multiple_runs_rejected():
    data = sample_features()
    data.loc[4, "run_id"] = "another_motor"

    response = upload(
        data.to_csv(index=False).encode()
    )

    assert response.status_code == 422
