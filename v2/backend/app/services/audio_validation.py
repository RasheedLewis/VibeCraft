"""Audio file validation service."""

import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.config import get_settings

settings = get_settings()

# Allowed audio formats
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a"}
ALLOWED_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
}

# Validation limits
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_DURATION_SECONDS = 5 * 60  # 5 minutes


@dataclass
class ValidationResult:
    """Result of audio file validation."""

    is_valid: bool
    error_message: Optional[str] = None
    duration_sec: Optional[float] = None
    file_format: Optional[str] = None


def validate_audio_file(file_bytes: bytes, filename: str) -> ValidationResult:
    """Validate an audio file.

    Checks:
    - File format (MP3, WAV, M4A)
    - File size (max 50MB)
    - Duration (max 5 minutes)
    - File is actually a valid audio file

    Args:
        file_bytes: Raw file bytes
        filename: Original filename

    Returns:
        ValidationResult with validation status and metadata
    """
    # Check file size
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return ValidationResult(
            is_valid=False,
            error_message=f"File size exceeds maximum of {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f} MB",
        )

    # Check file extension
    file_path = Path(filename)
    extension = file_path.suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return ValidationResult(
            is_valid=False,
            error_message=f"Unsupported file format. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Validate using ffprobe (if available)
    duration_sec = None
    try:
        duration_sec = _get_audio_duration(file_bytes, extension)
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            error_message=f"Invalid audio file: {str(e)}",
        )

    # Check duration
    if duration_sec is None:
        return ValidationResult(
            is_valid=False,
            error_message="Could not determine audio duration",
        )

    if duration_sec > MAX_DURATION_SECONDS:
        return ValidationResult(
            is_valid=False,
            error_message=f"Audio duration exceeds maximum of {MAX_DURATION_SECONDS / 60:.0f} minutes",
        )

    if duration_sec <= 0:
        return ValidationResult(
            is_valid=False,
            error_message="Audio duration must be greater than 0",
        )

    return ValidationResult(
        is_valid=True,
        duration_sec=duration_sec,
        file_format=extension[1:],  # Remove leading dot
    )


def _get_audio_duration(file_bytes: bytes, extension: str) -> Optional[float]:
    """Get audio duration using ffprobe.

    Args:
        file_bytes: Raw file bytes
        extension: File extension (with dot)

    Returns:
        Duration in seconds, or None if unable to determine

    Raises:
        RuntimeError: If ffprobe fails or file is invalid
    """
    # Create temporary file
    suffix = extension if extension.startswith(".") else f".{extension}"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        tmp_path = Path(tmp_file.name)
        tmp_file.write(file_bytes)

    try:
        # Use ffprobe to get duration
        ffprobe_bin = settings.ffmpeg_bin.replace("ffmpeg", "ffprobe")
        if not ffprobe_bin or ffprobe_bin == settings.ffmpeg_bin:
            # Fallback: try common ffprobe locations
            ffprobe_bin = "ffprobe"

        cmd = [
            ffprobe_bin,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(tmp_path),
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")

        duration_str = result.stdout.strip()
        if not duration_str:
            raise RuntimeError("No duration information found in audio file")

        duration_sec = float(duration_str)
        return duration_sec

    finally:
        # Clean up temporary file
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

