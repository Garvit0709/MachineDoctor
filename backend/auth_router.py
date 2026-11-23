
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth_dependencies import get_current_admin
from backend.auth_service import (
    create_access_token,
    verify_password,
)
from backend.database import get_db
from backend.models import Administrator


router = APIRouter(
    prefix="/api/auth",
    tags=["Administrator Authentication"],
)


class LoginRequest(BaseModel):
    username: str = Field(
        min_length=1,
        max_length=100,
    )
    password: str = Field(
        min_length=1,
        max_length=1024,
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AdministratorResponse(BaseModel):
    id: int
    username: str
    is_active: bool


@router.post(
    "/login",
    response_model=TokenResponse,
)
def administrator_login(
    payload: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    username = payload.username.strip()

    administrator = db.scalar(
        select(Administrator).where(
            Administrator.username == username
        )
    )

    if (
        administrator is None
        or not administrator.is_active
        or not verify_password(
            payload.password,
            administrator.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        administrator.id
    )

    return TokenResponse(
        access_token=token,
    )


@router.get(
    "/me",
    response_model=AdministratorResponse,
)
def get_administrator_profile(
    administrator: Annotated[
        Administrator,
        Depends(get_current_admin),
    ],
):
    return AdministratorResponse(
        id=administrator.id,
        username=administrator.username,
        is_active=administrator.is_active,
    )
