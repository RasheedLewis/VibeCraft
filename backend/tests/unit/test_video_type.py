"""Unit tests for video_type functionality.

Tests the should_use_sections_for_song() function and VideoTypeUpdate schema validation.
"""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from app.core.config import should_use_sections_for_song
from app.schemas.song import VideoTypeUpdate


class TestShouldUseSectionsForSong:
    """Tests for should_use_sections_for_song() function."""

    def test_full_length_returns_true(self):
        """Test that full_length video_type returns True."""
        mock_song = Mock()
        mock_song.video_type = "full_length"
        
        result = should_use_sections_for_song(mock_song)
        assert result is True

    def test_short_form_returns_false(self):
        """Test that short_form video_type returns False."""
        mock_song = Mock()
        mock_song.video_type = "short_form"
        
        result = should_use_sections_for_song(mock_song)
        assert result is False

    def test_none_video_type_returns_false(self):
        """Test that None video_type returns False (default)."""
        mock_song = Mock()
        mock_song.video_type = None
        
        result = should_use_sections_for_song(mock_song)
        assert result is False

    def test_missing_video_type_attribute_returns_false(self):
        """Test that song without video_type attribute returns False."""
        mock_song = Mock(spec=[])  # No video_type attribute
        
        result = should_use_sections_for_song(mock_song)
        assert result is False

    def test_empty_string_video_type_returns_false(self):
        """Test that empty string video_type returns False."""
        mock_song = Mock()
        mock_song.video_type = ""
        
        result = should_use_sections_for_song(mock_song)
        assert result is False


class TestVideoTypeUpdateSchema:
    """Tests for VideoTypeUpdate schema validation."""

    def test_valid_full_length(self):
        """Test that 'full_length' is accepted."""
        schema = VideoTypeUpdate(video_type="full_length")
        assert schema.video_type == "full_length"

    def test_valid_short_form(self):
        """Test that 'short_form' is accepted."""
        schema = VideoTypeUpdate(video_type="short_form")
        assert schema.video_type == "short_form"

    def test_invalid_video_type_raises_error(self):
        """Test that invalid video_type raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            VideoTypeUpdate(video_type="invalid_type")
        
        errors = exc_info.value.errors()
        assert len(errors) > 0
        assert any("full_length" in str(error) and "short_form" in str(error) for error in errors)

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValidationError."""
        with pytest.raises(ValidationError):
            VideoTypeUpdate(video_type="")

    def test_none_raises_error(self):
        """Test that None raises ValidationError (required field)."""
        with pytest.raises(ValidationError):
            VideoTypeUpdate(video_type=None)

