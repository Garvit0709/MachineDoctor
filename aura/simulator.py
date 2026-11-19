
import numpy as np
import pandas as pd
from pathlib import Path


def generate_bearing_signal(
    condition="healthy",
    duration=5.0,
    sampling_rate=2000,
    rpm=1500,
    seed=42,
):
    """
    Generate a simplified synthetic motor-bearing vibration signal.

    Conditions:
        healthy
        speed_change
        degradation

    Returns:
        pandas DataFrame containing time, vibration, and RPM.
    """

    valid_conditions = {"healthy", "speed_change", "degradation"}

    if condition not in valid_conditions:
        raise ValueError(f"Condition must be one of {valid_conditions}")

    if duration <= 0 or sampling_rate <= 0 or rpm <= 0:
        raise ValueError("Duration, sampling rate and RPM must be positive.")

    rng = np.random.default_rng(seed)

    n_samples = int(duration * sampling_rate)

    if n_samples < 2:
        raise ValueError("At least two samples are required.")

    time = np.arange(n_samples) / sampling_rate

    # RPM profile: constant or gradually increasing.
    if condition == "speed_change":
        rpm_profile = np.linspace(rpm, rpm * 1.4, n_samples)
    else:
        rpm_profile = np.full(n_samples, rpm, dtype=float)

    # Convert instantaneous RPM to rotational frequency (Hz).
    rotational_frequency = rpm_profile / 60.0

    # Integrate frequency to obtain continuous rotational phase.
    phase = 2 * np.pi * np.cumsum(rotational_frequency) / sampling_rate

    # Simplified shaft-related vibration.
    vibration = (
        0.5 * np.sin(phase)
        + 0.15 * np.sin(2 * phase)
    )

    # Speed-dependent vibration amplitude.
    speed_factor = (rpm_profile / rpm) ** 2
    vibration *= speed_factor

    # Add measurement noise.
    vibration += rng.normal(0, 0.08, n_samples)

    if condition == "degradation":
        # Illustrative defect impacts, not a calibrated bearing model.
        defect_frequency = 95.0

        # Impacts gradually become stronger over time.
        severity = 0.05 + 0.65 * (time / duration)

        # Generate periodic defect-like excitation.
        impact_phase = np.mod(time * defect_frequency, 1.0)

        # Narrow impulse at each defect cycle.
        impacts = np.exp(
            -0.5 * (impact_phase / 0.045) ** 2
        )

        # Simplified decaying resonance after each impact.
        vibration += severity * impacts

    return pd.DataFrame(
        {
            "time_s": time,
            "vibration": vibration,
            "rpm": rpm_profile,
            "condition": condition,
        }
    )


def save_simulations():
    output_dir = Path("data/generated")
    output_dir.mkdir(parents=True, exist_ok=True)

    conditions = [
        "healthy",
        "speed_change",
        "degradation",
    ]

    for condition in conditions:
        data = generate_bearing_signal(condition=condition)

        file_path = output_dir / f"{condition}.csv"
        data.to_csv(file_path, index=False)

        print(f"Saved: {file_path} ({len(data)} samples)")


if __name__ == "__main__":
    save_simulations()
