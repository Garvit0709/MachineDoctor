
from pathlib import Path

from backend.aura_contract import validate_aura_features
from backend.aura_model_store import load_aura_model
from experiments.aura_run_calibration import build_base_calibration


OUTPUT = Path(
    "results/generated/aura_diagnostic_test.csv"
)


def main():
    model, metadata = load_aura_model(
        "aura_v01_synthetic"
    )

    data = build_base_calibration().copy()

    required_columns = [
        "run_id",
        "time_start",
        "time_end",
        *metadata["feature_columns"],
        *metadata["condition_columns"],
    ]

    required_columns = list(
        dict.fromkeys(required_columns)
    )

    missing = [
        column
        for column in required_columns
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Source data missing columns: {missing}"
        )

    run_id = data["run_id"].iloc[0]

    selected = data.loc[
        data["run_id"] == run_id,
        required_columns,
    ].copy()

    selected = selected.sort_values(
        ["time_start", "time_end"]
    )

    selected = validate_aura_features(selected)

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    selected.to_csv(
        OUTPUT,
        index=False,
    )

    print("\n=== AURA TEST CSV GENERATED ===")
    print("Model ready:", model.is_ready)
    print("Run ID:", run_id)
    print("Windows:", len(selected))
    print("Columns:", selected.columns.tolist())
    print("Saved:", OUTPUT.resolve())


if __name__ == "__main__":
    main()
