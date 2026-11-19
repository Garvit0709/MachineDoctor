
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def visualize_signals():
    conditions = [
        "healthy",
        "speed_change",
        "degradation",
    ]

    fig, axes = plt.subplots(
        3, 1,
        figsize=(12, 9),
        sharex=True,
    )

    for ax, condition in zip(axes, conditions):
        file_path = Path("data/generated") / f"{condition}.csv"

        data = pd.read_csv(file_path)

        ax.plot(
            data["time_s"],
            data["vibration"],
            linewidth=0.7,
        )

        ax.set_title(condition.replace("_", " ").title())
        ax.set_ylabel("Relative Vibration")
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel("Time (seconds)")

    fig.suptitle(
        "MachineDoctor - Synthetic Motor Bearing Signals",
        fontsize=14,
    )

    plt.tight_layout()

    output_dir = Path("results/generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "bearing_signals.png"

    plt.savefig(output_file, dpi=200)
    plt.show()

    print(f"Visualization saved: {output_file}")


if __name__ == "__main__":
    visualize_signals()
