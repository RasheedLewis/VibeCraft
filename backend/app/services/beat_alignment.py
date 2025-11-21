"""Beat alignment service for calculating beat-aligned clip boundaries.

Implements beat-to-frame alignment algorithm for video generation.
Supports configurable FPS (defaults to 24 FPS).
"""

import logging
from typing import NamedTuple

from app.core.constants import ACCEPTABLE_ALIGNMENT

logger = logging.getLogger(__name__)

# Default video FPS (can be overridden)
VIDEO_FPS = 24
FRAME_INTERVAL = 1.0 / VIDEO_FPS

# Clip duration constraints (in seconds)
MIN_CLIP_DURATION = 3.0
MAX_CLIP_DURATION = 6.0

# Alignment quality thresholds (in seconds)
# These are absolute time thresholds that work well across common FPS values (8-30 FPS)
EXCELLENT_ALIGNMENT = 0.02  # Excellent: < 20ms error
GOOD_ALIGNMENT = 0.05  # Good: < 50ms error


class BeatFrameAlignment(NamedTuple):
    """Alignment between a beat and a frame."""

    beat_index: int
    beat_time: float
    frame_index: int
    frame_time: float
    error_sec: float


class ClipBoundary(NamedTuple):
    """A clip boundary with beat alignment metadata."""

    start_time: float
    end_time: float
    start_beat_index: int
    end_beat_index: int
    start_frame_index: int
    end_frame_index: int
    start_alignment_error: float
    end_alignment_error: float
    duration_sec: float
    beats_in_clip: list[int]


def map_beats_to_frames(beat_times: list[float], fps: float = VIDEO_FPS) -> list[BeatFrameAlignment]:
    """
    Map each beat to its nearest frame index.

    Args:
        beat_times: List of beat times in seconds
        fps: Video frames per second (default: 8)

    Returns:
        List of BeatFrameAlignment objects
    """
    alignments = []
    frame_interval = 1.0 / fps

    for beat_idx, beat_time in enumerate(beat_times):
        # Find nearest frame
        frame_idx = round(beat_time * fps)
        frame_time = frame_idx * frame_interval

        # Calculate alignment error
        error = abs(beat_time - frame_time)

        alignments.append(
            BeatFrameAlignment(
                beat_index=beat_idx,
                beat_time=beat_time,
                frame_index=frame_idx,
                frame_time=frame_time,
                error_sec=error,
            )
        )

    return alignments


def find_nearest_beat_index(time: float, beat_times: list[float]) -> int:
    """
    Find the index of the beat nearest to the given time.

    Args:
        time: Time in seconds
        beat_times: List of beat times in seconds

    Returns:
        Index of nearest beat
    """
    if not beat_times:
        raise ValueError("beat_times cannot be empty")

    min_distance = float("inf")
    nearest_idx = 0

    for idx, beat_time in enumerate(beat_times):
        distance = abs(beat_time - time)
        if distance < min_distance:
            min_distance = distance
            nearest_idx = idx

    return nearest_idx


def calculate_beat_aligned_boundaries(
    beat_times: list[float],
    song_duration: float,
    min_duration: float = MIN_CLIP_DURATION,
    max_duration: float = MAX_CLIP_DURATION,
    fps: float = VIDEO_FPS,
) -> list[ClipBoundary]:
    """
    Calculate optimal clip boundaries aligned to beats.

    Algorithm:
    1. Start with first beat as first boundary
    2. For each subsequent beat, check if adding it would create a clip within duration constraints
    3. If yes, add it as a boundary
    4. If no, find the best beat to end the current clip and start a new one
    5. Ensure last boundary aligns with song end (or nearest beat)

    Args:
        beat_times: List of beat times in seconds (must be sorted)
        song_duration: Total song duration in seconds
        min_duration: Minimum clip duration in seconds (default: 3.0)
        max_duration: Maximum clip duration in seconds (default: 6.0)
        fps: Video frames per second (default: 8)

    Returns:
        List of ClipBoundary objects with beat alignment metadata
    """
    if not beat_times:
        raise ValueError("beat_times cannot be empty")

    if song_duration <= 0:
        raise ValueError("song_duration must be positive")

    if min_duration >= max_duration:
        raise ValueError("min_duration must be less than max_duration")

    # Get beat-to-frame alignments
    alignments = map_beats_to_frames(beat_times, fps)

    boundaries: list[ClipBoundary] = []
    current_start_beat_idx = 0
    current_start_time = beat_times[0]

    frame_interval = 1.0 / fps

    # Find beats that can serve as boundaries
    for beat_idx in range(1, len(beat_times)):
        beat_time = beat_times[beat_idx]
        duration = beat_time - current_start_time

        # If adding this beat would exceed max duration, finalize current clip
        if duration > max_duration:
            # Find the best beat to end the current clip (closest to max_duration)
            best_end_beat_idx = beat_idx - 1
            best_end_time = beat_times[best_end_beat_idx]

            # Check if we can extend to current beat while staying within max
            # (This handles the case where we're just over max)
            if duration <= max_duration * 1.1:  # Allow 10% tolerance
                best_end_beat_idx = beat_idx
                best_end_time = beat_time

            # Ensure minimum duration
            if best_end_time - current_start_time < min_duration:
                # Extend to next beat if possible
                if beat_idx < len(beat_times) - 1:
                    next_beat_time = beat_times[beat_idx + 1]
                    if next_beat_time - current_start_time <= max_duration:
                        best_end_beat_idx = beat_idx + 1
                        best_end_time = next_beat_time

            # Create boundary
            end_alignment = alignments[best_end_beat_idx]
            start_alignment = alignments[current_start_beat_idx]

            # Get beats in this clip
            beats_in_clip = list(range(current_start_beat_idx, best_end_beat_idx + 1))

            boundary = ClipBoundary(
                start_time=current_start_time,
                end_time=best_end_time,
                start_beat_index=current_start_beat_idx,
                end_beat_index=best_end_beat_idx,
                start_frame_index=start_alignment.frame_index,
                end_frame_index=end_alignment.frame_index,
                start_alignment_error=start_alignment.error_sec,
                end_alignment_error=end_alignment.error_sec,
                duration_sec=best_end_time - current_start_time,
                beats_in_clip=beats_in_clip,
            )

            boundaries.append(boundary)

            # Start new clip
            current_start_beat_idx = best_end_beat_idx
            current_start_time = best_end_time

    # Handle last clip
    if current_start_time < song_duration:
        # Find best end beat (closest to song end, but within constraints)
        last_beat_idx = len(beat_times) - 1
        last_beat_time = beat_times[last_beat_idx]

        # If last beat is close to song end, use it
        if abs(last_beat_time - song_duration) < 0.5 or last_beat_time >= song_duration:
            end_time = min(song_duration, last_beat_time)
            end_beat_idx = last_beat_idx
        else:
            # Use last beat, but extend to song duration if needed
            end_time = song_duration
            end_beat_idx = last_beat_idx

        # Ensure minimum duration
        if end_time - current_start_time < min_duration:
            # Extend to song end if possible
            if song_duration - current_start_time <= max_duration:
                end_time = song_duration
            else:
                # Use last beat even if slightly under min (better than invalid)
                end_time = last_beat_time
                end_beat_idx = last_beat_idx

        # Get alignment for end (use last beat's alignment, or calculate for song end)
        if end_beat_idx < len(alignments):
            end_alignment = alignments[end_beat_idx]
            end_frame_idx = end_alignment.frame_index
            end_error = abs(end_time - end_alignment.frame_time)
        else:
            # Calculate frame for song end
            end_frame_idx = round(end_time * fps)
            end_error = abs(end_time - (end_frame_idx * frame_interval))

        start_alignment = alignments[current_start_beat_idx]

        # Get beats in this clip
        beats_in_clip = list(range(current_start_beat_idx, end_beat_idx + 1))

        boundary = ClipBoundary(
            start_time=current_start_time,
            end_time=end_time,
            start_beat_index=current_start_beat_idx,
            end_beat_index=end_beat_idx,
            start_frame_index=start_alignment.frame_index,
            end_frame_index=end_frame_idx,
            start_alignment_error=start_alignment.error_sec,
            end_alignment_error=end_error,
            duration_sec=end_time - current_start_time,
            beats_in_clip=beats_in_clip,
        )

        boundaries.append(boundary)

    return boundaries


def validate_boundaries(
    boundaries: list[ClipBoundary],
    beat_times: list[float],
    song_duration: float,
    max_drift: float = ACCEPTABLE_ALIGNMENT,
    fps: float = VIDEO_FPS,
) -> tuple[bool, float, float]:
    """
    Validate that boundaries don't drift from beat grid.

    Args:
        boundaries: List of clip boundaries
        beat_times: List of beat times in seconds
        song_duration: Total song duration in seconds
        max_drift: Maximum allowed drift from beat grid in seconds (default: 0.1)
        fps: Video frames per second (default: 8)

    Returns:
        Tuple of (is_valid, max_error, avg_error)
    """
    if not boundaries:
        return True, 0.0, 0.0

    errors = []
    frame_interval = 1.0 / fps

    for boundary in boundaries:
        # Check start alignment
        start_beat_time = beat_times[boundary.start_beat_index]
        start_frame_time = boundary.start_frame_index * frame_interval
        start_error = abs(boundary.start_time - start_beat_time) + abs(boundary.start_time - start_frame_time)
        errors.append(start_error)

        # Check end alignment
        end_beat_time = beat_times[boundary.end_beat_index]
        end_frame_time = boundary.end_frame_index * frame_interval
        end_error = abs(boundary.end_time - end_beat_time) + abs(boundary.end_time - end_frame_time)
        errors.append(end_error)

        # Validate duration
        if boundary.duration_sec < MIN_CLIP_DURATION or boundary.duration_sec > MAX_CLIP_DURATION * 1.1:
            logger.warning(
                f"Boundary duration {boundary.duration_sec:.3f}s outside constraints "
                f"[{MIN_CLIP_DURATION}, {MAX_CLIP_DURATION}]"
            )

    max_error = max(errors) if errors else 0.0
    avg_error = sum(errors) / len(errors) if errors else 0.0
    is_valid = max_error <= max_drift

    return is_valid, max_error, avg_error

