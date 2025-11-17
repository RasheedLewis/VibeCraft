"""Authentication schemas for request/response validation."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password meets requirements.

        Args:
            v: Password string to validate

        Returns:
            Validated password string

        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters long")
        return v


class LoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Public user information schema."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    created_at: str
    video_count: int
    storage_bytes: int


class AuthResponse(BaseModel):
    """Response schema for authentication endpoints."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead

