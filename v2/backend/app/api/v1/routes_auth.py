"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import SessionDep, get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    UserRead,
)
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    register_user,
)

router = APIRouter()
settings = get_settings()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    session: SessionDep,
) -> AuthResponse:
    """Register a new user.

    Args:
        request: Registration request with email and password
        session: Database session

    Returns:
        AuthResponse with access token and user info

    Raises:
        HTTPException: If email already exists or validation fails
    """
    try:
        user = register_user(session, request.email, request.password)
        access_token = create_access_token(user.id)
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserRead(
                id=user.id,
                email=user.email,
                created_at=user.created_at.isoformat(),
                video_count=user.video_count,
                storage_bytes=user.storage_bytes,
            ),
        )
    except ValueError as e:
        if "already registered" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    session: SessionDep,
) -> AuthResponse:
    """Login with email and password.

    Args:
        request: Login request with email and password
        session: Database session

    Returns:
        AuthResponse with access token and user info

    Raises:
        HTTPException: If credentials are invalid
    """
    user = authenticate_user(session, request.email, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.id)
    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserRead(
            id=user.id,
            email=user.email,
            created_at=user.created_at.isoformat(),
            video_count=user.video_count,
            storage_bytes=user.storage_bytes,
        ),
    )


@router.get("/me", response_model=UserRead)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserRead:
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user (from dependency)

    Returns:
        UserRead with user information
    """
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
        video_count=current_user.video_count,
        storage_bytes=current_user.storage_bytes,
    )

