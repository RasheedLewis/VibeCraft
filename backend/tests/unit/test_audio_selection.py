"""Unit tests for audio selection validation service."""

import pytest

from app.core.constants import (
    MAX_AUDIO_SELECTION_DURATION_SEC,
    MIN_AUDIO_SELECTION_DURATION_SEC,
)
from app.services.audio_selection import validate_audio_selection


class TestValidateAudioSelection:
    """Tests for validate_audio_selection function."""

    def test_valid_selection(self):
        """Test that a valid selection passes validation."""
        validate_audio_selection(start_sec=10.0, end_sec=20.0, song_duration_sec=60.0)

    def test_valid_at_song_start(self):
        """Test that selection starting at 0 is valid."""
        validate_audio_selection(start_sec=0.0, end_sec=30.0, song_duration_sec=60.0)

    def test_valid_at_song_end(self):
        """Test that selection ending at song duration is valid."""
        validate_audio_selection(start_sec=30.0, end_sec=60.0, song_duration_sec=60.0)

    def test_none_duration_raises_error(self):
        """Test that None duration raises ValueError."""
        with pytest.raises(ValueError, match="Song duration not available"):
            validate_audio_selection(start_sec=10.0, end_sec=20.0, song_duration_sec=None)

    def test_negative_start_raises_error(self):
        """Test that negative start time raises ValueError."""
        with pytest.raises(ValueError, match="Start time must be >= 0"):
            validate_audio_selection(start_sec=-1.0, end_sec=20.0, song_duration_sec=60.0)

    def test_end_exceeds_duration_raises_error(self):
        """Test that end time exceeding song duration raises ValueError."""
        with pytest.raises(ValueError, match="exceeds song duration"):
            validate_audio_selection(start_sec=10.0, end_sec=70.0, song_duration_sec=60.0)

    def test_end_equals_start_raises_error(self):
        """Test that end time equal to start time raises ValueError."""
        with pytest.raises(ValueError, match="End time must be greater than start time"):
            validate_audio_selection(start_sec=10.0, end_sec=10.0, song_duration_sec=60.0)

    def test_end_less_than_start_raises_error(self):
        """Test that end time less than start time raises ValueError."""
        with pytest.raises(ValueError, match="End time must be greater than start time"):
            validate_audio_selection(start_sec=20.0, end_sec=10.0, song_duration_sec=60.0)

    def test_duration_exactly_maximum(self):
        """Test that exactly 30 seconds is valid (boundary case)."""
        validate_audio_selection(
            start_sec=10.0,
            end_sec=10.0 + MAX_AUDIO_SELECTION_DURATION_SEC,
            song_duration_sec=60.0,
        )

    def test_duration_exactly_minimum(self):
        """Test that exactly 1 second is valid (boundary case)."""
        validate_audio_selection(
            start_sec=10.0,
            end_sec=10.0 + MIN_AUDIO_SELECTION_DURATION_SEC,
            song_duration_sec=60.0,
        )

    def test_short_song_valid_selection(self):
        """Test that valid selection works for short songs."""
        # Song is 15 seconds, selection is 9 seconds (minimum)
        validate_audio_selection(start_sec=1.0, end_sec=10.0, song_duration_sec=15.0)

    def test_short_song_exceeds_duration_raises_error(self):
        """Test that selection cannot exceed short song duration."""
        with pytest.raises(ValueError, match="exceeds song duration"):
            validate_audio_selection(start_sec=1.0, end_sec=6.0, song_duration_sec=5.0)

