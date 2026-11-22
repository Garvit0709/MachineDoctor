
import math

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.models import (
    Motor,
    Bearing,
    DiagnosticSession,
    DiagnosticWindow,
)


class DiagnosticHistoryError(ValueError):
    pass


def validate_equipment(
    db: Session,
    motor_id: int,
    bearing_id: int | None,
):
    motor = db.get(Motor, motor_id)

    if motor is None:
        raise DiagnosticHistoryError(
            "Motor not found."
        )

    if bearing_id is not None:
        bearing = db.get(Bearing, bearing_id)

        if bearing is None:
            raise DiagnosticHistoryError(
                "Bearing not found."
            )

        if bearing.motor_id != motor_id:
            raise DiagnosticHistoryError(
                "Bearing does not belong to the selected motor."
            )

    return motor


def safe_number(value):
    """
    Convert finite numeric scores to float.
    Preserve unavailable measurements as None.
    """
    if value is None:
        return None

    number = float(value)

    if not math.isfinite(number):
        return None

    return number


def save_diagnostic_result(
    db: Session,
    *,
    motor_id: int,
    bearing_id: int | None,
    recording_name: str,
    result: dict,
):
    """
    Persist one complete AURA diagnostic session.

    The caller supplies a trusted result generated
    by the AURA inference service.
    """

    validate_equipment(
        db,
        motor_id,
        bearing_id,
    )

    if result.get("data_scope") != (
        "compatible_synthetic_features_only"
    ):
        raise DiagnosticHistoryError(
            "Unsupported diagnostic data scope."
        )

    predictions = result["predictions"]
    counts = result["state_counts"]

    if not predictions:
        raise DiagnosticHistoryError(
            "Cannot save an empty diagnostic sequence."
        )

    if len(predictions) != result["total_windows"]:
        raise DiagnosticHistoryError(
            "Prediction count mismatch."
        )

    actual_counts = {
        state: sum(
            prediction["state"] == state
            for prediction in predictions
        )
        for state in ("NORMAL", "WARNING", "UNKNOWN")
    }

    if actual_counts != {
        state: int(counts.get(state, 0))
        for state in actual_counts
    }:
        raise DiagnosticHistoryError(
            "Diagnostic state counts are inconsistent."
        )

    session = DiagnosticSession(
        motor_id=motor_id,
        bearing_id=bearing_id,
        run_id=result["run_id"],
        recording_name=recording_name,
        data_source="synthetic",
        model_name=result["model_name"],
        model_version=result["model_version"],
        total_windows=len(predictions),
        normal_count=actual_counts["NORMAL"],
        warning_count=actual_counts["WARNING"],
        unknown_count=actual_counts["UNKNOWN"],
    )

    for index, prediction in enumerate(predictions):
        window = DiagnosticWindow(
            window_index=index,
            time_start=float(prediction["time_start"]),
            time_end=float(prediction["time_end"]),
            state=prediction["state"],
            reason=prediction.get("reason"),
            persistent_score=safe_number(
                prediction.get("persistent_score")
            ),
            instantaneous_score=safe_number(
                prediction.get("instantaneous_score")
            ),
            uncertainty_distance=safe_number(
                prediction.get("uncertainty_distance")
            ),
            memory_size=(
                int(prediction["memory_size"])
                if prediction.get("memory_size") is not None
                else None
            ),
        )

        session.windows.append(window)

    try:
        db.add(session)
        db.commit()
        db.refresh(session)
    except Exception:
        db.rollback()
        raise

    return session


def list_diagnostic_sessions(
    db: Session,
    motor_id: int | None = None,
):
    statement = select(DiagnosticSession)

    if motor_id is not None:
        statement = statement.where(
            DiagnosticSession.motor_id == motor_id
        )

    statement = statement.order_by(
        DiagnosticSession.created_at.desc(),
        DiagnosticSession.id.desc(),
    )

    return db.scalars(statement).all()


def get_diagnostic_session(
    db: Session,
    session_id: int,
):
    statement = (
        select(DiagnosticSession)
        .options(selectinload(DiagnosticSession.windows))
        .where(DiagnosticSession.id == session_id)
    )

    return db.scalar(statement)
