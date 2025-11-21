"""Unit tests for beat filter service.

Tests FFmpeg filter generation logic for beat-reactive effects - pure functions, fast.
Validates generate_beat_filter_expression() and generate_beat_filter_complex() in isolation.

Run with: pytest backend/tests/unit/test_beat_filters.py -v
Or from backend/: pytest tests/unit/test_beat_filters.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.beat_filters import (  # noqa: E402
    generate_beat_filter_complex,
    generate_beat_filter_expression,
)


class TestGenerateBeatFilterExpression:
    """Test beat filter expression generation."""

    def test_empty_beat_times_returns_empty(self):
        """Test that empty beat times returns empty string."""
        result = generate_beat_filter_expression([])
        assert result == ""

    def test_single_beat_flash_filter(self):
        """Test flash filter generation for single beat."""
        beat_times = [1.0]
        result = generate_beat_filter_expression(beat_times, filter_type="flash", frame_rate=24.0)
        
        assert "geq" in result
        assert "r+" in result or "r=" in result
        assert "g+" in result or "g=" in result
        assert "b+" in result or "b=" in result

    def test_multiple_beats_flash_filter(self):
        """Test flash filter generation for multiple beats."""
        beat_times = [1.0, 2.0, 3.0]
        result = generate_beat_filter_expression(beat_times, filter_type="flash", frame_rate=24.0)
        
        assert "geq" in result
        # Should contain OR conditions for multiple beats
        assert "||" in result or "n >=" in result

    def test_color_burst_filter(self):
        """Test color burst filter generation."""
        beat_times = [1.0]
        result = generate_beat_filter_expression(beat_times, filter_type="color_burst", frame_rate=24.0)
        
        assert "eq" in result
        assert "saturation" in result.lower()
        assert "brightness" in result.lower()

    def test_brightness_pulse_filter(self):
        """Test brightness pulse filter generation."""
        beat_times = [1.0]
        result = generate_beat_filter_expression(beat_times, filter_type="brightness_pulse", frame_rate=24.0)
        
        assert "eq" in result
        assert "brightness" in result.lower()

    def test_zoom_pulse_filter(self):
        """Test zoom pulse filter generation."""
        beat_times = [1.0]
        result = generate_beat_filter_expression(beat_times, filter_type="zoom_pulse", frame_rate=24.0)
        
        assert "scale" in result.lower()

    def test_invalid_filter_type_defaults_to_flash(self):
        """Test that invalid filter type defaults to flash."""
        beat_times = [1.0]
        result = generate_beat_filter_expression(beat_times, filter_type="invalid_type")
        
        assert "geq" in result  # Flash uses geq

    def test_frame_rate_affects_frame_calculation(self):
        """Test that frame rate affects frame number calculations."""
        beat_times = [1.0]
        result_24fps = generate_beat_filter_expression(beat_times, frame_rate=24.0)
        result_30fps = generate_beat_filter_expression(beat_times, frame_rate=30.0)
        
        # Frame numbers should be different
        assert result_24fps != result_30fps

    def test_tolerance_affects_frame_range(self):
        """Test that tolerance affects the frame range."""
        beat_times = [1.0]
        result_20ms = generate_beat_filter_expression(beat_times, tolerance_ms=20.0, frame_rate=24.0)
        result_50ms = generate_beat_filter_expression(beat_times, tolerance_ms=50.0, frame_rate=24.0)
        
        # Different tolerances should produce different frame ranges
        assert result_20ms != result_50ms


class TestGenerateBeatFilterComplex:
    """Test beat filter complex generation."""

    def test_empty_beat_times_returns_empty_list(self):
        """Test that empty beat times returns empty list."""
        result = generate_beat_filter_complex([])
        assert result == []

    def test_single_beat_flash_filter_complex(self):
        """Test flash filter complex for single beat."""
        beat_times = [1.0]
        result = generate_beat_filter_complex(beat_times, filter_type="flash", frame_rate=24.0)
        
        assert len(result) == 1
        assert "select" in result[0]
        assert "between(t" in result[0]
        assert "geq" in result[0]

    def test_multiple_beats_flash_filter_complex(self):
        """Test flash filter complex for multiple beats."""
        beat_times = [1.0, 2.0, 3.0]
        result = generate_beat_filter_complex(beat_times, filter_type="flash", frame_rate=24.0)
        
        assert len(result) == 3
        for filter_str in result:
            assert "select" in filter_str
            assert "between(t" in filter_str

    def test_color_burst_filter_complex(self):
        """Test color burst filter complex."""
        beat_times = [1.0]
        result = generate_beat_filter_complex(beat_times, filter_type="color_burst", frame_rate=24.0)
        
        assert len(result) == 1
        assert "eq" in result[0]
        assert "saturation" in result[0].lower()

    def test_unsupported_filter_type_returns_empty(self):
        """Test that unsupported filter types return empty list."""
        beat_times = [1.0]
        result = generate_beat_filter_complex(beat_times, filter_type="zoom_pulse")
        
        # zoom_pulse is not implemented in filter_complex, should return empty
        assert result == []

    def test_tolerance_affects_time_range(self):
        """Test that tolerance affects the time range in filter complex."""
        beat_times = [1.0]
        result_20ms = generate_beat_filter_complex(beat_times, tolerance_ms=20.0)
        result_50ms = generate_beat_filter_complex(beat_times, tolerance_ms=50.0)
        
        # Different tolerances should produce different time ranges
        assert result_20ms != result_50ms

    def test_negative_beat_time_handled(self):
        """Test that negative beat times are handled (clamped to 0)."""
        beat_times = [-0.1, 1.0]
        result = generate_beat_filter_complex(beat_times, filter_type="flash")
        
        # Should still generate filters, with start_time clamped
        assert len(result) == 2
        assert "between(t,0" in result[0] or "between(t,0.0" in result[0]

