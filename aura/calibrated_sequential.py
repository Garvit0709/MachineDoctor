
import numpy as np


def detect(scores, threshold, method, parameter):
    """
    Return a binary alert sequence.

    Methods:
        single
        consecutive
        cusum
    """

    scores = np.asarray(scores, dtype=float)

    if scores.ndim != 1 or not np.all(np.isfinite(scores)):
        raise ValueError("Scores must be finite and one-dimensional.")

    if threshold <= 0:
        raise ValueError("Threshold must be positive.")

    alerts = np.zeros(len(scores), dtype=int)

    if method == "single":
        return (scores > threshold).astype(int)

    if method == "consecutive":
        required = int(parameter)
        if required < 1:
            raise ValueError("Consecutive count must be positive.")

        count = 0

        for i, score in enumerate(scores):
            count = count + 1 if score > threshold else 0

            if count >= required:
                alerts[i] = 1

        return alerts

    if method == "cusum":
        k, h = parameter

        if k < 0 or h <= 0:
            raise ValueError("Invalid CUSUM parameters.")

        cumulative = 0.0

        for i, score in enumerate(scores):
            evidence = score / threshold - 1.0

            cumulative = max(
                0.0,
                cumulative + evidence - k,
            )

            if cumulative > h:
                alerts[i] = 1
                cumulative = 0.0

        return alerts

    raise ValueError(f"Unknown method: {method}")
