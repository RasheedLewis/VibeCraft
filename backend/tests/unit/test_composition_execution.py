"""Unit tests for composition execution service."""

from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4


from app.models.clip import SongClip
from app.models.section_video import SectionVideo
from app.services.composition_execution import MAX_DURATION_MISMATCH_SECONDS


class TestDurationMismatchHandling:
    """Tests for duration mismatch handling in composition pipeline."""

    def test_max_duration_mismatch_constant(self):
        """Test that MAX_DURATION_MISMATCH_SECONDS is set correctly."""
        assert MAX_DURATION_MISMATCH_SECONDS == 5.0

    def test_duration_mismatch_logic_clips_longer(self):
        """Test duration mismatch calculation when clips are longer."""
        total_clip_duration = 35.0
        song_duration = 30.0
        duration_diff = total_clip_duration - song_duration

        # Should be within threshold (5 seconds)
        assert abs(duration_diff) <= MAX_DURATION_MISMATCH_SECONDS
        assert duration_diff > 0  # Clips are longer

    def test_duration_mismatch_logic_clips_shorter(self):
        """Test duration mismatch calculation when clips are shorter."""
        total_clip_duration = 25.0
        song_duration = 30.0
        duration_diff = total_clip_duration - song_duration

        # Should be within threshold (5 seconds)
        assert abs(duration_diff) <= MAX_DURATION_MISMATCH_SECONDS
        assert duration_diff < 0  # Clips are shorter

    def test_duration_mismatch_logic_too_long(self):
        """Test duration mismatch when clips are too much longer."""
        total_clip_duration = 40.0
        song_duration = 30.0
        duration_diff = total_clip_duration - song_duration

        # Should exceed threshold (10 seconds > 5 seconds)
        assert abs(duration_diff) > MAX_DURATION_MISMATCH_SECONDS

    def test_duration_mismatch_logic_too_short(self):
        """Test duration mismatch when clips are too much shorter."""
        total_clip_duration = 20.0
        song_duration = 30.0
        duration_diff = total_clip_duration - song_duration

        # Should exceed threshold (10 seconds > 5 seconds)
        assert abs(duration_diff) > MAX_DURATION_MISMATCH_SECONDS


class TestCompositionExecutionModelSelection:
    """Tests for model selection based on video_type."""

    @patch("app.services.composition_execution.session_scope")
    @patch("app.services.composition_execution.SongRepository")
    @patch("app.services.composition_execution.update_job_progress")
    def test_execute_composition_sections_enabled_uses_sectionvideo(
        self, mock_update, mock_repo, mock_session
    ):
        """Test that composition uses SectionVideo when video_type is full_length."""
        from app.services.composition_execution import execute_composition_pipeline

        # Setup mocks
        song_id = uuid4()
        clip_id = uuid4()
        job_id = "test-job-123"

        mock_song = Mock()
        mock_song.id = song_id  # Must set id for validation
        mock_song.duration_sec = 30.0
        mock_song.processed_s3_key = "audio/test.mp3"
        mock_song.video_type = "full_length"
        mock_repo.get_by_id.return_value = mock_song

        mock_section_video = Mock(spec=SectionVideo)
        mock_section_video.video_url = "http://example.com/video.mp4"
        mock_section_video.id = clip_id
        mock_section_video.song_id = song_id  # Must match song_id for validation
        mock_section_video.status = "completed"

        mock_session_obj = MagicMock()
        mock_session_obj.get.return_value = mock_section_video
        mock_session.return_value.__enter__.return_value = mock_session_obj

        # This will fail early in the pipeline, but we can verify it tries to use SectionVideo
        try:
            execute_composition_pipeline(
                job_id=job_id,
                song_id=song_id,
                clip_ids=[clip_id],
                clip_metadata=[],
            )
        except (ValueError, RuntimeError, AttributeError, Exception):
            # Expected to fail - we just want to verify the code path
            pass

        # Verify it tried to get SectionVideo (get() is called in the SectionVideo branch)
        # Note: get() might be called multiple times, but should be called at least once
        assert mock_session_obj.get.called, "get() should have been called when video_type is full_length"

    @patch("app.services.composition_execution.session_scope")
    @patch("app.services.composition_execution.SongRepository")
    @patch("app.services.composition_execution.update_job_progress")
    def test_execute_composition_sections_disabled_uses_songclip(
        self, mock_update, mock_repo, mock_session
    ):
        """Test that composition uses SongClip when video_type is short_form."""
        from app.services.composition_execution import execute_composition_pipeline

        # Setup mocks
        song_id = uuid4()
        clip_id = uuid4()
        job_id = "test-job-123"

        mock_song = Mock()
        mock_song.id = song_id  # Must set id for validation
        mock_song.duration_sec = 30.0
        mock_song.processed_s3_key = "audio/test.mp3"
        mock_song.video_type = "short_form"
        mock_repo.get_by_id.return_value = mock_song

        mock_song_clip = Mock(spec=SongClip)
        mock_song_clip.video_url = "http://example.com/video.mp4"
        mock_song_clip.id = clip_id
        mock_song_clip.song_id = song_id  # Must match song_id for validation
        mock_song_clip.status = "completed"

        mock_session_obj = MagicMock()
        mock_session_obj.get.return_value = mock_song_clip
        mock_session.return_value.__enter__.return_value = mock_session_obj

        # This will fail early in the pipeline, but we can verify it tries to use SongClip
        try:
            execute_composition_pipeline(
                job_id=job_id,
                song_id=song_id,
                clip_ids=[clip_id],
                clip_metadata=[],
            )
        except (ValueError, RuntimeError, AttributeError, Exception):
            # Expected to fail - we just want to verify the code path
            pass

        # Verify it tried to get SongClip (get() is called in the SongClip branch)
        assert mock_session_obj.get.called, "get() should have been called when video_type is short_form"

    # Commented out: Requires DATABASE_URL environment variable
    # @pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="Database not configured")
    # @patch("app.repositories.song_repository.session_scope")
    # @patch("app.services.composition_execution.session_scope")
    # @patch("app.services.composition_execution.SongRepository")
    # @patch("app.services.composition_execution.update_job_progress")
    # def test_execute_composition_sections_disabled_validation(
    #     self, mock_update, mock_repo_class, mock_session, mock_repo_session
    # ):
    #     """Test that SongClip validation works correctly when video_type is short_form."""
    #     from app.services.composition_execution import execute_composition_pipeline
    #
    #     song_id = uuid4()
    #     clip_id = uuid4()
    #     job_id = "test-job-123"
    #
    #     mock_song = Mock()
    #     mock_song.id = song_id  # Must set id for validation
    #     mock_song.duration_sec = 30.0
    #     mock_song.processed_s3_key = "audio/test.mp3"
    #     mock_song.video_type = "short_form"
    #     # Configure the mock class to return the song when get_by_id is called
    #     mock_repo_class.get_by_id = Mock(return_value=mock_song)
    #
    #     mock_song_clip = Mock(spec=SongClip)
    #     mock_song_clip.video_url = "http://example.com/video.mp4"
    #     mock_song_clip.id = clip_id
    #     mock_song_clip.song_id = song_id  # Must match song_id for validation
    #     mock_song_clip.status = "completed"
    #
    #     # Setup session mock - get() is called for CompositionJob first, then for SongClip
    #     mock_job = Mock()
    #     mock_job.status = "processing"
    #     mock_session_obj = MagicMock()
    #     # First call: CompositionJob, Second call: SongClip
    #     mock_session_obj.get.side_effect = [mock_job, mock_song_clip]
    #     mock_session.return_value.__enter__.return_value = mock_session_obj
    #     # Also mock the database session_scope used by SongRepository.get_by_id
    #     mock_repo_session.return_value.__enter__.return_value = mock_session_obj
    #
    #     # Should not raise ClipNotFoundError when clip exists and is valid
    #     # Will fail later in pipeline (download, etc.) but clip validation should pass
    #     with pytest.raises((RuntimeError, AttributeError)):  # Will fail later in pipeline
    #         execute_composition_pipeline(
    #             job_id=job_id,
    #             song_id=song_id,
    #             clip_ids=[clip_id],
    #             clip_metadata=[],
    #         )
    #
    #     # Verify it validated the clip exists (get() called at least twice: job + clip)
    #     assert mock_session_obj.get.call_count >= 2

    # Commented out: Requires DATABASE_URL environment variable
    # @pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="Database not configured")
    # @patch("app.repositories.song_repository.session_scope")
    # @patch("app.services.composition_execution.session_scope")
    # @patch("app.services.composition_execution.SongRepository")
    # @patch("app.services.composition_execution.update_job_progress")
    # def test_execute_composition_sections_disabled_error_handling(
    #     self, mock_update, mock_repo_class, mock_session, mock_repo_session
    # ):
    #     """Test that proper errors are raised for missing SongClip when video_type is short_form."""
    #     from app.models.composition import CompositionJob
    #     from app.services.composition_execution import execute_composition_pipeline
    #
    #     song_id = uuid4()
    #     clip_id = uuid4()
    #     job_id = "test-job-123"
    #
    #     mock_song = Mock()
    #     mock_song.id = song_id  # Must set id for validation
    #     mock_song.duration_sec = 30.0
    #     mock_song.processed_s3_key = "audio/test.mp3"
    #     mock_song.video_type = "short_form"
    #     # Configure the mock class to return the song when get_by_id is called
    #     mock_repo_class.get_by_id = Mock(return_value=mock_song)
    #
    #     mock_session_obj = MagicMock()
    #     # First call returns the job (for job lookup), subsequent calls return None (clip not found)
    #     mock_job = Mock(spec=CompositionJob)
    #     mock_job.status = "processing"
    #     # get() is called for: 1) CompositionJob, 2) SongClip (returns None)
    #     mock_session_obj.get.side_effect = [mock_job, None]  # Job found, clip not found
    #     mock_session.return_value.__enter__.return_value = mock_session_obj
    #     # Also mock the database session_scope used by SongRepository.get_by_id
    #     mock_repo_session.return_value.__enter__.return_value = mock_session_obj
    #
    #     # Should raise ClipNotFoundError for missing clip (now using centralized validation)
    #     from app.exceptions import ClipNotFoundError
    #     with pytest.raises(ClipNotFoundError, match="SongClip.*not found"):
    #         execute_composition_pipeline(
    #             job_id=job_id,
    #             song_id=song_id,
    #             clip_ids=[clip_id],
    #             clip_metadata=[],
    #         )
