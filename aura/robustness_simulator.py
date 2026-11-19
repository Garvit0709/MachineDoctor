
import numpy as np
import pandas as pd


def generate_robustness_signal(
    duration=10.0,
    sampling_rate=2000,
    start_rpm=1500,
    acceleration=60,
    profile="accelerating",
    fault_start=3.0,
    max_severity=0.8,
    noise_std=0.08,
    seed=42,
):
    """
    Generate synthetic vibration signals with
    configurable operating conditions and noise.

    This is an experimental simulator, not a
    physically validated bearing model.
    """

    if duration <= 0 or sampling_rate <= 0:
        raise ValueError("Invalid duration or sampling rate.")

    if start_rpm <= 0 or noise_std < 0 or max_severity < 0:
        raise ValueError("Invalid motor or signal parameters.")

    if not 0 <= fault_start < duration:
        raise ValueError("Invalid fault onset.")

    if profile not in {"constant", "accelerating"}:
        raise ValueError("Invalid profile.")

    rng = np.random.default_rng(seed)

    n = int(duration * sampling_rate)
    if n < 2:
        raise ValueError("At least two samples required.")

    time = np.arange(n) / sampling_rate

    if profile == "accelerating":
        rpm = start_rpm + acceleration * time
    else:
        rpm = np.full(n, start_rpm, dtype=float)

    if np.any(rpm <= 0):
        raise ValueError("RPM must remain positive.")

    frequency = rpm / 60.0

    phase = 2 * np.pi * np.cumsum(frequency) / sampling_rate

    speed_factor = (rpm / 1500.0) ** 2

    vibration = speed_factor * (
        0.5 * np.sin(phase)
        + 0.15 * np.sin(2 * phase)
    )

    vibration += rng.normal(0, noise_std, n)

    severity = np.zeros(n)

    mask = time >= fault_start

    severity[mask] = (
        max_severity
        * (time[mask] - fault_start)
        / (duration - fault_start)
    )

    defect_frequency = 3.8 * frequency
    defect_phase = np.cumsum(defect_frequency) / sampling_rate

    cycle_position = np.mod(defect_phase, 1.0)

    distance = np.minimum(
        cycle_position,
        1.0 - cycle_position,
    )

    impacts = np.exp(
        -0.5 * (distance / 0.025) ** 2
    )

    vibration += severity * impacts

    return pd.DataFrame({
        "time_s": time,
        "vibration": vibration,
        "rpm": rpm,
        "severity": severity,
    })
