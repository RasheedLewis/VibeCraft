"""Beat filter applicator for centralized effect application logic."""

import logging
from typing import Optional

from app.core.config import BeatEffectConfig, get_beat_effect_config

logger = logging.getLogger(__name__)


class BeatFilterApplicator:
    """Centralized beat filter application logic."""

    def __init__(self, effect_config: Optional[BeatEffectConfig] = None, test_mode: Optional[bool] = None):
        """Initialize applicator with config and test mode."""
        self.effect_config = effect_config or get_beat_effect_config()
        # Use config test mode if not explicitly provided
        if test_mode is None:
            import os
            test_mode = (
                self.effect_config.test_mode_enabled
                or os.getenv("BEAT_EFFECT_TEST_MODE", "false").lower() == "true"
            )
        self.test_mode = test_mode

    def get_tolerance_sec(self) -> float:
        """Get tolerance in seconds (exaggerated in test mode)."""
        if self.test_mode:
            return (
                self.effect_config.tolerance_ms
                * self.effect_config.test_mode_tolerance_multiplier
                / 1000.0
            )
        return self.effect_config.tolerance_ms / 1000.0

    def apply_flash_filter(self, video_stream, beat_condition: str) -> any:
        """Apply flash effect filter."""
        if self.test_mode:
            intensity_multiplier = self.effect_config.test_mode_flash_intensity_multiplier
        else:
            intensity_multiplier = 1.0
        intensity = int(self.effect_config.flash_intensity * intensity_multiplier)
        return video_stream.filter(
            "geq",
            r=f"r+if({beat_condition},{intensity},0)",
            g=f"g+if({beat_condition},{intensity},0)",
            b=f"b+if({beat_condition},{intensity},0)",
        )

    def apply_glitch_filter(self, video_stream, beat_condition: str) -> any:
        """Apply glitch effect filter."""
        if self.test_mode:
            glitch_intensity = self.effect_config.test_mode_glitch_intensity
        else:
            glitch_intensity = self.effect_config.glitch_intensity
        shift_pixels = int(glitch_intensity * 10)
        return video_stream.filter(
            "geq",
            r=f"if({beat_condition},p(X+{shift_pixels},Y),p(X,Y))",
            g="p(X,Y)",
            b=f"if({beat_condition},p(X-{shift_pixels},Y),p(X,Y))",
        )

    def apply_color_burst_filter(self, video_stream, beat_condition: str) -> any:
        """Apply color burst effect filter."""
        if self.test_mode:
            saturation = self.effect_config.test_mode_color_burst_saturation
            brightness = self.effect_config.test_mode_color_burst_brightness
        else:
            saturation = self.effect_config.color_burst_saturation
            brightness = self.effect_config.color_burst_brightness
        return video_stream.filter(
            "eq",
            saturation=f"if({beat_condition},{saturation},1)",
            brightness=f"if({beat_condition},{brightness},0)",
        )

    def apply_brightness_pulse_filter(self, video_stream, beat_condition: str) -> any:
        """Apply brightness pulse effect filter."""
        if self.test_mode:
            brightness = self.effect_config.test_mode_brightness_pulse
        else:
            brightness = self.effect_config.brightness_pulse_amount
        return video_stream.filter(
            "eq",
            brightness=f"if({beat_condition},{brightness},0)",
        )

    def apply_zoom_pulse_filter(self, video_stream, beat_condition: str) -> any:
        """Apply zoom pulse effect filter."""
        if self.test_mode:
            zoom = self.effect_config.test_mode_zoom_pulse
        else:
            zoom = self.effect_config.zoom_pulse_amount
        return video_stream.filter(
            "scale",
            w=f"iw*if({beat_condition},{zoom},1)",
            h=f"ih*if({beat_condition},{zoom},1)",
        )

    def apply_filter(
        self,
        video_stream: any,
        beat_condition: str,
        filter_type: str,
    ) -> any:
        """
        Apply a beat filter to video stream based on filter type.
        
        Args:
            video_stream: FFmpeg video stream
            beat_condition: Beat condition expression (e.g., "min(1,condition1+condition2)")
            filter_type: Type of effect (flash, glitch, color_burst, brightness_pulse, zoom_pulse)
            
        Returns:
            Filtered video stream
        """
        if filter_type == "flash":
            return self.apply_flash_filter(video_stream, beat_condition)
        elif filter_type == "glitch":
            return self.apply_glitch_filter(video_stream, beat_condition)
        elif filter_type == "color_burst":
            return self.apply_color_burst_filter(video_stream, beat_condition)
        elif filter_type == "brightness_pulse":
            return self.apply_brightness_pulse_filter(video_stream, beat_condition)
        elif filter_type == "zoom_pulse":
            return self.apply_zoom_pulse_filter(video_stream, beat_condition)
        else:
            logger.warning(f"Unknown filter type: {filter_type}, skipping beat effects")
            return video_stream

    def should_chunk(self, filter_type: str, beat_count: int, chunk_size: int = 200) -> bool:
        """Determine if effect needs chunking for large beat counts."""
        return beat_count > chunk_size and filter_type in ["flash", "glitch"]

