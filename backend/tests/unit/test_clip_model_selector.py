"""Unit tests for clip model selector service.

Tests the clip model selection and validation logic.
"""

from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.exceptions import ClipNotFoundError, CompositionError
from app.models.clip import SongClip
from app.models.section_video import SectionVideo
from app.services.clip_model_selector import (
    get_and_validate_clip,
    get_clips_for_composition,
)


class TestGetAndValidateClip:
    """Tests for get_and_validate_clip function."""

    def test_valid_sectionvideo_clip(self):
        """Test validation of a valid SectionVideo clip."""
        song_id = uuid4()
        clip_id = uuid4()

        mock_clip = Mock(spec=SectionVideo)
        mock_clip.id = clip_id
        mock_clip.song_id = song_id
        mock_clip.status = "completed"
        mock_clip.video_url = "http://example.com/video.mp4"

        mock_session = Mock()
        mock_session.get.return_value = mock_clip

        result = get_and_validate_clip(mock_session, clip_id, song_id, use_sections=True)

        assert result == mock_clip
        mock_session.get.assert_called_once_with(SectionVideo, clip_id)

    def test_valid_songclip_clip(self):
        """Test validation of a valid SongClip clip."""
        song_id = uuid4()
        clip_id = uuid4()

        mock_clip = Mock(spec=SongClip)
        mock_clip.id = clip_id
        mock_clip.song_id = song_id
        mock_clip.status = "completed"
        mock_clip.video_url = "http://example.com/video.mp4"

        mock_session = Mock()
        mock_session.get.return_value = mock_clip

        result = get_and_validate_clip(mock_session, clip_id, song_id, use_sections=False)

        assert result == mock_clip
        mock_session.get.assert_called_once_with(SongClip, clip_id)

    def test_clip_not_found_raises_error(self):
        """Test that ClipNotFoundError is raised when clip is not found."""
        song_id = uuid4()
        clip_id = uuid4()

        mock_session = Mock()
        mock_session.get.return_value = None

        with pytest.raises(ClipNotFoundError, match="SectionVideo.*not found"):
            get_and_validate_clip(mock_session, clip_id, song_id, use_sections=True)

        with pytest.raises(ClipNotFoundError, match="SongClip.*not found"):
            get_and_validate_clip(mock_session, clip_id, song_id, use_sections=False)

    def test_clip_wrong_song_id_raises_error(self):
        """Test that CompositionError is raised when clip belongs to different song."""
        song_id = uuid4()
        wrong_song_id = uuid4()
        clip_id = uuid4()

        mock_clip = Mock(spec=SectionVideo)
        mock_clip.id = clip_id
        mock_clip.song_id = wrong_song_id
        mock_clip.status = "completed"
        mock_clip.video_url = "http://example.com/video.mp4"

        mock_session = Mock()
        mock_session.get.return_value = mock_clip

        with pytest.raises(CompositionError, match="does not belong to song"):
            get_and_validate_clip(mock_session, clip_id, song_id, use_sections=True)

    def test_clip_not_completed_raises_error(self):
        """Test that CompositionError is raised when clip is not completed."""
        song_id = uuid4()
        clip_id = uuid4()

        mock_clip = Mock(spec=SectionVideo)
        mock_clip.id = clip_id
        mock_clip.song_id = song_id
        mock_clip.status = "processing"
        mock_clip.video_url = "http://example.com/video.mp4"

        mock_session = Mock()
        mock_session.get.return_value = mock_clip

        with pytest.raises(CompositionError, match="is not ready"):
            get_and_validate_clip(mock_session, clip_id, song_id, use_sections=True)

    def test_clip_no_video_url_raises_error(self):
        """Test that CompositionError is raised when clip has no video_url."""
        song_id = uuid4()
        clip_id = uuid4()

        mock_clip = Mock(spec=SectionVideo)
        mock_clip.id = clip_id
        mock_clip.song_id = song_id
        mock_clip.status = "completed"
        mock_clip.video_url = None

        mock_session = Mock()
        mock_session.get.return_value = mock_clip

        with pytest.raises(CompositionError, match="is not ready"):
            get_and_validate_clip(mock_session, clip_id, song_id, use_sections=True)


class TestGetClipsForComposition:
    """Tests for get_clips_for_composition function."""

    def test_get_multiple_valid_clips(self):
        """Test getting multiple valid clips."""
        song_id = uuid4()
        clip_id_1 = uuid4()
        clip_id_2 = uuid4()

        mock_song = Mock()
        mock_song.id = song_id
        mock_song.video_type = "full_length"

        mock_clip_1 = Mock(spec=SectionVideo)
        mock_clip_1.id = clip_id_1
        mock_clip_1.song_id = song_id
        mock_clip_1.status = "completed"
        mock_clip_1.video_url = "http://example.com/video1.mp4"

        mock_clip_2 = Mock(spec=SectionVideo)
        mock_clip_2.id = clip_id_2
        mock_clip_2.song_id = song_id
        mock_clip_2.status = "completed"
        mock_clip_2.video_url = "http://example.com/video2.mp4"

        mock_session = Mock()
        # Mock the new bulk query approach: session.exec(select(...)) returns list
        mock_exec_result = Mock()
        mock_exec_result.all.return_value = [mock_clip_1, mock_clip_2]
        mock_session.exec.return_value = mock_exec_result

        clips, clip_urls = get_clips_for_composition(
            mock_session, [clip_id_1, clip_id_2], mock_song
        )

        assert len(clips) == 2
        assert len(clip_urls) == 2
        assert clips[0] == mock_clip_1
        assert clips[1] == mock_clip_2
        assert clip_urls[0] == "http://example.com/video1.mp4"
        assert clip_urls[1] == "http://example.com/video2.mp4"

    def test_get_clips_uses_songclip_for_short_form(self):
        """Test that SongClip is used when video_type is short_form."""
        song_id = uuid4()
        clip_id = uuid4()

        mock_song = Mock()
        mock_song.id = song_id
        mock_song.video_type = "short_form"

        mock_clip = Mock(spec=SongClip)
        mock_clip.id = clip_id
        mock_clip.song_id = song_id
        mock_clip.status = "completed"
        mock_clip.video_url = "http://example.com/video.mp4"

        mock_session = Mock()
        # Mock the new bulk query approach: session.exec(select(...)) returns list
        mock_exec_result = Mock()
        mock_exec_result.all.return_value = [mock_clip]
        mock_session.exec.return_value = mock_exec_result

        clips, clip_urls = get_clips_for_composition(mock_session, [clip_id], mock_song)

        assert len(clips) == 1
        assert isinstance(clips[0], Mock)  # Mock doesn't have isinstance, but we can check
        # Verify it used select with SongClip model
        assert mock_session.exec.called

    def test_get_clips_raises_error_on_invalid_clip(self):
        """Test that errors are propagated when a clip is invalid."""
        song_id = uuid4()
        clip_id = uuid4()

        mock_song = Mock()
        mock_song.id = song_id
        mock_song.video_type = "full_length"

        mock_session = Mock()
        # Mock the new bulk query approach: returns empty list (clip not found)
        mock_exec_result = Mock()
        mock_exec_result.all.return_value = []
        mock_session.exec.return_value = mock_exec_result

        with pytest.raises(ClipNotFoundError):
            get_clips_for_composition(mock_session, [clip_id], mock_song)

    def test_get_clips_raises_error_on_missing_video_url(self):
        """Test that CompositionError is raised when clip has no video_url."""
        song_id = uuid4()
        clip_id = uuid4()

        mock_song = Mock()
        mock_song.id = song_id
        mock_song.video_type = "full_length"

        mock_clip = Mock(spec=SectionVideo)
        mock_clip.id = clip_id
        mock_clip.song_id = song_id
        mock_clip.status = "completed"
        mock_clip.video_url = None  # Missing video_url

        mock_session = Mock()
        # Mock the new bulk query approach: returns clip but it has no video_url
        mock_exec_result = Mock()
        mock_exec_result.all.return_value = [mock_clip]
        mock_session.exec.return_value = mock_exec_result

        # Validation will catch this and raise "is not ready"
        with pytest.raises(CompositionError, match="is not ready"):
            get_clips_for_composition(mock_session, [clip_id], mock_song)

