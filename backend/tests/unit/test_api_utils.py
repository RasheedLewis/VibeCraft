"""Unit tests for API utility functions."""

from unittest.mock import Mock
from uuid import uuid4

from app.api.v1.utils import update_song_field
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

