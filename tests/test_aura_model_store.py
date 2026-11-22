
import pytest

from aura.aura_v01 import AURAPrototype

import backend.aura_model_store as store

from experiments.calibrated_sequential_experiment import FEATURES
from experiments.aura_run_calibration import (
    build_training_data,
    build_base_calibration,
)


@pytest.fixture
def trained_model():
    model = AURAPrototype(
        feature_columns=FEATURES,
        condition_columns=[
            "rpm",
            "rpm_acceleration",
        ],
    )

    model.fit(
        build_training_data(),
        build_base_calibration(),
    )

    return model


def test_save_and_load_model(
    trained_model,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        store,
        "MODEL_DIRECTORY",
        tmp_path,
    )

    store.save_aura_model(
        trained_model,
        "test_model",
        "test_training",
        "test_calibration",
    )

    loaded, metadata = store.load_aura_model(
        "test_model"
    )

    assert loaded.is_ready
    assert metadata["model_name"] == "test_model"


def test_reject_untrained_model(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        store,
        "MODEL_DIRECTORY",
        tmp_path,
    )

    model = AURAPrototype(
        feature_columns=FEATURES,
    )

    with pytest.raises(store.AURAModelError):
        store.save_aura_model(
            model,
            "untrained",
            "training",
            "calibration",
        )


def test_checksum_verification(
    trained_model,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        store,
        "MODEL_DIRECTORY",
        tmp_path,
    )

    store.save_aura_model(
        trained_model,
        "checksum_test",
        "training",
        "calibration",
    )

    model_path = tmp_path / "checksum_test.joblib"

    with model_path.open("ab") as file:
        file.write(b"modified")

    with pytest.raises(
        store.AURAModelError,
        match="checksum",
    ):
        store.load_aura_model("checksum_test")
