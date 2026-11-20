
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from aura.aura_v01 import AURAPrototype
from aura.robustness_simulator import generate_robustness_signal

from experiments.calibrated_sequential_experiment import (
    window_features,
    FEATURES,
)

from experiments.aura_run_calibration import (
    build_training_data,
    build_base_calibration,
)


OUTPUT = Path("results/generated")
FAULT_START = 3.0
DURATION = 10.0

# Previously measured experimental thresholds.
THRESHOLDS = {
    "window_level": 0.8151,
    "all_window_run": 5.9929,
    "familiar_only_run": 1.2838,
}

SCENARIOS = {
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


def build_model():
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

    return model


def evaluate_run(model, scenario, settings, seed):
    signal = generate_robustness_signal(
        duration=DURATION,
        profile="accelerating",
        fault_start=FAULT_START,
        noise_std=0.08,
        seed=seed,
        **settings,
    )

    windows = window_features(
        signal,
        f"{scenario}_{seed}",
    )

    # Compute the memory and uncertainty evidence once.
    output = model.predict_sequence(windows)

    persistence = output[
        "persistent_score"
    ].to_numpy()

    uncertainty = output[
        "uncertainty_distance"
    ].to_numpy()

    history = output[
        "memory_size"
    ].to_numpy()

    starts = windows["time_start"].to_numpy()
    ends = windows["time_end"].to_numpy()

    familiar = (
        uncertainty <= model.uncertainty.threshold_
    )

    eligible = history >= model.min_history

    records = []

    for strategy, threshold in THRESHOLDS.items():

        # Same decision rule; only persistence
        # threshold changes between strategies.
        warnings = (
            familiar
            & eligible
            & (persistence > threshold)
        )

        unknown = ~familiar | ~eligible

        if "degradation" in scenario:
            pre_fault = ends < FAULT_START
            post_fault = starts >= FAULT_START
        else:
            pre_fault = np.ones(len(windows), dtype=bool)
            post_fault = np.zeros(len(windows), dtype=bool)

        false_warning = bool(
            np.any(warnings & pre_fault)
        )

        detected_indices = np.flatnonzero(
            warnings & post_fault
        )

        detected = len(detected_indices) > 0

        delay = (
            float(ends[detected_indices[0]] - FAULT_START)
            if detected else np.nan
        )

        records.append({
            "scenario": scenario,
            "seed": seed,
            "strategy": strategy,
            "threshold": threshold,
            "false_warning": false_warning,
            "detected": detected,
            "delay": delay,
            "unknown_rate": float(np.mean(unknown)),
            "warning_rate": float(np.mean(warnings)),
        })

    return records


def create_plots(summary):
    familiar = summary[
        summary["scenario"].isin(
            ["healthy", "degradation"]
        )
    ].copy()

    fig, ax = plt.subplots(figsize=(9, 5))

    for scenario in ["healthy", "degradation"]:
        subset = familiar[
            familiar["scenario"] == scenario
        ]

        ax.plot(
            subset["strategy"],
            subset["false_warning_runs"],
            marker="o",
            label=scenario,
        )

    ax.set_title("AURA False Warnings by Calibration Strategy")
    ax.set_ylabel("Runs with pre-fault warnings")
    ax.set_xlabel("Calibration strategy")
    ax.legend()
    ax.grid(alpha=0.25)

    plt.xticks(rotation=15)
    plt.tight_layout()

    plt.savefig(
        OUTPUT / "aura_threshold_false_warnings.png",
        dpi=200,
    )
    plt.close()

    degraded = summary[
        summary["scenario"] == "degradation"
    ]

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.bar(
        degraded["strategy"],
        degraded["mean_delay"],
    )

    ax.set_title("AURA Detection Delay by Calibration Strategy")
    ax.set_ylabel("Mean detection delay (seconds)")
    ax.set_xlabel("Calibration strategy")
    ax.grid(axis="y", alpha=0.25)

    plt.xticks(rotation=15)
    plt.tight_layout()

    plt.savefig(
        OUTPUT / "aura_threshold_detection_delay.png",
        dpi=200,
    )
    plt.close()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    model = build_model()

    records = []

    for scenario, settings in SCENARIOS.items():
        for seed in range(1000, 1030):
            records.extend(
                evaluate_run(
                    model, scenario, settings, seed
                )
            )

    results = pd.DataFrame(records)

    summary = results.groupby(
        ["scenario", "strategy"],
        sort=False,
    ).agg(
        runs=("seed", "size"),
        false_warning_runs=("false_warning", "sum"),
        detected_runs=("detected", "sum"),
        mean_delay=("delay", "mean"),
        unknown_rate=("unknown_rate", "mean"),
        warning_rate=("warning_rate", "mean"),
    ).reset_index()

    print("\n=== AURA THRESHOLD COMPARISON ===")
    print(summary.round(4).to_string(index=False))

    results.to_csv(
        OUTPUT / "aura_threshold_comparison_runs.csv",
        index=False,
    )

    summary.to_csv(
        OUTPUT / "aura_threshold_comparison_summary.csv",
        index=False,
    )

    create_plots(summary)

    print("\nComparison completed.")
    print("Saved CSV files and diagnostic graphs.")


if __name__ == "__main__":
    main()
