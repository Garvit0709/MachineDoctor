
from pathlib import Path

import pandas as pd

from aura.features import extract_features


DATA_DIR = Path("data/generated")
OUTPUT_DIR = Path("results/generated")

SAMPLING_RATE = 2000
WINDOW_SIZE = 2000
STEP_SIZE = 1000


def process_condition(condition):
    file_path = DATA_DIR / f"{condition}.csv"

    data = pd.read_csv(file_path)

    required_columns = {"time_s", "vibration", "rpm"}

    if not required_columns.issubset(data.columns):
        raise ValueError(f"Missing required columns in {file_path}")

    records = []

    for start in range(
        0,
        len(data) - WINDOW_SIZE + 1,
        STEP_SIZE
    ):
        end = start + WINDOW_SIZE
        window = data.iloc[start:end]

        features = extract_features(
            window["vibration"].to_numpy(),
            sampling_rate=SAMPLING_RATE
        )

        features["condition"] = condition
        features["time_s"] = float(window["time_s"].mean())
        features["rpm"] = float(window["rpm"].mean())

        records.append(features)

    return records


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    conditions = [
        "healthy",
        "speed_change",
        "degradation",
    ]

    all_records = []

    for condition in conditions:
        records = process_condition(condition)
        all_records.extend(records)

        print(
            f"{condition}: {len(records)} feature windows extracted"
        )

    feature_data = pd.DataFrame(all_records)

    output_path = OUTPUT_DIR / "bearing_features.csv"
    feature_data.to_csv(output_path, index=False)

    print("\nFeature extraction completed.")
    print(f"Saved to: {output_path}")

    print("\nAverage features by condition:")
    print(
        feature_data.groupby("condition")[
            ["rms", "crest_factor", "kurtosis", "dominant_frequency"]
        ].mean().round(4)
    )


if __name__ == "__main__":
    main()
