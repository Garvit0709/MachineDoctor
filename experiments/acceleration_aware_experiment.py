
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from aura.simulator_v2 import generate_motor_signal
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


def create_run(condition, profile, seed, start_rpm, acceleration):
    data = generate_motor_signal(
        condition=condition,
        profile=profile,
        start_rpm=start_rpm,
        acceleration=acceleration,
        sampling_rate=SAMPLING_RATE,
        seed=seed,
    )

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

        features["condition"] = condition
        features["profile"] = profile
        features["run_id"] = (
            f"{condition}_{profile}_{start_rpm}_"
            f"{acceleration}_{seed}"
        )

        records.append(features)

    return pd.DataFrame(records)


def build_data(seeds, include_faults):
    frames = []

    conditions = (
        ["healthy", "degradation"]
        if include_faults
        else ["healthy"]
    )

    for condition in conditions:
        for profile in ["constant", "accelerating"]:
            for start_rpm in [1200, 1500, 1800]:
                for acceleration in [60, 120]:
                    for seed in seeds:
                        frames.append(
                            create_run(
                                condition,
                                profile,
                                seed,
                                start_rpm,
                                acceleration,
                            )
                        )

    return pd.concat(frames, ignore_index=True)


def evaluate(name, detector, test_data):
    actual = (
        test_data["condition"] == "degradation"
    ).astype(int)

    predicted = detector.predict(test_data)

    print(f"\n=== {name} ===")

    print(
        "Precision:",
        round(precision_score(actual, predicted, zero_division=0), 4)
    )
    print(
        "Recall:",
        round(recall_score(actual, predicted, zero_division=0), 4)
    )
    print(
        "F1:",
        round(f1_score(actual, predicted, zero_division=0), 4)
    )

    print("\nConfusion matrix:")
    print(confusion_matrix(actual, predicted))

    result = test_data.copy()
    result["prediction"] = predicted
    result["anomaly_score"] = detector.anomaly_score(test_data)

    print("\nAnomaly rate by condition and profile:")
    print(
        result.groupby(
            ["condition", "profile"]
        )["prediction"].mean().round(4)
    )

    return result


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)

    # Independent seed groups.
    train = build_data(range(100, 110), include_faults=False)
    calibration = build_data(range(500, 505), include_faults=False)
    test = build_data(range(1000, 1010), include_faults=True)

    print("Training windows:", len(train))
    print("Calibration windows:", len(calibration))
    print("Testing windows:", len(test))

    models = {
        "RPM only": ["rpm"],
        "RPM + acceleration": ["rpm", "rpm_acceleration"],
    }

    for name, condition_columns in models.items():
        detector = AccelerationAwareDetector(
            feature_columns=FEATURES,
            condition_columns=condition_columns,
        )

        detector.fit(train)
        detector.calibrate(calibration, quantile=0.95)

        result = evaluate(name, detector, test)

        filename = (
            "b004_rpm_only.csv"
            if name == "RPM only"
            else "b004_acceleration_aware.csv"
        )

        result.to_csv(OUTPUT / filename, index=False)

    print("\nAURA-B004 completed.")


if __name__ == "__main__":
    main()
