
import numpy as np
import pandas as pd
import pytest

from aura.aura_v01 import AURAPrototype


FEATURES = [
    "rms",
    "crest_factor",
    "kurtosis",
]


def make_data(seed, runs=8, windows=10):
    rng = np.random.default_rng(seed)
    rows = []

    for run_id in range(runs):
        rpm = rng.uniform(1200, 1900)
        acceleration = rng.choice([0, 60, 120])

        for i in range(windows):
            rows.append({
                "run_id": f"run_{run_id}",
                "rpm": rpm + acceleration * i * 0.5,
                "rpm_acceleration": acceleration,
                "rms": (
                    0.0002 * rpm
                    + rng.normal(0, 0.01)
                ),
                "crest_factor": (
                    2.0 + rng.normal(0, 0.1)
                ),
                "kurtosis": (
                    3.0 + rng.normal(0, 0.2)
                ),
            })

    return pd.DataFrame(rows)


def fitted_model():
    model = AURAPrototype(
        feature_columns=FEATURES,
        min_history=3,
    )

    model.fit(
        make_data(42),
        make_data(100),
    )

    return model


def test_integrated_prediction():
    model = fitted_model()

    test_data = make_data(200, runs=1)

    result = model.predict_sequence(test_data)

    assert len(result) == len(test_data)

    assert set(result["state"]).issubset({
        "NORMAL", "WARNING", "UNKNOWN"
    })


def test_initial_history_is_unknown():
    model = fitted_model()

    test_data = make_data(201, runs=1)

    result = model.predict_sequence(test_data)

    assert result.iloc[0]["state"] == "UNKNOWN"
    assert result.iloc[1]["state"] == "UNKNOWN"


def test_unfamiliar_conditions_are_unknown():
    model = fitted_model()

    test_data = make_data(202, runs=1)

    test_data["rpm"] = 3000
    test_data["rpm_acceleration"] = 400

    result = model.predict_sequence(test_data)

    assert (result["state"] == "UNKNOWN").all()


def test_memory_resets_between_sequences():
    model = fitted_model()

    test_data = make_data(203, runs=1)

    first = model.predict_sequence(test_data)
    second = model.predict_sequence(test_data)

    pd.testing.assert_frame_equal(first, second)


def test_prediction_before_fit():
    model = AURAPrototype(feature_columns=FEATURES)

    with pytest.raises(RuntimeError):
        model.predict_sequence(make_data(300, runs=1))
