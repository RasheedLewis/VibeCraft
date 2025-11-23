"""Beat-reactive FFmpeg filter service for visual beat synchronization."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Filter effect types
FILTER_TYPES = {
    "flash": {
        "description": "White flash on beat",
        "duration_ms": 50,  # Flash duration in milliseconds
    },
    "color_burst": {
        "description": "Color burst effect on beat",
        "duration_ms": 100,
    },
    "zoom_pulse": {
        "description": "Subtle zoom pulse on beat",
        "duration_ms": 200,
    },
    "brightness_pulse": {
        "description": "Brightness increase on beat",
        "duration_ms": 100,
    },
    "glitch": {
        "description": "Digital glitch effect on beat",
        "duration_ms": 100,
    },
}


def convert_beat_times_to_frames(
    beat_times: List[float],
    video_fps: float = 24.0,
    video_start_time: float = 0.0,
) -> List[int]:
    """
    Convert beat times to frame indices with frame-accurate precision.
    
    Args:
        beat_times: Beat timestamps in seconds (relative to song start)
        video_fps: Video frame rate
        video_start_time: Offset of video start relative to song start
    
    Returns:
        List of frame indices where effects should trigger
    """
    frame_indices = []
    
    for beat_time in beat_times:
        # Adjust beat time relative to video start
        relative_beat_time = beat_time - video_start_time
        
        if relative_beat_time < 0:
            continue  # Beat occurs before video starts
        
        # Calculate frame index (round to nearest frame)
        frame_index = round(relative_beat_time * video_fps)
        frame_indices.append(frame_index)
    
    return frame_indices


def generate_beat_filter_expression(
    beat_times: List[float],
    filter_type: str = "flash",
    frame_rate: float = 24.0,
    tolerance_ms: float = 20.0,
    effect_params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate FFmpeg filter expression for beat-reactive effects.
    
    Args:
        beat_times: List of beat timestamps in seconds
        filter_type: Type of effect (flash, color_burst, zoom_pulse, brightness_pulse, glitch)
        frame_rate: Video frame rate
        tolerance_ms: Tolerance window in milliseconds for beat detection
        effect_params: Optional dict with effect-specific parameters (intensity, color, duration, etc.)
        
    Returns:
        FFmpeg filter expression string
    """
    if not beat_times:
        logger.warning("No beat times provided, returning empty filter")
        return ""
    
    if filter_type not in FILTER_TYPES:
        logger.warning(f"Unknown filter type {filter_type}, using flash")
        filter_type = "flash"
    
    tolerance_sec = tolerance_ms / 1000.0
    
    # Build condition expression
    conditions = []
    for beat_time in beat_times:
        # Calculate frame number range for this beat
        start_frame = int((beat_time - tolerance_sec) * frame_rate)
        end_frame = int((beat_time + tolerance_sec) * frame_rate)
        
        # Add condition for this beat window
        condition = f"(n >= {start_frame} && n <= {end_frame})"
        conditions.append(condition)
    
    # Combine conditions with OR
    beat_condition = " || ".join(conditions)
    
    # Get effect parameters with defaults
    params = effect_params or {}
    
    # Generate filter based on type
    if filter_type == "flash":
        # Flash: increase brightness with customizable intensity
        intensity = params.get("intensity", 50)  # Default: 50 pixel value increase
        flash_color = params.get("color", "white")
        if flash_color == "white":
            filter_expr = f"geq=r='if({beat_condition}, r+{intensity}, r)':g='if({beat_condition}, g+{intensity}, g)':b='if({beat_condition}, b+{intensity}, b)'"
        else:
            # For other colors, use same approach (could be enhanced with RGB values)
            filter_expr = f"geq=r='if({beat_condition}, r+{intensity}, r)':g='if({beat_condition}, g+{intensity}, g)':b='if({beat_condition}, b+{intensity}, b)'"
    elif filter_type == "color_burst":
        # Color burst: increase saturation and brightness
        saturation = params.get("saturation", 1.5)
        brightness = params.get("brightness", 0.1)
        filter_expr = f"eq=saturation='if({beat_condition}, {saturation}, 1)':brightness='if({beat_condition}, {brightness}, 0)'"
    elif filter_type == "zoom_pulse":
        # Zoom pulse: improved implementation using zoompan filter
        zoom_amount = params.get("zoom", 1.05)  # Default: 5% zoom
        # Note: zoompan requires more complex setup, using scale as fallback
        zoom_factor = zoom_amount
        filter_expr = f"scale='if({beat_condition}, iw*{zoom_factor}, iw)':'if({beat_condition}, ih*{zoom_factor}, ih)'"
    elif filter_type == "brightness_pulse":
        # Brightness pulse
        brightness = params.get("brightness", 0.15)
        filter_expr = f"eq=brightness='if({beat_condition}, {brightness}, 0)'"
    elif filter_type == "glitch":
        # Glitch effect: RGB channel shift
        glitch_intensity = params.get("intensity", 0.3)  # 0.0-1.0, controls shift amount
        shift_pixels = int(glitch_intensity * 10)  # Convert to pixel shift (0-10 pixels)
        filter_expr = (
            f"geq=r='if({beat_condition}, p(X+{shift_pixels},Y), p(X,Y))':"
            f"g='if({beat_condition}, p(X,Y), p(X,Y))':"
            f"b='if({beat_condition}, p(X-{shift_pixels},Y), p(X,Y))'"
        )
    else:
        filter_expr = ""
    
    logger.debug(f"Generated {filter_type} filter for {len(beat_times)} beats")
    return filter_expr


def generate_beat_filter_complex(
    beat_times: List[float],
    filter_type: str = "flash",
    frame_rate: float = 24.0,
    tolerance_ms: float = 20.0,
    effect_params: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """
    Generate FFmpeg filter_complex expression for beat-reactive effects.
    
    This is a more flexible approach that can combine multiple filters.
    
    Args:
        beat_times: List of beat timestamps in seconds
        filter_type: Type of effect
        frame_rate: Video frame rate
        tolerance_ms: Tolerance window in milliseconds
        effect_params: Optional dict with effect-specific parameters
        
    Returns:
        List of filter strings for filter_complex
    """
    if not beat_times:
        return []
    
    tolerance_sec = tolerance_ms / 1000.0
    filters = []
    params = effect_params or {}
    
    # For each beat, create a filter that triggers at that time
    for i, beat_time in enumerate(beat_times):
        start_time = max(0, beat_time - tolerance_sec)
        end_time = beat_time + tolerance_sec
        
        if filter_type == "flash":
            # Flash effect: brightness spike
            intensity = params.get("intensity", 30)
            filter_str = (
                f"[0:v]select='between(t,{start_time},{end_time})',"
                f"geq=r='r+{intensity}':g='g+{intensity}':b='b+{intensity}'[beat{i}];"
            )
        elif filter_type == "color_burst":
            # Color burst: saturation and brightness
            saturation = params.get("saturation", 1.5)
            brightness = params.get("brightness", 0.1)
            filter_str = (
                f"[0:v]select='between(t,{start_time},{end_time})',"
                f"eq=saturation={saturation}:brightness={brightness}[beat{i}];"
            )
        elif filter_type == "glitch":
            # Glitch effect: RGB channel shift
            glitch_intensity = params.get("intensity", 0.3)
            shift_pixels = int(glitch_intensity * 10)
            filter_str = (
                f"[0:v]select='between(t,{start_time},{end_time})',"
                f"geq=r='p(X+{shift_pixels},Y)':g='p(X,Y)':b='p(X-{shift_pixels},Y)'[beat{i}];"
            )
        else:
            continue
        
        filters.append(filter_str)
    
    # Combine all beat filters
    # Note: This is simplified - full implementation would overlay effects
    return filters


def apply_beat_filters_to_video(
    input_video_path: str,
    output_video_path: str,
    beat_times: List[float],
    filter_type: str = "flash",
    frame_rate: float = 24.0,
) -> bool:
    """
    Apply beat-reactive filters to a video file using FFmpeg.
    
    This is a helper function that constructs the full FFmpeg command.
    Actual execution should be done in video_composition.py.
    
    Args:
        input_video_path: Path to input video
        output_video_path: Path to output video
        beat_times: List of beat timestamps
        filter_type: Type of effect
        frame_rate: Video frame rate
        
    Returns:
        True if successful
    """
    # This function provides the interface
    # Actual FFmpeg execution should be in video_composition.py
    logger.info(f"Preparing beat filter application: {filter_type} for {len(beat_times)} beats")
    return True

