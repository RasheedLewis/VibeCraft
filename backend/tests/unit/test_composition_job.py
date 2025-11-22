"""Unit tests for composition job service.

Tests model validation based on feature flag.

Run with: pytest backend/tests/unit/test_composition_job.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from app.exceptions import ClipNotFoundError  # noqa: E402
from app.models.clip import SongClip  # noqa: E402
from app.models.section_video import SectionVideo  # noqa: E402


class TestCompositionJobModelValidation:
    """Tests for model validation based on video_type."""

    @patch("app.services.composition_job.session_scope")
    @patch("app.services.composition_job.SongRepository")
    @patch("app.services.composition_job.get_queue")
    def test_enqueue_composition_sections_enabled_validates_sectionvideo(
        self, mock_queue, mock_repo, mock_session
    ):
        """Test that SectionVideo is validated when video_type is full_length."""
        from app.services.composition_job import enqueue_composition

        song_id = uuid4()
        clip_id = uuid4()

        mock_song = Mock()
        mock_song.video_type = "full_length"
        mock_repo.get_by_id.return_value = mock_song

        mock_section_video = Mock(spec=SectionVideo)
        mock_section_video.song_id = song_id
        mock_section_video.status = "completed"
        mock_section_video.video_url = "http://example.com/video.mp4"

        mock_session_obj = MagicMock()
        mock_session_obj.get.return_value = mock_section_video
        mock_session.return_value.__enter__.return_value = mock_session_obj

        mock_job = Mock()
        mock_job.id = "test-job-123"
        mock_queue_obj = Mock()
        mock_queue_obj.enqueue.return_value = mock_job
        mock_queue.return_value = mock_queue_obj

        # Should succeed
        job_id, job = enqueue_composition(
            song_id=song_id,
            clip_ids=[clip_id],
            clip_metadata=[],
        )

        assert job_id == "test-job-123"
        # Verify it tried to get SectionVideo
        mock_session_obj.get.assert_called()
        call_args = mock_session_obj.get.call_args
        if call_args:
            model_class = call_args[0][0] if call_args[0] else None
            assert model_class == SectionVideo or (
                hasattr(model_class, "__name__") and model_class.__name__ == "SectionVideo"
            )

    @patch("app.services.composition_job.session_scope")
    @patch("app.services.composition_job.SongRepository")
    @patch("app.services.composition_job.get_queue")
    def test_enqueue_composition_sections_disabled_validates_songclip(
        self, mock_queue, mock_repo, mock_session
    ):
        """Test that SongClip is validated when video_type is short_form."""
        from app.services.composition_job import enqueue_composition

        song_id = uuid4()
        clip_id = uuid4()

        mock_song = Mock()
        mock_song.video_type = "short_form"
        mock_repo.get_by_id.return_value = mock_song

        mock_song_clip = Mock(spec=SongClip)
        mock_song_clip.song_id = song_id
        mock_song_clip.status = "completed"
        mock_song_clip.video_url = "http://example.com/video.mp4"

        mock_session_obj = MagicMock()
        mock_session_obj.get.return_value = mock_song_clip
        mock_session.return_value.__enter__.return_value = mock_session_obj

        mock_job = Mock()
        mock_job.id = "test-job-123"
        mock_queue_obj = Mock()
        mock_queue_obj.enqueue.return_value = mock_job
        mock_queue.return_value = mock_queue_obj

        # Should succeed
        job_id, job = enqueue_composition(
            song_id=song_id,
            clip_ids=[clip_id],
            clip_metadata=[],
        )

        assert job_id == "test-job-123"
        # Verify it tried to get SongClip
        mock_session_obj.get.assert_called()
        call_args = mock_session_obj.get.call_args
        if call_args:
            model_class = call_args[0][0] if call_args[0] else None
            assert model_class == SongClip or (
                hasattr(model_class, "__name__") and model_class.__name__ == "SongClip"
            )

    @patch("app.services.composition_job.session_scope")
    @patch("app.services.composition_job.SongRepository")
    def test_enqueue_composition_sections_disabled_rejects_sectionvideo(
        self, mock_repo, mock_session
    ):
        """Test that SectionVideo is rejected when video_type is short_form."""
        from app.services.composition_job import enqueue_composition

        song_id = uuid4()
        clip_id = uuid4()

        mock_song = Mock()
        mock_song.video_type = "short_form"
        mock_repo.get_by_id.return_value = mock_song

        # Return None (SectionVideo not found when looking for SongClip)
        mock_session_obj = MagicMock()
        mock_session_obj.get.return_value = None
        mock_session.return_value.__enter__.return_value = mock_session_obj

        # Should raise ClipNotFoundError
        with pytest.raises(ClipNotFoundError, match="SongClip.*not found"):
            enqueue_composition(
                song_id=song_id,
                clip_ids=[clip_id],
                clip_metadata=[],
            )

        # Verify it tried to get SongClip (not SectionVideo)
        mock_session_obj.get.assert_called()
        call_args = mock_session_obj.get.call_args
        if call_args:
            model_class = call_args[0][0] if call_args[0] else None
            assert model_class == SongClip or (
                hasattr(model_class, "__name__") and model_class.__name__ == "SongClip"
            )

    @patch("app.services.composition_job.session_scope")
    @patch("app.services.composition_job.SongRepository")
    def test_enqueue_composition_sections_enabled_rejects_songclip(
        self, mock_repo, mock_session
    ):
        """Test that SongClip is rejected when video_type is full_length."""
        from app.services.composition_job import enqueue_composition

        song_id = uuid4()
        clip_id = uuid4()

        mock_song = Mock()
        mock_song.video_type = "full_length"
        mock_repo.get_by_id.return_value = mock_song

        # Return None (SongClip not found when looking for SectionVideo)
        mock_session_obj = MagicMock()
        mock_session_obj.get.return_value = None
        mock_session.return_value.__enter__.return_value = mock_session_obj

        # Should raise ClipNotFoundError
        with pytest.raises(ClipNotFoundError, match="SectionVideo.*not found"):
            enqueue_composition(
                song_id=song_id,
                clip_ids=[clip_id],
                clip_metadata=[],
            )

        # Verify it tried to get SectionVideo (not SongClip)
        mock_session_obj.get.assert_called()
        call_args = mock_session_obj.get.call_args
        if call_args:
            model_class = call_args[0][0] if call_args[0] else None
            assert model_class == SectionVideo or (
                hasattr(model_class, "__name__") and model_class.__name__ == "SectionVideo"
            )

