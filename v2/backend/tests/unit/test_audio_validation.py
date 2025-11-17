"""Unit tests for audio validation service.

Tests audio file validation logic with mocked ffprobe - no real audio files needed, fast (~0.1s).
Validates validate_audio_file() covering file format, size, duration checks, and edge cases.

Run with: pytest backend/tests/unit/test_audio_validation.py -v
Or from backend/: pytest tests/unit/test_audio_validation.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Mock settings before importing modules that use get_settings()
mock_settings = MagicMock()
mock_settings.ffmpeg_bin = "ffmpeg"
with patch("app.core.config.get_settings", return_value=mock_settings):
    from app.services.audio_validation import (  # noqa: E402
        MAX_DURATION_SECONDS,
        MAX_FILE_SIZE_BYTES,
        validate_audio_file,
    )


class TestValidateAudioFileFormat:
    """Test file format validation."""

    @patch("app.services.audio_validation._get_audio_duration")
    def test_valid_mp3(self, mock_duration):
        """Test valid MP3 file."""
        mock_duration.return_value = 120.0
        file_bytes = b"fake mp3 content" * 1000
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is True
        assert result.file_format == "mp3"
        assert result.duration_sec == 120.0

    @patch("app.services.audio_validation._get_audio_duration")
    def test_valid_wav(self, mock_duration):
        """Test valid WAV file."""
        mock_duration.return_value = 60.0
        file_bytes = b"fake wav content" * 1000
        result = validate_audio_file(file_bytes, "test.wav")
        assert result.is_valid is True
        assert result.file_format == "wav"

    @patch("app.services.audio_validation._get_audio_duration")
    def test_valid_m4a(self, mock_duration):
        """Test valid M4A file."""
        mock_duration.return_value = 180.0
        file_bytes = b"fake m4a content" * 1000
        result = validate_audio_file(file_bytes, "test.m4a")
        assert result.is_valid is True
        assert result.file_format == "m4a"

    def test_invalid_format_txt(self):
        """Test invalid text file format."""
        file_bytes = b"this is not audio"
        result = validate_audio_file(file_bytes, "test.txt")
        assert result.is_valid is False
        assert "Unsupported file format" in result.error_message

    def test_invalid_format_pdf(self):
        """Test invalid PDF format."""
        file_bytes = b"%PDF-1.4 fake pdf content"
        result = validate_audio_file(file_bytes, "test.pdf")
        assert result.is_valid is False

    def test_invalid_format_no_extension(self):
        """Test file with no extension."""
        file_bytes = b"some content"
        result = validate_audio_file(file_bytes, "test")
        assert result.is_valid is False

    def test_case_insensitive_extension(self):
        """Test that extension matching is case-insensitive."""
        with patch("app.services.audio_validation._get_audio_duration", return_value=60.0):
            file_bytes = b"content" * 1000
            result = validate_audio_file(file_bytes, "test.MP3")
            assert result.is_valid is True
            assert result.file_format == "mp3"

    def test_special_characters_in_filename(self):
        """Test filename with special characters."""
        with patch("app.services.audio_validation._get_audio_duration", return_value=60.0):
            file_bytes = b"content" * 1000
            result = validate_audio_file(file_bytes, "test-song (1).mp3")
            assert result.is_valid is True


class TestValidateAudioFileSize:
    """Test file size validation."""

    @patch("app.services.audio_validation._get_audio_duration")
    def test_valid_size_under_limit(self, mock_duration):
        """Test file under size limit."""
        mock_duration.return_value = 60.0
        file_bytes = b"x" * (MAX_FILE_SIZE_BYTES - 1)
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is True

    @patch("app.services.audio_validation._get_audio_duration")
    def test_valid_size_at_limit(self, mock_duration):
        """Test file exactly at size limit."""
        mock_duration.return_value = 60.0
        file_bytes = b"x" * MAX_FILE_SIZE_BYTES
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is True

    def test_invalid_size_over_limit(self):
        """Test file over size limit."""
        file_bytes = b"x" * (MAX_FILE_SIZE_BYTES + 1)
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is False
        assert "File size exceeds maximum" in result.error_message

    @patch("app.services.audio_validation._get_audio_duration")
    def test_empty_file(self, mock_duration):
        """Test empty file."""
        mock_duration.return_value = 0.0
        file_bytes = b""
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is False
        assert "Audio duration must be greater than 0" in result.error_message


class TestValidateAudioFileDuration:
    """Test audio duration validation."""

    @patch("app.services.audio_validation._get_audio_duration")
    def test_valid_duration_under_limit(self, mock_duration):
        """Test duration under limit."""
        mock_duration.return_value = MAX_DURATION_SECONDS - 1
        file_bytes = b"content" * 1000
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is True

    @patch("app.services.audio_validation._get_audio_duration")
    def test_valid_duration_at_limit(self, mock_duration):
        """Test duration exactly at limit."""
        mock_duration.return_value = MAX_DURATION_SECONDS
        file_bytes = b"content" * 1000
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is True

    @patch("app.services.audio_validation._get_audio_duration")
    def test_invalid_duration_over_limit(self, mock_duration):
        """Test duration over limit."""
        mock_duration.return_value = MAX_DURATION_SECONDS + 1
        file_bytes = b"content" * 1000
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is False
        assert "Audio duration exceeds maximum" in result.error_message

    @patch("app.services.audio_validation._get_audio_duration")
    def test_invalid_duration_zero(self, mock_duration):
        """Test zero duration."""
        mock_duration.return_value = 0.0
        file_bytes = b"content" * 1000
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is False
        assert "Audio duration must be greater than 0" in result.error_message

    @patch("app.services.audio_validation._get_audio_duration")
    def test_invalid_duration_negative(self, mock_duration):
        """Test negative duration."""
        mock_duration.return_value = -1.0
        file_bytes = b"content" * 1000
        result = validate_audio_file(file_bytes, "test.mp3")
        assert result.is_valid is False
        assert "Audio duration must be greater than 0" in result.error_message


class TestValidateAudioFileFfprobe:
    """Test ffprobe integration and error handling."""

    @patch("app.services.audio_validation._get_audio_duration")
    def test_ffprobe_success(self, mock_duration):
        """Test successful ffprobe execution."""
        mock_duration.return_value = 120.5

        # File must be large enough to pass size validation
        file_bytes = b"audio content" * 1000
        result = validate_audio_file(file_bytes, "test.wav")
        assert result.is_valid is True
        assert result.duration_sec == 120.5

    @patch("app.services.audio_validation._get_audio_duration")
    def test_ffprobe_failure(self, mock_duration):
        """Test ffprobe failure."""
        mock_duration.side_effect = RuntimeError("ffprobe error: invalid file")

        # File must be large enough to pass size validation
        file_bytes = b"invalid audio" * 1000
        result = validate_audio_file(file_bytes, "test.wav")
        assert result.is_valid is False
        assert "Invalid audio file" in result.error_message

    @patch("app.services.audio_validation._get_audio_duration")
    def test_ffprobe_no_duration(self, mock_duration):
        """Test ffprobe returns no duration."""
        mock_duration.return_value = None

        # File must be large enough to pass size validation
        file_bytes = b"audio content" * 1000
        result = validate_audio_file(file_bytes, "test.wav")
        assert result.is_valid is False
        assert "Could not determine audio duration" in result.error_message

    def test_ffprobe_exception_handling(self):
        """Test exception during ffprobe execution."""
        with patch("app.services.audio_validation._get_audio_duration", side_effect=RuntimeError("ffprobe not found")):
            file_bytes = b"audio content"
            result = validate_audio_file(file_bytes, "test.mp3")
            assert result.is_valid is False
            assert "Invalid audio file" in result.error_message


class TestValidateAudioFileEdgeCases:
    """Test edge cases and special scenarios."""

    @patch("app.services.audio_validation._get_audio_duration")
    def test_missing_filename(self, mock_duration):
        """Test with empty filename."""
        mock_duration.return_value = 60.0
        file_bytes = b"content" * 1000
        result = validate_audio_file(file_bytes, "")
        # Should handle gracefully - no extension means invalid format
        assert result.is_valid is False

    @patch("app.services.audio_validation._get_audio_duration")
    def test_very_long_filename(self, mock_duration):
        """Test with very long filename."""
        mock_duration.return_value = 60.0
        file_bytes = b"content" * 1000
        long_name = "a" * 500 + ".mp3"
        result = validate_audio_file(file_bytes, long_name)
        assert result.is_valid is True

    @patch("app.services.audio_validation._get_audio_duration")
    def test_multiple_dots_in_filename(self, mock_duration):
        """Test filename with multiple dots."""
        mock_duration.return_value = 60.0
        file_bytes = b"content" * 1000
        result = validate_audio_file(file_bytes, "test.song.v2.mp3")
        assert result.is_valid is True
        assert result.file_format == "mp3"  # Should use last extension

    @patch("app.services.audio_validation._get_audio_duration")
    def test_unicode_filename(self, mock_duration):
        """Test filename with unicode characters."""
        mock_duration.return_value = 60.0
        file_bytes = b"content" * 1000
        result = validate_audio_file(file_bytes, "测试歌曲.mp3")
        assert result.is_valid is True

