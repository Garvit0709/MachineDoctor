
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database import Base
from backend.models import Motor
from backend.diagnostic_history import (
    DiagnosticHistoryError,
    get_diagnostic_session,
    save_diagnostic_result,
)


@pytest.fixture
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


def sample_result():
    return {
        "data_scope": "compatible_synthetic_features_only",
        "run_id": "test_run_001",
        "model_name": "aura_v01_synthetic",
        "model_version": "aura-v0.1",
        "total_windows": 3,
        "state_counts": {
            "NORMAL": 1,
            "WARNING": 1,
            "UNKNOWN": 1,
        },
        "predictions": [
            {
                "time_start": 0.0,
                "time_end": 0.5,
                "state": "UNKNOWN",
                "reason": "Insufficient history",
                "persistent_score": None,
                "instantaneous_score": None,
                "uncertainty_distance": 0.2,
                "memory_size": 1,
            },
            {
                "time_start": 0.5,
                "time_end": 1.0,
                "state": "NORMAL",
                "reason": "Within baseline",
                "persistent_score": 0.4,
                "instantaneous_score": 0.3,
                "uncertainty_distance": 0.2,
                "memory_size": 2,
            },
            {
                "time_start": 1.0,
                "time_end": 1.5,
                "state": "WARNING",
                "reason": "Persistent deviation",
                "persistent_score": 1.8,
                "instantaneous_score": 1.7,
                "uncertainty_distance": 0.3,
                "memory_size": 3,
            },
        ],
    }


def create_motor(db):
    motor = Motor(
        motor_code="MTR-HISTORY-001",
        name="History Test Motor",
    )

    db.add(motor)
    db.commit()
    db.refresh(motor)

    return motor


def test_save_diagnostic_session(db):
    motor = create_motor(db)

    saved = save_diagnostic_result(
        db,
        motor_id=motor.id,
        bearing_id=None,
        recording_name="test.csv",
        result=sample_result(),
    )

    assert saved.id is not None
    assert saved.total_windows == 3

    loaded = get_diagnostic_session(db, saved.id)

    assert loaded is not None
    assert len(loaded.windows) == 3
    assert loaded.windows[2].state == "WARNING"


def test_reject_unknown_motor(db):
    with pytest.raises(
        DiagnosticHistoryError,
        match="Motor not found",
    ):
        save_diagnostic_result(
            db,
            motor_id=999,
            bearing_id=None,
            recording_name="test.csv",
            result=sample_result(),
        )


def test_reject_inconsistent_counts(db):
    motor = create_motor(db)
    result = sample_result()
    result["state_counts"]["WARNING"] = 0

    with pytest.raises(
        DiagnosticHistoryError,
        match="inconsistent",
    ):
        save_diagnostic_result(
            db,
            motor_id=motor.id,
            bearing_id=None,
            recording_name="test.csv",
            result=result,
        )
