"""Tests for animations preference API endpoint.

Tests the PATCH /auth/me/animations endpoint including:
- Requires authentication
- Updates animations_disabled field
- Returns updated user info
- Persists to database
"""

from __future__ import annotations

import secrets

from fastapi.testclient import TestClient

from app.core.auth import create_access_token
from app.core.database import init_db, session_scope
from app.main import create_app
from app.models.user import User

init_db()


def _cleanup_user(user_id: str) -> None:
    """Clean up test user."""
    with session_scope() as session:
        user = session.get(User, user_id)
        if user:
            session.delete(user)
            session.commit()


class TestAnimationsPreferenceEndpoint:
    """Tests for PATCH /auth/me/animations endpoint."""

    def setup_method(self):
        """Set up test client and create a test user."""
        self.app = create_app()
        self.client = TestClient(self.app)

        # Create a test user with unique email
        with session_scope() as session:
            user_id = f"user_{secrets.token_urlsafe(16)}"
            unique_email = f"test_{secrets.token_urlsafe(8)}@example.com"
            user = User(
                id=user_id,
                email=unique_email,
                display_name="Test User",
                animations_disabled=False,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            self.user_id = user_id
            self.user_email = user.email

            # Create access token
            self.token = create_access_token(user_id)

    def teardown_method(self):
        """Clean up test user."""
        _cleanup_user(self.user_id)

    def test_update_animations_disabled_to_true(self):
        """Test updating animations_disabled to True."""
        response = self.client.patch(
            "/api/v1/auth/me/animations",
            json={"animations_disabled": True},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["animations_disabled"] is True
        assert data["user_id"] == self.user_id
        assert data["email"] == self.user_email

        # Verify it's persisted
        with session_scope() as session:
            user = session.get(User, self.user_id)
            assert user.animations_disabled is True

    def test_update_animations_disabled_to_false(self):
        """Test updating animations_disabled to False."""
        # First set it to True
        with session_scope() as session:
            user = session.get(User, self.user_id)
            user.animations_disabled = True
            session.add(user)
            session.commit()

        # Then update to False
        response = self.client.patch(
            "/api/v1/auth/me/animations",
            json={"animations_disabled": False},
            headers={"Authorization": f"Bearer {self.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["animations_disabled"] is False

        # Verify it's persisted
        with session_scope() as session:
            user = session.get(User, self.user_id)
            assert user.animations_disabled is False

    def test_update_animations_requires_auth(self):
        """Test that updating animations preference requires authentication."""
        response = self.client.patch(
            "/api/v1/auth/me/animations",
            json={"animations_disabled": True},
            # No Authorization header
        )

        assert response.status_code == 401

    def test_update_animations_invalid_token(self):
        """Test that invalid token returns 401."""
        response = self.client.patch(
            "/api/v1/auth/me/animations",
            json={"animations_disabled": True},
            headers={"Authorization": "Bearer invalid-token"},
        )

        assert response.status_code == 401

    def test_get_me_includes_animations_disabled(self):
        """Test that GET /auth/me includes animations_disabled field."""
        # Set animations_disabled to True
        with session_scope() as session:
            user = session.get(User, self.user_id)
            user.animations_disabled = True
            session.add(user)
            session.commit()

        # Get user info
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {self.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "animations_disabled" in data
        assert data["animations_disabled"] is True

    def test_get_me_defaults_animations_disabled_to_false(self):
        """Test that GET /auth/me defaults animations_disabled to False if not set."""
        # Ensure field is False (or doesn't exist in old records)
        with session_scope() as session:
            user = session.get(User, self.user_id)
            user.animations_disabled = False
            session.add(user)
            session.commit()

        # Get user info
        response = self.client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {self.token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "animations_disabled" in data
        assert data["animations_disabled"] is False

