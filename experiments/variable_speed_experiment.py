
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

from aura.simulator import generate_bearing_signal
from aura.features import extract_features
from aura.condition_aware import RPMConditionedDetector


SAMPLING_RATE = 2000
WINDOW_SIZE = 2000
STEP_SIZE = 1000

BASE_FEATURES = [
    "rms",
    "std",
    "peak_to_peak",
    "crest_factor",
    "kurtosis",
    "dominant_frequency",
    "spectral_centroid",
]

OUTPUT_DIR = Path("results/generated")


def create_run(condition, seed, rpm=1500):
    data = generate_bearing_signal(
        condition=condition,
        duration=5.0,
        sampling_rate=SAMPLING_RATE,
        rpm=rpm,
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
            sampling_rate=SAMPLING_RATE,
        )

        rpm_values = window["rpm"].to_numpy()
        time_values = window["time_s"].to_numpy()

        duration = time_values[-1] - time_values[0]

        features["rpm"] = float(np.mean(rpm_values))

        features["rpm_range"] = float(
            np.max(rpm_values) - np.min(rpm_values)
        )

        features["rpm_acceleration"] = float(
            (rpm_values[-1] - rpm_values[0]) / duration
        )

        features["condition"] = condition
        features["run_id"] = f"{condition}_{rpm}_{seed}"

        records.append(features)

    return pd.DataFrame(records)


def build_training_data():
    """
    Healthy constant-speed training data.
    """

    frames = []

    speeds = [
        1200, 1350, 1500, 1650,
        1800, 1950, 2100,
    ]

    for rpm in speeds:
        for seed in range(100, 120):
            frames.append(
                create_run("healthy", seed, rpm)
            )

    return pd.concat(frames, ignore_index=True)


def build_test_data():
    frames = []

    for condition in [
        "healthy",
        "speed_change",
        "degradation",
    ]:
        for seed in range(1000, 1020):
            frames.append(
                create_run(condition, seed)
            )

    return pd.concat(frames, ignore_index=True)


def evaluate_model(name, detector, test_data):
    predictions = detector.predict(test_data)

    actual = (
        test_data["condition"] == "degradation"
    ).astype(int)

    print(f"\n=== {name} ===")

    print(
        "Precision:",
        round(precision_score(actual, predictions, zero_division=0), 4)
    )

    print(
        "Recall:",
        round(recall_score(actual, predictions, zero_division=0), 4)
    )

    print(
        "F1:",
        round(f1_score(actual, predictions, zero_division=0), 4)
    )

    print("Confusion matrix:")
    print(confusion_matrix(actual, predictions))

    results = test_data.copy()
    results["prediction"] = predictions

    rates = (
        results.groupby("condition")["prediction"]
        .mean()
        .round(4)
    )

    print("\nAnomaly rate by condition:")
    print(rates)

    return results


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    train_data = build_training_data()
    test_data = build_test_data()

    print("Training windows:", len(train_data))
    print("Testing windows:", len(test_data))

    # B002-equivalent model, reconstructed on the
    # same data for a controlled comparison.
    baseline = RPMConditionedDetector(
        feature_columns=BASE_FEATURES,
        threshold_quantile=0.95,
    )

    baseline.fit(train_data)

    baseline_results = evaluate_model(
        "B003-A: RPM-conditioned baseline",
        baseline,
        test_data,
    )

    # Experimental variant: append RPM variation
    # and acceleration as diagnostic features.
    extended_features = BASE_FEATURES + [
        "rpm_range",
        "rpm_acceleration",
    ]

    extended = RPMConditionedDetector(
        feature_columns=extended_features,
        threshold_quantile=0.95,
    )

    extended.fit(train_data)

    extended_results = evaluate_model(
        "B003-B: Extended features",
        extended,
        test_data,
    )

    baseline_results.to_csv(
        OUTPUT_DIR / "b003_baseline.csv",
        index=False,
    )

    extended_results.to_csv(
        OUTPUT_DIR / "b003_extended.csv",
        index=False,
    )

    print("\nExperiment B003 completed.")


if __name__ == "__main__":
    main()
