"""Unit tests for User model.

Tests password hashing and verification logic - critical security functionality, fast (~0.1s).
Validates bcrypt hashing, password verification, and edge cases (unicode, long passwords).

Run with: pytest backend/tests/unit/test_user_model.py -v
Or from backend/: pytest tests/unit/test_user_model.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.models.user import User  # noqa: E402


class TestHashPassword:
    """Test password hashing functionality."""

    def test_hash_password_valid(self):
        """Test hashing a valid password."""
        password = "testpassword123"
        hashed = User.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt hash format

    def test_hash_password_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        password1 = "password1"
        password2 = "password2"

        hashed1 = User.hash_password(password1)
        hashed2 = User.hash_password(password2)

        assert hashed1 != hashed2

    def test_hash_password_same_password_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "samepassword"

        hashed1 = User.hash_password(password)
        hashed2 = User.hash_password(password)

        # Different salts should produce different hashes
        assert hashed1 != hashed2

    def test_hash_password_long_password(self):
        """Test hashing password longer than 72 bytes (bcrypt limit)."""
        # Create password longer than 72 bytes
        long_password = "a" * 100
        hashed = User.hash_password(long_password)

        assert hashed.startswith("$2b$")
        # Should still be able to verify it
        user = User(email="test@example.com", password_hash=hashed)
        assert user.verify_password(long_password)

    def test_hash_password_unicode(self):
        """Test hashing password with unicode characters."""
        unicode_password = "测试密码🔒123"
        hashed = User.hash_password(unicode_password)

        assert hashed.startswith("$2b$")
        # Should still be able to verify it
        user = User(email="test@example.com", password_hash=hashed)
        assert user.verify_password(unicode_password)

    def test_hash_password_emoji(self):
        """Test hashing password with emoji."""
        emoji_password = "password😀🎉🔥"
        hashed = User.hash_password(emoji_password)

        assert hashed.startswith("$2b$")
        # Should still be able to verify it
        user = User(email="test@example.com", password_hash=hashed)
        assert user.verify_password(emoji_password)

    def test_hash_password_empty(self):
        """Test hashing empty password."""
        hashed = User.hash_password("")
        assert hashed.startswith("$2b$")


class TestVerifyPassword:
    """Test password verification functionality."""

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "testpassword123"
        hashed = User.hash_password(password)
        user = User(email="test@example.com", password_hash=hashed)

        assert user.verify_password(password) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = User.hash_password(password)
        user = User(email="test@example.com", password_hash=hashed)

        assert user.verify_password(wrong_password) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "TestPassword123"
        hashed = User.hash_password(password)
        user = User(email="test@example.com", password_hash=hashed)

        assert user.verify_password("testpassword123") is False
        assert user.verify_password("TestPassword123") is True

    def test_verify_password_empty_wrong(self):
        """Test verifying empty password against non-empty hash."""
        password = "testpassword123"
        hashed = User.hash_password(password)
        user = User(email="test@example.com", password_hash=hashed)

        assert user.verify_password("") is False

    def test_verify_password_long_password(self):
        """Test verifying password longer than 72 bytes (truncated by bcrypt)."""
        long_password = "a" * 100
        hashed = User.hash_password(long_password)
        user = User(email="test@example.com", password_hash=hashed)

        # Both passwords > 72 bytes get truncated to first 72 bytes, so they match
        assert user.verify_password(long_password) is True
        # Different character should fail
        different_long = "b" * 100
        assert user.verify_password(different_long) is False

    def test_verify_password_unicode(self):
        """Test verifying password with unicode characters."""
        unicode_password = "测试密码🔒123"
        hashed = User.hash_password(unicode_password)
        user = User(email="test@example.com", password_hash=hashed)

        assert user.verify_password(unicode_password) is True
        assert user.verify_password("测试密码🔒124") is False

    def test_verify_password_emoji(self):
        """Test verifying password with emoji."""
        emoji_password = "password😀🎉🔥"
        hashed = User.hash_password(emoji_password)
        user = User(email="test@example.com", password_hash=hashed)

        assert user.verify_password(emoji_password) is True
        assert user.verify_password("password😀🎉💧") is False

    def test_verify_password_special_characters(self):
        """Test verifying password with special characters."""
        special_password = "p@ssw0rd!#$%^&*()"
        hashed = User.hash_password(special_password)
        user = User(email="test@example.com", password_hash=hashed)

        assert user.verify_password(special_password) is True
        assert user.verify_password("p@ssw0rd!#$%^&*() ") is False  # Extra space

