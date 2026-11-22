
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from backend.database import Base
from backend.models import (
    Motor,
    Bearing,
    DiagnosticSession,
    DiagnosticWindow,
)


def test_diagnostic_session_relationship():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            motor = Motor(
                motor_code="MTR-DIAG-001",
                name="Diagnostic Test Motor",
                rated_rpm=1500,
            )

            bearing = Bearing(
                bearing_code="BRG-DE-001",
                position="DRIVE_END",
            )

            motor.bearings.append(bearing)
            db.add(motor)
            db.flush()

            session = DiagnosticSession(
                motor_id=motor.id,
                bearing_id=bearing.id,
                run_id="run_001",
                recording_name="test_features.csv",
                data_source="synthetic",
                model_name="aura_v01_synthetic",
                model_version="aura-v0.1",
                total_windows=3,
                normal_count=1,
                warning_count=1,
                unknown_count=1,
            )

            session.windows = [
                DiagnosticWindow(
                    window_index=0,
                    time_start=0.0,
                    time_end=0.5,
                    state="UNKNOWN",
                    reason="Insufficient history",
                ),
                DiagnosticWindow(
                    window_index=1,
                    time_start=0.5,
                    time_end=1.0,
                    state="NORMAL",
                    persistent_score=0.4,
                ),
                DiagnosticWindow(
                    window_index=2,
                    time_start=1.0,
                    time_end=1.5,
                    state="WARNING",
                    persistent_score=1.8,
                ),
            ]

            db.add(session)
            db.commit()

            saved = db.scalar(
                select(DiagnosticSession)
                .where(DiagnosticSession.run_id == "run_001")
            )

            assert saved is not None
            assert saved.total_windows == 3
            assert len(saved.windows) == 3
            assert saved.windows[2].state == "WARNING"

    finally:
        engine.dispose()


def test_diagnostic_windows_deleted_with_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as db:
            motor = Motor(
                motor_code="MTR-DIAG-002",
                name="Test Motor",
            )

            db.add(motor)
            db.flush()

            session = DiagnosticSession(
                motor_id=motor.id,
                run_id="run_002",
                recording_name="test.csv",
                data_source="synthetic",
                model_name="aura_v01_synthetic",
                model_version="aura-v0.1",
                total_windows=1,
                normal_count=1,
                warning_count=0,
                unknown_count=0,
            )

            session.windows.append(
                DiagnosticWindow(
                    window_index=0,
                    time_start=0.0,
                    time_end=0.5,
                    state="NORMAL",
                )
            )

            db.add(session)
            db.commit()

            db.delete(session)
            db.commit()

            remaining = db.scalars(
                select(DiagnosticWindow)
            ).all()

            assert len(remaining) == 0

    finally:
        engine.dispose()
