
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from aura.aura_v01 import AURAPrototype

from experiments.calibrated_sequential_experiment import (
    healthy_runs,
    FEATURES,
)

from experiments.aura_run_calibration import (
    build_training_data,
    build_base_calibration,
    create_healthy_run,
)


OUTPUT = Path("results/generated")
OUTPUT.mkdir(parents=True, exist_ok=True)

QUANTILES = [0.90, 0.95, 0.975, 0.99]


def build_model():
    model = AURAPrototype(
        feature_columns=FEATURES,
        condition_columns=["rpm", "rpm_acceleration"],
        alpha=0.3,
        memory_window=10,
        min_history=3,
    )

    model.fit(
        build_training_data(),
        build_base_calibration(),
    )

    return model


def collect_calibration_data(model):
    records = []

    for start_rpm in [1200, 1500, 1800]:
        for acceleration in [60, 120]:
            for seed in range(700, 730):

                run = create_healthy_run(
                    seed, start_rpm, acceleration
                )

                output = model.predict_sequence(run)

                eligible = output[
                    output["memory_size"] >= model.min_history
                ].copy()

                if eligible.empty:
                    continue

                threshold = (
                    model.uncertainty.threshold_
                )

                familiar = eligible[
                    eligible["uncertainty_distance"]
                    <= threshold
                ]

                records.append({
                    "run_id": (
                        f"{start_rpm}_{acceleration}_{seed}"
                    ),
                    "start_rpm": start_rpm,
                    "acceleration": acceleration,
                    "seed": seed,
                    "all_max": float(
                        eligible["persistent_score"].max()
                    ),
                    "familiar_max": (
                        float(
                            familiar["persistent_score"].max()
                        )
                        if not familiar.empty else np.nan
                    ),
                    "unfamiliar_fraction": float(
                        np.mean(
                            eligible["uncertainty_distance"]
                            > threshold
                        )
                    ),
                    "familiar_windows": len(familiar),
                })

    return pd.DataFrame(records)


def analyze_thresholds(data):
    all_maxima = data["all_max"].dropna()
    familiar_maxima = data["familiar_max"].dropna()

    print("\n=== THRESHOLD COMPARISON ===")

    rows = []

    for quantile in QUANTILES:
        all_threshold = float(
            all_maxima.quantile(quantile)
        )

        familiar_threshold = (
            float(familiar_maxima.quantile(quantile))
            if not familiar_maxima.empty
            else np.nan
        )

        rows.append({
            "quantile": quantile,
            "all_windows_threshold": all_threshold,
            "familiar_only_threshold": familiar_threshold,
        })

    comparison = pd.DataFrame(rows)

    print(comparison.round(4).to_string(index=False))

    return comparison


def create_plots(data, comparison):
    fig, ax = plt.subplots(figsize=(10, 5))

    ax.hist(
        data["all_max"].dropna(),
        bins=25,
        alpha=0.6,
        label="All eligible windows",
    )

    ax.hist(
        data["familiar_max"].dropna(),
        bins=25,
        alpha=0.6,
        label="Familiar eligible windows",
    )

    ax.set_title("AURA Healthy Run Maximum Persistence Scores")
    ax.set_xlabel("Maximum persistence score")
    ax.set_ylabel("Number of runs")
    ax.legend()
    ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(
        OUTPUT / "aura_calibration_distribution.png",
        dpi=200,
    )
    plt.close()

    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(
        comparison["quantile"],
        comparison["all_windows_threshold"],
        marker="o",
        label="All eligible windows",
    )

    ax.plot(
        comparison["quantile"],
        comparison["familiar_only_threshold"],
        marker="o",
        label="Familiar-only windows",
    )

    ax.set_title("AURA Calibration Threshold Sensitivity")
    ax.set_xlabel("Quantile")
    ax.set_ylabel("Persistence threshold")
    ax.legend()
    ax.grid(alpha=0.25)

    plt.tight_layout()
    plt.savefig(
        OUTPUT / "aura_threshold_sensitivity.png",
        dpi=200,
    )
    plt.close()


def main():
    model = build_model()

    data = collect_calibration_data(model)

    if data.empty:
        raise RuntimeError("No calibration data collected.")

    print("\n=== AURA CALIBRATION DISTRIBUTION AUDIT ===")

    print("Total calibration runs:", len(data))

    print("\nTop 10 highest persistence scores:")
    print(
        data.sort_values(
            "all_max", ascending=False
        )[
            [
                "run_id",
                "start_rpm",
                "acceleration",
                "all_max",
                "familiar_max",
                "unfamiliar_fraction",
            ]
        ].head(10).round(4).to_string(index=False)
    )

    print("\nMean values by operating profile:")
    print(
        data.groupby(
            ["start_rpm", "acceleration"]
        )[
            [
                "all_max",
                "familiar_max",
                "unfamiliar_fraction",
            ]
        ].mean().round(4).to_string()
    )

    comparison = analyze_thresholds(data)

    create_plots(data, comparison)

    data.to_csv(
        OUTPUT / "aura_calibration_audit.csv",
        index=False,
    )

    comparison.to_csv(
        OUTPUT / "aura_calibration_thresholds.csv",
        index=False,
    )

    print("\nAudit completed.")
    print("Saved calibration tables and graphs.")


if __name__ == "__main__":
    main()
