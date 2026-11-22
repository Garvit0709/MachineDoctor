
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Motor(Base):
    __tablename__ = "motors"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    motor_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    motor_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    rated_rpm: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rated_power_kw: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    operational_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="REGISTERED",
        server_default="REGISTERED",
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    bearings: Mapped[list["Bearing"]] = relationship(
        back_populates="motor",
        cascade="all, delete-orphan",
    )


class Bearing(Base):
    __tablename__ = "bearings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    motor_id: Mapped[int] = mapped_column(
        ForeignKey("motors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    bearing_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    bearing_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    position: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    manufacturer: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    model_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    motor: Mapped["Motor"] = relationship(
        back_populates="bearings",
    )

    __table_args__ = (
        UniqueConstraint(
            "motor_id",
            "bearing_code",
            name="uq_motor_bearing_code",
        ),
    )
