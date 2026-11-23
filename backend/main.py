from fastapi import File, HTTPException, UploadFile
from backend.diagnostic_router import router as diagnostic_router
import io
import pandas as pd
from backend.auth_router import router as auth_router
from backend.motor_router import router as motor_router
from backend.aura_contract import AURAInputError
from backend.aura_inference import diagnose_feature_sequence
from backend.aura_model_store import AURAModelError
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from backend.auth_router import limiter
from backend.signal_processing import (
    MAX_FILE_BYTES,
    SignalValidationError,
    analyze_vibration_csv,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi import Depends
from backend.auth_dependencies import get_current_admin

app = FastAPI(
    title="MachineDoctor API",
    description=(
        "Motor-bearing diagnostic platform "
        "powered by the experimental AURA algorithm."
    ),
    version="0.1.0",
)
app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)
app.include_router(motor_router)
app.include_router(diagnostic_router)
app.include_router(auth_router)

# Local development frontend origins only.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)


class HealthResponse(BaseModel):
    status: str
    application: str
    algorithm: str
    version: str


@app.get("/")
def root():
    return {
        "application": "MachineDoctor",
        "message": "MachineDoctor API is running.",
        "algorithm": "AURA",
    }


@app.get("/api/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="operational",
        application="MachineDoctor",
        algorithm="AURA",
        version="0.1.0",
    )


@app.get("/api/capabilities")
def capabilities():
    return {
        "application": "MachineDoctor",
        "features": {
            "signal_explorer": "frontend_prototype",
            "aura_diagnostics": "not_integrated",
            "motor_registry": "demonstration_only",
            "database": "not_connected",
        },
    }

@app.post("/api/signals/analyze")
async def analyze_signal(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=415,
            detail="Only CSV files are supported.",
        )

    try:
        content = await file.read(MAX_FILE_BYTES + 1)

        if len(content) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Uploaded file exceeds 12 MB.",
            )

        return analyze_vibration_csv(content)

    except SignalValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    finally:
        await file.close()

MAX_FEATURE_FILE_BYTES = 2 * 1024 * 1024


@app.post(
    "/api/aura/diagnose",
    dependencies=[Depends(get_current_admin)],
)
async def diagnose_aura(
    file: UploadFile = File(...),
):
    """
    Diagnose one precomputed feature-window CSV.

    Experimental endpoint for local research use.
    """

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=415,
            detail="Only CSV files are supported.",
        )

    try:
        content = await file.read(
            MAX_FEATURE_FILE_BYTES + 1
        )

        if len(content) > MAX_FEATURE_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="Feature CSV exceeds 2 MB.",
            )

        try:
            features = pd.read_csv(
                io.BytesIO(content),
                encoding="utf-8-sig",
            )
        except (pd.errors.ParserError, UnicodeError) as exc:
            raise HTTPException(
                status_code=422,
                detail="Unable to parse feature CSV.",
            ) from exc

        return diagnose_feature_sequence(features)

    except AURAInputError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except AURAModelError as exc:
        raise HTTPException(
            status_code=503,
            detail="AURA model unavailable or invalid.",
        ) from exc

    finally:
        await file.close()
