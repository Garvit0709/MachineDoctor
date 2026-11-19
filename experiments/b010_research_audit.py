
from pathlib import Path
from datetime import datetime, timezone
import json

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results" / "generated"
REPORT_DIR = ROOT / "docs"

EXPERIMENT_FILES = {
    "B001": "baseline_predictions.csv",
    "B002": "condition_aware_predictions.csv",
    "B003": "b003_extended.csv",
    "B004": "b004_acceleration_aware.csv",
    "B005": "b005_early_warning.csv",
    "B006": "b006_sequential_results.csv",
    "B007": "b007_calibrated_results.csv",
    "B008": "b008_robustness_results.csv",
    "B009": "b009_real_anomaly_results.csv",
}


def inspect_file(experiment, filename):
    path = RESULTS / filename

    if not path.exists():
        return {
            "experiment": experiment,
            "file": filename,
            "status": "missing",
            "rows": None,
            "columns": [],
        }

    data = pd.read_csv(path)

    return {
        "experiment": experiment,
        "file": filename,
        "status": "available",
        "rows": len(data),
        "columns": list(data.columns),
    }


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    audit = [
        inspect_file(exp, filename)
        for exp, filename in EXPERIMENT_FILES.items()
    ]

    available = sum(
        item["status"] == "available"
        for item in audit
    )

    report = {
        "project": "MachineDoctor",
        "algorithm": "AURA",
        "experiment": "B010",
        "created_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "dataset_scope": (
            "Synthetic experiments and exploratory "
            "CWRU real-recording analysis"
        ),
        "novelty_verified": False,
        "experiments": audit,
    }

    json_path = REPORT_DIR / "b010_research_audit.json"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)

    summary = pd.DataFrame([
        {
            "Experiment": item["experiment"],
            "Status": item["status"],
            "Rows": item["rows"],
        }
        for item in audit
    ])

    print("\n=== AURA-B010 RESEARCH AUDIT ===")
    print(summary.to_string(index=False))

    print(f"\nAvailable result files: {available}/9")
    print(f"Audit saved: {json_path}")

    if available < 9:
        print(
            "\nSome results are missing. "
            "Review the original experiments before "
            "finalizing the research audit."
        )


if __name__ == "__main__":
    main()
