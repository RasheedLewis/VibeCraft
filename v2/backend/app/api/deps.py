"""FastAPI dependencies for authentication and database access."""

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

from app.core.database import get_session
from app.models.user import User
from app.services.auth_service import get_user_by_id, verify_token

# HTTP Bearer token security scheme
security = HTTPBearer()


def get_db_session() -> Generator[Session, None, None]:
    """Dependency to get database session.

    Yields:
        Database session
    """
    yield from get_session()


# Type alias for database session dependency
SessionDep = Annotated[Session, Depends(get_db_session)]


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Session = Depends(get_db_session),
) -> User:
    """Dependency to get current authenticated user.

    Args:
        credentials: HTTP Bearer token credentials
        session: Database session

    Returns:
        Current authenticated User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    user_id = verify_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user_by_id(session, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

