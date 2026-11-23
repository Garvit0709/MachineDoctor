
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt

from dotenv import load_dotenv
from pwdlib import PasswordHash


PROJECT_ROOT = Path(__file__).resolve().parents[1]

load_dotenv(PROJECT_ROOT / ".env")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

JWT_ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)

password_hash = PasswordHash.recommended()


def validate_jwt_configuration() -> None:
    """
    Validate JWT security configuration.
    """

    if not JWT_SECRET_KEY:
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured."
        )

    if len(JWT_SECRET_KEY.encode("utf-8")) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must contain at least 32 bytes."
        )

    if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
        raise RuntimeError(
            "ACCESS_TOKEN_EXPIRE_MINUTES must be positive."
        )


def hash_password(password: str) -> str:
    """
    Hash an administrator password using Argon2.
    """

    if not password:
        raise ValueError(
            "Password cannot be empty."
        )

    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify an administrator password.
    """

    return password_hash.verify(
        plain_password,
        hashed_password,
    )


def create_access_token(
    administrator_id: int,
) -> str:
    """
    Generate a signed JWT access token.
    """

    validate_jwt_configuration()

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(administrator_id),
        "iat": now,
        "exp": now + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> int:
    """
    Decode and validate an administrator JWT.
    """

    validate_jwt_configuration()

    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={
            "require": ["sub", "iat", "exp"]
        },
    )

    administrator_id = int(payload["sub"])

    if administrator_id <= 0:
        raise ValueError(
            "Invalid administrator identifier."
        )

    return administrator_id
