
from pathlib import Path

import numpy as np
import pandas as pd

from aura.aura_v01 import AURAPrototype
from aura.robustness_simulator import generate_robustness_signal

from experiments.calibrated_sequential_experiment import (
    healthy_runs,
    window_features,
    FEATURES,
)


OUTPUT = Path("results/generated")
DURATION = 10.0
FAULT_START = 3.0

# Candidate thresholds are selected from healthy
# recording-level maximum persistence scores.
QUANTILE = 0.95


def build_training_data():
    return pd.concat(
        healthy_runs(range(100, 110)),
        ignore_index=True,
    )


def build_base_calibration():
    return pd.concat(
        healthy_runs(range(500, 505)),
        ignore_index=True,
    )


def create_healthy_run(seed, start_rpm, acceleration):
    signal = generate_robustness_signal(
        duration=DURATION,
        profile="accelerating",
        start_rpm=start_rpm,
        acceleration=acceleration,
        noise_std=0.08,
        max_severity=0.0,
        fault_start=FAULT_START,
        seed=seed,
    )

    return window_features(
        signal,
        f"healthy_{start_rpm}_{acceleration}_{seed}",
    )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    model = AURAPrototype(
        feature_columns=FEATURES,
        condition_columns=["rpm", "rpm_acceleration"],
        alpha=0.3,
        memory_window=10,
        min_history=3,
    )

    model.fit(
        build_training_data(),
        build_base_calibration(),
    )

    print("\n=== AURA RUN-LEVEL CALIBRATION ===")

    print(
        "Original persistence threshold:",
        round(model.decision.persistence_threshold, 4),
    )

    calibration_maxima = []

    # Separate calibration seeds and varied healthy profiles.
    for start_rpm in [1200, 1500, 1800]:
        for acceleration in [60, 120]:
            for seed in range(700, 730):
                run = create_healthy_run(
                    seed, start_rpm, acceleration
                )

                output = model.predict_sequence(run)

                eligible = output[
                    output["memory_size"] >= model.min_history
                ]

                if not eligible.empty:
                    calibration_maxima.append(
                        eligible["persistent_score"].max()
                    )

    if not calibration_maxima:
        raise RuntimeError("No calibration maxima available.")

    new_threshold = float(
        np.quantile(calibration_maxima, QUANTILE)
    )

    model.decision.persistence_threshold = max(
        new_threshold, 1e-8
    )

    print(
        "New run-level threshold:",
        round(model.decision.persistence_threshold, 4),
    )

    scenarios = {
        "healthy": {
            "start_rpm": 1500,
            "acceleration": 60,
            "max_severity": 0.0,
        },
        "degradation": {
            "start_rpm": 1500,
            "acceleration": 60,
            "max_severity": 0.8,
        },
        "unfamiliar_healthy": {
            "start_rpm": 2200,
            "acceleration": 250,
            "max_severity": 0.0,
        },
        "unfamiliar_degradation": {
            "start_rpm": 2200,
            "acceleration": 250,
            "max_severity": 0.8,
        },
    }

    records = []

    for scenario, settings in scenarios.items():
        for seed in range(1000, 1030):
            signal = generate_robustness_signal(
                duration=DURATION,
                profile="accelerating",
                fault_start=FAULT_START,
                noise_std=0.08,
                seed=seed,
                **settings,
            )

            run = window_features(
                signal, f"{scenario}_{seed}"
            )

            output = model.predict_sequence(run)

            states = output["state"].to_numpy()
            ends = run["time_end"].to_numpy()
            starts = run["time_start"].to_numpy()

            # For progressive degradation, only fully
            # pre-onset windows count as pre-fault.
            if "degradation" in scenario:
                pre_fault = ends < FAULT_START
                post_fault = starts >= FAULT_START
            else:
                pre_fault = np.ones(len(run), dtype=bool)
                post_fault = np.zeros(len(run), dtype=bool)

            false_warning = bool(
                np.any(
                    (states == "WARNING") & pre_fault
                )
            )

            detected_indices = np.flatnonzero(
                (states == "WARNING") & post_fault
            )

            detected = len(detected_indices) > 0

            delay = (
                float(
                    ends[detected_indices[0]] - FAULT_START
                )
                if detected else np.nan
            )

            records.append({
                "scenario": scenario,
                "seed": seed,
                "false_warning": false_warning,
                "detected": detected,
                "delay": delay,
                "unknown_rate": float(
                    np.mean(states == "UNKNOWN")
                ),
            })

    results = pd.DataFrame(records)

    summary = results.groupby("scenario").agg(
        runs=("seed", "size"),
        false_warning_runs=("false_warning", "sum"),
        detected_runs=("detected", "sum"),
        mean_delay=("delay", "mean"),
        unknown_rate=("unknown_rate", "mean"),
    )

    print("\n=== CALIBRATED AURA RESULTS ===")
    print(summary.round(4).to_string())

    results.to_csv(
        OUTPUT / "aura_run_calibration_results.csv",
        index=False,
    )

    summary.to_csv(
        OUTPUT / "aura_run_calibration_summary.csv",
    )

    print("\nCalibration experiment completed.")


if __name__ == "__main__":
    main()
