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
    convert_beat_times_to_frames,
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


class TestConvertBeatTimesToFrames:
    """Test frame-accurate beat time conversion.
    
    Justification: Frame-accurate timing is critical for beat sync effects.
    This ensures effects trigger at the correct frame indices.
    """

    def test_convert_single_beat(self):
        """Test conversion of single beat time to frame."""
        beat_times = [1.0]
        frames = convert_beat_times_to_frames(beat_times, video_fps=24.0)
        
        assert len(frames) == 1
        assert frames[0] == 24  # 1.0s * 24fps = frame 24

    def test_convert_multiple_beats(self):
        """Test conversion of multiple beat times."""
        beat_times = [0.0, 0.5, 1.0, 1.5, 2.0]
        frames = convert_beat_times_to_frames(beat_times, video_fps=24.0)
        
        assert len(frames) == 5
        assert frames[0] == 0   # 0.0s
        assert frames[1] == 12  # 0.5s * 24fps
        assert frames[2] == 24  # 1.0s * 24fps
        assert frames[3] == 36  # 1.5s * 24fps
        assert frames[4] == 48  # 2.0s * 24fps

    def test_video_start_time_offset(self):
        """Test conversion with video start time offset."""
        beat_times = [5.0, 6.0, 7.0]
        frames = convert_beat_times_to_frames(beat_times, video_fps=24.0, video_start_time=5.0)
        
        # Beats at 5.0s, 6.0s, 7.0s relative to song
        # Video starts at 5.0s, so relative times are 0.0s, 1.0s, 2.0s
        assert len(frames) == 3
        assert frames[0] == 0   # 0.0s relative
        assert frames[1] == 24  # 1.0s relative
        assert frames[2] == 48  # 2.0s relative

    def test_beats_before_video_start_filtered(self):
        """Test that beats before video start are filtered out."""
        beat_times = [1.0, 2.0, 3.0]
        frames = convert_beat_times_to_frames(beat_times, video_fps=24.0, video_start_time=2.5)
        
        # Only beats at 2.0s and 3.0s should be included (after video start)
        assert len(frames) == 1  # Only 3.0s beat
        assert frames[0] == 12  # (3.0 - 2.5) * 24fps = 12 frames

    def test_different_fps_values(self):
        """Test conversion with different FPS values."""
        beat_times = [1.0]
        frames_24fps = convert_beat_times_to_frames(beat_times, video_fps=24.0)
        frames_30fps = convert_beat_times_to_frames(beat_times, video_fps=30.0)
        
        assert frames_24fps[0] == 24
        assert frames_30fps[0] == 30

    def test_rounding_to_nearest_frame(self):
        """Test that beat times round to nearest frame."""
        beat_times = [0.521]  # Not exactly on a frame boundary at 24fps
        frames = convert_beat_times_to_frames(beat_times, video_fps=24.0)
        
        # 0.521s * 24fps = 12.504 frames, should round to 13
        assert frames[0] == 13


class TestEffectParameters:
    """Test effect parameter customization.
    
    Justification: Effect parameters allow fine-tuning of visual effects.
    This ensures parameters are correctly applied to filter generation.
    """

    def test_flash_with_custom_intensity(self):
        """Test flash filter with custom intensity parameter."""
        beat_times = [1.0]
        result_default = generate_beat_filter_expression(beat_times, filter_type="flash")
        result_custom = generate_beat_filter_expression(
            beat_times, 
            filter_type="flash",
            effect_params={"intensity": 100}
        )
        
        # Custom intensity should produce different filter
        assert result_default != result_custom
        assert "100" in result_custom  # Should contain custom intensity value

    def test_color_burst_with_custom_params(self):
        """Test color burst with custom saturation and brightness."""
        beat_times = [1.0]
        result = generate_beat_filter_expression(
            beat_times,
            filter_type="color_burst",
            effect_params={"saturation": 2.0, "brightness": 0.2}
        )
        
        assert "2.0" in result or "2" in result  # Custom saturation
        assert "0.2" in result  # Custom brightness

    def test_zoom_pulse_with_custom_zoom(self):
        """Test zoom pulse with custom zoom amount."""
        beat_times = [1.0]
        result = generate_beat_filter_expression(
            beat_times,
            filter_type="zoom_pulse",
            effect_params={"zoom": 1.1}  # 10% zoom
        )
        
        assert "1.1" in result  # Custom zoom factor

    def test_glitch_effect_with_intensity(self):
        """Test glitch effect with custom intensity parameter."""
        beat_times = [1.0]
        result = generate_beat_filter_expression(
            beat_times,
            filter_type="glitch",
            effect_params={"intensity": 0.5}
        )
        
        # Glitch effect should contain pixel shift values
        assert "p(X+" in result or "p(X-" in result  # Channel shift
        assert "5" in result  # 0.5 * 10 = 5 pixels

    def test_glitch_filter_complex(self):
        """Test glitch effect in filter complex generation."""
        beat_times = [1.0, 2.0]
        result = generate_beat_filter_complex(
            beat_times,
            filter_type="glitch",
            effect_params={"intensity": 0.4}
        )
        
        assert len(result) == 2  # One filter per beat
        assert "geq" in result[0]  # Glitch uses geq filter
        assert "p(X+" in result[0] or "p(X-" in result[0]  # Channel shift

