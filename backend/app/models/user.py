"""
User model - Placeholder for future authentication.

Currently, the MVP uses DEFAULT_USER_ID ("default-user") for all songs.
This model exists to satisfy foreign key constraints but is not actively used.
Authentication and user management will be added in a future version.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    User model - Placeholder for future authentication.
    
    Note: Currently unused in MVP. All songs use DEFAULT_USER_ID.
    """
    __tablename__ = "users"

    id: str = Field(primary_key=True, max_length=128)
    email: Optional[str] = Field(default=None, unique=True, index=True, max_length=256)
    display_name: Optional[str] = Field(default=None, max_length=128)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


