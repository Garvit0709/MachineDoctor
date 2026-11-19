
from pathlib import Path

import pandas as pd

from aura.cwru_loader import load_cwru_record
from aura.features import extract_features


OUTPUT_DIR = Path("results/generated")

FILE_IDS = [97, 98, 130, 131]

WINDOW_SIZE = 12000
STEP_SIZE = 12000


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    records = []

    for file_id in FILE_IDS:
        record = load_cwru_record(file_id)

        signal = record["signal"]
        sampling_rate = record["sampling_rate"]

        print(f"\nProcessing file: {file_id}.mat")
        print(f"Condition: {record['condition']}")
        print(f"Motor RPM: {record['rpm']}")

        window_count = 0

        for start in range(
            0,
            len(signal) - WINDOW_SIZE + 1,
            STEP_SIZE,
        ):
            window = signal[start:start + WINDOW_SIZE]

            features = extract_features(
                window,
                sampling_rate=sampling_rate,
            )

            features.update({
                "file_id": file_id,
                "condition": record["condition"],
                "load_hp": record["load_hp"],
                "rpm": record["rpm"],
                "window_start_s": start / sampling_rate,
            })

            records.append(features)
            window_count += 1

        print(f"Extracted windows: {window_count}")

    features_df = pd.DataFrame(records)

    output_path = OUTPUT_DIR / "b009_cwru_features.csv"
    features_df.to_csv(output_path, index=False)

    print("\n=== AURA-B009 REAL DATA FEATURES ===")
    print("Total feature windows:", len(features_df))

    print("\nWindows by recording:")
    print(
        features_df.groupby(
            ["file_id", "condition"]
        ).size()
    )

    print("\nAverage features by condition:")
    print(
        features_df.groupby("condition")[
            [
                "rms",
                "crest_factor",
                "kurtosis",
                "dominant_frequency",
            ]
        ].mean().round(4)
    )

    print(f"\nResults saved to: {output_path}")


if __name__ == "__main__":
    main()
