
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MotorCreate(BaseModel):
    motor_code: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=150)
    location: str | None = Field(default=None, max_length=200)
    motor_type: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=150)
    rated_rpm: float | None = Field(default=None, gt=0)
    rated_power_kw: float | None = Field(default=None, gt=0)
    notes: str | None = None


class MotorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    location: str | None = Field(default=None, max_length=200)
    motor_type: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=150)
    rated_rpm: float | None = Field(default=None, gt=0)
    rated_power_kw: float | None = Field(default=None, gt=0)
    operational_status: str | None = Field(default=None, max_length=30)
    notes: str | None = None


class BearingCreate(BaseModel):
    bearing_code: str = Field(min_length=1, max_length=50)
    position: str = Field(min_length=1, max_length=50)
    bearing_type: str | None = Field(default=None, max_length=100)
    manufacturer: str | None = Field(default=None, max_length=150)
    model_number: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class BearingRead(BearingCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    motor_id: int
    created_at: datetime


class MotorRead(MotorCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    operational_status: str
    created_at: datetime
    bearings: list[BearingRead] = Field(default_factory=list)
