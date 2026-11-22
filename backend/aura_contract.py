
import numpy as np
import pandas as pd


REQUIRED_COLUMNS = [
    "run_id",
    "time_start",
    "time_end",
    "rms",
    "crest_factor",
    "kurtosis",
    "rpm",
    "rpm_acceleration",
]


class AURAInputError(ValueError):
    """Raised when diagnostic feature data is invalid."""


def validate_aura_features(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """
    Validate a single ordered AURA feature sequence.

    This function does not perform inference.
    """

    if not isinstance(data, pd.DataFrame):
        raise AURAInputError(
            "AURA input must be a pandas DataFrame."
        )

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in data.columns
    ]

    if missing:
        raise AURAInputError(
            f"Missing required columns: {missing}"
        )

    if len(data) < 3:
        raise AURAInputError(
            "At least three feature windows are required."
        )

    validated = data.copy()

    if validated["run_id"].isna().any():
        raise AURAInputError(
            "run_id contains missing values."
        )

    validated["run_id"] = validated["run_id"].astype(str)

    if (
        validated["run_id"].str.strip() == ""
    ).any():
        raise AURAInputError(
            "run_id cannot be empty."
        )

    if validated["run_id"].nunique() != 1:
        raise AURAInputError(
            "One diagnostic request must contain one run_id."
        )

    numeric_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column != "run_id"
    ]

    try:
        for column in numeric_columns:
            validated[column] = pd.to_numeric(
                validated[column],
                errors="raise",
            )
    except (ValueError, TypeError) as exc:
        raise AURAInputError(
            "Diagnostic features must be numeric."
        ) from exc

    values = validated[
        numeric_columns
    ].to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise AURAInputError(
            "Diagnostic features contain non-finite values."
        )

    starts = validated[
        "time_start"
    ].to_numpy(dtype=float)

    ends = validated[
        "time_end"
    ].to_numpy(dtype=float)

    if np.any(ends <= starts):
        raise AURAInputError(
            "Each window must have positive duration."
        )

    if np.any(np.diff(starts) <= 0):
        raise AURAInputError(
            "Windows must be ordered by increasing start time."
        )

    if np.any(np.diff(ends) <= 0):
        raise AURAInputError(
            "Window end times must increase."
        )

    if np.any(validated["rpm"] < 0):
        raise AURAInputError(
            "RPM cannot be negative."
        )

    if np.any(validated["rms"] < 0):
        raise AURAInputError(
            "RMS cannot be negative."
        )

    if np.any(validated["crest_factor"] < 0):
        raise AURAInputError(
            "Crest factor cannot be negative."
        )

    if np.any(validated["kurtosis"] < 0):
        raise AURAInputError(
            "Kurtosis cannot be negative."
        )

    return validated.reset_index(drop=True)
