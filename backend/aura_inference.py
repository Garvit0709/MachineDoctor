
import copy
from functools import lru_cache

import pandas as pd

from backend.aura_contract import (
    AURAInputError,
    validate_aura_features,
)
from backend.aura_model_store import load_aura_model


MODEL_NAME = "aura_v01_synthetic"


@lru_cache(maxsize=1)
def get_aura_model():
    """
    Load the trusted local AURA model once per process.
    """
    return load_aura_model(MODEL_NAME)


def diagnose_feature_sequence(
    features: pd.DataFrame,
):
    """
    Run AURA on one validated feature sequence.

    This model currently supports compatible
    synthetic motor-bearing feature data only.
    """

    # 1. Validate the incoming feature sequence
    validated = validate_aura_features(features)

    # 2. Load the trained model and its metadata
    model, metadata = get_aura_model()

    # 3. Check model-specific feature requirements
    required_features = metadata["feature_columns"]
    required_conditions = metadata["condition_columns"]

    required = set(
        required_features + required_conditions
    )

    missing = sorted(
        required - set(validated.columns)
    )

    if missing:
        raise AURAInputError(
            "Feature sequence does not match model schema. "
            f"Missing columns: {missing}"
        )

    # 4. Isolate mutable memory for this request
    request_model = copy.deepcopy(model)

    # 5. Perform actual AURA inference
    predictions = request_model.predict_sequence(validated)

    # 6. Validate expected prediction columns
    expected_prediction_columns = [
        "state",
        "reason",
        "persistent_score",
        "instantaneous_score",
        "uncertainty_distance",
        "memory_size",
    ]

    missing_predictions = [
        column
        for column in expected_prediction_columns
        if column not in predictions.columns
    ]

    if missing_predictions:
        raise RuntimeError(
            "AURA model returned an incompatible prediction "
            f"schema: {missing_predictions}"
        )

    if len(predictions) != len(validated):
        raise RuntimeError(
            "AURA prediction count does not match input windows."
        )

    # 7. Build the diagnostic output
    output = validated[
        ["run_id", "time_start", "time_end"]
    ].copy()

    for column in expected_prediction_columns:
        output[column] = predictions[column].to_numpy()

    # 8. Count diagnostic states
    state_counts = output["state"].value_counts()

    # 9. Return structured results
    return {
        "application": "MachineDoctor",
        "algorithm": "AURA",
        "model_name": metadata["model_name"],
        "model_version": metadata["model_version"],
        "data_scope": "compatible_synthetic_features_only",
        "run_id": str(validated["run_id"].iloc[0]),
        "total_windows": len(output),
        "state_counts": {
            state: int(state_counts.get(state, 0))
            for state in [
                "NORMAL",
                "WARNING",
                "UNKNOWN",
            ]
        },
        "thresholds": {
            "uncertainty": float(
                metadata["uncertainty_threshold"]
            ),
            "persistence": float(
                metadata["persistence_threshold"]
            ),
        },
        "predictions": output.to_dict(
            orient="records"
        ),
        "limitations": (
            "Experimental synthetic-data model. "
            "Not validated for industrial safety decisions."
        ),
    }
