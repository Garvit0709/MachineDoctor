
import numpy as np

from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_COLUMNS = [
    "rms",
    "std",
    "peak_to_peak",
    "crest_factor",
    "kurtosis",
    "dominant_frequency",
    "spectral_centroid",
]


class BearingBaselineDetector:
    """
    Healthy-only anomaly detector using Isolation Forest.

    This is an experimental baseline, not the AURA algorithm.
    """

    def __init__(self, contamination=0.05, seed=42):
        self.model = Pipeline([
            ("scaler", StandardScaler()),
            (
                "detector",
                IsolationForest(
                    n_estimators=200,
                    contamination=contamination,
                    random_state=seed,
                ),
            ),
        ])

        self.is_fitted = False

    def fit(self, healthy_features):
        self.model.fit(healthy_features[FEATURE_COLUMNS])
        self.is_fitted = True
        return self

    def predict(self, features):
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted first.")

        predictions = self.model.predict(
            features[FEATURE_COLUMNS]
        )

        # sklearn: 1 = normal, -1 = anomaly
        return np.where(predictions == -1, 1, 0)

    def anomaly_score(self, features):
        if not self.is_fitted:
            raise RuntimeError("Model must be fitted first.")

        # Higher values indicate greater abnormality.
        return -self.model.decision_function(
            features[FEATURE_COLUMNS]
        )
