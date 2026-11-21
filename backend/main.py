from fastapi import File, HTTPException, UploadFile

from backend.signal_processing import (
    MAX_FILE_BYTES,
    SignalValidationError,
    analyze_vibration_csv,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(
    title="MachineDoctor API",
    description=(
        "Motor-bearing diagnostic platform "
        "powered by the experimental AURA algorithm."
    ),
    version="0.1.0",
)

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
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
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
