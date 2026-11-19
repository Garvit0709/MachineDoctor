
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

FEATURE_COLUMNS = [
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

        features["rpm"] = float(window["rpm"].mean())
        features["condition"] = condition
        features["run_id"] = f"{condition}_{rpm}_{seed}"

        records.append(features)

    return pd.DataFrame(records)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    training_speeds = [
        1200, 1350, 1500, 1650,
        1800, 1950, 2100,
    ]

    training_frames = []

    for rpm in training_speeds:
        for seed in range(100, 120):
            training_frames.append(
                create_run("healthy", seed, rpm)
            )

    train_data = pd.concat(
        training_frames, ignore_index=True
    )

    test_frames = []

    for condition in [
        "healthy",
        "speed_change",
        "degradation",
    ]:
        for seed in range(1000, 1020):
            test_frames.append(
                create_run(condition, seed)
            )

    test_data = pd.concat(
        test_frames, ignore_index=True
    )

    detector = RPMConditionedDetector(
        feature_columns=FEATURE_COLUMNS,
        threshold_quantile=0.95,
    )

    detector.fit(train_data)

    test_data["prediction"] = detector.predict(test_data)
    test_data["anomaly_score"] = detector.anomaly_score(test_data)

    test_data["actual"] = (
        test_data["condition"] == "degradation"
    ).astype(int)

    y_true = test_data["actual"]
    y_pred = test_data["prediction"]

    print("\n=== AURA-B002 EXPERIMENT ===")

    print("Training windows:", len(train_data))
    print("Testing windows:", len(test_data))

    print(
        "Precision:",
        round(precision_score(y_true, y_pred, zero_division=0), 4),
    )

    print(
        "Recall:",
        round(recall_score(y_true, y_pred, zero_division=0), 4),
    )

    print(
        "F1 Score:",
        round(f1_score(y_true, y_pred, zero_division=0), 4),
    )

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, y_pred))

    print("\nAnomaly rate by condition:")
    print(
        test_data.groupby("condition")["prediction"]
        .mean()
        .round(4)
    )

    test_data.to_csv(
        OUTPUT_DIR / "condition_aware_predictions.csv",
        index=False,
    )


if __name__ == "__main__":
    main()
