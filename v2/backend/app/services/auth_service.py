"""Authentication service for user registration, login, and JWT token management."""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from sqlmodel import Session, select

from app.core.config import get_settings
from app.models.user import User

settings = get_settings()

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


def create_access_token(user_id: str) -> str:
    """Create a JWT access token for a user.

    Args:
        user_id: User ID to encode in the token

    Returns:
        Encoded JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": user_id, "exp": expire}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """Verify a JWT token and extract user ID.

    Args:
        token: JWT token string to verify

    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def register_user(session: Session, email: str, password: str) -> User:
    """Register a new user.

    Args:
        session: Database session
        email: User email address
        password: Plain text password

    Returns:
        Created User object

    Raises:
        ValueError: If email already exists
    """
    # Check if user already exists
    statement = select(User).where(User.email == email)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise ValueError("Email already registered")

    # Create new user
    password_hash = User.hash_password(password)
    user = User(
        email=email,
        password_hash=password_hash,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user with email and password.

    Args:
        session: Database session
        email: User email address
        password: Plain text password

    Returns:
        User object if authentication succeeds, None otherwise
    """
    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    if not user:
        return None
    if not user.verify_password(password):
        return None
    return user


def get_user_by_id(session: Session, user_id: str) -> Optional[User]:
    """Get a user by ID.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        User object if found, None otherwise
    """
    return session.get(User, user_id)

