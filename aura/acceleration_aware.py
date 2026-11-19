
import numpy as np

from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import (
    PolynomialFeatures,
    StandardScaler,
)
from sklearn.linear_model import Ridge


class AccelerationAwareDetector:
    """
    Healthy-only residual anomaly detector.

    Conditioning variables:
        rpm
        rpm_acceleration
    """

    def __init__(
        self,
        feature_columns,
        condition_columns=("rpm", "rpm_acceleration"),
        degree=2,
    ):
        self.feature_columns = list(feature_columns)
        self.condition_columns = list(condition_columns)
        self.degree = degree

        self.models = {}
        self.scales = {}
        self.threshold = None

    def fit(self, training_data):
        conditions = training_data[
            self.condition_columns
        ].to_numpy()

        for feature in self.feature_columns:
            target = training_data[feature].to_numpy()

            model = make_pipeline(
                PolynomialFeatures(
                    degree=self.degree,
                    include_bias=False,
                ),
                StandardScaler(),
                Ridge(alpha=1.0),
            )

            model.fit(conditions, target)

            residuals = target - model.predict(conditions)

            self.models[feature] = model
            self.scales[feature] = max(
                float(np.std(residuals)),
                1e-6,
            )

        return self

    def anomaly_score(self, data):
        conditions = data[
            self.condition_columns
        ].to_numpy()

        residuals = []

        for feature in self.feature_columns:
            expected = self.models[feature].predict(
                conditions
            )

            observed = data[feature].to_numpy()

            standardized = (
                observed - expected
            ) / self.scales[feature]

            residuals.append(standardized)

        residual_matrix = np.column_stack(residuals)

        return np.sqrt(
            np.mean(residual_matrix ** 2, axis=1)
        )

    def calibrate(self, healthy_calibration_data, quantile=0.95):
        if not 0 < quantile < 1:
            raise ValueError("Quantile must be between 0 and 1.")

        scores = self.anomaly_score(
            healthy_calibration_data
        )

        self.threshold = float(np.quantile(scores, quantile))
        return self

    def predict(self, data):
        if self.threshold is None:
            raise RuntimeError(
                "Calibrate the detector before prediction."
            )

        scores = self.anomaly_score(data)

        return (scores > self.threshold).astype(int)
