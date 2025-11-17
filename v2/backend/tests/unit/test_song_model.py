"""Unit tests for Song model and schemas.

Tests Song model creation, validation, and schema serialization - fast (~0.05s).
Validates data integrity, field constraints, and Pydantic schema conversion.

Run with: pytest backend/tests/unit/test_song_model.py -v
Or from backend/: pytest tests/unit/test_song_model.py -v
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.models.song import Song  # noqa: E402
from app.schemas.song import SongCreate, SongRead, SongUploadResponse  # noqa: E402


class TestSongModel:
    """Test Song SQLModel."""

    def test_song_creation_valid(self):
        """Test creating a valid Song instance."""
        song = Song(
            user_id="user-123",
            title="Test Song",
            duration_sec=120.5,
            audio_s3_key="songs/song-123/audio.mp3",
        )

        assert song.user_id == "user-123"
        assert song.title == "Test Song"
        assert song.duration_sec == 120.5
        assert song.audio_s3_key == "songs/song-123/audio.mp3"
        assert isinstance(song.id, str)
        assert isinstance(song.created_at, datetime)

    def test_song_id_generation(self):
        """Test that Song ID is automatically generated."""
        song1 = Song(
            user_id="user-123",
            title="Song 1",
            duration_sec=60.0,
            audio_s3_key="songs/1/audio.mp3",
        )
        song2 = Song(
            user_id="user-123",
            title="Song 2",
            duration_sec=60.0,
            audio_s3_key="songs/2/audio.mp3",
        )

        assert song1.id != song2.id
        assert len(song1.id) > 0
        assert len(song2.id) > 0

    def test_song_created_at_auto_set(self):
        """Test that created_at is automatically set."""
        before = datetime.now(UTC)
        song = Song(
            user_id="user-123",
            title="Test Song",
            duration_sec=60.0,
            audio_s3_key="songs/123/audio.mp3",
        )
        after = datetime.now(UTC)

        assert before <= song.created_at <= after

    def test_song_duration_validation(self):
        """Test that duration must be non-negative."""
        # This should work (SQLModel validation happens at DB level)
        song = Song(
            user_id="user-123",
            title="Test Song",
            duration_sec=0.0,
            audio_s3_key="songs/123/audio.mp3",
        )
        assert song.duration_sec == 0.0

        # Negative duration should be caught by Pydantic validation in SongCreate schema
        with pytest.raises(ValueError):
            SongCreate(
                user_id="user-123",
                title="Test",
                duration_sec=-1.0,  # Invalid - should fail ge=0 constraint
                audio_s3_key="songs/123/audio.mp3",
            )


class TestSongCreateSchema:
    """Test SongCreate Pydantic schema."""

    def test_song_create_valid(self):
        """Test creating valid SongCreate."""
        song_create = SongCreate(
            user_id="user-123",
            title="Test Song",
            duration_sec=120.5,
            audio_s3_key="songs/song-123/audio.mp3",
        )

        assert song_create.user_id == "user-123"
        assert song_create.title == "Test Song"
        assert song_create.duration_sec == 120.5
        assert song_create.audio_s3_key == "songs/song-123/audio.mp3"

    def test_song_create_missing_fields(self):
        """Test SongCreate with missing required fields."""
        with pytest.raises(ValueError):
            SongCreate(
                user_id="user-123",
                # Missing title, duration_sec, audio_s3_key
            )

    def test_song_create_negative_duration(self):
        """Test SongCreate with negative duration."""
        with pytest.raises(ValueError):
            SongCreate(
                user_id="user-123",
                title="Test Song",
                duration_sec=-1.0,  # Invalid
                audio_s3_key="songs/123/audio.mp3",
            )

    def test_song_create_zero_duration(self):
        """Test SongCreate with zero duration (should be valid)."""
        song_create = SongCreate(
            user_id="user-123",
            title="Test Song",
            duration_sec=0.0,
            audio_s3_key="songs/123/audio.mp3",
        )
        assert song_create.duration_sec == 0.0


class TestSongReadSchema:
    """Test SongRead Pydantic schema."""

    def test_song_read_from_model(self):
        """Test creating SongRead from Song model."""
        song = Song(
            user_id="user-123",
            title="Test Song",
            duration_sec=120.5,
            audio_s3_key="songs/song-123/audio.mp3",
        )
        song.id = "song-123"
        song.created_at = datetime(2024, 1, 1, 12, 0, 0)

        song_read = SongRead.model_validate(song)

        assert song_read.id == "song-123"
        assert song_read.user_id == "user-123"
        assert song_read.title == "Test Song"
        assert song_read.duration_sec == 120.5
        assert song_read.audio_s3_key == "songs/song-123/audio.mp3"
        assert song_read.created_at == datetime(2024, 1, 1, 12, 0, 0)

    def test_song_read_direct_creation(self):
        """Test creating SongRead directly."""
        song_read = SongRead(
            id="song-123",
            user_id="user-123",
            title="Test Song",
            duration_sec=120.5,
            audio_s3_key="songs/song-123/audio.mp3",
            created_at=datetime(2024, 1, 1, 12, 0, 0),
        )

        assert song_read.id == "song-123"
        assert song_read.title == "Test Song"

    def test_song_read_missing_fields(self):
        """Test SongRead with missing required fields."""
        with pytest.raises(ValueError):
            SongRead(
                id="song-123",
                # Missing other required fields
            )


class TestSongUploadResponseSchema:
    """Test SongUploadResponse Pydantic schema."""

    def test_song_upload_response_valid(self):
        """Test creating valid SongUploadResponse."""
        response = SongUploadResponse(
            song_id="song-123",
            status="uploaded",
            title="Test Song",
            duration_sec=120.5,
        )

        assert response.song_id == "song-123"
        assert response.status == "uploaded"
        assert response.title == "Test Song"
        assert response.duration_sec == 120.5

    def test_song_upload_response_default_status(self):
        """Test SongUploadResponse with default status."""
        response = SongUploadResponse(
            song_id="song-123",
            title="Test Song",
            duration_sec=120.5,
        )

        assert response.status == "uploaded"  # Default value

    def test_song_upload_response_custom_status(self):
        """Test SongUploadResponse with custom status."""
        response = SongUploadResponse(
            song_id="song-123",
            status="processing",
            title="Test Song",
            duration_sec=120.5,
        )

        assert response.status == "processing"

    def test_song_upload_response_missing_fields(self):
        """Test SongUploadResponse with missing required fields."""
        with pytest.raises(ValueError):
            SongUploadResponse(
                song_id="song-123",
                # Missing title and duration_sec
            )

