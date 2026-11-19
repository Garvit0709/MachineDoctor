
from pathlib import Path

import numpy as np
import pandas as pd

from aura.acceleration_aware import AccelerationAwareDetector
from aura.calibrated_sequential import detect
from aura.robustness_simulator import generate_robustness_signal

from experiments.calibrated_sequential_experiment import (
    healthy_runs,
    window_features,
    FEATURES,
    FAULT_START,
)


OUTPUT = Path("results/generated")

SCENARIOS = {
    "reference": {
        "start_rpm": 1500,
        "acceleration": 60,
        "noise_std": 0.08,
        "max_severity": 0.8,
    },
    "high_noise": {
        "start_rpm": 1500,
        "acceleration": 60,
        "noise_std": 0.20,
        "max_severity": 0.8,
    },
    "unseen_rpm": {
        "start_rpm": 2200,
        "acceleration": 60,
        "noise_std": 0.08,
        "max_severity": 0.8,
    },
    "unseen_acceleration": {
        "start_rpm": 1500,
        "acceleration": 250,
        "noise_std": 0.08,
        "max_severity": 0.8,
    },
    "weak_degradation": {
        "start_rpm": 1500,
        "acceleration": 60,
        "noise_std": 0.08,
        "max_severity": 0.25,
    },
}


def build_detector():
    train = pd.concat(
        healthy_runs(range(100, 110)),
        ignore_index=True,
    )

    calibration = pd.concat(
        healthy_runs(range(500, 505)),
        ignore_index=True,
    )

    detector = AccelerationAwareDetector(
        feature_columns=FEATURES,
        condition_columns=["rpm", "rpm_acceleration"],
    )

    detector.fit(train)
    detector.calibrate(calibration, quantile=0.95)

    return detector


def evaluate_run(
    detector,
    scenario,
    settings,
    seed,
    method,
):
    signal = generate_robustness_signal(
        **settings,
        seed=seed,
        fault_start=FAULT_START,
    )

    windows = window_features(
        signal,
        f"{scenario}_{seed}",
    )

    scores = detector.anomaly_score(windows)

    if method == "single":
        alerts = detect(
            scores,
            detector.threshold,
            "single",
            None,
        )
    else:
        # Parameters selected in B007.
        alerts = detect(
            scores,
            detector.threshold,
            "cusum",
            (0.0, 0.5),
        )

    before = (
        windows["time_end"].to_numpy()
        < FAULT_START
    )

    after = (
        windows["time_start"].to_numpy()
        >= FAULT_START
    )

    false_alarm = bool(np.any(alerts[before]))

    detected_indices = np.flatnonzero(
        (alerts == 1) & after
    )

    if len(detected_indices):
        index = detected_indices[0]
        delay = (
            float(windows.iloc[index]["time_end"])
            - FAULT_START
        )
        detected = True
    else:
        delay = np.nan
        detected = False

    return {
        "scenario": scenario,
        "method": method,
        "seed": seed,
        "false_alarm": false_alarm,
        "detected": detected,
        "delay": delay,
    }


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    detector = build_detector()

    records = []

    for scenario, settings in SCENARIOS.items():
        for seed in range(1000, 1030):
            for method in ["single", "cusum"]:
                records.append(
                    evaluate_run(
                        detector,
                        scenario,
                        settings,
                        seed,
                        method,
                    )
                )

    results = pd.DataFrame(records)

    summary = results.groupby(
        ["scenario", "method"]
    ).agg(
        runs=("detected", "size"),
        false_alarm_runs=("false_alarm", "sum"),
        detected_runs=("detected", "sum"),
        mean_delay=("delay", "mean"),
    )

    print("\n=== AURA-B008 RESULTS ===")
    print(summary.round(4).to_string())

    results.to_csv(
        OUTPUT / "b008_robustness_results.csv",
        index=False,
    )

    summary.to_csv(
        OUTPUT / "b008_robustness_summary.csv",
    )

    print("\nAURA-B008 completed.")


if __name__ == "__main__":
    main()
