
from pathlib import Path

import numpy as np
import pandas as pd

from aura.simulator_v2 import generate_motor_signal
from aura.progressive_simulator import generate_progressive_signal
from aura.features import extract_features
from aura.acceleration_aware import AccelerationAwareDetector

from aura.sequential import (
    single_window_detector,
    consecutive_detector,
    cusum_detector,
)


SAMPLING_RATE = 2000
WINDOW_SIZE = 2000
STEP_SIZE = 1000

FAULT_START = 3.0

FEATURES = [
    "rms",
    "std",
    "peak_to_peak",
    "crest_factor",
    "kurtosis",
    "dominant_frequency",
    "spectral_centroid",
]

OUTPUT = Path("results/generated")


def extract_windows(data, run_id):
    records = []

    for start in range(
        0,
        len(data) - WINDOW_SIZE + 1,
        STEP_SIZE,
    ):
        window = data.iloc[start:start + WINDOW_SIZE]

        features = extract_features(
            window["vibration"].to_numpy(),
            SAMPLING_RATE,
        )

        rpm = window["rpm"].to_numpy()
        time = window["time_s"].to_numpy()

        features["rpm"] = float(np.mean(rpm))
        features["rpm_acceleration"] = float(
            (rpm[-1] - rpm[0]) / (time[-1] - time[0])
        )

        features["time_start"] = float(time[0])
        features["time_end"] = float(time[-1])
        features["run_id"] = run_id

        records.append(features)

    return pd.DataFrame(records)


def build_healthy_dataset(seeds):
    frames = []

    for profile in ["constant", "accelerating"]:
        for rpm in [1200, 1500, 1800]:
            for acceleration in [60, 120]:
                for seed in seeds:
                    signal = generate_motor_signal(
                        condition="healthy",
                        profile=profile,
                        start_rpm=rpm,
                        acceleration=acceleration,
                        seed=seed,
                    )

                    frames.append(
                        extract_windows(
                            signal,
                            f"healthy_{profile}_{rpm}_{acceleration}_{seed}",
                        )
                    )

    return pd.concat(frames, ignore_index=True)


def evaluate_method(method_name, results):
    print(f"\n=== {method_name} ===")

    for profile, group in results.groupby("profile"):
        false_alarm_runs = 0
        missed_runs = 0
        delays = []

        for run_id, run in group.groupby("run_id"):
            run = run.sort_values("time_start")

            before_fault = run[
                run["time_end"] < FAULT_START
            ]

            if before_fault["alert"].any():
                false_alarm_runs += 1

            after_fault = run[
                run["time_start"] >= FAULT_START
            ]

            detections = after_fault[
                after_fault["alert"] == 1
            ]

            if detections.empty:
                missed_runs += 1
            else:
                first_detection = detections["time_end"].min()
                delays.append(first_detection - FAULT_START)

        print(f"\nProfile: {profile}")
        print("Total runs:", group["run_id"].nunique())
        print("Pre-fault false-alarm runs:", false_alarm_runs)
        print("Missed post-onset runs:", missed_runs)
        print(
            "Mean detection delay:",
            round(float(np.mean(delays)), 4)
            if delays else "N/A",
        )


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    # Healthy-only model training and calibration.
    train = build_healthy_dataset(range(100, 110))
    calibration = build_healthy_dataset(range(500, 505))

    detector = AccelerationAwareDetector(
        feature_columns=FEATURES,
        condition_columns=["rpm", "rpm_acceleration"],
    )

    detector.fit(train)
    detector.calibrate(calibration, quantile=0.95)

    all_runs = []

    for profile in ["constant", "accelerating"]:
        for seed in range(1000, 1020):
            signal = generate_progressive_signal(
                profile=profile,
                fault_start=FAULT_START,
                seed=seed,
            )

            windows = extract_windows(
                signal,
                f"{profile}_{seed}",
            )

            windows["score"] = detector.anomaly_score(windows)
            windows["profile"] = profile

            all_runs.append(windows)

    data = pd.concat(all_runs, ignore_index=True)

    methods = [
        "single",
        "consecutive_2",
        "consecutive_3",
        "cusum",
    ]

    all_results = []

    for method in methods:
        method_results = []

        for run_id, run in data.groupby("run_id"):
            run = run.sort_values("time_start").copy()
            scores = run["score"].to_numpy()

            if method == "single":
                alerts = single_window_detector(
                    scores, detector.threshold
                )

            elif method == "consecutive_2":
                alerts = consecutive_detector(
                    scores, detector.threshold, required=2
                )

            elif method == "consecutive_3":
                alerts = consecutive_detector(
                    scores, detector.threshold, required=3
                )

            else:
                alerts = cusum_detector(
                    scores, detector.threshold,
                    k=0.5, h=3.0
                )

            run["alert"] = alerts
            run["method"] = method

            method_results.append(run)

        result = pd.concat(method_results, ignore_index=True)

        evaluate_method(method, result)

        all_results.append(result)

    combined = pd.concat(all_results, ignore_index=True)

    combined.to_csv(
        OUTPUT / "b006_sequential_results.csv",
        index=False,
    )

    print("\nAURA-B006 completed.")


if __name__ == "__main__":
    main()
