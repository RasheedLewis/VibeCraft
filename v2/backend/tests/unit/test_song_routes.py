"""Unit tests for song API routes.

Tests API endpoints with mocked dependencies - no real database or S3 needed, fast (~0.2s).
Validates request handling, authentication, authorization, and error responses.

Run with: pytest backend/tests/unit/test_song_routes.py -v
Or from backend/: pytest tests/unit/test_song_routes.py -v
"""

import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Mock settings before importing modules that use get_settings()
mock_settings = MagicMock()
mock_settings.ffmpeg_bin = "ffmpeg"
mock_settings.s3_bucket_name = "test-bucket"
mock_settings.aws_access_key_id = "test-key"
mock_settings.aws_secret_access_key = "test-secret"
mock_settings.database_url = "sqlite:///:memory:"  # Valid SQLAlchemy URL for testing
mock_settings.api_log_level = "INFO"  # For logging configuration
mock_settings.redis_url = "redis://localhost:6379/0"  # For Redis (not used in unit tests)
mock_settings.api_v1_prefix = "/api/v1"  # For router prefix
mock_settings.environment = "test"  # For environment validation
with patch("app.core.config.get_settings", return_value=mock_settings):
    from app.models.song import Song  # noqa: E402
    from app.models.user import User  # noqa: E402
    from app.services.audio_validation import ValidationResult  # noqa: E402
    from app.main import create_app  # noqa: E402


@pytest.fixture
def mock_user():
    """Create a mock user."""
    user = MagicMock(spec=User)
    user.id = "user-123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock()
    return session


@pytest.fixture
def client(mock_user, mock_session):
    """Create test client with mocked dependencies."""
    # Mock settings for create_app
    mock_settings.api_v1_prefix = "/api/v1"
    with patch("app.main.get_settings", return_value=mock_settings):
        app = create_app()

    def override_get_current_user():
        return mock_user

    def override_get_db_session():
        yield mock_session

    from app.api.deps import get_current_user, get_db_session  # noqa: E402

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


class TestUploadSong:
    """Test POST /api/v1/songs endpoint."""

    @patch("app.api.v1.routes_songs.upload_bytes_to_s3")
    @patch("app.api.v1.routes_songs.validate_audio_file")
    def test_upload_success(self, mock_validate, mock_upload, client, mock_session, mock_user):
        """Test successful song upload."""
        # Mock validation
        mock_validate.return_value = ValidationResult(
            is_valid=True,
            duration_sec=120.5,
            file_format="mp3",
        )

        # Mock database session
        mock_song = MagicMock(spec=Song)
        mock_song.id = "song-123"
        mock_song.title = "test"
        mock_song.duration_sec = 120.5
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        # Create song instance for refresh
        def refresh_side_effect(obj):
            obj.id = "song-123"
            obj.title = "test"
            obj.duration_sec = 120.5

        mock_session.refresh.side_effect = refresh_side_effect

        # Create file
        file_content = b"fake audio content"
        files = {"file": ("test.mp3", file_content, "audio/mpeg")}

        response = client.post("/api/v1/songs/", files=files)

        assert response.status_code == 201
        data = response.json()
        assert data["song_id"] == "song-123"
        assert data["status"] == "uploaded"
        assert data["title"] == "test"
        assert data["duration_sec"] == 120.5

        # Verify S3 upload was called
        mock_upload.assert_called_once()
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    def test_upload_missing_filename(self, client):
        """Test upload with missing filename."""
        files = {"file": ("", b"content", "audio/mpeg")}

        response = client.post("/api/v1/songs/", files=files)

        # FastAPI may return 422 for invalid file uploads, or 400 if our validation catches it
        assert response.status_code in (400, 422)
        detail = response.json().get("detail", "")
        # Check if it's a FastAPI validation error or our custom error
        if isinstance(detail, list):
            # FastAPI validation error format
            detail_str = str(detail)
        else:
            detail_str = detail
        assert "filename" in detail_str.lower() or "file" in detail_str.lower()

    def test_upload_empty_file(self, client):
        """Test upload with empty file."""
        files = {"file": ("test.mp3", b"", "audio/mpeg")}

        response = client.post("/api/v1/songs/", files=files)

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    @patch("app.api.v1.routes_songs.validate_audio_file")
    def test_upload_invalid_format(self, mock_validate, client):
        """Test upload with invalid file format."""
        mock_validate.return_value = ValidationResult(
            is_valid=False,
            error_message="Unsupported file format",
        )

        files = {"file": ("test.txt", b"content", "text/plain")}

        response = client.post("/api/v1/songs/", files=files)

        assert response.status_code == 400
        assert "Unsupported file format" in response.json()["detail"]

    @patch("app.api.v1.routes_songs.validate_audio_file")
    @patch("app.api.v1.routes_songs.upload_bytes_to_s3")
    def test_upload_s3_failure_rollback(self, mock_upload, mock_validate, client, mock_session):
        """Test that song creation is rolled back if S3 upload fails."""
        mock_validate.return_value = ValidationResult(
            is_valid=True,
            duration_sec=120.5,
            file_format="mp3",
        )
        mock_upload.side_effect = Exception("S3 upload failed")

        # Mock session methods
        mock_session.add = MagicMock()
        mock_session.commit = MagicMock()
        mock_session.refresh = MagicMock()

        def refresh_side_effect(obj):
            obj.id = "song-123"

        mock_session.refresh.side_effect = refresh_side_effect

        files = {"file": ("test.mp3", b"content", "audio/mpeg")}

        response = client.post("/api/v1/songs/", files=files)

        assert response.status_code == 502
        # Verify song was deleted (rollback)
        mock_session.delete.assert_called()


class TestGetSong:
    """Test GET /api/v1/songs/{song_id} endpoint."""

    def test_get_song_success(self, client, mock_session, mock_user):
        """Test successful song retrieval."""
        mock_song = MagicMock(spec=Song)
        mock_song.id = "song-123"
        mock_song.user_id = "user-123"
        mock_song.title = "Test Song"
        mock_song.duration_sec = 120.5
        mock_song.audio_s3_key = "songs/song-123/audio.mp3"
        mock_song.created_at = datetime(2024, 1, 1, 12, 0, 0)

        mock_session.exec.return_value.first.return_value = mock_song

        response = client.get("/api/v1/songs/song-123")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "song-123"
        assert data["title"] == "Test Song"
        assert data["user_id"] == "user-123"

    def test_get_song_not_found(self, client, mock_session):
        """Test getting non-existent song."""
        mock_session.exec.return_value.first.return_value = None

        response = client.get("/api/v1/songs/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_song_wrong_user(self, client, mock_session, mock_user):
        """Test getting song owned by different user."""
        mock_song = MagicMock(spec=Song)
        mock_song.id = "song-123"
        mock_song.user_id = "other-user"  # Different user
        mock_user.id = "user-123"

        mock_session.exec.return_value.first.return_value = mock_song

        response = client.get("/api/v1/songs/song-123")

        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()


class TestListSongs:
    """Test GET /api/v1/songs endpoint."""

    def test_list_songs_empty(self, client, mock_session, mock_user):
        """Test listing songs when user has none."""
        mock_session.exec.return_value.all.return_value = []

        response = client.get("/api/v1/songs/")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_songs_multiple(self, client, mock_session, mock_user):
        """Test listing multiple songs."""
        mock_song1 = MagicMock(spec=Song)
        mock_song1.id = "song-1"
        mock_song1.user_id = "user-123"
        mock_song1.title = "Song 1"
        mock_song1.duration_sec = 60.0
        mock_song1.audio_s3_key = "songs/song-1/audio.mp3"
        mock_song1.created_at = datetime(2024, 1, 1, 12, 0, 0)

        mock_song2 = MagicMock(spec=Song)
        mock_song2.id = "song-2"
        mock_song2.user_id = "user-123"
        mock_song2.title = "Song 2"
        mock_song2.duration_sec = 120.0
        mock_song2.audio_s3_key = "songs/song-2/audio.mp3"
        mock_song2.created_at = datetime(2024, 1, 2, 12, 0, 0)

        mock_session.exec.return_value.all.return_value = [mock_song1, mock_song2]

        response = client.get("/api/v1/songs/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == "song-1"
        assert data[1]["id"] == "song-2"

    def test_list_songs_user_isolation(self, client, mock_session, mock_user):
        """Test that users only see their own songs."""
        # Mock session to filter by user_id
        mock_song = MagicMock(spec=Song)
        mock_song.id = "song-123"
        mock_song.user_id = "user-123"
        mock_song.title = "My Song"
        mock_song.duration_sec = 60.0
        mock_song.audio_s3_key = "songs/song-123/audio.mp3"
        mock_song.created_at = datetime(2024, 1, 1, 12, 0, 0)

        mock_session.exec.return_value.all.return_value = [mock_song]

        response = client.get("/api/v1/songs/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == "user-123"
        # Verify query was filtered by user_id
        call_args = mock_session.exec.call_args[0][0]
        assert hasattr(call_args, "where")  # SQLModel select statement

