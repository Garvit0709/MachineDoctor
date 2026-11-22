
from aura.aura_v01 import AURAPrototype

from backend.aura_model_store import save_aura_model

from experiments.aura_run_calibration import (
    build_training_data,
    build_base_calibration,
)

from experiments.calibrated_sequential_experiment import FEATURES


MODEL_NAME = "aura_v01_synthetic"


def main():
    print("\n=== AURA MODEL TRAINING ===")

    training = build_training_data()
    calibration = build_base_calibration()

    model = AURAPrototype(
        feature_columns=FEATURES,
        condition_columns=[
            "rpm",
            "rpm_acceleration",
        ],
        alpha=0.3,
        memory_window=10,
        min_history=3,
    )

    model.fit(training, calibration)

    # Familiar-only run-level calibration selected
    # during our previous synthetic experiments.
    #
    # This threshold is experimental and specific
    # to the simulator configuration.
    model.decision.persistence_threshold = 1.2838

    result = save_aura_model(
        model=model,
        model_name=MODEL_NAME,
        training_source="synthetic_healthy_training",
        calibration_source=(
            "synthetic_healthy_calibration_"
            "familiar_only_run_level"
        ),
    )

    print("Model saved:", result["model_path"])

    print(
        "Uncertainty threshold:",
        model.uncertainty.threshold_,
    )

    print(
        "Persistence threshold:",
        model.decision.persistence_threshold,
    )

    print("Training completed.")


if __name__ == "__main__":
    main()
