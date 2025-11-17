"""Unit tests for authentication dependencies.

Tests get_current_user dependency - critical for protected route security, fast (~0.1s).
Validates token extraction, verification, and user lookup with error handling.

Run with: pytest backend/tests/unit/test_auth_deps.py -v
Or from backend/: pytest tests/unit/test_auth_deps.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.api.deps import get_current_user  # noqa: E402
from app.models.user import User  # noqa: E402


class TestGetCurrentUser:
    """Test get_current_user dependency."""

    @patch("app.api.deps.get_user_by_id")
    @patch("app.api.deps.verify_token")
    def test_get_current_user_success(self, mock_verify_token, mock_get_user_by_id):
        """Test successful user retrieval with valid token."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid-token"
        mock_session = MagicMock()

        mock_user = MagicMock(spec=User)
        mock_user.id = "user-123"
        mock_user.email = "test@example.com"

        mock_verify_token.return_value = "user-123"
        mock_get_user_by_id.return_value = mock_user

        user = get_current_user(mock_credentials, mock_session)

        assert user == mock_user
        mock_verify_token.assert_called_once_with("valid-token")
        mock_get_user_by_id.assert_called_once_with(mock_session, "user-123")

    @patch("app.api.deps.verify_token")
    def test_get_current_user_invalid_token(self, mock_verify_token):
        """Test with invalid token."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "invalid-token"
        mock_session = MagicMock()

        mock_verify_token.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_session)

        assert exc_info.value.status_code == 401
        assert "Invalid authentication credentials" in exc_info.value.detail
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

    @patch("app.api.deps.get_user_by_id")
    @patch("app.api.deps.verify_token")
    def test_get_current_user_expired_token(self, mock_verify_token, mock_get_user_by_id):
        """Test with expired token."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "expired-token"
        mock_session = MagicMock()

        mock_verify_token.return_value = None  # Expired token returns None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_session)

        assert exc_info.value.status_code == 401
        mock_get_user_by_id.assert_not_called()

    @patch("app.api.deps.get_user_by_id")
    @patch("app.api.deps.verify_token")
    def test_get_current_user_user_not_found(self, mock_verify_token, mock_get_user_by_id):
        """Test when token is valid but user doesn't exist."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "valid-token"
        mock_session = MagicMock()

        mock_verify_token.return_value = "user-123"
        mock_get_user_by_id.return_value = None  # User not found

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_session)

        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail
        assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"
        mock_get_user_by_id.assert_called_once_with(mock_session, "user-123")

    @patch("app.api.deps.verify_token")
    def test_get_current_user_tampered_token(self, mock_verify_token):
        """Test with tampered token."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "tampered-token"
        mock_session = MagicMock()

        mock_verify_token.return_value = None  # Tampered token fails verification

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(mock_credentials, mock_session)

        assert exc_info.value.status_code == 401

    @patch("app.api.deps.get_user_by_id")
    @patch("app.api.deps.verify_token")
    def test_get_current_user_correct_user_returned(self, mock_verify_token, mock_get_user_by_id):
        """Test that correct user is returned based on token."""
        mock_credentials = MagicMock(spec=HTTPAuthorizationCredentials)
        mock_credentials.credentials = "token-for-user-456"
        mock_session = MagicMock()

        mock_user = MagicMock(spec=User)
        mock_user.id = "user-456"
        mock_user.email = "user456@example.com"

        mock_verify_token.return_value = "user-456"
        mock_get_user_by_id.return_value = mock_user

        user = get_current_user(mock_credentials, mock_session)

        assert user.id == "user-456"
        assert user.email == "user456@example.com"
        mock_get_user_by_id.assert_called_once_with(mock_session, "user-456")

