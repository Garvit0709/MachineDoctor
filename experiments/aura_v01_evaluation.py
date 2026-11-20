
from pathlib import Path

import numpy as np
import pandas as pd

from aura.aura_v01 import AURAPrototype
from aura.simulator_v2 import generate_motor_signal
from aura.progressive_simulator import generate_progressive_signal
from experiments.calibrated_sequential_experiment import (
    healthy_runs,
    window_features,
    FEATURES,
)


OUTPUT = Path("results/generated")
FAULT_START = 3.0


def build_healthy(seeds):
    return pd.concat(
        healthy_runs(seeds),
        ignore_index=True,
    )


def evaluate_run(model, signal, run_id, scenario):
    windows = window_features(signal, run_id)

    predictions = model.predict_sequence(windows)

    result = pd.concat(
        [
            windows.reset_index(drop=True),
            predictions.drop(columns=["index"]),
        ],
        axis=1,
    )

    result["scenario"] = scenario
    return result


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    training = build_healthy(range(100, 110))
    calibration = build_healthy(range(500, 505))

    model = AURAPrototype(
        feature_columns=FEATURES,
        condition_columns=["rpm", "rpm_acceleration"],
        alpha=0.3,
        memory_window=10,
        min_history=3,
    )

    model.fit(training, calibration)

    records = []

    for seed in range(1000, 1030):
        # S1: Familiar healthy operation
        healthy = generate_motor_signal(
            condition="healthy",
            profile="accelerating",
            start_rpm=1500,
            acceleration=60,
            seed=seed,
        )

        records.append(
            evaluate_run(
                model,
                healthy,
                f"healthy_{seed}",
                "healthy",
            )
        )

        # S2: Progressive degradation
        degraded = generate_progressive_signal(
            profile="accelerating",
            start_rpm=1500,
            acceleration=60,
            fault_start=FAULT_START,
            seed=seed,
        )

        records.append(
            evaluate_run(
                model,
                degraded,
                f"degradation_{seed}",
                "degradation",
            )
        )

        # S3: Unfamiliar healthy operation
        unfamiliar = generate_motor_signal(
            condition="healthy",
            profile="accelerating",
            start_rpm=2200,
            acceleration=250,
            seed=seed,
        )

        records.append(
            evaluate_run(
                model,
                unfamiliar,
                f"unfamiliar_{seed}",
                "unfamiliar",
            )
        )

    results = pd.concat(records, ignore_index=True)

    print("\n=== AURA v0.1 EVALUATION ===")

    print("\nDiagnostic state counts:")
    print(
        pd.crosstab(
            results["scenario"],
            results["state"],
        )
    )

    print("\nDiagnostic state percentages:")
    percentages = pd.crosstab(
        results["scenario"],
        results["state"],
        normalize="index",
    ) * 100

    print(percentages.round(2))

    print("\nMean persistent score:")
    print(
        results.groupby("scenario")[
            "persistent_score"
        ].mean().round(4)
    )

    results.to_csv(
        OUTPUT / "aura_v01_evaluation.csv",
        index=False,
    )

    print("\nResults saved successfully.")


if __name__ == "__main__":
    main()
