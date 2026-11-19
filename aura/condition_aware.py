
import numpy as np

from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline


class RPMConditionedDetector:
    """
    Experimental RPM-conditioned residual detector.

    Learns healthy feature expectations as a function
    of RPM and detects unusual residual patterns.
    """

    def __init__(self, feature_columns, threshold_quantile=0.95):
        self.feature_columns = feature_columns
        self.threshold_quantile = threshold_quantile

        self.models = {}
        self.scales = {}
        self.threshold = None

    def fit(self, data):
        rpm = data[["rpm"]].to_numpy()

        residual_matrix = []

        for feature in self.feature_columns:
            values = data[feature].to_numpy()

            model = make_pipeline(
                PolynomialFeatures(degree=2, include_bias=False),
                StandardScaler(),
                Ridge(alpha=1.0),
            )

            model.fit(rpm, values)

            expected = model.predict(rpm)
            residual = values - expected

            scale = max(np.std(residual), 1e-8)

            self.models[feature] = model
            self.scales[feature] = scale

            residual_matrix.append(residual / scale)

        residual_matrix = np.column_stack(residual_matrix)

        scores = np.sqrt(
            np.mean(residual_matrix ** 2, axis=1)
        )

        self.threshold = float(
            np.quantile(scores, self.threshold_quantile)
        )

        return self

    def anomaly_score(self, data):
        if self.threshold is None:
            raise RuntimeError("Model must be fitted first.")

        rpm = data[["rpm"]].to_numpy()

        standardized_residuals = []

        for feature in self.feature_columns:
            observed = data[feature].to_numpy()
            expected = self.models[feature].predict(rpm)

            residual = (
                observed - expected
            ) / self.scales[feature]

            standardized_residuals.append(residual)

        residual_matrix = np.column_stack(
            standardized_residuals
        )

        scores = np.sqrt(
            np.mean(residual_matrix ** 2, axis=1)
        )

        return scores

    def predict(self, data):
        scores = self.anomaly_score(data)
        return (scores > self.threshold).astype(int)
