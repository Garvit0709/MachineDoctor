
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.auth_service import decode_access_token
from backend.database import get_db
from backend.models import Administrator


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
    db: Session = Depends(get_db),
) -> Administrator:
    """
    Validate a JWT and return the active administrator.
    """

    error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise error

    try:
        administrator_id = decode_access_token(
            credentials.credentials
        )
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise error from None

    administrator = db.get(
        Administrator,
        administrator_id,
    )

    if administrator is None or not administrator.is_active:
        raise error

    return administrator
