
import numpy as np


class AURADecisionEngine:
    """
    AURA v0.1 experimental diagnostic decision engine.

    States:
        NORMAL
        WARNING
        UNKNOWN

    This component combines calibrated operating-condition
    unfamiliarity with persistent residual evidence.

    It does not calculate failure probabilities.
    """

    def __init__(
        self,
        uncertainty_threshold,
        persistence_threshold,
        min_history=3,
    ):
        if not np.isfinite(uncertainty_threshold):
            raise ValueError("Invalid uncertainty threshold.")

        if not np.isfinite(persistence_threshold):
            raise ValueError("Invalid persistence threshold.")

        if uncertainty_threshold <= 0:
            raise ValueError(
                "Uncertainty threshold must be positive."
            )

        if persistence_threshold <= 0:
            raise ValueError(
                "Persistence threshold must be positive."
            )

        if not isinstance(min_history, int) or min_history < 1:
            raise ValueError("min_history must be >= 1.")

        self.uncertainty_threshold = uncertainty_threshold
        self.persistence_threshold = persistence_threshold
        self.min_history = min_history

    def decide(
        self,
        uncertainty_distance,
        memory_result,
    ):
        """
        Combine uncertainty and memory evidence.

        Returns a diagnostic decision dictionary.
        """

        if not np.isfinite(uncertainty_distance):
            raise ValueError("Invalid uncertainty distance.")

        required_keys = {
            "persistent_score",
            "instantaneous_score",
            "memory_size",
        }

        if not required_keys.issubset(memory_result):
            raise ValueError(
                "Missing required memory measurements."
            )

        persistent = float(
            memory_result["persistent_score"]
        )

        instantaneous = float(
            memory_result["instantaneous_score"]
        )

        history_size = int(
            memory_result["memory_size"]
        )

        if (
            not np.isfinite(persistent)
            or not np.isfinite(instantaneous)
            or persistent < 0
            or instantaneous < 0
            or history_size < 0
        ):
            raise ValueError("Invalid memory evidence.")

        if uncertainty_distance > self.uncertainty_threshold:
            state = "UNKNOWN"
            reason = "Unfamiliar operating conditions"

        elif history_size < self.min_history:
            state = "UNKNOWN"
            reason = "Insufficient observation history"

        elif persistent > self.persistence_threshold:
            state = "WARNING"
            reason = "Persistent abnormal residual behavior"

        else:
            state = "NORMAL"
            reason = "Residual evidence within configured limits"

        return {
            "state": state,
            "reason": reason,
            "uncertainty_distance": float(
                uncertainty_distance
            ),
            "persistent_score": persistent,
            "instantaneous_score": instantaneous,
            "memory_size": history_size,
        }
