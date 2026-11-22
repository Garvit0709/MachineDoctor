
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db
from backend.models import Motor, Bearing
from backend.schemas import (
    MotorCreate,
    MotorUpdate,
    MotorRead,
    BearingCreate,
    BearingRead,
)


router = APIRouter(
    prefix="/api/motors",
    tags=["Motor Registry"],
)


def find_motor(db: Session, motor_id: int):
    statement = (
        select(Motor)
        .options(selectinload(Motor.bearings))
        .where(Motor.id == motor_id)
    )

    motor = db.scalar(statement)

    if motor is None:
        raise HTTPException(
            status_code=404,
            detail="Motor not found.",
        )

    return motor


@router.post(
    "",
    response_model=MotorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_motor(
    payload: MotorCreate,
    db: Session = Depends(get_db),
):
    motor = Motor(**payload.model_dump())

    db.add(motor)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Motor code already exists.",
        ) from exc

    return find_motor(db, motor.id)


@router.get(
    "",
    response_model=list[MotorRead],
)
def list_motors(
    db: Session = Depends(get_db),
):
    statement = (
        select(Motor)
        .options(selectinload(Motor.bearings))
        .order_by(Motor.id)
    )

    return db.scalars(statement).all()


@router.get(
    "/{motor_id}",
    response_model=MotorRead,
)
def get_motor(
    motor_id: int,
    db: Session = Depends(get_db),
):
    return find_motor(db, motor_id)


@router.patch(
    "/{motor_id}",
    response_model=MotorRead,
)
def update_motor(
    motor_id: int,
    payload: MotorUpdate,
    db: Session = Depends(get_db),
):
    motor = find_motor(db, motor_id)

    changes = payload.model_dump(exclude_unset=True)

    for field, value in changes.items():
        setattr(motor, field, value)

    db.commit()

    return find_motor(db, motor_id)


@router.delete(
    "/{motor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_motor(
    motor_id: int,
    db: Session = Depends(get_db),
):
    motor = find_motor(db, motor_id)

    db.delete(motor)
    db.commit()


@router.post(
    "/{motor_id}/bearings",
    response_model=BearingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_bearing(
    motor_id: int,
    payload: BearingCreate,
    db: Session = Depends(get_db),
):
    find_motor(db, motor_id)

    bearing = Bearing(
        motor_id=motor_id,
        **payload.model_dump(),
    )

    db.add(bearing)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Bearing code already exists for this motor.",
        ) from exc

    db.refresh(bearing)

    return bearing


@router.get(
    "/{motor_id}/bearings",
    response_model=list[BearingRead],
)
def list_bearings(
    motor_id: int,
    db: Session = Depends(get_db),
):
    find_motor(db, motor_id)

    statement = (
        select(Bearing)
        .where(Bearing.motor_id == motor_id)
        .order_by(Bearing.id)
    )

    return db.scalars(statement).all()
