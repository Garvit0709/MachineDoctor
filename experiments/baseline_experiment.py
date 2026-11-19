
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)

from aura.simulator import generate_bearing_signal
from aura.features import extract_features
from aura.baseline import (
    BearingBaselineDetector,
    FEATURE_COLUMNS,
)


SAMPLING_RATE = 2000
WINDOW_SIZE = 2000
STEP_SIZE = 1000

OUTPUT_DIR = Path("results/generated")


def create_run(condition, seed, rpm=1500):
    """
    Generate one independent synthetic recording
    and extract features from its windows.
    """

    signal_data = generate_bearing_signal(
        condition=condition,
        duration=5.0,
        sampling_rate=SAMPLING_RATE,
        rpm=rpm,
        seed=seed,
    )

    records = []

    for start in range(
        0,
        len(signal_data) - WINDOW_SIZE + 1,
        STEP_SIZE,
    ):
        window = signal_data.iloc[start:start + WINDOW_SIZE]

        features = extract_features(
            window["vibration"].to_numpy(),
            sampling_rate=SAMPLING_RATE,
        )

        features["condition"] = condition
        features["run_id"] = seed
        features["rpm"] = float(window["rpm"].mean())

        records.append(features)

    return pd.DataFrame(records)


def build_dataset(conditions, seeds):
    frames = []

    for condition in conditions:
        for seed in seeds:
            frames.append(create_run(condition, seed))

    return pd.concat(frames, ignore_index=True)


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Training and testing use disjoint simulation runs.
    train_data = build_dataset(
        conditions=["healthy"],
        seeds=range(100, 150),
    )

    test_data = build_dataset(
        conditions=[
            "healthy",
            "speed_change",
            "degradation",
        ],
        seeds=range(1000, 1020),
    )

    detector = BearingBaselineDetector(
        contamination=0.05,
        seed=42,
    )

    detector.fit(train_data)

    test_data["prediction"] = detector.predict(test_data)
    test_data["anomaly_score"] = detector.anomaly_score(test_data)

    # For this experiment, only degradation is labelled
    # as a fault. Speed changes remain healthy.
    test_data["actual"] = (
        test_data["condition"] == "degradation"
    ).astype(int)

    y_true = test_data["actual"]
    y_pred = test_data["prediction"]

    print("\n=== BASELINE EXPERIMENT ===")

    print(f"Training windows: {len(train_data)}")
    print(f"Testing windows: {len(test_data)}")

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
        OUTPUT_DIR / "baseline_predictions.csv",
        index=False,
    )

    # Visualize anomaly scores.
    conditions = [
        "healthy",
        "speed_change",
        "degradation",
    ]

    fig, ax = plt.subplots(figsize=(10, 5))

    scores = [
        test_data.loc[
            test_data["condition"] == condition,
            "anomaly_score",
        ].to_numpy()
        for condition in conditions
    ]

    ax.boxplot(scores, tick_labels=conditions)
    ax.axhline(
        y=0,
        linestyle="--",
        label="Decision threshold",
    )

    ax.set_title("Isolation Forest: Anomaly Scores")
    ax.set_ylabel("Anomaly score")
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(
        OUTPUT_DIR / "baseline_anomaly_scores.png",
        dpi=200,
    )
    plt.show()


if __name__ == "__main__":
    main()
