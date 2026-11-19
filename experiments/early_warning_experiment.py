
from pathlib import Path

import numpy as np
import pandas as pd

from aura.simulator_v2 import generate_motor_signal
from aura.progressive_simulator import generate_progressive_signal
from aura.features import extract_features
from aura.acceleration_aware import AccelerationAwareDetector


SAMPLING_RATE = 2000
WINDOW_SIZE = 2000
STEP_SIZE = 1000

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
        features["severity"] = float(
            window["severity"].mean()
        ) if "severity" in window else 0.0

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


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    # Independent healthy training and calibration runs.
    train = build_healthy_dataset(range(100, 110))
    calibration = build_healthy_dataset(range(500, 505))

    detector = AccelerationAwareDetector(
        feature_columns=FEATURES,
        condition_columns=["rpm", "rpm_acceleration"],
    )

    detector.fit(train)
    detector.calibrate(calibration, quantile=0.95)

    results = []

    for profile in ["constant", "accelerating"]:
        for seed in range(1000, 1020):
            signal = generate_progressive_signal(
                profile=profile,
                fault_start=3.0,
                seed=seed,
            )

            windows = extract_windows(
                signal,
                f"{profile}_{seed}",
            )

            windows["anomaly_score"] = (
                detector.anomaly_score(windows)
            )

            windows["prediction"] = (
                detector.predict(windows)
            )

            windows["profile"] = profile
            windows["seed"] = seed

            results.append(windows)

    results = pd.concat(results, ignore_index=True)

    fault_start = 3.0

    print("\n=== AURA-B005 RESULTS ===")

    for profile, group in results.groupby("profile"):
        delays = []
        false_alarm_runs = 0
        missed_runs = 0

        for run_id, run in group.groupby("run_id"):
            # Only windows ending before onset are
            # considered entirely healthy.
            before_fault = run[
                run["time_end"] < fault_start
            ]

            if before_fault["prediction"].any():
                false_alarm_runs += 1

            # Windows starting after onset are
            # fully post-onset.
            after_fault = run[
                run["time_start"] >= fault_start
            ]

            detections = after_fault[
                after_fault["prediction"] == 1
            ]

            if len(detections) == 0:
                missed_runs += 1
            else:
                first_detection = detections[
                    "time_end"
                ].min()

                delays.append(
                    first_detection - fault_start
                )

        total_runs = group["run_id"].nunique()

        print(f"\nProfile: {profile}")
        print("Total runs:", total_runs)

        print(
            "Runs with pre-fault false alarms:",
            false_alarm_runs,
        )

        print(
            "Runs with no post-onset detection:",
            missed_runs,
        )

        print(
            "Mean detection delay (detected runs only):",
            round(float(np.mean(delays)), 4)
            if delays else "N/A",
        )

    results.to_csv(
        OUTPUT / "b005_early_warning.csv",
        index=False,
    )

    print("\nResults saved successfully.")


if __name__ == "__main__":
    main()
