
from datetime import datetime, timezone

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    CheckConstraint,
    Index,
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

class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    motor_id: Mapped[int] = mapped_column(
        ForeignKey("motors.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    bearing_id: Mapped[int | None] = mapped_column(
        ForeignKey("bearings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    run_id: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    recording_name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    data_source: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    model_version: Mapped[str] = mapped_column(
        String(50), nullable=False
    )

    total_windows: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    normal_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    warning_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    unknown_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    windows: Mapped[list["DiagnosticWindow"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="DiagnosticWindow.window_index",
    )

    __table_args__ = (
        CheckConstraint(
            "total_windows >= 0",
            name="ck_session_total_windows",
        ),
        CheckConstraint(
            "normal_count >= 0 AND warning_count >= 0 "
            "AND unknown_count >= 0",
            name="ck_session_nonnegative_counts",
        ),
        CheckConstraint(
            "normal_count + warning_count + unknown_count "
            "= total_windows",
            name="ck_session_count_consistency",
        ),
    )


class DiagnosticWindow(Base):
    __tablename__ = "diagnostic_windows"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "diagnostic_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    window_index: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    time_start: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    time_end: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    state: Mapped[str] = mapped_column(
        String(20), nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    persistent_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    instantaneous_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    uncertainty_distance: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )

    memory_size: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )

    session: Mapped["DiagnosticSession"] = relationship(
        back_populates="windows"
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "window_index",
            name="uq_session_window_index",
        ),
        CheckConstraint(
            "time_end > time_start",
            name="ck_window_positive_duration",
        ),
        CheckConstraint(
            "state IN ('NORMAL', 'WARNING', 'UNKNOWN')",
            name="ck_window_valid_state",
        ),
        CheckConstraint(
            "window_index >= 0",
            name="ck_window_nonnegative_index",
        ),
    )
