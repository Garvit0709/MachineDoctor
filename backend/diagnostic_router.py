
import io

import pandas as pd

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.aura_contract import AURAInputError
from backend.aura_inference import diagnose_feature_sequence
from backend.aura_model_store import AURAModelError

from backend.diagnostic_history import (
    DiagnosticHistoryError,
    get_diagnostic_session,
    list_diagnostic_sessions,
    save_diagnostic_result,
)


router = APIRouter(
    prefix="/api/diagnostic-sessions",
    tags=["Diagnostic History"],
)

MAX_FEATURE_BYTES = 2 * 1024 * 1024


@router.post("", status_code=201)
async def create_diagnostic_session(
    motor_id: int = Form(..., gt=0),
    bearing_id: int | None = Form(default=None, gt=0),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=415,
            detail="Only feature CSV files are supported.",
        )

    try:
        content = await file.read(MAX_FEATURE_BYTES + 1)

        if len(content) > MAX_FEATURE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Feature CSV exceeds 2 MB.",
            )

        try:
            features = pd.read_csv(
                io.BytesIO(content),
                encoding="utf-8-sig",
            )
        except (
            pd.errors.ParserError,
            UnicodeError,
            ValueError,
        ) as exc:
            raise HTTPException(
                status_code=422,
                detail="Unable to parse feature CSV.",
            ) from exc

        # Actual AURA inference, not a demonstration result.
        result = diagnose_feature_sequence(features)

        session = save_diagnostic_result(
            db,
            motor_id=motor_id,
            bearing_id=bearing_id,
            recording_name=file.filename,
            result=result,
        )

        return {
            "id": session.id,
            "motor_id": session.motor_id,
            "bearing_id": session.bearing_id,
            "run_id": session.run_id,
            "model_name": session.model_name,
            "model_version": session.model_version,
            "total_windows": session.total_windows,
            "state_counts": result["state_counts"],
            "created_at": session.created_at,
        }

    except AURAInputError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except DiagnosticHistoryError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except AURAModelError as exc:
        raise HTTPException(
            status_code=503,
            detail="AURA model unavailable.",
        ) from exc

    finally:
        await file.close()


@router.get("")
def list_sessions(
    motor_id: int | None = None,
    db: Session = Depends(get_db),
):
    sessions = list_diagnostic_sessions(
        db,
        motor_id=motor_id,
    )

    return [
        {
            "id": session.id,
            "motor_id": session.motor_id,
            "bearing_id": session.bearing_id,
            "run_id": session.run_id,
            "recording_name": session.recording_name,
            "model_name": session.model_name,
            "model_version": session.model_version,
            "total_windows": session.total_windows,
            "normal_count": session.normal_count,
            "warning_count": session.warning_count,
            "unknown_count": session.unknown_count,
            "created_at": session.created_at,
        }
        for session in sessions
    ]


@router.get("/{session_id}")
def retrieve_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    session = get_diagnostic_session(
        db,
        session_id,
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Diagnostic session not found.",
        )

    return {
        "id": session.id,
        "motor_id": session.motor_id,
        "bearing_id": session.bearing_id,
        "run_id": session.run_id,
        "recording_name": session.recording_name,
        "data_source": session.data_source,
        "model_name": session.model_name,
        "model_version": session.model_version,
        "created_at": session.created_at,
        "total_windows": session.total_windows,
        "state_counts": {
            "NORMAL": session.normal_count,
            "WARNING": session.warning_count,
            "UNKNOWN": session.unknown_count,
        },
        "predictions": [
            {
                "window_index": window.window_index,
                "time_start": window.time_start,
                "time_end": window.time_end,
                "state": window.state,
                "reason": window.reason,
                "persistent_score": window.persistent_score,
                "instantaneous_score": window.instantaneous_score,
                "uncertainty_distance": window.uncertainty_distance,
                "memory_size": window.memory_size,
            }
            for window in session.windows
        ],
    }
