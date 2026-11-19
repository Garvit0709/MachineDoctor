
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline


DATA_PATH = Path(
    "results/generated/b009_cwru_features.csv"
)

OUTPUT_DIR = Path("results/generated")

FEATURES = [
    "rms",
    "std",
    "peak_to_peak",
    "crest_factor",
    "kurtosis",
    "dominant_frequency",
    "spectral_centroid",
]


def evaluate_split(data, train_id, test_id, experiment_name):
    """
    Train on one healthy recording and evaluate
    on another healthy recording plus two faults.
    """

    train = data[data["file_id"] == train_id].copy()

    test = data[
        data["file_id"].isin([test_id, 130, 131])
    ].copy()

    if train.empty or test.empty:
        raise ValueError("Missing training or testing data.")

    model = make_pipeline(
        StandardScaler(),
        IsolationForest(
            n_estimators=200,
            contamination=0.05,
            random_state=42,
        ),
    )

    model.fit(train[FEATURES])

    predictions = model.predict(test[FEATURES])

    test["prediction"] = np.where(
        predictions == -1, 1, 0
    )

    test["anomaly_score"] = -model.decision_function(
        test[FEATURES]
    )

    test["actual"] = (
        test["condition"] == "outer_race_fault"
    ).astype(int)

    print(f"\n=== {experiment_name} ===")

    print(f"Training recording: {train_id}.mat")
    print(f"Healthy test recording: {test_id}.mat")

    print("\nAnomaly rate by recording:")
    print(
        test.groupby(
            ["file_id", "condition"]
        )["prediction"].mean().round(4)
    )

    print("\nRecording-level summary:")

    for file_id, group in test.groupby("file_id"):
        anomaly_rate = group["prediction"].mean()

        print(
            f"File {file_id}: "
            f"{len(group)} windows, "
            f"{anomaly_rate:.2%} anomalous"
        )

    test["experiment"] = experiment_name

    return test


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            "Run cwru_feature_experiment.py first."
        )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = pd.read_csv(DATA_PATH)

    required = set(FEATURES + ["file_id", "condition"])

    if not required.issubset(data.columns):
        raise ValueError("Required feature columns missing.")

    results_a = evaluate_split(
        data,
        train_id=97,
        test_id=98,
        experiment_name="B009-A",
    )

    results_b = evaluate_split(
        data,
        train_id=98,
        test_id=97,
        experiment_name="B009-B",
    )

    combined = pd.concat(
        [results_a, results_b],
        ignore_index=True,
    )

    output_path = (
        OUTPUT_DIR / "b009_real_anomaly_results.csv"
    )

    combined.to_csv(output_path, index=False)

    print("\n=== AURA-B009 PART 2 COMPLETED ===")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
