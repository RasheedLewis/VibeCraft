"""Unit tests for composition execution service."""



from app.services.composition_execution import MAX_DURATION_MISMATCH_SECONDS


class TestDurationMismatchHandling:
    """Tests for duration mismatch handling in composition pipeline."""

    def test_max_duration_mismatch_constant(self):
        """Test that MAX_DURATION_MISMATCH_SECONDS is set correctly."""
        assert MAX_DURATION_MISMATCH_SECONDS == 5.0

    def test_duration_mismatch_logic_clips_longer(self):
        """Test duration mismatch calculation when clips are longer."""
        total_clip_duration = 35.0
        song_duration = 30.0
        duration_diff = total_clip_duration - song_duration

        # Should be within threshold (5 seconds)
        assert abs(duration_diff) <= MAX_DURATION_MISMATCH_SECONDS
        assert duration_diff > 0  # Clips are longer

    def test_duration_mismatch_logic_clips_shorter(self):
        """Test duration mismatch calculation when clips are shorter."""
        total_clip_duration = 25.0
        song_duration = 30.0
        duration_diff = total_clip_duration - song_duration

        # Should be within threshold (5 seconds)
        assert abs(duration_diff) <= MAX_DURATION_MISMATCH_SECONDS
        assert duration_diff < 0  # Clips are shorter

    def test_duration_mismatch_logic_too_long(self):
        """Test duration mismatch when clips are too much longer."""
        total_clip_duration = 40.0
        song_duration = 30.0
        duration_diff = total_clip_duration - song_duration

        # Should exceed threshold (10 seconds > 5 seconds)
        assert abs(duration_diff) > MAX_DURATION_MISMATCH_SECONDS

    def test_duration_mismatch_logic_too_short(self):
        """Test duration mismatch when clips are too much shorter."""
        total_clip_duration = 20.0
        song_duration = 30.0
        duration_diff = total_clip_duration - song_duration

        # Should exceed threshold (10 seconds > 5 seconds)
        assert abs(duration_diff) > MAX_DURATION_MISMATCH_SECONDS

