
import numpy as np


def single_window_detector(scores, threshold):
    """Flag every score exceeding the threshold."""
    scores = np.asarray(scores, dtype=float)
    return (scores > threshold).astype(int)


def consecutive_detector(scores, threshold, required=2):
    """
    Trigger an alert after 'required' consecutive
    anomalous windows.

    Returns an alarm at the confirmation window.
    """
    if required < 1:
        raise ValueError("required must be at least 1")

    scores = np.asarray(scores, dtype=float)

    alerts = np.zeros(len(scores), dtype=int)
    count = 0

    for i, score in enumerate(scores):
        if score > threshold:
            count += 1
        else:
            count = 0

        if count >= required:
            alerts[i] = 1

    return alerts


def cusum_detector(scores, threshold, k=0.5, h=3.0):
    """
    Upper-sided CUSUM on normalized anomaly scores.

    The original threshold normalizes scores.
    k and h are dimensionless parameters.
    """
    if threshold <= 0:
        raise ValueError("Threshold must be positive.")

    if k < 0 or h <= 0:
        raise ValueError("Invalid CUSUM parameters.")

    scores = np.asarray(scores, dtype=float)

    normalized = scores / threshold

    alerts = np.zeros(len(scores), dtype=int)
    cumulative = 0.0

    for i, value in enumerate(normalized):
        cumulative = max(
            0.0,
            cumulative + value - k,
        )

        if cumulative > h:
            alerts[i] = 1

            # Reset after alarm.
            cumulative = 0.0

    return alerts
