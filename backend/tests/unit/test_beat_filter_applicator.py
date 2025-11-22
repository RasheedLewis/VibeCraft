"""Unit tests for beat filter applicator.

Tests the centralized BeatFilterApplicator class that handles all beat-synced visual effects.
Validates all 5 effect types, test mode, tolerance, and chunking logic.

Run with: pytest backend/tests/unit/test_beat_filter_applicator.py -v
"""

import os
from unittest.mock import Mock, patch

import pytest

from app.core.config import BeatEffectConfig
from app.services.beat_filter_applicator import BeatFilterApplicator


def create_test_config(**overrides):
    """Create a test BeatEffectConfig with default values."""
    # Use model_validate to create config with overrides
    defaults = {
        "flash_intensity": 50.0,
        "glitch_intensity": 0.3,
        "color_burst_saturation": 1.5,
        "color_burst_brightness": 0.1,
        "brightness_pulse_amount": 0.15,
        "zoom_pulse_amount": 1.05,
        "tolerance_ms": 20.0,
        "test_mode_enabled": False,
        "test_mode_tolerance_multiplier": 3.0,
        "test_mode_flash_intensity_multiplier": 3.0,
        "test_mode_glitch_intensity": 0.8,
        "test_mode_color_burst_saturation": 2.0,
        "test_mode_color_burst_brightness": 0.2,
        "test_mode_brightness_pulse": 0.3,
        "test_mode_zoom_pulse": 1.15,
    }
    defaults.update(overrides)
    # Create a mock config object instead of using Pydantic
    config = Mock(spec=BeatEffectConfig)
    for key, value in defaults.items():
        setattr(config, key, value)
    return config


class TestBeatFilterApplicatorInitialization:
    """Test BeatFilterApplicator initialization."""

    @patch("app.services.beat_filter_applicator.get_beat_effect_config")
    def test_default_config_used_when_none_provided(self, mock_get_config):
        """Test that default config is used when none provided."""
        mock_config = create_test_config()
        mock_get_config.return_value = mock_config
        applicator = BeatFilterApplicator()
        assert applicator.effect_config is not None
        assert isinstance(applicator.effect_config, BeatEffectConfig)

    def test_custom_config_used_when_provided(self):
        """Test that custom config is used when provided."""
        custom_config = create_test_config(flash_intensity=100.0)
        applicator = BeatFilterApplicator(effect_config=custom_config)
        assert applicator.effect_config.flash_intensity == 100.0

    @patch.dict(os.environ, {"BEAT_EFFECT_TEST_MODE": "true"})
    @patch("app.services.beat_filter_applicator.get_beat_effect_config")
    def test_test_mode_from_env_var(self, mock_get_config):
        """Test that test mode is enabled from environment variable."""
        mock_config = create_test_config()
        mock_get_config.return_value = mock_config
        applicator = BeatFilterApplicator()
        assert applicator.test_mode is True

    @patch.dict(os.environ, {"BEAT_EFFECT_TEST_MODE": "false"})
    def test_test_mode_explicitly_false(self):
        """Test that test mode can be explicitly set to False."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config, test_mode=False)
        assert applicator.test_mode is False

    def test_test_mode_explicitly_true(self):
        """Test that test mode can be explicitly set to True."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config, test_mode=True)
        assert applicator.test_mode is True


class TestGetToleranceSec:
    """Test tolerance calculation."""

    def test_normal_mode_tolerance(self):
        """Test tolerance in normal mode uses config value."""
        config = create_test_config(tolerance_ms=20.0)
        applicator = BeatFilterApplicator(effect_config=config, test_mode=False)
        assert applicator.get_tolerance_sec() == 0.02  # 20ms / 1000

    def test_test_mode_tolerance_multiplier(self):
        """Test tolerance in test mode uses multiplier."""
        config = create_test_config(tolerance_ms=20.0, test_mode_tolerance_multiplier=3.0)
        applicator = BeatFilterApplicator(effect_config=config, test_mode=True)
        expected = (20.0 * 3.0) / 1000.0  # 60ms / 1000
        assert applicator.get_tolerance_sec() == expected


class TestFlashFilter:
    """Test flash effect filter application."""

    def test_flash_filter_normal_mode(self):
        """Test flash filter uses correct intensity in normal mode."""
        config = create_test_config(flash_intensity=50.0)
        applicator = BeatFilterApplicator(effect_config=config, test_mode=False)
        mock_stream = Mock()
        
        result = applicator.apply_flash_filter(mock_stream, "min(1,condition)")
        
        mock_stream.filter.assert_called_once()
        call_args = mock_stream.filter.call_args
        assert call_args[0][0] == "geq"
        assert "r+if(min(1,condition),50,0)" in call_args[1]["r"]
        assert "g+if(min(1,condition),50,0)" in call_args[1]["g"]
        assert "b+if(min(1,condition),50,0)" in call_args[1]["b"]

    def test_flash_filter_test_mode_multiplier(self):
        """Test flash filter multiplies intensity in test mode."""
        config = create_test_config(
            flash_intensity=50.0,
            test_mode_flash_intensity_multiplier=3.0
        )
        applicator = BeatFilterApplicator(effect_config=config, test_mode=True)
        mock_stream = Mock()
        
        result = applicator.apply_flash_filter(mock_stream, "min(1,condition)")
        
        call_args = mock_stream.filter.call_args
        # Should be 50 * 3 = 150
        assert "r+if(min(1,condition),150,0)" in call_args[1]["r"]


class TestGlitchFilter:
    """Test glitch effect filter application."""

    def test_glitch_filter_normal_mode(self):
        """Test glitch filter uses correct intensity in normal mode."""
        config = create_test_config(glitch_intensity=0.3)
        applicator = BeatFilterApplicator(effect_config=config, test_mode=False)
        mock_stream = Mock()
        
        result = applicator.apply_glitch_filter(mock_stream, "min(1,condition)")
        
        call_args = mock_stream.filter.call_args
        assert call_args[0][0] == "geq"
        # shift_pixels = 0.3 * 10 = 3
        assert "p(X+3,Y)" in call_args[1]["r"]
        assert "p(X-3,Y)" in call_args[1]["b"]

    def test_glitch_filter_test_mode(self):
        """Test glitch filter uses test mode intensity."""
        config = create_test_config(
            glitch_intensity=0.3,
            test_mode_glitch_intensity=0.8
        )
        applicator = BeatFilterApplicator(effect_config=config, test_mode=True)
        mock_stream = Mock()
        
        result = applicator.apply_glitch_filter(mock_stream, "min(1,condition)")
        
        call_args = mock_stream.filter.call_args
        # shift_pixels = 0.8 * 10 = 8
        assert "p(X+8,Y)" in call_args[1]["r"]
        assert "p(X-8,Y)" in call_args[1]["b"]


class TestColorBurstFilter:
    """Test color burst effect filter application."""

    def test_color_burst_filter_normal_mode(self):
        """Test color burst filter uses correct values in normal mode."""
        config = create_test_config(
            color_burst_saturation=1.5,
            color_burst_brightness=0.1
        )
        applicator = BeatFilterApplicator(effect_config=config, test_mode=False)
        mock_stream = Mock()
        
        result = applicator.apply_color_burst_filter(mock_stream, "min(1,condition)")
        
        call_args = mock_stream.filter.call_args
        assert call_args[0][0] == "eq"
        assert "if(min(1,condition),1.5,1)" in call_args[1]["saturation"]
        assert "if(min(1,condition),0.1,0)" in call_args[1]["brightness"]

    def test_color_burst_filter_test_mode(self):
        """Test color burst filter uses test mode values."""
        config = create_test_config(
            color_burst_saturation=1.5,
            color_burst_brightness=0.1,
            test_mode_color_burst_saturation=2.0,
            test_mode_color_burst_brightness=0.2
        )
        applicator = BeatFilterApplicator(effect_config=config, test_mode=True)
        mock_stream = Mock()
        
        result = applicator.apply_color_burst_filter(mock_stream, "min(1,condition)")
        
        call_args = mock_stream.filter.call_args
        assert "if(min(1,condition),2.0,1)" in call_args[1]["saturation"]
        assert "if(min(1,condition),0.2,0)" in call_args[1]["brightness"]


class TestBrightnessPulseFilter:
    """Test brightness pulse effect filter application."""

    def test_brightness_pulse_filter_normal_mode(self):
        """Test brightness pulse filter uses correct value in normal mode."""
        config = create_test_config(brightness_pulse_amount=0.15)
        applicator = BeatFilterApplicator(effect_config=config, test_mode=False)
        mock_stream = Mock()
        
        result = applicator.apply_brightness_pulse_filter(mock_stream, "min(1,condition)")
        
        call_args = mock_stream.filter.call_args
        assert call_args[0][0] == "eq"
        assert "if(min(1,condition),0.15,0)" in call_args[1]["brightness"]

    def test_brightness_pulse_filter_test_mode(self):
        """Test brightness pulse filter uses test mode value."""
        config = create_test_config(
            brightness_pulse_amount=0.15,
            test_mode_brightness_pulse=0.3
        )
        applicator = BeatFilterApplicator(effect_config=config, test_mode=True)
        mock_stream = Mock()
        
        result = applicator.apply_brightness_pulse_filter(mock_stream, "min(1,condition)")
        
        call_args = mock_stream.filter.call_args
        assert "if(min(1,condition),0.3,0)" in call_args[1]["brightness"]


class TestZoomPulseFilter:
    """Test zoom pulse effect filter application."""

    def test_zoom_pulse_filter_normal_mode(self):
        """Test zoom pulse filter uses correct value in normal mode."""
        config = create_test_config(zoom_pulse_amount=1.05)
        applicator = BeatFilterApplicator(effect_config=config, test_mode=False)
        mock_stream = Mock()
        
        result = applicator.apply_zoom_pulse_filter(mock_stream, "min(1,condition)")
        
        call_args = mock_stream.filter.call_args
        assert call_args[0][0] == "scale"
        assert "if(min(1,condition),1.05,1)" in call_args[1]["w"]
        assert "if(min(1,condition),1.05,1)" in call_args[1]["h"]

    def test_zoom_pulse_filter_test_mode(self):
        """Test zoom pulse filter uses test mode value."""
        config = create_test_config(
            zoom_pulse_amount=1.05,
            test_mode_zoom_pulse=1.15
        )
        applicator = BeatFilterApplicator(effect_config=config, test_mode=True)
        mock_stream = Mock()
        
        result = applicator.apply_zoom_pulse_filter(mock_stream, "min(1,condition)")
        
        call_args = mock_stream.filter.call_args
        assert "if(min(1,condition),1.15,1)" in call_args[1]["w"]


class TestApplyFilter:
    """Test the main apply_filter method that routes to specific filters."""

    def test_apply_filter_flash(self):
        """Test apply_filter routes to flash filter."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        mock_stream = Mock()
        
        with patch.object(applicator, 'apply_flash_filter') as mock_flash:
            mock_flash.return_value = mock_stream
            result = applicator.apply_filter(mock_stream, "condition", "flash")
            
            mock_flash.assert_called_once_with(mock_stream, "condition")

    def test_apply_filter_glitch(self):
        """Test apply_filter routes to glitch filter."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        mock_stream = Mock()
        
        with patch.object(applicator, 'apply_glitch_filter') as mock_glitch:
            mock_glitch.return_value = mock_stream
            result = applicator.apply_filter(mock_stream, "condition", "glitch")
            
            mock_glitch.assert_called_once_with(mock_stream, "condition")

    def test_apply_filter_color_burst(self):
        """Test apply_filter routes to color_burst filter."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        mock_stream = Mock()
        
        with patch.object(applicator, 'apply_color_burst_filter') as mock_color:
            mock_color.return_value = mock_stream
            result = applicator.apply_filter(mock_stream, "condition", "color_burst")
            
            mock_color.assert_called_once_with(mock_stream, "condition")

    def test_apply_filter_brightness_pulse(self):
        """Test apply_filter routes to brightness_pulse filter."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        mock_stream = Mock()
        
        with patch.object(applicator, 'apply_brightness_pulse_filter') as mock_bright:
            mock_bright.return_value = mock_stream
            result = applicator.apply_filter(mock_stream, "condition", "brightness_pulse")
            
            mock_bright.assert_called_once_with(mock_stream, "condition")

    def test_apply_filter_zoom_pulse(self):
        """Test apply_filter routes to zoom_pulse filter."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        mock_stream = Mock()
        
        with patch.object(applicator, 'apply_zoom_pulse_filter') as mock_zoom:
            mock_zoom.return_value = mock_stream
            result = applicator.apply_filter(mock_stream, "condition", "zoom_pulse")
            
            mock_zoom.assert_called_once_with(mock_stream, "condition")

    def test_apply_filter_unknown_type_returns_original(self):
        """Test apply_filter returns original stream for unknown filter type."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        mock_stream = Mock()
        
        result = applicator.apply_filter(mock_stream, "condition", "unknown_type")
        
        assert result == mock_stream
        # Should not call any filter methods
        assert not hasattr(mock_stream, 'filter') or not mock_stream.filter.called


class TestShouldChunk:
    """Test chunking logic for large beat counts."""

    def test_should_chunk_flash_large_count(self):
        """Test should_chunk returns True for flash with >200 beats."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        assert applicator.should_chunk("flash", 201) is True
        assert applicator.should_chunk("flash", 200) is False
        assert applicator.should_chunk("flash", 199) is False

    def test_should_chunk_glitch_large_count(self):
        """Test should_chunk returns True for glitch with >200 beats."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        assert applicator.should_chunk("glitch", 201) is True
        assert applicator.should_chunk("glitch", 200) is False

    def test_should_chunk_other_effects_never_chunk(self):
        """Test should_chunk returns False for other effect types."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        assert applicator.should_chunk("color_burst", 1000) is False
        assert applicator.should_chunk("brightness_pulse", 1000) is False
        assert applicator.should_chunk("zoom_pulse", 1000) is False

    def test_should_chunk_custom_chunk_size(self):
        """Test should_chunk respects custom chunk_size parameter."""
        config = create_test_config()
        applicator = BeatFilterApplicator(effect_config=config)
        assert applicator.should_chunk("flash", 101, chunk_size=100) is True
        assert applicator.should_chunk("flash", 100, chunk_size=100) is False

