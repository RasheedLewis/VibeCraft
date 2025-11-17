"""User model for authentication and user management."""

import bcrypt
from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel

# Bcrypt rounds for password hashing (higher = more secure but slower)
BCRYPT_ROUNDS = 12


class User(SQLModel, table=True):
    """User model for authentication and user management."""

    __tablename__ = "users"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        max_length=128,
    )
    email: str = Field(unique=True, index=True, max_length=256)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    video_count: int = Field(default=0)
    storage_bytes: int = Field(default=0)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plain text password to hash

        Returns:
            Hashed password string
        """
        # Bcrypt has a 72-byte limit, so we need to encode and truncate if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        # Generate salt and hash
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    def verify_password(self, password: str) -> bool:
        """Verify a password against the stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        # Bcrypt has a 72-byte limit, so we need to encode and truncate if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        # Verify password
        return bcrypt.checkpw(password_bytes, self.password_hash.encode('utf-8'))

