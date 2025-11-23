"""Unit tests for configuration service.

Tests feature flag configuration, especially is_sections_enabled().

Run with: pytest backend/tests/unit/test_config.py -v
"""

import os
import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import get_settings, is_sections_enabled  # noqa: E402


class TestFeatureFlagConfiguration:
    """Tests for feature flag configuration."""

    def test_is_sections_enabled_default_true(self):
        """Test that default value is True for backward compatibility."""
        # Clear cache to get fresh settings
        is_sections_enabled.cache_clear()
        get_settings.cache_clear()

        # Remove env var if it exists
        env_backup = os.environ.pop("ENABLE_SECTIONS", None)

        try:
            result = is_sections_enabled()
            assert result is True, "Default should be True for backward compatibility"
        finally:
            # Restore env var if it was set
            if env_backup is not None:
                os.environ["ENABLE_SECTIONS"] = env_backup
            is_sections_enabled.cache_clear()
            get_settings.cache_clear()

    def test_is_sections_enabled_env_override_true(self):
        """Test that environment variable can override to True."""
        is_sections_enabled.cache_clear()
        get_settings.cache_clear()

        env_backup = os.environ.get("ENABLE_SECTIONS")

        try:
            os.environ["ENABLE_SECTIONS"] = "true"
            result = is_sections_enabled()
            assert result is True
        finally:
            if env_backup is not None:
                os.environ["ENABLE_SECTIONS"] = env_backup
            elif "ENABLE_SECTIONS" in os.environ:
                del os.environ["ENABLE_SECTIONS"]
            is_sections_enabled.cache_clear()
            get_settings.cache_clear()

    def test_is_sections_enabled_env_override_false(self):
        """Test that environment variable can override to False."""
        is_sections_enabled.cache_clear()
        get_settings.cache_clear()

        env_backup = os.environ.get("ENABLE_SECTIONS")

        try:
            os.environ["ENABLE_SECTIONS"] = "false"
            result = is_sections_enabled()
            assert result is False
        finally:
            if env_backup is not None:
                os.environ["ENABLE_SECTIONS"] = env_backup
            elif "ENABLE_SECTIONS" in os.environ:
                del os.environ["ENABLE_SECTIONS"]
            is_sections_enabled.cache_clear()
            get_settings.cache_clear()

    def test_is_sections_enabled_case_insensitive(self):
        """Test that case variations work (False, FALSE, false)."""
        is_sections_enabled.cache_clear()
        get_settings.cache_clear()

        env_backup = os.environ.get("ENABLE_SECTIONS")

        try:
            for value in ["False", "FALSE", "false", "0"]:
                os.environ["ENABLE_SECTIONS"] = value
                is_sections_enabled.cache_clear()
                get_settings.cache_clear()
                result = is_sections_enabled()
                assert result is False, f"Should be False for value: {value}"

            for value in ["True", "TRUE", "true", "1"]:
                os.environ["ENABLE_SECTIONS"] = value
                is_sections_enabled.cache_clear()
                get_settings.cache_clear()
                result = is_sections_enabled()
                assert result is True, f"Should be True for value: {value}"
        finally:
            if env_backup is not None:
                os.environ["ENABLE_SECTIONS"] = env_backup
            elif "ENABLE_SECTIONS" in os.environ:
                del os.environ["ENABLE_SECTIONS"]
            is_sections_enabled.cache_clear()
            get_settings.cache_clear()

    def test_is_sections_enabled_caching(self):
        """Test that @lru_cache works correctly."""
        is_sections_enabled.cache_clear()
        get_settings.cache_clear()

        env_backup = os.environ.get("ENABLE_SECTIONS")

        try:
            # Set to False
            os.environ["ENABLE_SECTIONS"] = "false"
            is_sections_enabled.cache_clear()
            get_settings.cache_clear()
            result1 = is_sections_enabled()

            # Change env var but don't clear cache - should return cached value
            os.environ["ENABLE_SECTIONS"] = "true"
            result2 = is_sections_enabled()
            assert result1 == result2, "Should return cached value"

            # Clear cache and try again - should get new value
            is_sections_enabled.cache_clear()
            get_settings.cache_clear()
            result3 = is_sections_enabled()
            assert result3 is True, "Should get new value after cache clear"
        finally:
            if env_backup is not None:
                os.environ["ENABLE_SECTIONS"] = env_backup
            elif "ENABLE_SECTIONS" in os.environ:
                del os.environ["ENABLE_SECTIONS"]
            is_sections_enabled.cache_clear()
            get_settings.cache_clear()

