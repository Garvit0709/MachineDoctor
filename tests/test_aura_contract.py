
import pandas as pd
import pytest

from backend.aura_contract import (
    AURAInputError,
    validate_aura_features,
)


def valid_data():
    return pd.DataFrame({
        "run_id": ["motor_01"] * 4,
        "time_start": [0.0, 0.5, 1.0, 1.5],
        "time_end": [0.5, 1.0, 1.5, 2.0],
        "rms": [0.2, 0.21, 0.24, 0.28],
        "crest_factor": [2.1, 2.2, 2.3, 2.5],
        "kurtosis": [3.0, 3.1, 3.3, 3.8],
        "rpm": [1500, 1510, 1520, 1530],
        "rpm_acceleration": [20, 20, 20, 20],
    })


def test_valid_features():
    result = validate_aura_features(valid_data())

    assert len(result) == 4
    assert result["run_id"].nunique() == 1


def test_missing_feature():
    data = valid_data().drop(columns=["kurtosis"])

    with pytest.raises(AURAInputError):
        validate_aura_features(data)


def test_invalid_rpm():
    data = valid_data()
    data.loc[0, "rpm"] = -100

    with pytest.raises(AURAInputError):
        validate_aura_features(data)


def test_nonfinite_features():
    data = valid_data()
    data.loc[1, "rms"] = float("nan")

    with pytest.raises(AURAInputError):
        validate_aura_features(data)


def test_unordered_windows():
    data = valid_data()
    data.loc[2, "time_start"] = 0.25

    with pytest.raises(AURAInputError):
        validate_aura_features(data)


def test_multiple_runs_rejected():
    data = valid_data()
    data.loc[3, "run_id"] = "motor_02"

    with pytest.raises(AURAInputError):
        validate_aura_features(data)


def test_insufficient_windows():
    data = valid_data().iloc[:2]

    with pytest.raises(AURAInputError):
        validate_aura_features(data)
