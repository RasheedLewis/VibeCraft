"""Unit tests for clip planning functions."""

import pytest

from app.services.clip_planner import (
    _calculate_optimal_num_clips,
    get_clip_time_ranges,
    plan_clips_for_section,
)


class TestPlanClipsForSection:
    """Test plan_clips_for_section function."""

    def test_single_clip_short_section(self):
        """Test section that fits in one clip."""
        result = plan_clips_for_section(4.5, min_clip_duration_sec=3.0, max_clip_duration_sec=6.0)
        assert result == [4.5]
        assert sum(result) == 4.5

    def test_single_clip_exact_max(self):
        """Test section that exactly matches max clip duration."""
        result = plan_clips_for_section(6.0, min_clip_duration_sec=3.0, max_clip_duration_sec=6.0)
        assert result == [6.0]
        assert sum(result) == 6.0

    def test_multiple_clips_exact_fit(self):
        """Test section that divides evenly into max-duration clips."""
        result = plan_clips_for_section(18.0, min_clip_duration_sec=3.0, max_clip_duration_sec=6.0)
        assert result == [6.0, 6.0, 6.0]
        assert sum(result) == 18.0

    def test_multiple_clips_with_remainder(self):
        """Test section that needs max clips + one smaller clip."""
        result = plan_clips_for_section(15.0, min_clip_duration_sec=3.0, max_clip_duration_sec=6.0)
        assert result == [6.0, 6.0, 3.0]
        assert sum(result) == 15.0

    def test_complex_case_25_125_seconds(self):
        """Test the example from the user: 25.125 seconds."""
        result = plan_clips_for_section(25.125, min_clip_duration_sec=3.0, max_clip_duration_sec=6.0)
        # Should be 5 clips of ~5.025s each
        assert len(result) == 5
        assert abs(sum(result) - 25.125) < 0.001
        assert all(3.0 <= clip <= 6.0 for clip in result)

    def test_remainder_too_short_redistributes(self):
        """Test case where remainder is too short, needs redistribution."""
        # 25.125s: 4 clips of 6s = 24s, remaining 1.125s (too short)
        # Should redistribute to 5 clips of ~5.025s
        result = plan_clips_for_section(25.125, min_clip_duration_sec=3.0, max_clip_duration_sec=6.0)
        assert len(result) == 5
        assert abs(sum(result) - 25.125) < 0.001
        assert all(3.0 <= clip <= 6.0 for clip in result)

    def test_very_long_section(self):
        """Test a very long section."""
        result = plan_clips_for_section(60.0, min_clip_duration_sec=3.0, max_clip_duration_sec=6.0)
        # Should be 10 clips of 6s each
        assert result == [6.0] * 10
        assert sum(result) == 60.0

    def test_section_shorter_than_min(self):
        """Test section shorter than minimum clip duration."""
        # Should still return it, but log a warning
        result = plan_clips_for_section(2.0, min_clip_duration_sec=3.0, max_clip_duration_sec=6.0)
        assert result == [2.0]
        assert sum(result) == 2.0

    def test_edge_case_exact_min(self):
        """Test section exactly at minimum clip duration."""
        result = plan_clips_for_section(3.0, min_clip_duration_sec=3.0, max_clip_duration_sec=6.0)
        assert result == [3.0]
        assert sum(result) == 3.0

    def test_invalid_inputs(self):
        """Test invalid inputs raise errors."""
        with pytest.raises(ValueError, match="must be positive"):
            plan_clips_for_section(-1.0, 3.0, 6.0)
        
        with pytest.raises(ValueError, match="must be positive"):
            plan_clips_for_section(10.0, -1.0, 6.0)
        
        with pytest.raises(ValueError, match="must be <="):
            plan_clips_for_section(10.0, 6.0, 3.0)


class TestCalculateOptimalNumClips:
    """Test _calculate_optimal_num_clips helper function."""

    def test_simple_case(self):
        """Test simple case."""
        result = _calculate_optimal_num_clips(25.125, 3.0, 6.0)
        # 25.125 / 5 = 5.025 (within 3-6 range)
        assert result == 5

    def test_exact_division(self):
        """Test case that divides exactly."""
        result = _calculate_optimal_num_clips(18.0, 3.0, 6.0)
        # 18.0 / 3 = 6.0 (exactly max)
        assert result == 3

    def test_minimum_clips(self):
        """Test case requiring minimum number of clips."""
        result = _calculate_optimal_num_clips(7.0, 3.0, 6.0)
        # 7.0 / 2 = 3.5 (within range)
        assert result == 2


class TestGetClipTimeRanges:
    """Test get_clip_time_ranges function."""

    def test_simple_case(self):
        """Test simple case with exact durations."""
        result = get_clip_time_ranges(10.0, 15.0, [6.0, 6.0, 3.0])
        assert result == [(10.0, 16.0), (16.0, 22.0), (22.0, 25.0)]
        assert result[-1][1] == 10.0 + 15.0  # Last end = section start + duration

    def test_single_clip(self):
        """Test single clip."""
        result = get_clip_time_ranges(5.0, 4.5, [4.5])
        assert result == [(5.0, 9.5)]

    def test_mismatched_duration_adjusts(self):
        """Test case where clip durations don't sum to section duration."""
        result = get_clip_time_ranges(0.0, 15.0, [6.0, 6.0, 2.0])  # Sums to 14.0
        # Should adjust last clip to 3.0
        assert result == [(0.0, 6.0), (6.0, 12.0), (12.0, 15.0)]
        assert result[-1][1] == 15.0

    def test_complex_case(self):
        """Test complex case with many clips."""
        clip_durations = [5.025, 5.025, 5.025, 5.025, 5.025]
        result = get_clip_time_ranges(0.0, 25.125, clip_durations)
        assert len(result) == 5
        assert result[0][0] == 0.0
        assert abs(result[-1][1] - 25.125) < 0.001
        # Check no gaps or overlaps
        for i in range(len(result) - 1):
            assert abs(result[i][1] - result[i + 1][0]) < 0.001

