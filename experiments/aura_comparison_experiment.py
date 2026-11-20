
from pathlib import Path

import numpy as np
import pandas as pd

from aura.aura_v01 import AURAPrototype
from aura.acceleration_aware import AccelerationAwareDetector
from aura.calibrated_sequential import detect
from aura.robustness_simulator import generate_robustness_signal

from experiments.calibrated_sequential_experiment import (
    healthy_runs,
    window_features,
    FEATURES,
)


OUTPUT = Path("results/generated")
FAULT_START = 3.0

# Same recording length across all scenarios.
DURATION = 10.0

SCENARIOS = {
    "healthy": {
        "start_rpm": 1500,
        "acceleration": 60,
        "noise_std": 0.08,
        "max_severity": 0.0,
    },
    "degradation": {
        "start_rpm": 1500,
        "acceleration": 60,
        "noise_std": 0.08,
        "max_severity": 0.8,
    },
    "unfamiliar": {
        "start_rpm": 2200,
        "acceleration": 250,
        "noise_std": 0.08,
        "max_severity": 0.0,
    },
}


def build_healthy(seeds):
    return pd.concat(
        healthy_runs(seeds),
        ignore_index=True,
    )


def prepare_models():
    train = build_healthy(range(100, 110))
    calibration = build_healthy(range(500, 505))

    aura = AURAPrototype(
        feature_columns=FEATURES,
        condition_columns=["rpm", "rpm_acceleration"],
        alpha=0.3,
        memory_window=10,
        min_history=3,
    )

    aura.fit(train, calibration)

    baseline = AccelerationAwareDetector(
        feature_columns=FEATURES,
        condition_columns=["rpm", "rpm_acceleration"],
    )

    baseline.fit(train)
    baseline.calibrate(calibration, quantile=0.95)

    return aura, baseline


def evaluate_run(aura, baseline, scenario, settings, seed):
    signal = generate_robustness_signal(
        duration=DURATION,
        fault_start=FAULT_START,
        profile="accelerating",
        seed=seed,
        **settings,
    )

    windows = window_features(
        signal,
        f"{scenario}_{seed}",
    )

    aura_output = aura.predict_sequence(windows)

    scores = baseline.anomaly_score(windows)

    single = detect(
        scores,
        baseline.threshold,
        "single",
        None,
    )

    # Previously selected B007 CUSUM parameters.
    cusum = detect(
        scores,
        baseline.threshold,
        "cusum",
        (0.0, 0.5),
    )

    states = aura_output["state"].to_numpy()

    # Ablation: remove only the uncertainty gate.
    # Preserve the same memory and persistence threshold.
    persistent = aura_output[
        "persistent_score"
    ].to_numpy()

    history = aura_output[
        "memory_size"
    ].to_numpy()

    aura_without_gate = (
        (persistent > aura.decision.persistence_threshold)
        & (history >= aura.min_history)
    ).astype(int)

    methods = {
        "single": single,
        "cusum": cusum,
        "aura": (states == "WARNING").astype(int),
        "aura_no_gate": aura_without_gate,
    }

    unknown = (states == "UNKNOWN")

    # Use time_end as the time an alert is available.
    ends = windows["time_end"].to_numpy()
    starts = windows["time_start"].to_numpy()

    # Fully healthy windows before onset.
    pre_fault = ends < FAULT_START

    # Fully post-onset windows.
    post_fault = starts >= FAULT_START

    records = []

    for method, alerts in methods.items():
        if scenario == "degradation":
            false_alarm = bool(np.any(alerts[pre_fault]))

            detection_indices = np.flatnonzero(
                (alerts == 1) & post_fault
            )

            detected = len(detection_indices) > 0

            delay = (
                float(ends[detection_indices[0]] - FAULT_START)
                if detected else np.nan
            )
        else:
            false_alarm = bool(np.any(alerts))
            detected = False
            delay = np.nan

        records.append({
            "scenario": scenario,
            "seed": seed,
            "method": method,
            "false_alarm": false_alarm,
            "detected": detected,
            "delay": delay,
            "unknown_rate": (
                float(np.mean(unknown))
                if method == "aura" else np.nan
            ),
        })

    return records


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    aura, baseline = prepare_models()

    records = []

    for scenario, settings in SCENARIOS.items():
        for seed in range(1000, 1030):
            records.extend(
                evaluate_run(
                    aura, baseline,
                    scenario, settings, seed,
                )
            )

    results = pd.DataFrame(records)

    summary = results.groupby(
        ["scenario", "method"]
    ).agg(
        runs=("seed", "size"),
        false_alarm_runs=("false_alarm", "sum"),
        detected_runs=("detected", "sum"),
        mean_delay=("delay", "mean"),
        unknown_rate=("unknown_rate", "mean"),
    )

    print("\n=== AURA v0.1 COMPARATIVE EVALUATION ===")
    print(summary.round(4).to_string())

    results.to_csv(
        OUTPUT / "aura_comparison_runs.csv",
        index=False,
    )

    summary.to_csv(
        OUTPUT / "aura_comparison_summary.csv",
    )

    print("\nComparison completed.")


if __name__ == "__main__":
    main()
