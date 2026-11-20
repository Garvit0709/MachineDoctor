
import numpy as np
from sklearn.preprocessing import StandardScaler


class OperatingConditionUncertainty:
    """
    Measures unfamiliarity of operating conditions
    using regularized Mahalanobis distance.

    This is a baseline uncertainty proxy,
    not a calibrated failure probability.
    """

    def __init__(self, regularization=0.01):
        if regularization <= 0:
            raise ValueError(
                "Regularization must be positive."
            )

        self.regularization = regularization
        self.scaler = StandardScaler()
        self.mean_ = None
        self.inverse_covariance_ = None
        self.threshold_ = None

    def fit(self, conditions):
        x = np.asarray(conditions, dtype=float)

        if x.ndim != 2 or x.shape[0] < 3:
            raise ValueError(
                "Expected at least three 2D observations."
            )

        if not np.all(np.isfinite(x)):
            raise ValueError(
                "Operating conditions must be finite."
            )

        z = self.scaler.fit_transform(x)

        self.mean_ = np.mean(z, axis=0)

        covariance = np.atleast_2d(
            np.cov(z, rowvar=False)
        )

        covariance += (
            self.regularization
            * np.eye(covariance.shape[0])
        )

        self.inverse_covariance_ = np.linalg.inv(
            covariance
        )

        return self

    def distance(self, conditions):
        if self.mean_ is None:
            raise RuntimeError(
                "Fit the model before prediction."
            )

        x = np.asarray(conditions, dtype=float)

        if x.ndim != 2:
            raise ValueError(
                "Expected a 2D input array."
            )

        if x.shape[1] != len(self.mean_):
            raise ValueError(
                "Unexpected number of features."
            )

        if not np.all(np.isfinite(x)):
            raise ValueError(
                "Input contains invalid values."
            )

        z = self.scaler.transform(x)
        delta = z - self.mean_

        squared_distance = np.einsum(
            "ij,jk,ik->i",
            delta,
            self.inverse_covariance_,
            delta,
        )

        return np.sqrt(
            np.maximum(squared_distance, 0.0)
        )

    def calibrate(self, healthy_conditions, quantile=0.95):
        if not 0 < quantile < 1:
            raise ValueError(
                "Quantile must be between 0 and 1."
            )

        distances = self.distance(healthy_conditions)

        self.threshold_ = float(
            np.quantile(distances, quantile)
        )

        return self

    def is_unfamiliar(self, conditions):
        if self.threshold_ is None:
            raise RuntimeError(
                "Calibrate the threshold first."
            )

        return (
            self.distance(conditions) > self.threshold_
        )
