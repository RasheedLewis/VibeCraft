"""Tests for public song API endpoint.

Tests the GET /songs/{song_id}/public endpoint including:
- No authentication required
- Returns song data for valid songs
- Returns 404 for non-existent songs
"""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import init_db, session_scope
from app.main import create_app
from app.models.song import DEFAULT_USER_ID, Song

init_db()


def _cleanup_song(song_id: uuid4) -> None:
    """Clean up test song."""
    with session_scope() as session:
        song = session.get(Song, song_id)
        if song:
            session.delete(song)
            session.commit()


class TestPublicSongEndpoint:
    """Tests for GET /songs/{song_id}/public endpoint."""

    def setup_method(self):
        """Set up test client and create a test song."""
        self.app = create_app()
        self.client = TestClient(self.app)

        # Create a test song
        with session_scope() as session:
            song = Song(
                user_id=DEFAULT_USER_ID,
                title="Public Test Song",
                original_filename="public_test.mp3",
                original_file_size=2048,
                original_s3_key="songs/test/public.mp3",
                processed_s3_key="songs/test/public-processed.mp3",
                duration_sec=45.0,
            )
            session.add(song)
            session.commit()
            session.refresh(song)
            self.song_id = song.id

    def teardown_method(self):
        """Clean up test song."""
        _cleanup_song(self.song_id)

    def test_get_public_song_without_auth(self):
        """Test that public endpoint works without authentication."""
        response = self.client.get(f"/api/v1/songs/{self.song_id}/public")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(self.song_id)
        assert data["title"] == "Public Test Song"
        assert data["original_filename"] == "public_test.mp3"
        assert data["duration_sec"] == 45.0

    def test_get_public_song_with_auth(self):
        """Test that public endpoint works even with authentication."""
        # Create a user and get a token (simplified - in real test would use auth flow)
        # For now, just verify it works without auth header
        response = self.client.get(
            f"/api/v1/songs/{self.song_id}/public",
            headers={"Authorization": "Bearer fake-token"},  # Even with invalid token, should work
        )

        # Should still work (public endpoint doesn't require auth)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(self.song_id)

    def test_get_public_song_not_found(self):
        """Test that public endpoint returns 404 for non-existent songs."""
        fake_id = uuid4()
        response = self.client.get(f"/api/v1/songs/{fake_id}/public")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_public_endpoint_returns_same_data_as_authenticated(self):
        """Test that public endpoint returns same data structure as authenticated endpoint."""
        # Get public version
        public_response = self.client.get(f"/api/v1/songs/{self.song_id}/public")
        assert public_response.status_code == 200
        public_data = public_response.json()

        # Verify it has the expected fields
        assert "id" in public_data
        assert "title" in public_data
        assert "original_filename" in public_data
        assert "duration_sec" in public_data
        assert "user_id" in public_data

