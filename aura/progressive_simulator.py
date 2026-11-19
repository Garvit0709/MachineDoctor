
import numpy as np
import pandas as pd


def generate_progressive_signal(
    duration=10.0,
    sampling_rate=2000,
    start_rpm=1500,
    acceleration=60,
    profile="accelerating",
    fault_start=3.0,
    max_severity=0.8,
    seed=42,
):
    """
    Generate a simplified vibration signal with
    a known degradation onset time.

    Fault severity increases linearly after onset.
    """

    if duration <= 0 or sampling_rate <= 0:
        raise ValueError("Duration and sampling rate must be positive.")

    if not 0 <= fault_start < duration:
        raise ValueError("Invalid fault onset time.")

    if max_severity < 0:
        raise ValueError("Severity cannot be negative.")

    if profile not in {"constant", "accelerating"}:
        raise ValueError("Invalid profile.")

    rng = np.random.default_rng(seed)

    n = int(duration * sampling_rate)
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

    # Severity is zero before the fault begins.
    severity = np.zeros(n)

    fault_mask = time >= fault_start

    severity[fault_mask] = (
        max_severity
        * (time[fault_mask] - fault_start)
        / (duration - fault_start)
    )

    # Simplified speed-dependent defect impacts.
    defect_frequency = 3.8 * rotational_frequency

    defect_phase = np.cumsum(
        defect_frequency
    ) / sampling_rate

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
        "fault_active": fault_mask.astype(int),
        "profile": profile,
    })
