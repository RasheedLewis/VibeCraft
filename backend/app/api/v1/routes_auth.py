"""Authentication endpoints."""

import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.user import User

router = APIRouter()


class RegisterRequest(BaseModel):
    """Registration request model."""

    email: EmailStr
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request model."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Authentication response model."""

    access_token: str
    user_id: str
    email: str
    display_name: Optional[str] = None


class UserInfoResponse(BaseModel):
    """User info response model (no token)."""

    user_id: str
    email: str
    display_name: Optional[str] = None


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Register a new user.
    
    Returns access token and user info.
    """
    # Check if user already exists
    statement = select(User).where(User.email == request.email)
    existing_user = db.exec(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user_id = f"user_{secrets.token_urlsafe(16)}"
    
    user = User(
        id=user_id,
        email=request.email,
        display_name=request.display_name or request.email.split("@")[0],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = create_access_token(user_id)
    
    return AuthResponse(
        access_token=access_token,
        user_id=user_id,
        email=user.email,
        display_name=user.display_name,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
) -> AuthResponse:
    """
    Login with email and password.
    
    Returns access token and user info.
    Note: For MVP, password validation is simplified.
    """
    # Find user by email
    statement = select(User).where(User.email == request.email)
    user = db.exec(statement).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # For MVP: Accept any password (password storage can be added later)
    access_token = create_access_token(user.id)
    
    return AuthResponse(
        access_token=access_token,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
    )


@router.get("/me", response_model=UserInfoResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserInfoResponse:
    """Get current user information."""
    return UserInfoResponse(
        user_id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
    )

