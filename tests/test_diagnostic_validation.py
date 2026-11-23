
import copy

import pytest

from backend.diagnostic_validation import (
    DiagnosticValidationError,
    validate_diagnostic_result,
)


def sample_result():
    return {
        "total_windows": 2,
        "state_counts": {
            "NORMAL": 1,
            "WARNING": 1,
            "UNKNOWN": 0,
        },
        "predictions": [
            {
                "time_start": 0.0,
                "time_end": 1.0,
                "state": "NORMAL",
            },
            {
                "time_start": 1.0,
                "time_end": 2.0,
                "state": "WARNING",
            },
        ],
    }


def test_valid_result():
    validate_diagnostic_result(sample_result())


def test_mismatched_window_count():
    result = sample_result()
    result["total_windows"] = 3

    with pytest.raises(DiagnosticValidationError):
        validate_diagnostic_result(result)


def test_invalid_state():
    result = sample_result()
    result["predictions"][0]["state"] = "CRITICAL"

    with pytest.raises(DiagnosticValidationError):
        validate_diagnostic_result(result)


def test_invalid_duration():
    result = sample_result()
    result["predictions"][0]["time_end"] = 0.0

    with pytest.raises(DiagnosticValidationError):
        validate_diagnostic_result(result)


def test_inconsistent_state_counts():
    result = sample_result()
    result["state_counts"]["WARNING"] = 0

    with pytest.raises(DiagnosticValidationError):
        validate_diagnostic_result(result)


def test_nonfinite_time():
    result = sample_result()
    result["predictions"][0]["time_start"] = float("nan")

    with pytest.raises(DiagnosticValidationError):
        validate_diagnostic_result(result)


def test_out_of_order_windows():
    result = copy.deepcopy(sample_result())
    result["predictions"][1]["time_start"] = -1.0

    with pytest.raises(DiagnosticValidationError):
        validate_diagnostic_result(result)
def test_overlapping_windows_are_allowed():
    result = sample_result()

    result["predictions"][1]["time_start"] = 0.5

    validate_diagnostic_result(result)