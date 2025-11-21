"""Beat-reactive FFmpeg filter service for visual beat synchronization."""

import logging
from typing import List

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
}


def generate_beat_filter_expression(
    beat_times: List[float],
    filter_type: str = "flash",
    frame_rate: float = 24.0,
    tolerance_ms: float = 20.0,
) -> str:
    """
    Generate FFmpeg filter expression for beat-reactive effects.
    
    Args:
        beat_times: List of beat timestamps in seconds
        filter_type: Type of effect (flash, color_burst, zoom_pulse, brightness_pulse)
        frame_rate: Video frame rate
        tolerance_ms: Tolerance window in milliseconds for beat detection
        
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
    
    # Generate filter based on type
    if filter_type == "flash":
        # White flash: increase brightness and add white overlay
        filter_expr = f"geq=r='if({beat_condition}, r+50, r)':g='if({beat_condition}, g+50, g)':b='if({beat_condition}, b+50, b)'"
    elif filter_type == "color_burst":
        # Color burst: increase saturation and brightness
        filter_expr = f"eq=saturation='if({beat_condition}, 1.5, 1)':brightness='if({beat_condition}, 0.1, 0)'"
    elif filter_type == "zoom_pulse":
        # Zoom pulse: subtle scale increase
        # Note: This requires crop/scale filter, more complex
        filter_expr = f"scale='if({beat_condition}, iw*1.02, iw)':'if({beat_condition}, ih*1.02, ih)'"
    elif filter_type == "brightness_pulse":
        # Brightness pulse
        filter_expr = f"eq=brightness='if({beat_condition}, 0.15, 0)'"
    else:
        filter_expr = ""
    
    logger.debug(f"Generated {filter_type} filter for {len(beat_times)} beats")
    return filter_expr


def generate_beat_filter_complex(
    beat_times: List[float],
    filter_type: str = "flash",
    frame_rate: float = 24.0,
    tolerance_ms: float = 20.0,
) -> List[str]:
    """
    Generate FFmpeg filter_complex expression for beat-reactive effects.
    
    This is a more flexible approach that can combine multiple filters.
    
    Args:
        beat_times: List of beat timestamps in seconds
        filter_type: Type of effect
        frame_rate: Video frame rate
        tolerance_ms: Tolerance window in milliseconds
        
    Returns:
        List of filter strings for filter_complex
    """
    if not beat_times:
        return []
    
    tolerance_sec = tolerance_ms / 1000.0
    filters = []
    
    # For each beat, create a filter that triggers at that time
    for i, beat_time in enumerate(beat_times):
        start_time = max(0, beat_time - tolerance_sec)
        end_time = beat_time + tolerance_sec
        
        if filter_type == "flash":
            # Flash effect: brightness spike
            filter_str = (
                f"[0:v]select='between(t,{start_time},{end_time})',"
                f"geq=r='r+30':g='g+30':b='b+30'[beat{i}];"
            )
        elif filter_type == "color_burst":
            # Color burst: saturation and brightness
            filter_str = (
                f"[0:v]select='between(t,{start_time},{end_time})',"
                f"eq=saturation=1.5:brightness=0.1[beat{i}];"
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

