
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.database import Base
from backend.models import Motor, Bearing


def test_motor_bearing_relationship():
    # Isolated in-memory database for model tests.
    engine = create_engine("sqlite+pysqlite:///:memory:")

    Base.metadata.create_all(engine)

    with Session(engine) as session:
        motor = Motor(
            motor_code="MTR-TEST-001",
            name="Test Induction Motor",
            location="Laboratory",
            rated_rpm=1500,
        )

        bearing = Bearing(
            bearing_code="BRG-DE-001",
            position="DRIVE_END",
            bearing_type="Ball Bearing",
        )

        motor.bearings.append(bearing)

        session.add(motor)
        session.commit()

        saved_motor = session.query(Motor).first()

        assert saved_motor is not None
        assert saved_motor.motor_code == "MTR-TEST-001"
        assert len(saved_motor.bearings) == 1
        assert saved_motor.bearings[0].position == "DRIVE_END"

    engine.dispose()
