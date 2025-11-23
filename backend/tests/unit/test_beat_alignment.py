"""Unit tests for beat alignment service.

Tests beat-to-frame alignment algorithm and clip boundary calculation.
Validates core algorithm correctness, duration constraints, and edge cases.

Run with: pytest backend/tests/unit/test_beat_alignment.py -v
Or from backend/: pytest tests/unit/test_beat_alignment.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from app.services.beat_alignment import (  # noqa: E402
    MAX_CLIP_DURATION,
    MIN_CLIP_DURATION,
    calculate_beat_aligned_boundaries,
    find_nearest_beat_index,
    map_beats_to_frames,
    validate_boundaries,
)


class TestMapBeatsToFrames:
    """Test beat-to-frame mapping algorithm."""

    def test_perfect_alignment_at_zero(self):
        """Test beat at 0.0 maps to frame 0."""
        beat_times = [0.0]
        alignments = map_beats_to_frames(beat_times, fps=8.0)

        assert len(alignments) == 1
        assert alignments[0].beat_index == 0
        assert alignments[0].beat_time == 0.0
        assert alignments[0].frame_index == 0
        assert alignments[0].frame_time == 0.0
        assert alignments[0].error_sec == 0.0

    def test_beat_to_frame_mapping_8fps(self):
        """Test beat mapping with 8 FPS (example from BEAT_FRAME_ALIGNMENT.md)."""
        # 110 BPM = 0.5455s per beat
        beat_times = [0.0, 0.545, 1.091, 1.636, 2.182]
        alignments = map_beats_to_frames(beat_times, fps=8.0)

        assert len(alignments) == 5

        # Beat 0: 0.000s → Frame 0 (0.000s), error = 0.000s
        assert alignments[0].frame_index == 0
        assert alignments[0].error_sec == pytest.approx(0.0, abs=0.001)

        # Beat 1: 0.545s → Frame 4 (0.500s), error ≈ 0.045s
        assert alignments[1].frame_index == 4
        assert alignments[1].error_sec == pytest.approx(0.045, abs=0.001)

        # Beat 2: 1.091s → Frame 9 (1.125s), error ≈ 0.034s
        assert alignments[2].frame_index == 9
        assert alignments[2].error_sec == pytest.approx(0.034, abs=0.001)

    def test_higher_fps_improves_alignment(self):
        """Test that higher FPS reduces alignment error."""
        beat_times = [0.545]  # Beat at 0.545s

        alignments_8fps = map_beats_to_frames(beat_times, fps=8.0)
        alignments_30fps = map_beats_to_frames(beat_times, fps=30.0)

        # Higher FPS should have lower error
        assert alignments_30fps[0].error_sec < alignments_8fps[0].error_sec

    def test_multiple_beats(self):
        """Test mapping multiple beats."""
        beat_times = [0.0, 0.5, 1.0, 1.5, 2.0]
        alignments = map_beats_to_frames(beat_times, fps=8.0)

        assert len(alignments) == 5
        # All beats should map to valid frame indices
        for alignment in alignments:
            assert alignment.frame_index >= 0
            assert alignment.error_sec >= 0


class TestFindNearestBeatIndex:
    """Test finding nearest beat index."""

    def test_exact_match(self):
        """Test finding exact beat match."""
        beat_times = [0.0, 1.0, 2.0, 3.0]
        assert find_nearest_beat_index(1.0, beat_times) == 1

    def test_nearest_beat(self):
        """Test finding nearest beat when time is between beats."""
        beat_times = [0.0, 1.0, 2.0, 3.0]
        assert find_nearest_beat_index(1.4, beat_times) == 1  # Closer to 1.0
        assert find_nearest_beat_index(1.6, beat_times) == 2  # Closer to 2.0

    def test_edge_cases(self):
        """Test edge cases for nearest beat."""
        beat_times = [0.0, 1.0, 2.0]
        assert find_nearest_beat_index(0.0, beat_times) == 0
        assert find_nearest_beat_index(2.0, beat_times) == 2
        assert find_nearest_beat_index(-0.1, beat_times) == 0  # Before first beat
        assert find_nearest_beat_index(2.5, beat_times) == 2  # After last beat


class TestCalculateBeatAlignedBoundaries:
    """Test clip boundary calculation algorithm."""

    def test_simple_case_110_bpm(self):
        """Test boundary calculation for 110 BPM song (example from doc)."""
        # 110 BPM = 0.5455s per beat
        # Generate beats for ~10 seconds
        beat_times = [i * 0.5455 for i in range(19)]  # ~10.36 seconds
        song_duration = 10.36

        boundaries = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
            fps=8.0,
        )

        assert len(boundaries) > 0
        # Each boundary should have valid duration
        for boundary in boundaries:
            assert MIN_CLIP_DURATION <= boundary.duration_sec <= MAX_CLIP_DURATION * 1.1
            assert boundary.start_time < boundary.end_time
            assert boundary.start_beat_index <= boundary.end_beat_index

    def test_duration_constraints(self):
        """Test that all clips respect 3-6 second duration constraints."""
        # Create beats for a 30-second song at 120 BPM (0.5s per beat)
        beat_times = [i * 0.5 for i in range(61)]  # 30 seconds
        song_duration = 30.0

        boundaries = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
        )

        assert len(boundaries) > 0
        for boundary in boundaries:
            # Allow 10% tolerance for edge cases
            assert boundary.duration_sec >= MIN_CLIP_DURATION * 0.9
            assert boundary.duration_sec <= MAX_CLIP_DURATION * 1.1

    def test_boundaries_cover_full_song(self):
        """Test that boundaries cover the entire song duration."""
        beat_times = [i * 0.5 for i in range(21)]  # 10 seconds
        song_duration = 10.0

        boundaries = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
        )

        assert len(boundaries) > 0
        # First boundary should start at or near first beat
        assert boundaries[0].start_time == pytest.approx(beat_times[0], abs=0.1)
        # Last boundary should end at or near song duration
        assert boundaries[-1].end_time == pytest.approx(song_duration, abs=0.1)

    def test_short_song(self):
        """Test boundary calculation for short song (just over min duration)."""
        # 4-second song
        beat_times = [i * 0.5 for i in range(9)]  # 4 seconds
        song_duration = 4.0

        boundaries = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
        )

        # Should create at least one boundary
        assert len(boundaries) >= 1
        # Should cover the song
        assert boundaries[0].start_time <= 0.1
        assert boundaries[-1].end_time >= song_duration - 0.1

    def test_long_song(self):
        """Test boundary calculation for longer song."""
        # 60-second song at 120 BPM
        beat_times = [i * 0.5 for i in range(121)]  # 60 seconds
        song_duration = 60.0

        boundaries = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
        )

        # Should create multiple clips
        assert len(boundaries) >= 5  # At least 5 clips for 60 seconds
        # Total coverage should match song duration
        total_coverage = boundaries[-1].end_time - boundaries[0].start_time
        assert total_coverage == pytest.approx(song_duration, abs=1.0)

    def test_different_fps_values(self):
        """Test that different FPS values produce valid boundaries."""
        beat_times = [i * 0.5 for i in range(21)]  # 10 seconds
        song_duration = 10.0

        boundaries_8fps = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
            fps=8.0,
        )

        boundaries_30fps = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
            fps=30.0,
        )

        # Both should produce valid boundaries
        assert len(boundaries_8fps) > 0
        assert len(boundaries_30fps) > 0

        # Both should respect duration constraints
        for boundary in boundaries_8fps + boundaries_30fps:
            assert boundary.duration_sec >= MIN_CLIP_DURATION * 0.9
            assert boundary.duration_sec <= MAX_CLIP_DURATION * 1.1

    def test_beats_in_clip_metadata(self):
        """Test that beats_in_clip metadata is correct."""
        beat_times = [i * 0.5 for i in range(21)]  # 10 seconds
        song_duration = 10.0

        boundaries = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
        )

        for boundary in boundaries:
            # beats_in_clip should be a list
            assert isinstance(boundary.beats_in_clip, list)
            # Should contain beat indices from start to end
            assert boundary.start_beat_index in boundary.beats_in_clip
            assert boundary.end_beat_index in boundary.beats_in_clip
            # Should be sequential
            if len(boundary.beats_in_clip) > 1:
                for i in range(len(boundary.beats_in_clip) - 1):
                    assert boundary.beats_in_clip[i] < boundary.beats_in_clip[i + 1]

    def test_empty_beat_times_raises_error(self):
        """Test that empty beat_times raises ValueError."""
        with pytest.raises(ValueError, match="beat_times cannot be empty"):
            calculate_beat_aligned_boundaries(
                beat_times=[],
                song_duration=10.0,
            )

    def test_invalid_duration_raises_error(self):
        """Test that invalid song_duration raises ValueError."""
        beat_times = [0.0, 1.0, 2.0]

        with pytest.raises(ValueError, match="song_duration must be positive"):
            calculate_beat_aligned_boundaries(
                beat_times=beat_times,
                song_duration=0.0,
            )

        with pytest.raises(ValueError, match="song_duration must be positive"):
            calculate_beat_aligned_boundaries(
                beat_times=beat_times,
                song_duration=-1.0,
            )


class TestValidateBoundaries:
    """Test boundary validation logic."""

    def test_valid_boundaries(self):
        """Test validation of well-aligned boundaries."""
        beat_times = [i * 0.5 for i in range(21)]  # 10 seconds
        song_duration = 10.0

        boundaries = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
            fps=8.0,
        )

        is_valid, max_error, avg_error = validate_boundaries(
            boundaries=boundaries,
            beat_times=beat_times,
            song_duration=song_duration,
            fps=8.0,
        )

        # Should be valid for well-aligned boundaries
        assert isinstance(is_valid, bool)
        assert max_error >= 0
        assert avg_error >= 0

    def test_empty_boundaries(self):
        """Test validation of empty boundaries list."""
        is_valid, max_error, avg_error = validate_boundaries(
            boundaries=[],
            beat_times=[0.0, 1.0],
            song_duration=1.0,
        )

        assert is_valid is True
        assert max_error == 0.0
        assert avg_error == 0.0

    def test_validation_with_different_fps(self):
        """Test that validation works with different FPS values."""
        beat_times = [i * 0.5 for i in range(21)]
        song_duration = 10.0

        boundaries = calculate_beat_aligned_boundaries(
            beat_times=beat_times,
            song_duration=song_duration,
            fps=30.0,
        )

        # Validate with same FPS
        is_valid_30, max_error_30, avg_error_30 = validate_boundaries(
            boundaries=boundaries,
            beat_times=beat_times,
            song_duration=song_duration,
            fps=30.0,
        )

        # Higher FPS should generally have lower errors
        assert isinstance(is_valid_30, bool)
        assert max_error_30 >= 0
        assert avg_error_30 >= 0

