
from collections import deque

import numpy as np


class DualMemoryResidualEngine:
    """
    AURA v0.1 experimental dual-memory component.

    Long-term memory:
        Frozen healthy residual reference.

    Short-term memory:
        EWMA of recent standardized residuals.

    No automatic baseline adaptation in this version.
    """

    def __init__(self, alpha=0.3, window_size=10):
        if not 0 < alpha <= 1:
            raise ValueError("alpha must be in (0, 1].")

        if not isinstance(window_size, int) or window_size < 2:
            raise ValueError("window_size must be an integer >= 2.")

        self.alpha = alpha
        self.window_size = window_size

        self.long_term_mean = None
        self.long_term_scale = None

        self.short_term_memory = None
        self.history = deque(maxlen=window_size)
        self.is_fitted = False

    def _validate_vector(self, vector):
        x = np.asarray(vector, dtype=float)

        if x.ndim != 1 or x.size == 0:
            raise ValueError("Expected a nonempty 1D vector.")

        if not np.all(np.isfinite(x)):
            raise ValueError("Vector must contain finite values.")

        return x

    def fit(self, healthy_residuals):
        """
        Fit a frozen long-term reference using
        verified healthy residual observations.
        """
        x = np.asarray(healthy_residuals, dtype=float)

        if x.ndim != 2 or x.shape[0] < 3:
            raise ValueError(
                "Expected at least three healthy residual rows."
            )

        if x.shape[1] == 0 or not np.all(np.isfinite(x)):
            raise ValueError("Invalid healthy residual matrix.")

        self.long_term_mean = np.mean(x, axis=0)

        self.long_term_scale = np.maximum(
            np.std(x, axis=0),
            1e-6,
        )

        self.is_fitted = True
        self.reset_short_term()

        return self

    def reset_short_term(self):
        """
        Reset recent history without changing
        the frozen healthy reference.
        """
        self.short_term_memory = None
        self.history.clear()

    def update(self, residual):
        """
        Process one new residual vector.

        Returns diagnostic evidence, not a
        calibrated failure probability.
        """
        if not self.is_fitted:
            raise RuntimeError("Fit the engine first.")

        x = self._validate_vector(residual)

        if x.size != self.long_term_mean.size:
            raise ValueError("Unexpected feature dimension.")

        z = (
            x - self.long_term_mean
        ) / self.long_term_scale

        if self.short_term_memory is None:
            self.short_term_memory = np.zeros_like(z)

        self.short_term_memory = (
            self.alpha * z
            + (1 - self.alpha) * self.short_term_memory
        )

        self.history.append(z.copy())

        history_matrix = np.vstack(self.history)

        # Instantaneous standardized residual magnitude.
        instantaneous_score = float(
            np.sqrt(np.mean(z ** 2))
        )

        # Persistent signed deviation magnitude.
        persistent_score = float(
            np.sqrt(np.mean(self.short_term_memory ** 2))
        )

        # Mean recent anomaly magnitude.
        recent_scores = np.sqrt(
            np.mean(history_matrix ** 2, axis=1)
        )

        recent_mean_score = float(
            np.mean(recent_scores)
        )

        # Change in anomaly magnitude across recent history.
        if len(recent_scores) >= 2:
            trend = float(
                recent_scores[-1] - recent_scores[0]
            )
        else:
            trend = 0.0

        return {
            "instantaneous_score": instantaneous_score,
            "persistent_score": persistent_score,
            "recent_mean_score": recent_mean_score,
            "trend": trend,
            "memory_size": len(self.history),
            "standardized_residual": z.copy(),
            "short_term_memory": self.short_term_memory.copy(),
        }
