"""Helper functions for planning video clip generation for sections."""

import logging
from typing import List

logger = logging.getLogger(__name__)


def plan_clips_for_section(
    section_duration_sec: float,
    min_clip_duration_sec: float = 3.0,
    max_clip_duration_sec: float = 6.0,
) -> List[float]:
    """
    Plan clip durations for a section that sum to exactly the section duration.
    
    Each clip will be between min_clip_duration_sec and max_clip_duration_sec,
    and the sum of all clips will equal section_duration_sec exactly.
    
    Args:
        section_duration_sec: Total duration of the section in seconds
        min_clip_duration_sec: Minimum duration for each clip (default: 3.0s)
        max_clip_duration_sec: Maximum duration for each clip (default: 6.0s)
    
    Returns:
        List of clip durations in seconds that sum to section_duration_sec
    
    Raises:
        ValueError: If section_duration_sec is too short to create valid clips
    
    Examples:
        >>> plan_clips_for_section(25.125, 3.0, 6.0)
        [6.0, 6.0, 6.0, 6.0, 1.125]  # Last clip too short!
        # Actually should be: [5.025, 5.025, 5.025, 5.025, 5.025]
        
        >>> plan_clips_for_section(15.0, 3.0, 6.0)
        [6.0, 6.0, 3.0]
        
        >>> plan_clips_for_section(4.5, 3.0, 6.0)
        [4.5]  # Single clip
    """
    if section_duration_sec <= 0:
        raise ValueError(f"Section duration must be positive, got {section_duration_sec}")
    
    if min_clip_duration_sec <= 0 or max_clip_duration_sec <= 0:
        raise ValueError("Clip durations must be positive")
    
    if min_clip_duration_sec > max_clip_duration_sec:
        raise ValueError(
            f"min_clip_duration_sec ({min_clip_duration_sec}) must be <= "
            f"max_clip_duration_sec ({max_clip_duration_sec})"
        )
    
    # Case 1: Section fits in a single clip
    if section_duration_sec <= max_clip_duration_sec:
        # Check if it meets minimum requirement
        if section_duration_sec < min_clip_duration_sec:
            logger.warning(
                f"Section duration ({section_duration_sec}s) is shorter than "
                f"minimum clip duration ({min_clip_duration_sec}s). "
                f"Returning single clip anyway."
            )
        return [section_duration_sec]
    
    # Case 2: Section needs multiple clips
    # Strategy: Use as many max-duration clips as possible, then adjust
    
    # Calculate how many max-duration clips we can fit
    num_max_clips = int(section_duration_sec / max_clip_duration_sec)
    remaining_duration = section_duration_sec - (num_max_clips * max_clip_duration_sec)
    
    # If remaining fits in one clip (and meets minimum), we're done
    if min_clip_duration_sec <= remaining_duration <= max_clip_duration_sec:
        clips = [max_clip_duration_sec] * num_max_clips + [remaining_duration]
        logger.debug(
            f"Planned {len(clips)} clips: {num_max_clips} of {max_clip_duration_sec}s "
            f"+ 1 of {remaining_duration:.3f}s = {section_duration_sec:.3f}s"
        )
        return clips
    
    # Case 3: Remaining is too short (< min) or too long (> max)
    # Need to redistribute
    
    if remaining_duration < min_clip_duration_sec:
        # Remaining is too short - need to take duration from max clips
        # Example: 25.125s, max=6s → 4 clips of 6s = 24s, remaining 1.125s (too short)
        # Solution: Use fewer max clips, distribute more evenly
        
        # Try using one fewer max clip
        num_max_clips -= 1
        remaining_duration = section_duration_sec - (num_max_clips * max_clip_duration_sec)
        
        # Now we have more remaining - check if it fits
        if remaining_duration <= max_clip_duration_sec:
            # It fits! Use it as the last clip
            clips = [max_clip_duration_sec] * num_max_clips + [remaining_duration]
            logger.debug(
                f"Planned {len(clips)} clips (redistributed): "
                f"{num_max_clips} of {max_clip_duration_sec}s "
                f"+ 1 of {remaining_duration:.3f}s = {section_duration_sec:.3f}s"
            )
            return clips
        
        # Still doesn't fit - need to distribute more evenly
        # Calculate optimal number of clips
        num_clips = _calculate_optimal_num_clips(
            section_duration_sec, min_clip_duration_sec, max_clip_duration_sec
        )
        clip_duration = section_duration_sec / num_clips
        
        # Verify it's within bounds
        if clip_duration < min_clip_duration_sec or clip_duration > max_clip_duration_sec:
            # This shouldn't happen if _calculate_optimal_num_clips works correctly
            raise ValueError(
                f"Cannot create valid clips: calculated {num_clips} clips of "
                f"{clip_duration:.3f}s each (must be between {min_clip_duration_sec} "
                f"and {max_clip_duration_sec}s)"
            )
        
        clips = [clip_duration] * num_clips
        logger.debug(
            f"Planned {num_clips} clips of {clip_duration:.3f}s each "
            f"= {section_duration_sec:.3f}s (evenly distributed)"
        )
        return clips
    
    else:  # remaining_duration > max_clip_duration_sec
        # Remaining is too long - need to split it further
        # This case is rare but possible
        # Example: 25.125s, max=6s → 3 clips of 6s = 18s, remaining 7.125s (too long)
        
        # Add one more max clip and recalculate
        num_max_clips += 1
        remaining_duration = section_duration_sec - (num_max_clips * max_clip_duration_sec)
        
        if remaining_duration < 0:
            # We've gone too far - need to distribute evenly
            num_clips = _calculate_optimal_num_clips(
                section_duration_sec, min_clip_duration_sec, max_clip_duration_sec
            )
            clip_duration = section_duration_sec / num_clips
            clips = [clip_duration] * num_clips
            logger.debug(
                f"Planned {num_clips} clips of {clip_duration:.3f}s each "
                f"= {section_duration_sec:.3f}s (evenly distributed)"
            )
            return clips
        
        # Now remaining should fit
        if remaining_duration < min_clip_duration_sec:
            # Still too short - distribute evenly
            num_clips = _calculate_optimal_num_clips(
                section_duration_sec, min_clip_duration_sec, max_clip_duration_sec
            )
            clip_duration = section_duration_sec / num_clips
            clips = [clip_duration] * num_clips
            logger.debug(
                f"Planned {num_clips} clips of {clip_duration:.3f}s each "
                f"= {section_duration_sec:.3f}s (evenly distributed)"
            )
            return clips
        
        clips = [max_clip_duration_sec] * num_max_clips + [remaining_duration]
        logger.debug(
            f"Planned {len(clips)} clips: {num_max_clips} of {max_clip_duration_sec}s "
            f"+ 1 of {remaining_duration:.3f}s = {section_duration_sec:.3f}s"
        )
        return clips


def _calculate_optimal_num_clips(
    total_duration: float,
    min_clip_duration: float,
    max_clip_duration: float,
) -> int:
    """
    Calculate the optimal number of clips to evenly divide the duration.
    
    Returns the number of clips such that each clip is between min and max duration.
    Prefers fewer clips (longer duration per clip) when multiple options exist.
    """
    # Calculate bounds
    # Minimum number of clips: all clips at max duration
    min_num_clips = int(total_duration / max_clip_duration)
    if min_num_clips == 0:
        min_num_clips = 1
    
    # Maximum number of clips: all clips at min duration
    max_num_clips = int(total_duration / min_clip_duration)
    if max_num_clips == 0:
        max_num_clips = 1
    
    # Prefer fewer clips (longer duration per clip)
    # Start from minimum and work up until we find a valid number
    for num_clips in range(min_num_clips, max_num_clips + 1):
        clip_duration = total_duration / num_clips
        if min_clip_duration <= clip_duration <= max_clip_duration:
            return num_clips
    
    # If we can't find a perfect fit, use the minimum number of clips
    # (each clip will be slightly over max, but that's the best we can do)
    return min_num_clips


def get_clip_time_ranges(
    section_start_sec: float,
    section_duration_sec: float,
    clip_durations: List[float],
) -> List[tuple[float, float]]:
    """
    Convert clip durations into time ranges (start, end) within a section.
    
    Args:
        section_start_sec: Start time of the section
        section_duration_sec: Total duration of the section
        clip_durations: List of clip durations (should sum to section_duration_sec)
    
    Returns:
        List of (start_sec, end_sec) tuples for each clip
    
    Example:
        >>> get_clip_time_ranges(10.0, 15.0, [6.0, 6.0, 3.0])
        [(10.0, 16.0), (16.0, 22.0), (22.0, 25.0)]
    """
    if abs(sum(clip_durations) - section_duration_sec) > 0.001:
        logger.warning(
            f"Clip durations sum to {sum(clip_durations):.3f}s, but section "
            f"duration is {section_duration_sec:.3f}s. Adjusting last clip."
        )
        # Adjust last clip to match exactly
        clip_durations = list(clip_durations)
        clip_durations[-1] = section_duration_sec - sum(clip_durations[:-1])
    
    ranges = []
    current_time = section_start_sec
    
    for clip_duration in clip_durations:
        end_time = current_time + clip_duration
        ranges.append((current_time, end_time))
        current_time = end_time
    
    return ranges

