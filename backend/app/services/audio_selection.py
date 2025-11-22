"""Audio selection validation service."""

from app.core.constants import (
    MAX_AUDIO_SELECTION_DURATION_SEC,
    MIN_AUDIO_SELECTION_DURATION_SEC,
)


def validate_audio_selection(
    start_sec: float,
    end_sec: float,
    song_duration_sec: float | None,
) -> None:
    """
    Validate audio selection parameters.

    Args:
        start_sec: Start time in seconds
        end_sec: End time in seconds
        song_duration_sec: Total song duration in seconds (None if not available)

    Raises:
        ValueError: If validation fails with descriptive error message
    """
    if song_duration_sec is None:
        raise ValueError("Song duration not available")

    if start_sec < 0:
        raise ValueError("Start time must be >= 0")

    if end_sec > song_duration_sec:
        raise ValueError(f"End time ({end_sec}s) exceeds song duration ({song_duration_sec}s)")

    if end_sec <= start_sec:
        raise ValueError("End time must be greater than start time")

    duration = end_sec - start_sec
    if duration > MAX_AUDIO_SELECTION_DURATION_SEC:
        raise ValueError(
            f"Selection duration ({duration:.1f}s) exceeds maximum ({MAX_AUDIO_SELECTION_DURATION_SEC}s)"
        )

    if duration < MIN_AUDIO_SELECTION_DURATION_SEC:
        raise ValueError(
            f"Selection duration ({duration:.1f}s) is below minimum ({MIN_AUDIO_SELECTION_DURATION_SEC}s)"
        )

