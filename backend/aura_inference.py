
import copy
from functools import lru_cache

import pandas as pd

from backend.aura_contract import validate_aura_features
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

    AURA v0.1 currently supports compatible
    synthetic motor-bearing feature data only.
    """

    # Step 1: Validate the feature sequence
    validated = validate_aura_features(features)

    # Step 2: Load the trained model and metadata
    model, metadata = get_aura_model()

    # Step 3: Verify the required feature schema
    required_features = metadata["feature_columns"]
    required_conditions = metadata["condition_columns"]

    required = set(
        required_features + required_conditions
    )

    if not required.issubset(validated.columns):
        raise ValueError(
            "Feature sequence does not match model schema."
        )

    # Step 4: Isolate mutable memory for each request
    request_model = copy.deepcopy(model)

    # Step 5: Run AURA inference
    predictions = request_model.predict_sequence(validated)

    # Step 6: Combine input metadata with predictions
    output = validated[
        ["run_id", "time_start", "time_end"]
    ].copy()

    output["state"] = predictions["state"].to_numpy()
    output["reason"] = predictions["reason"].to_numpy()

    output["persistent_score"] = (
        predictions["persistent_score"].to_numpy()
    )

    output["instantaneous_score"] = (
        predictions["instantaneous_score"].to_numpy()
    )

    output["uncertainty_distance"] = (
        predictions["uncertainty_distance"].to_numpy()
    )

    output["memory_size"] = (
        predictions["memory_size"].to_numpy()
    )

    # Step 7: Count diagnostic states
    state_counts = output["state"].value_counts()

    # Step 8: Return structured diagnostic results
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
