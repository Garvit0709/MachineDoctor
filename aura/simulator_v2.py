
import numpy as np
import pandas as pd


def generate_motor_signal(
    condition="healthy",
    profile="constant",
    start_rpm=1500,
    acceleration=120,
    duration=5.0,
    sampling_rate=2000,
    seed=42,
):
    """
    Simplified synthetic motor-bearing vibration simulator.

    condition: healthy or degradation
    profile: constant or accelerating
    acceleration: RPM per second
    """

    if condition not in {"healthy", "degradation"}:
        raise ValueError("Invalid condition.")

    if profile not in {"constant", "accelerating"}:
        raise ValueError("Invalid speed profile.")

    if duration <= 0 or sampling_rate <= 0 or start_rpm <= 0:
        raise ValueError("Invalid simulation parameters.")

    n = int(duration * sampling_rate)

    if n < 2:
        raise ValueError("At least two samples are required.")

    rng = np.random.default_rng(seed)
    time = np.arange(n) / sampling_rate

    if profile == "accelerating":
        rpm = start_rpm + acceleration * time
    else:
        rpm = np.full(n, start_rpm, dtype=float)

    if np.any(rpm <= 0):
        raise ValueError("RPM must remain positive.")

    rotational_frequency = rpm / 60.0

    phase = (
        2 * np.pi
        * np.cumsum(rotational_frequency)
        / sampling_rate
    )

    speed_factor = (rpm / 1500.0) ** 2

    vibration = speed_factor * (
        0.5 * np.sin(phase)
        + 0.15 * np.sin(2 * phase)
    )

    vibration += rng.normal(0, 0.08, n)

    if condition == "degradation":
        # Simplified bearing-related impact repetition.
        # The factor 3.8 is illustrative, not derived
        # from a specific bearing's geometry.
        defect_frequency = 3.8 * rotational_frequency

        defect_phase = np.cumsum(
            defect_frequency
        ) / sampling_rate

        # Short pulses near each defect cycle.
        distance_to_impact = np.minimum(
            np.mod(defect_phase, 1.0),
            1.0 - np.mod(defect_phase, 1.0),
        )

        impacts = np.exp(
            -0.5 * (distance_to_impact / 0.025) ** 2
        )

        severity = 0.05 + 0.65 * time / duration

        vibration += severity * impacts

    return pd.DataFrame({
        "time_s": time,
        "vibration": vibration,
        "rpm": rpm,
        "condition": condition,
        "profile": profile,
    })
