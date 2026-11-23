
import math


VALID_STATES = {
    "NORMAL",
    "WARNING",
    "UNKNOWN",
}


class DiagnosticValidationError(ValueError):
    """Raised when diagnostic results contain invalid data."""
    pass


def validate_diagnostic_result(result: dict) -> None:
    """
    Validate AURA diagnostic results before database storage.

    Overlapping windows are allowed.
    Window start times must remain chronologically ordered.
    """

    if not isinstance(result, dict):
        raise DiagnosticValidationError(
            "Diagnostic result must be a dictionary."
        )

    predictions = result.get("predictions")
    total_windows = result.get("total_windows")
    state_counts = result.get("state_counts")

    if not isinstance(predictions, list) or not predictions:
        raise DiagnosticValidationError(
            "Diagnostic predictions cannot be empty."
        )

    if (
        type(total_windows) is not int
        or total_windows != len(predictions)
    ):
        raise DiagnosticValidationError(
            "Diagnostic window count mismatch."
        )

    if not isinstance(state_counts, dict):
        raise DiagnosticValidationError(
            "Diagnostic state counts are missing."
        )

    actual_counts = {
        state: 0
        for state in VALID_STATES
    }

    previous_start = None

    for index, prediction in enumerate(predictions):
        if not isinstance(prediction, dict):
            raise DiagnosticValidationError(
                f"Invalid prediction at window {index}."
            )

        state = prediction.get("state")

        if state not in VALID_STATES:
            raise DiagnosticValidationError(
                f"Invalid diagnostic state at window {index}."
            )

        actual_counts[state] += 1

        try:
            start = float(prediction["time_start"])
            end = float(prediction["time_end"])
        except (KeyError, TypeError, ValueError, OverflowError):
            raise DiagnosticValidationError(
                f"Invalid time values at window {index}."
            ) from None

        if not math.isfinite(start) or not math.isfinite(end):
            raise DiagnosticValidationError(
                f"Non-finite time values at window {index}."
            )

        if end <= start:
            raise DiagnosticValidationError(
                f"Invalid window duration at index {index}."
            )

        # AURA can generate overlapping feature windows.
        # Only reject windows that move backward in start time.
        if (
            previous_start is not None
            and start < previous_start - 1e-9
        ):
            raise DiagnosticValidationError(
                "Diagnostic windows are out of chronological order."
            )

        previous_start = start

    for state, actual in actual_counts.items():
        supplied = state_counts.get(state)

        if (
            type(supplied) is not int
            or supplied != actual
        ):
            raise DiagnosticValidationError(
                f"inconsistent {state} count."
            )
