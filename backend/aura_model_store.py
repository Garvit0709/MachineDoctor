
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

import joblib


MODEL_VERSION = "aura-v0.1"
SCHEMA_VERSION = "1.0"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIRECTORY = PROJECT_ROOT / "models"


class AURAModelError(RuntimeError):
    """Raised when a saved AURA model is invalid."""


def calculate_sha256(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def save_aura_model(
    model,
    model_name: str,
    training_source: str,
    calibration_source: str,
):
    """
    Save a locally trained AURA model and metadata.

    Never load model artifacts from untrusted users.
    """

    if not model.is_ready:
        raise AURAModelError(
            "Cannot save an untrained AURA model."
        )

    if not model_name.replace("_", "").replace("-", "").isalnum():
        raise AURAModelError(
            "Model name contains unsupported characters."
        )

    MODEL_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    model_path = MODEL_DIRECTORY / f"{model_name}.joblib"
    metadata_path = MODEL_DIRECTORY / f"{model_name}.json"

    if model_path.exists() or metadata_path.exists():
        raise AURAModelError(
            "Model artifact already exists."
        )

    joblib.dump(model, model_path)

    checksum = calculate_sha256(model_path)

    metadata = {
        "model_name": model_name,
        "model_version": MODEL_VERSION,
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "training_source": training_source,
        "calibration_source": calibration_source,
        "feature_columns": model.feature_columns,
        "condition_columns": model.condition_columns,
        "alpha": model.alpha,
        "memory_window": model.memory_window,
        "min_history": model.min_history,
        "uncertainty_threshold": (
            model.uncertainty.threshold_
        ),
        "persistence_threshold": (
            model.decision.persistence_threshold
        ),
        "sha256": checksum,
    }

    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    return {
        "model_path": str(model_path),
        "metadata_path": str(metadata_path),
        "metadata": metadata,
    }


def load_aura_model(model_name: str):
    """
    Load a trusted local model after verifying its checksum.

    A matching checksum detects file changes, but does
    not independently establish that a file is trustworthy.
    """

    if not model_name.replace("_", "").replace("-", "").isalnum():
        raise AURAModelError(
            "Invalid model name."
        )

    model_path = MODEL_DIRECTORY / f"{model_name}.joblib"
    metadata_path = MODEL_DIRECTORY / f"{model_name}.json"

    if not model_path.exists() or not metadata_path.exists():
        raise AURAModelError(
            "Model artifact or metadata is missing."
        )

    metadata = json.loads(
        metadata_path.read_text(encoding="utf-8")
    )

    if metadata.get("model_version") != MODEL_VERSION:
        raise AURAModelError(
            "Unsupported AURA model version."
        )

    if metadata.get("schema_version") != SCHEMA_VERSION:
        raise AURAModelError(
            "Unsupported feature schema version."
        )

    actual_checksum = calculate_sha256(model_path)

    if actual_checksum != metadata.get("sha256"):
        raise AURAModelError(
            "Model checksum verification failed."
        )

    # Only trusted, locally generated artifacts
    # should reach this deserialization step.
    model = joblib.load(model_path)

    if not model.is_ready:
        raise AURAModelError(
            "Loaded model is not ready."
        )

    if model.feature_columns != metadata["feature_columns"]:
        raise AURAModelError(
            "Feature schema mismatch."
        )

    if model.condition_columns != metadata["condition_columns"]:
        raise AURAModelError(
            "Operating-condition schema mismatch."
        )

    return model, metadata
