"""Unit tests for video composition service."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.services.video_composition import (
    CompositionResult,
    concatenate_clips,
    extend_last_clip,
    normalize_clip,
    trim_last_clip,
    validate_composition_inputs,
    verify_composed_video,
)


class TestValidateCompositionInputs:
    """Tests for validate_composition_inputs function."""

    @patch("app.services.video_composition.subprocess.run")
    def test_validate_single_clip(self, mock_run):
        """Test validation of a single clip."""
        # Mock ffprobe output
        probe_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "24/1",
                    "codec_name": "h264",
                }
            ],
            "format": {"duration": "10.5"},
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(probe_output)
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        # Mock audio check (no audio)
        mock_audio_result = Mock()
        mock_audio_result.stdout = json.dumps({"streams": []})
        mock_audio_result.returncode = 0

        def run_side_effect(*args, **kwargs):
            if "a:0" in args[0]:
                return mock_audio_result
            return mock_result

        mock_run.side_effect = run_side_effect

        metadata_list = validate_composition_inputs(["http://example.com/clip.mp4"])

        assert len(metadata_list) == 1
        assert metadata_list[0].width == 1920
        assert metadata_list[0].height == 1080
        assert metadata_list[0].fps == 24.0
        assert metadata_list[0].duration_sec == 10.5
        assert metadata_list[0].codec == "h264"
        assert metadata_list[0].has_audio is False

    @patch("app.services.video_composition.subprocess.run")
    def test_validate_multiple_clips(self, mock_run):
        """Test validation of multiple clips."""
        probe_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 576,
                    "height": 320,
                    "r_frame_rate": "8/1",
                    "codec_name": "h264",
                }
            ],
            "format": {"duration": "5.0"},
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(probe_output)
        mock_result.returncode = 0

        mock_audio_result = Mock()
        mock_audio_result.stdout = json.dumps({"streams": []})
        mock_audio_result.returncode = 0

        def run_side_effect(*args, **kwargs):
            if "a:0" in args[0]:
                return mock_audio_result
            return mock_result

        mock_run.side_effect = run_side_effect

        metadata_list = validate_composition_inputs(
            ["http://example.com/clip1.mp4", "http://example.com/clip2.mp4"]
        )

        assert len(metadata_list) == 2
        assert all(m.width == 576 for m in metadata_list)
        assert all(m.fps == 8.0 for m in metadata_list)

    @patch("app.services.video_composition.subprocess.run")
    def test_validate_fails_on_invalid_clip(self, mock_run):
        """Test that validation fails for invalid clip."""
        import subprocess

        # When check=True, subprocess.run raises CalledProcessError on failure
        error = subprocess.CalledProcessError(
            returncode=1, cmd=["ffprobe"], stderr="Invalid file"
        )
        mock_run.side_effect = error

        with pytest.raises(RuntimeError, match="Failed to validate clip"):
            validate_composition_inputs(["http://example.com/invalid.mp4"])


class TestNormalizeClip:
    """Tests for normalize_clip function."""

    @patch("app.services.video_composition.ffmpeg")
    def test_normalize_clip_success(self, mock_ffmpeg):
        """Test successful clip normalization."""
        mock_input = Mock()
        mock_output = Mock()
        mock_overwrite = Mock()
        mock_ffmpeg.input.return_value = mock_input
        mock_input.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_overwrite

        normalize_clip("input.mp4", "output.mp4")

        mock_ffmpeg.input.assert_called_once()
        mock_input.output.assert_called_once()
        mock_output.overwrite_output.assert_called_once()
        mock_overwrite.run.assert_called_once()

    @patch("app.services.video_composition.ffmpeg")
    def test_normalize_clip_failure(self, mock_ffmpeg):
        """Test clip normalization failure."""
        # Create a mock exception that mimics ffmpeg.Error
        class MockFFmpegError(Exception):
            def __init__(self, cmd, stdout, stderr):
                super().__init__()
                self.cmd = cmd
                self.stdout = stdout
                self.stderr = stderr

        mock_input = Mock()
        mock_output = Mock()
        mock_overwrite = Mock()
        mock_ffmpeg.input.return_value = mock_input
        mock_input.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_overwrite

        # Mock FFmpeg error
        error = MockFFmpegError("ffmpeg", b"", b"Error message")
        mock_overwrite.run.side_effect = error

        # Patch ffmpeg.Error to be our mock exception
        with patch("app.services.video_composition.ffmpeg.Error", MockFFmpegError):
            with pytest.raises(RuntimeError, match="Failed to normalize clip"):
                normalize_clip("input.mp4", "output.mp4")


class TestConcatenateClips:
    """Tests for concatenate_clips function."""

    @patch("app.services.video_composition.verify_composed_video")
    @patch("app.services.video_composition.ffmpeg")
    @patch("app.services.video_composition.tempfile.NamedTemporaryFile")
    @patch("app.services.video_composition.subprocess.run")
    def test_concatenate_clips_success(
        self, mock_subprocess, mock_tempfile, mock_ffmpeg, mock_verify
    ):
        """Test successful clip concatenation."""
        # Mock temp file
        mock_file = Mock()
        mock_file.name = "/tmp/concat.txt"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        # Mock subprocess for ffprobe (duration check)
        mock_probe_result = Mock()
        mock_probe_result.stdout = '{"format": {"duration": "30.0"}}'
        mock_probe_result.returncode = 0
        mock_subprocess.return_value = mock_probe_result

        # Mock FFmpeg - need to handle multiple calls for concat, video, and audio
        mock_concat_input = Mock()
        mock_video_input = Mock()
        mock_audio_input = Mock()
        # Make mocks subscriptable for video_input["v"] and audio_input["a"]
        mock_concat_input.__getitem__ = Mock(return_value=mock_concat_input)
        mock_video_input.__getitem__ = Mock(return_value=mock_video_input)
        mock_audio_input.__getitem__ = Mock(return_value=mock_audio_input)
        mock_output = Mock()
        mock_overwrite = Mock()
        # First call is concat input, then video, then audio
        mock_ffmpeg.input.side_effect = [mock_concat_input, mock_video_input, mock_audio_input]
        mock_ffmpeg.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_overwrite

        # Mock verification
        mock_verify.return_value = CompositionResult(
            output_path=Path("output.mp4"),
            duration_sec=30.0,
            file_size_bytes=1000000,
            width=1920,
            height=1080,
            fps=24,
        )

        result = concatenate_clips(
            normalized_clip_paths=["clip1.mp4", "clip2.mp4"],
            audio_path="song.mp3",
            output_path="output.mp4",
            song_duration_sec=30.0,
        )

        assert result.duration_sec == 30.0
        assert result.width == 1920
        assert result.height == 1080
        # Should have multiple ffmpeg.input calls (concat, video, audio)
        assert mock_ffmpeg.input.call_count >= 2
        mock_ffmpeg.output.assert_called()
        mock_overwrite.run.assert_called()


class TestVerifyComposedVideo:
    """Tests for verify_composed_video function."""

    @patch("app.services.video_composition.subprocess.run")
    def test_verify_success(self, mock_run):
        """Test successful video verification."""
        probe_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "24/1",
                }
            ],
            "format": {"duration": "180.5", "size": "52428800"},
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(probe_output)
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = verify_composed_video("output.mp4")

        assert result.width == 1920
        assert result.height == 1080
        assert result.fps == 24
        assert result.duration_sec == 180.5
        assert result.file_size_bytes == 52428800

    @patch("app.services.video_composition.subprocess.run")
    def test_verify_fails_on_resolution_mismatch(self, mock_run):
        """Test that verification fails on resolution mismatch."""
        probe_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1280,
                    "height": 720,
                    "r_frame_rate": "24/1",
                }
            ],
            "format": {"duration": "180.5", "size": "52428800"},
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(probe_output)
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="Resolution mismatch"):
            verify_composed_video("output.mp4")

    @patch("app.services.video_composition.subprocess.run")
    def test_verify_fails_on_empty_file(self, mock_run):
        """Test that verification fails on empty file."""
        probe_output = {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 1920,
                    "height": 1080,
                    "r_frame_rate": "24/1",
                }
            ],
            "format": {"duration": "0", "size": "0"},
        }

        mock_result = Mock()
        mock_result.stdout = json.dumps(probe_output)
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with pytest.raises(RuntimeError, match="Composed video file is empty"):
            verify_composed_video("output.mp4")


class TestExtendLastClip:
    """Tests for extend_last_clip function."""

    @patch("app.services.video_composition.subprocess.run")
    @patch("app.services.video_composition.ffmpeg")
    def test_extend_clip_success(self, mock_ffmpeg, mock_run):
        """Test successful clip extension."""
        # Mock ffprobe to return current duration
        probe_output = {"format": {"duration": "5.0"}}
        mock_probe_result = Mock()
        mock_probe_result.stdout = json.dumps(probe_output)
        mock_probe_result.returncode = 0

        # Mock FFmpeg
        mock_input = Mock()
        mock_output = Mock()
        mock_overwrite = Mock()
        mock_ffmpeg.input.return_value = mock_input
        mock_input.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_overwrite

        def run_side_effect(*args, **kwargs):
            # First call is ffprobe, rest are ffmpeg
            if "ffprobe" in str(args[0]):
                return mock_probe_result
            return Mock(returncode=0)

        mock_run.side_effect = run_side_effect

        extend_last_clip("input.mp4", "output.mp4", target_duration_sec=10.0)

        mock_ffmpeg.input.assert_called_once()
        mock_input.output.assert_called_once()
        mock_output.overwrite_output.assert_called_once()
        mock_overwrite.run.assert_called_once()

    @patch("app.services.video_composition.subprocess.run")
    def test_extend_clip_fails_on_probe_error(self, mock_run):
        """Test that extension fails if ffprobe fails."""
        import subprocess

        error = subprocess.CalledProcessError(
            returncode=1, cmd=["ffprobe"], stderr="Error"
        )
        mock_run.side_effect = error

        with pytest.raises(RuntimeError, match="Failed to get clip duration"):
            extend_last_clip("input.mp4", "output.mp4", target_duration_sec=10.0)


class TestTrimLastClip:
    """Tests for trim_last_clip function."""

    @patch("app.services.video_composition.subprocess.run")
    @patch("app.services.video_composition.ffmpeg")
    def test_trim_clip_success(self, mock_ffmpeg, mock_run):
        """Test successful clip trimming."""
        # Mock ffprobe to return current duration
        probe_output = {"format": {"duration": "10.0"}}
        mock_probe_result = Mock()
        mock_probe_result.stdout = json.dumps(probe_output)
        mock_probe_result.returncode = 0

        # Mock FFmpeg
        mock_input = Mock()
        mock_output = Mock()
        mock_overwrite = Mock()
        mock_ffmpeg.input.return_value = mock_input
        mock_input.output.return_value = mock_output
        mock_output.overwrite_output.return_value = mock_overwrite

        def run_side_effect(*args, **kwargs):
            # First call is ffprobe, rest are ffmpeg
            if "ffprobe" in str(args[0]):
                return mock_probe_result
            return Mock(returncode=0)

        mock_run.side_effect = run_side_effect

        trim_last_clip("input.mp4", "output.mp4", target_duration_sec=5.0)

        mock_ffmpeg.input.assert_called_once()
        mock_input.output.assert_called_once()
        # Verify trim filter is used
        call_args = mock_input.output.call_args
        assert "trim=duration=5.0" in call_args[1]["vf"]

    @patch("app.services.video_composition.subprocess.run")
    def test_trim_clip_fails_on_probe_error(self, mock_run):
        """Test that trimming fails if ffprobe fails."""
        import subprocess

        error = subprocess.CalledProcessError(
            returncode=1, cmd=["ffprobe"], stderr="Error"
        )
        mock_run.side_effect = error

        with pytest.raises(RuntimeError, match="Failed to get clip duration"):
            trim_last_clip("input.mp4", "output.mp4", target_duration_sec=5.0)

