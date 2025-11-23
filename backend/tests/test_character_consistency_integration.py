"""Integration tests for character consistency workflow.

Tests the end-to-end character consistency flow:
1. Upload character image
2. Background job generates consistent character image
3. Clip generation uses character image
4. Video composition includes character consistency

Note: These tests require a running database. They are skipped if database is not available.

Run with: pytest backend/tests/test_character_consistency_integration.py -v
"""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch
from uuid import uuid4

from PIL import Image
from fastapi.testclient import TestClient

import pytest

from app.core.database import init_db, session_scope
from app.main import create_app
from app.models.song import DEFAULT_USER_ID, Song

# Try to initialize DB, skip tests if it fails (no database available)
try:
    init_db()
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False


def _create_test_image(format: str = "JPEG", width: int = 512, height: int = 512) -> bytes:
    """Create a test image in memory (valid image format)."""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    output = BytesIO()
    img.save(output, format=format)
    return output.getvalue()


def _cleanup_song(song_id: uuid4) -> None:
    """Clean up test song and related records."""
    with session_scope() as session:
        song = session.get(Song, song_id)
        if song:
            session.delete(song)
        session.commit()


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestCharacterImageUpload:
    """Tests for character image upload endpoint."""

    @patch("app.api.v1.routes_songs.upload_bytes_to_s3")
    @patch("app.api.v1.routes_songs.generate_presigned_get_url")
    @patch("app.core.queue.get_queue")
    def test_upload_character_image_success(
        self, mock_get_queue, mock_presigned, mock_upload
    ):
        """Test successful character image upload."""
        # Create test song
        song_id = uuid4()
        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                original_filename="test.mp3",
                original_file_size=1000,
                original_s3_key="songs/test.mp3",
                video_type="short_form",
            )
            session.add(song)
            session.commit()

        try:
            # Setup mocks
            mock_presigned.return_value = "https://presigned-url.com/image.jpg"
            mock_queue = MagicMock()
            mock_get_queue.return_value = mock_queue

            image_bytes = _create_test_image()

            with TestClient(create_app()) as client:
                response = client.post(
                    f"/api/v1/songs/{song_id}/character-image",
                    files={"image": ("test.jpg", image_bytes, "image/jpeg")},
                )

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "uploaded"
                assert "image_s3_key" in data
                assert "image_url" in data
                assert data["character_consistency_enabled"] is True

                # Verify background job was enqueued
                mock_get_queue.assert_called_once()
                assert mock_queue.enqueue.called

                # Verify song was updated
                with session_scope() as session:
                    updated_song = session.get(Song, song_id)
                    assert updated_song.character_reference_image_s3_key is not None
                    assert updated_song.character_consistency_enabled is True

        finally:
            _cleanup_song(song_id)

    def test_upload_character_image_wrong_video_type(self):
        """Test that character image upload fails for non-short_form videos."""
        # Create test song with full_length video type
        song_id = uuid4()
        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                original_filename="test.mp3",
                original_file_size=1000,
                original_s3_key="songs/test.mp3",
                video_type="full_length",
            )
            session.add(song)
            session.commit()

        try:
            image_bytes = _create_test_image()

            with TestClient(create_app()) as client:
                response = client.post(
                    f"/api/v1/songs/{song_id}/character-image",
                    files={"image": ("test.jpg", image_bytes, "image/jpeg")},
                )

                assert response.status_code == 400
                assert "short_form" in response.json()["detail"].lower()

        finally:
            _cleanup_song(song_id)

    def test_upload_character_image_invalid_format(self):
        """Test that invalid image format is rejected."""
        song_id = uuid4()
        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                original_filename="test.mp3",
                original_file_size=1000,
                original_s3_key="songs/test.mp3",
                video_type="short_form",
            )
            session.add(song)
            session.commit()

        try:
            # Create invalid file (not an image)
            invalid_bytes = b"not an image"

            with TestClient(create_app()) as client:
                response = client.post(
                    f"/api/v1/songs/{song_id}/character-image",
                    files={"image": ("test.txt", invalid_bytes, "text/plain")},
                )

                assert response.status_code == 400
                assert "image" in response.json()["detail"].lower()

        finally:
            _cleanup_song(song_id)


@pytest.mark.skipif(not DB_AVAILABLE, reason="Database not available")
class TestCharacterConsistencyWorkflow:
    """Tests for end-to-end character consistency workflow."""

    @patch("app.services.character_consistency.download_bytes_from_s3")
    @patch("app.services.character_consistency.generate_presigned_get_url")
    @patch("app.services.character_consistency.interrogate_reference_image")
    @patch("app.services.character_consistency.generate_consistent_character_image")
    @patch("app.services.character_consistency.httpx.get")
    @patch("app.services.character_consistency.upload_consistent_character_image")
    def test_character_image_generation_job_success(
        self,
        mock_upload,
        mock_httpx_get,
        mock_generate,
        mock_interrogate,
        mock_presigned,
        mock_download,
    ):
        """Test successful character image generation job."""
        from app.services.character_consistency import generate_character_image_job

        song_id = uuid4()
        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                original_filename="test.mp3",
                original_file_size=1000,
                original_s3_key="songs/test.mp3",
                video_type="short_form",
                character_reference_image_s3_key="songs/test/character_reference.jpg",
            )
            session.add(song)
            session.commit()

        try:
            # Setup mocks
            mock_download.return_value = b"image bytes"
            mock_presigned.return_value = "https://presigned-url.com/image.jpg"
            mock_interrogate.return_value = {
                "prompt": "test prompt",
                "character_description": "test description",
                "style_notes": "test notes",
            }
            mock_generate.return_value = (
                True,
                "https://replicate.delivery/pbxt/image.jpg",
                {"job_id": "pred-123"},
            )
            mock_response = MagicMock()
            mock_response.content = b"generated image bytes"
            mock_response.raise_for_status = MagicMock()
            mock_httpx_get.return_value = mock_response
            mock_upload.return_value = "songs/test/character_generated.jpg"

            # Run job
            result = generate_character_image_job(song_id)

            assert result["status"] == "completed"
            assert result["consistent_image_s3_key"] == "songs/test/character_generated.jpg"

            # Verify song was updated
            with session_scope() as session:
                updated_song = session.get(Song, song_id)
                assert updated_song.character_generated_image_s3_key is not None
                assert updated_song.character_interrogation_prompt is not None
                assert updated_song.character_consistency_enabled is True

        finally:
            _cleanup_song(song_id)

    @patch("app.services.character_consistency.download_bytes_from_s3")
    @patch("app.services.character_consistency.generate_presigned_get_url")
    @patch("app.services.character_consistency.interrogate_reference_image")
    @patch("app.services.character_consistency.generate_consistent_character_image")
    def test_character_image_generation_job_failure(
        self, mock_generate, mock_interrogate, mock_presigned, mock_download
    ):
        """Test character image generation job handles failures gracefully."""
        from app.services.character_consistency import generate_character_image_job

        song_id = uuid4()
        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                original_filename="test.mp3",
                original_file_size=1000,
                original_s3_key="songs/test.mp3",
                video_type="short_form",
                character_reference_image_s3_key="songs/test/character_reference.jpg",
                character_consistency_enabled=True,
            )
            session.add(song)
            session.commit()

        try:
            # Setup mocks for failure
            mock_download.return_value = b"image bytes"
            mock_presigned.return_value = "https://presigned-url.com/image.jpg"
            mock_interrogate.return_value = {
                "prompt": "test prompt",
                "character_description": "test description",
                "style_notes": "test notes",
            }
            mock_generate.return_value = (False, None, {"error": "Generation failed"})

            # Run job
            result = generate_character_image_job(song_id)

            assert result["status"] == "failed"
            assert "error" in result

            # Verify song was updated to disable consistency
            with session_scope() as session:
                updated_song = session.get(Song, song_id)
                assert updated_song.character_consistency_enabled is False

        finally:
            _cleanup_song(song_id)

