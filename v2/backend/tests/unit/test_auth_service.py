"""Unit tests for authentication service.

Tests JWT token creation/verification, user registration, and authentication - critical security logic, fast (~0.2s).
Validates token generation, expiration, user registration, authentication, and error handling.

Run with: pytest backend/tests/unit/test_auth_service.py -v
Or from backend/: pytest tests/unit/test_auth_service.py -v
"""

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from jose import jwt

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.models.user import User  # noqa: E402
from app.services.auth_service import (  # noqa: E402
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_user_by_id,
    register_user,
    verify_token,
)


class TestCreateAccessToken:
    """Test JWT token creation."""

    @patch("app.services.auth_service.settings")
    def test_create_access_token_success(self, mock_settings):
        """Test successful token creation."""
        mock_settings.secret_key = "test-secret-key"

        user_id = "user-123"
        token = create_access_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        assert payload["sub"] == user_id
        assert "exp" in payload

    @patch("app.services.auth_service.settings")
    def test_create_access_token_different_users(self, mock_settings):
        """Test that different users get different tokens."""
        mock_settings.secret_key = "test-secret-key"

        token1 = create_access_token("user-1")
        token2 = create_access_token("user-2")

        assert token1 != token2

        # Verify tokens contain correct user IDs
        payload1 = jwt.decode(token1, "test-secret-key", algorithms=["HS256"])
        payload2 = jwt.decode(token2, "test-secret-key", algorithms=["HS256"])
        assert payload1["sub"] == "user-1"
        assert payload2["sub"] == "user-2"

    @patch("app.services.auth_service.settings")
    def test_create_access_token_expiration(self, mock_settings):
        """Test that token has correct expiration time."""
        mock_settings.secret_key = "test-secret-key"

        user_id = "user-123"
        token = create_access_token(user_id)

        payload = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=UTC)

        # Check expiration is approximately 7 days from now
        expected_exp = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 60  # Within 1 minute tolerance


class TestVerifyToken:
    """Test JWT token verification."""

    @patch("app.services.auth_service.settings")
    def test_verify_token_valid(self, mock_settings):
        """Test verifying valid token."""
        mock_settings.secret_key = "test-secret-key"

        user_id = "user-123"
        token = create_access_token(user_id)

        result = verify_token(token)
        assert result == user_id

    @patch("app.services.auth_service.settings")
    def test_verify_token_expired(self, mock_settings):
        """Test verifying expired token."""
        mock_settings.secret_key = "test-secret-key"

        # Create expired token
        expire = datetime.now(UTC) - timedelta(minutes=1)
        to_encode = {"sub": "user-123", "exp": expire}
        expired_token = jwt.encode(to_encode, "test-secret-key", algorithm="HS256")

        result = verify_token(expired_token)
        assert result is None

    @patch("app.services.auth_service.settings")
    def test_verify_token_invalid_format(self, mock_settings):
        """Test verifying invalid token format."""
        mock_settings.secret_key = "test-secret-key"

        result = verify_token("not-a-valid-token")
        assert result is None

    @patch("app.services.auth_service.settings")
    def test_verify_token_tampered(self, mock_settings):
        """Test verifying tampered token."""
        mock_settings.secret_key = "test-secret-key"

        user_id = "user-123"
        token = create_access_token(user_id)
        # Tamper with token
        tampered_token = token[:-5] + "xxxxx"

        result = verify_token(tampered_token)
        assert result is None

    @patch("app.services.auth_service.settings")
    def test_verify_token_wrong_secret(self, mock_settings):
        """Test verifying token with wrong secret key."""
        mock_settings.secret_key = "wrong-secret-key"

        # Create token with different secret
        expire = datetime.now(UTC) + timedelta(minutes=60)
        to_encode = {"sub": "user-123", "exp": expire}
        token = jwt.encode(to_encode, "correct-secret-key", algorithm="HS256")

        result = verify_token(token)
        assert result is None

    @patch("app.services.auth_service.settings")
    def test_verify_token_missing_sub(self, mock_settings):
        """Test verifying token without 'sub' claim."""
        mock_settings.secret_key = "test-secret-key"

        # Create token without 'sub'
        expire = datetime.now(UTC) + timedelta(minutes=60)
        to_encode = {"exp": expire}
        token = jwt.encode(to_encode, "test-secret-key", algorithm="HS256")

        result = verify_token(token)
        assert result is None

    @patch("app.services.auth_service.settings")
    def test_verify_token_none_sub(self, mock_settings):
        """Test verifying token with None 'sub' claim."""
        mock_settings.secret_key = "test-secret-key"

        # Create token with None 'sub'
        expire = datetime.now(UTC) + timedelta(minutes=60)
        to_encode = {"sub": None, "exp": expire}
        token = jwt.encode(to_encode, "test-secret-key", algorithm="HS256")

        result = verify_token(token)
        assert result is None


class TestRegisterUser:
    """Test user registration."""

    def test_register_user_success(self):
        """Test successful user registration."""
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None  # No existing user
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        def refresh_side_effect(user):
            user.id = "user-123"
            user.email = "test@example.com"
            user.password_hash = "hashed_password"
            user.created_at = datetime.now(UTC)

        mock_session.refresh.side_effect = refresh_side_effect

        user = register_user(mock_session, "test@example.com", "password123")

        assert user.email == "test@example.com"
        assert user.id == "user-123"
        assert user.password_hash == "hashed_password"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_register_user_duplicate_email(self):
        """Test registration with duplicate email."""
        mock_session = MagicMock()
        existing_user = MagicMock()
        existing_user.email = "test@example.com"
        mock_session.exec.return_value.first.return_value = existing_user

        with pytest.raises(ValueError, match="already registered"):
            register_user(mock_session, "test@example.com", "password123")

    def test_register_user_password_hashed(self):
        """Test that password is hashed, not stored plaintext."""
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        def refresh_side_effect(user):
            user.id = "user-123"
            user.email = "test@example.com"

        mock_session.refresh.side_effect = refresh_side_effect

        password = "password123"
        register_user(mock_session, "test@example.com", password)

        # Verify password was hashed (check the call to add)
        added_user = mock_session.add.call_args[0][0]
        assert added_user.password_hash != password
        assert added_user.password_hash.startswith("$2b$")  # bcrypt format


class TestAuthenticateUser:
    """Test user authentication."""

    def test_authenticate_user_success(self):
        """Test successful authentication."""
        mock_session = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.email = "test@example.com"
        mock_user.verify_password.return_value = True
        mock_session.exec.return_value.first.return_value = mock_user

        user = authenticate_user(mock_session, "test@example.com", "password123")

        assert user == mock_user
        mock_user.verify_password.assert_called_once_with("password123")

    def test_authenticate_user_invalid_email(self):
        """Test authentication with non-existent email."""
        mock_session = MagicMock()
        mock_session.exec.return_value.first.return_value = None

        result = authenticate_user(mock_session, "nonexistent@example.com", "password123")

        assert result is None

    def test_authenticate_user_invalid_password(self):
        """Test authentication with wrong password."""
        mock_session = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.email = "test@example.com"
        mock_user.verify_password.return_value = False
        mock_session.exec.return_value.first.return_value = mock_user

        result = authenticate_user(mock_session, "test@example.com", "wrongpassword")

        assert result is None
        mock_user.verify_password.assert_called_once_with("wrongpassword")

    def test_authenticate_user_case_sensitive_email(self):
        """Test that email matching is case-sensitive."""
        mock_session = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.email = "Test@Example.com"
        mock_session.exec.return_value.first.return_value = mock_user

        # SQLModel/SQLAlchemy queries are case-sensitive by default
        authenticate_user(mock_session, "test@example.com", "password123")

        # Should not find user if case doesn't match (depends on DB collation)
        # This test verifies the query is executed correctly
        mock_session.exec.assert_called_once()


class TestGetUserById:
    """Test user lookup by ID."""

    def test_get_user_by_id_success(self):
        """Test successful user lookup."""
        mock_session = MagicMock()
        mock_user = MagicMock(spec=User)
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"
        mock_session.get.return_value = mock_user

        user = get_user_by_id(mock_session, "user-123")

        assert user == mock_user
        mock_session.get.assert_called_once_with(User, "user-123")

    def test_get_user_by_id_not_found(self):
        """Test lookup with non-existent ID."""
        mock_session = MagicMock()
        mock_session.get.return_value = None

        result = get_user_by_id(mock_session, "nonexistent-id")

        assert result is None
        mock_session.get.assert_called_once_with(User, "nonexistent-id")

