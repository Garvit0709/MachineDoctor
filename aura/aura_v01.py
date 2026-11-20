
import numpy as np
import pandas as pd

from aura.acceleration_aware import AccelerationAwareDetector
from aura.uncertainty import OperatingConditionUncertainty
from aura.dual_memory import DualMemoryResidualEngine
from aura.decision_engine import AURADecisionEngine


class AURAPrototype:
    """
    AURA v0.1: integrated experimental diagnostic pipeline.

    This prototype uses:
      - a frozen condition-aware healthy model
      - operating-condition unfamiliarity
      - short-term residual memory
      - a calibrated three-state decision rule

    No automatic adaptation or failure probability estimation.
    """

    def __init__(
        self,
        feature_columns,
        condition_columns=("rpm", "rpm_acceleration"),
        alpha=0.3,
        memory_window=10,
        min_history=3,
    ):
        self.feature_columns = list(feature_columns)
        self.condition_columns = list(condition_columns)

        self.alpha = alpha
        self.memory_window = memory_window
        self.min_history = min_history

        self.reference = AccelerationAwareDetector(
            feature_columns=self.feature_columns,
            condition_columns=self.condition_columns,
        )

        self.uncertainty = OperatingConditionUncertainty()

        self.memory = DualMemoryResidualEngine(
            alpha=alpha,
            window_size=memory_window,
        )

        self.decision = None
        self.is_ready = False

    def _residual_matrix(self, data):
        conditions = data[
            self.condition_columns
        ].to_numpy(dtype=float)

        residuals = []

        for feature in self.feature_columns:
            expected = self.reference.models[
                feature
            ].predict(conditions)

            observed = data[feature].to_numpy(
                dtype=float
            )

            residuals.append(observed - expected)

        return np.column_stack(residuals)

    def fit(self, healthy_training, healthy_calibration):
        """
        Fit healthy reference and calibrate thresholds.

        Training and calibration must come from
        independent healthy recordings.
        """

        self.reference.fit(healthy_training)

        training_residuals = self._residual_matrix(
            healthy_training
        )

        self.memory.fit(training_residuals)

        self.uncertainty.fit(
            healthy_training[
                self.condition_columns
            ].to_numpy(dtype=float)
        )

        calibration_conditions = healthy_calibration[
            self.condition_columns
        ].to_numpy(dtype=float)

        self.uncertainty.calibrate(
            calibration_conditions,
            quantile=0.95,
        )

        # Calibrate persistence using independent
        # healthy sequences, resetting short-term
        # memory at recording boundaries.
        persistence_scores = []

        if "run_id" not in healthy_calibration.columns:
            raise ValueError(
                "Calibration data requires run_id."
            )

        for _, run in healthy_calibration.groupby(
            "run_id", sort=False
        ):
            self.memory.reset_short_term()

            residuals = self._residual_matrix(run)

            for residual in residuals:
                result = self.memory.update(residual)

                if result["memory_size"] >= self.min_history:
                    persistence_scores.append(
                        result["persistent_score"]
                    )

        if not persistence_scores:
            raise ValueError(
                "Not enough calibration history."
            )

        persistence_threshold = float(
            np.quantile(persistence_scores, 0.95)
        )

        self.decision = AURADecisionEngine(
            uncertainty_threshold=self.uncertainty.threshold_,
            persistence_threshold=max(
                persistence_threshold, 1e-8
            ),
            min_history=self.min_history,
        )

        self.memory.reset_short_term()
        self.is_ready = True

        return self

    def predict_sequence(self, data):
        """
        Process one ordered machine recording.

        Reset memory at the beginning to prevent
        leakage between independent recordings.
        """
        if not self.is_ready:
            raise RuntimeError("Fit AURA before prediction.")

        if data.empty:
            raise ValueError("Input sequence is empty.")

        self.memory.reset_short_term()

        residuals = self._residual_matrix(data)

        conditions = data[
            self.condition_columns
        ].to_numpy(dtype=float)

        distances = self.uncertainty.distance(
            conditions
        )

        records = []

        for index, (residual, distance) in enumerate(
            zip(residuals, distances)
        ):
            memory_result = self.memory.update(residual)

            decision = self.decision.decide(
                float(distance),
                memory_result,
            )

            records.append({
                "index": index,
                "state": decision["state"],
                "reason": decision["reason"],
                "uncertainty_distance": (
                    decision["uncertainty_distance"]
                ),
                "persistent_score": (
                    decision["persistent_score"]
                ),
                "instantaneous_score": (
                    decision["instantaneous_score"]
                ),
                "memory_size": (
                    decision["memory_size"]
                ),
            })

        return pd.DataFrame(records)
