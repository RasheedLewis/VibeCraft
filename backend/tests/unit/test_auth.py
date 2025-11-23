"""Unit tests for authentication functions.

Tests JWT token creation/decoding, password hashing, and user authentication.
Validates security-critical authentication logic in isolation.

Run with: pytest backend/tests/unit/test_auth.py -v
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import Mock

import jwt
import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.auth import (  # noqa: E402
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
    JWT_SECRET_KEY,
    create_access_token,
    decode_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.user import User  # noqa: E402


class TestHashPassword:
    """Test password hashing functions."""

    def test_hash_password_returns_hex_string(self):
        """Test that hash_password returns a hex string."""
        result = hash_password("test_password")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest length

    def test_hash_password_deterministic(self):
        """Test that same password produces same hash."""
        password = "test_password"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 == hash2

    def test_hash_password_different_passwords(self):
        """Test that different passwords produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test verify_password returns True for correct password."""
        password = "test_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verify_password returns False for incorrect password."""
        password = "test_password"
        hashed = hash_password(password)
        assert verify_password("wrong_password", hashed) is False

    def test_verify_password_different_hash(self):
        """Test verify_password returns False for different hash."""
        password = "test_password"
        hashed2 = hash_password("different_password")
        assert verify_password(password, hashed2) is False


class TestCreateAccessToken:
    """Test JWT token creation."""

    def test_creates_valid_jwt(self):
        """Test token can be decoded and contains user_id."""
        user_id = "user_123"
        token = create_access_token(user_id)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == user_id

    def test_token_contains_expiration(self):
        """Test token has exp claim."""
        user_id = "user_123"
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert "exp" in payload
        assert "iat" in payload
        
        # Check expiration is approximately 7 days from now
        exp_time = datetime.fromtimestamp(payload["exp"], tz=UTC)
        expected_exp = datetime.now(UTC) + timedelta(hours=JWT_EXPIRATION_HOURS)
        # Allow 1 minute tolerance
        assert abs((exp_time - expected_exp).total_seconds()) < 60

    def test_token_contains_user_id_in_sub(self):
        """Test token contains user_id in 'sub' claim."""
        user_id = "user_456"
        token = create_access_token(user_id)
        
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == user_id


class TestDecodeAccessToken:
    """Test JWT token decoding."""

    def test_valid_token_returns_user_id(self):
        """Test valid token decodes correctly."""
        user_id = "user_123"
        token = create_access_token(user_id)
        
        decoded_id = decode_access_token(token)
        assert decoded_id == user_id

    def test_expired_token_returns_none(self):
        """Test expired token returns None."""
        # Create an expired token
        expiration = datetime.now(UTC) - timedelta(hours=1)  # Expired 1 hour ago
        payload = {
            "sub": "user_123",
            "exp": expiration,
            "iat": datetime.now(UTC) - timedelta(hours=2),
        }
        expired_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        result = decode_access_token(expired_token)
        assert result is None

    def test_invalid_token_returns_none(self):
        """Test invalid token returns None."""
        invalid_token = "not.a.valid.token"
        result = decode_access_token(invalid_token)
        assert result is None

    def test_malformed_token_returns_none(self):
        """Test malformed token returns None."""
        malformed_token = "invalid"
        result = decode_access_token(malformed_token)
        assert result is None

    def test_token_with_wrong_secret_returns_none(self):
        """Test token signed with wrong secret returns None."""
        wrong_secret = "wrong-secret-key"
        token = jwt.encode(
            {"sub": "user_123", "exp": datetime.now(UTC) + timedelta(hours=1)},
            wrong_secret,
            algorithm=JWT_ALGORITHM,
        )
        
        result = decode_access_token(token)
        assert result is None


class TestGetCurrentUser:
    """Test get_current_user dependency function."""

    def test_missing_credentials_raises_401(self):
        """Test missing auth header raises 401."""
        mock_db = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=None, db=mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Authentication required" in exc_info.value.detail

    def test_invalid_token_raises_401(self):
        """Test invalid token raises 401."""
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid_token"
        mock_db = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired token" in exc_info.value.detail

    def test_expired_token_raises_401(self):
        """Test expired token raises 401."""
        # Create expired token
        expiration = datetime.now(UTC) - timedelta(hours=1)
        payload = {
            "sub": "user_123",
            "exp": expiration,
            "iat": datetime.now(UTC) - timedelta(hours=2),
        }
        expired_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = expired_token
        mock_db = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_found_raises_401(self):
        """Test non-existent user raises 401."""
        user_id = "nonexistent_user"
        token = create_access_token(user_id)
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        mock_db = Mock()
        mock_db.get.return_value = None  # User not found
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=mock_credentials, db=mock_db)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "User not found" in exc_info.value.detail
        mock_db.get.assert_called_once_with(User, user_id)

    def test_valid_token_returns_user(self):
        """Test valid token with existing user returns user."""
        user_id = "user_123"
        token = create_access_token(user_id)
        
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        
        mock_credentials = Mock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = token
        mock_db = Mock()
        mock_db.get.return_value = mock_user
        
        result = get_current_user(credentials=mock_credentials, db=mock_db)
        
        assert result == mock_user
        mock_db.get.assert_called_once_with(User, user_id)

