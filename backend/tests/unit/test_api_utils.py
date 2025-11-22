"""Unit tests for API utility functions."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.api.v1.utils import ensure_no_analysis, update_song_field
from app.models.song import Song


class TestUpdateSongField:
    """Tests for update_song_field function."""

    def test_updates_field_and_commits(self):
        """Test that field is updated and changes are committed."""
        song_id = uuid4()
        mock_song = Mock(spec=Song)
        mock_song.id = song_id
        mock_song.video_type = None

        mock_db = Mock()

        result = update_song_field(mock_song, "video_type", "full_length", mock_db)

        assert result == mock_song
        assert mock_song.video_type == "full_length"
        mock_db.add.assert_called_once_with(mock_song)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_song)


class TestEnsureNoAnalysis:
    """Tests for ensure_no_analysis function."""

    def test_ensure_no_analysis_passes_when_no_analysis_exists(self):
        """Test that ensure_no_analysis passes when no analysis exists."""
        song_id = uuid4()

        with patch("app.api.v1.utils.get_latest_analysis", return_value=None):
            # Should not raise any exception
            ensure_no_analysis(song_id)

    def test_ensure_no_analysis_raises_409_when_analysis_exists(self):
        """Test that ensure_no_analysis raises 409 with correct message when analysis exists."""
        song_id = uuid4()
        mock_analysis = Mock()  # Any non-None value represents existing analysis

        with patch("app.api.v1.utils.get_latest_analysis", return_value=mock_analysis):
            with pytest.raises(HTTPException) as exc_info:
                ensure_no_analysis(song_id)

            assert exc_info.value.status_code == 409
            assert (
                "Cannot change after analysis has been completed"
                in exc_info.value.detail
            )
            assert "Please upload a new song" in exc_info.value.detail

    def test_ensure_no_analysis_calls_get_latest_analysis_with_correct_song_id(self):
        """Test that ensure_no_analysis calls get_latest_analysis with the correct song_id."""
        song_id = uuid4()

        with patch(
            "app.api.v1.utils.get_latest_analysis", return_value=None
        ) as mock_get:
            ensure_no_analysis(song_id)
            mock_get.assert_called_once_with(song_id)
