"""Unit tests for audio segment extraction.

Tests the _extract_audio_segment function that uses ffmpeg to extract
audio segments for composition.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.services.clip_generation import _extract_audio_segment


class TestExtractAudioSegment:
    """Tests for _extract_audio_segment function."""

    @patch("app.services.clip_generation.get_settings")
    @patch("app.services.clip_generation.subprocess.run")
    def test_extract_audio_segment_calls_ffmpeg_correctly(self, mock_run, mock_get_settings):
        """Test that ffmpeg is called with correct parameters."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.ffmpeg_bin = "/usr/bin/ffmpeg"
        mock_get_settings.return_value = mock_settings

        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        audio_path = Path("/tmp/input.wav")
        output_path = Path("/tmp/output.wav")
        start_sec = 10.0
        end_sec = 40.0
        expected_duration = end_sec - start_sec  # 30.0

        _extract_audio_segment(
            audio_path=audio_path,
            start_sec=start_sec,
            end_sec=end_sec,
            output_path=output_path,
        )

        # Verify subprocess.run was called
        assert mock_run.called

        # Get the call arguments
        call_args = mock_run.call_args
        cmd = call_args[0][0]  # First positional argument is the command list

        # Verify ffmpeg binary
        assert cmd[0] == "/usr/bin/ffmpeg"

        # Verify input file
        assert "-i" in cmd
        input_idx = cmd.index("-i")
        assert cmd[input_idx + 1] == str(audio_path)

        # Verify start time (-ss)
        assert "-ss" in cmd
        ss_idx = cmd.index("-ss")
        assert float(cmd[ss_idx + 1]) == start_sec

        # Verify duration (-t)
        assert "-t" in cmd
        t_idx = cmd.index("-t")
        assert float(cmd[t_idx + 1]) == expected_duration

        # Verify output file
        assert str(output_path) in cmd

        # Verify codec copy flag
        assert "-acodec" in cmd
        acodec_idx = cmd.index("-acodec")
        assert cmd[acodec_idx + 1] == "copy"

        # Verify overwrite flag
        assert "-y" in cmd

    @patch("app.services.clip_generation.get_settings")
    @patch("app.services.clip_generation.subprocess.run")
    def test_extract_audio_segment_handles_ffmpeg_failure(self, mock_run, mock_get_settings):
        """Test that RuntimeError is raised when ffmpeg fails."""
        import subprocess

        # Mock settings
        mock_settings = Mock()
        mock_settings.ffmpeg_bin = "/usr/bin/ffmpeg"
        mock_get_settings.return_value = mock_settings

        # Mock failed subprocess run - CalledProcessError is raised when check=True and process fails
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["ffmpeg", "-i", "/tmp/input.wav"],
            stderr="ffmpeg error: invalid input",
        )

        audio_path = Path("/tmp/input.wav")
        output_path = Path("/tmp/output.wav")

        with pytest.raises(RuntimeError, match="Failed to extract audio segment"):
            _extract_audio_segment(
                audio_path=audio_path,
                start_sec=10.0,
                end_sec=40.0,
                output_path=output_path,
            )

    @patch("app.services.clip_generation.get_settings")
    @patch("app.services.clip_generation.subprocess.run")
    def test_extract_audio_segment_handles_timeout(self, mock_run, mock_get_settings):
        """Test that timeout is handled correctly."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.ffmpeg_bin = "/usr/bin/ffmpeg"
        mock_get_settings.return_value = mock_settings

        # Mock timeout
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["ffmpeg"], timeout=60.0)

        audio_path = Path("/tmp/input.wav")
        output_path = Path("/tmp/output.wav")

        with pytest.raises(RuntimeError, match="timed out"):
            _extract_audio_segment(
                audio_path=audio_path,
                start_sec=10.0,
                end_sec=40.0,
                output_path=output_path,
            )

    @patch("app.services.clip_generation.get_settings")
    @patch("app.services.clip_generation.subprocess.run")
    def test_extract_audio_segment_calculates_duration_correctly(self, mock_run, mock_get_settings):
        """Test that duration is calculated correctly from start and end times."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.ffmpeg_bin = "/usr/bin/ffmpeg"
        mock_get_settings.return_value = mock_settings

        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        audio_path = Path("/tmp/input.wav")
        output_path = Path("/tmp/output.wav")

        test_cases = [
            (0.0, 30.0, 30.0),  # Start at 0, 30s duration
            (10.0, 40.0, 30.0),  # Start at 10s, 30s duration
            (5.5, 35.5, 30.0),  # Start at 5.5s, 30s duration
            (0.0, 1.0, 1.0),  # Minimum 1s
            (15.0, 16.0, 1.0),  # 1s selection
        ]

        for start_sec, end_sec, expected_duration in test_cases:
            mock_run.reset_mock()

            _extract_audio_segment(
                audio_path=audio_path,
                start_sec=start_sec,
                end_sec=end_sec,
                output_path=output_path,
            )

            # Verify duration in command
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            t_idx = cmd.index("-t")
            actual_duration = float(cmd[t_idx + 1])
            assert actual_duration == pytest.approx(expected_duration, abs=0.01)

    @patch("app.services.clip_generation.get_settings")
    @patch("app.services.clip_generation.subprocess.run")
    def test_extract_audio_segment_uses_codec_copy(self, mock_run, mock_get_settings):
        """Test that -acodec copy is used to avoid re-encoding."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.ffmpeg_bin = "/usr/bin/ffmpeg"
        mock_get_settings.return_value = mock_settings

        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        audio_path = Path("/tmp/input.wav")
        output_path = Path("/tmp/output.wav")

        _extract_audio_segment(
            audio_path=audio_path,
            start_sec=10.0,
            end_sec=40.0,
            output_path=output_path,
        )

        # Verify codec copy is used
        call_args = mock_run.call_args
        cmd = call_args[0][0]
        assert "-acodec" in cmd
        acodec_idx = cmd.index("-acodec")
        assert cmd[acodec_idx + 1] == "copy"

