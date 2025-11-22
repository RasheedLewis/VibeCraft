"""Unit tests for character consistency orchestration service.

Tests character consistency job orchestration with mocked dependencies.
Validates core business logic in isolation - fast.

Run with: pytest backend/tests/unit/test_character_consistency.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.models.song import Song  # noqa: E402
from app.services.character_consistency import generate_character_image_job  # noqa: E402


class TestGenerateCharacterImageJob:
    """Test character image generation job orchestration."""

    @patch("app.services.character_consistency.SongRepository")
    @patch("app.services.character_consistency.download_bytes_from_s3")
    @patch("app.services.character_consistency.generate_presigned_get_url")
    @patch("app.services.character_consistency.interrogate_reference_image")
    @patch("app.services.character_consistency.generate_consistent_character_image")
    @patch("app.services.character_consistency.httpx.get")
    @patch("app.services.character_consistency.upload_consistent_character_image")
    @patch("app.services.character_consistency.get_settings")
    def test_successful_job(
        self,
        mock_get_settings,
        mock_upload,
        mock_httpx_get,
        mock_generate,
        mock_interrogate,
        mock_presigned,
        mock_download,
        mock_repo,
    ):
        """Test successful character image generation job."""
        song_id = uuid4()
        
        # Setup song
        song = Song(
            id=song_id,
            character_reference_image_s3_key="songs/test/character_reference.jpg",
            character_consistency_enabled=False,
        )
        mock_repo.get_by_id.return_value = song
        mock_repo.update.return_value = song

        # Setup settings
        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

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

        result = generate_character_image_job(song_id)

        assert result["status"] == "completed"
        assert result["consistent_image_s3_key"] == "songs/test/character_generated.jpg"
        assert song.character_consistency_enabled is True
        assert song.character_generated_image_s3_key == "songs/test/character_generated.jpg"
        assert song.character_interrogation_prompt is not None

        # Verify calls
        mock_repo.get_by_id.assert_called_once_with(song_id)
        mock_download.assert_called_once()
        mock_interrogate.assert_called_once()
        mock_generate.assert_called_once()
        mock_upload.assert_called_once()
        assert mock_repo.update.call_count >= 2  # At least for interrogation and final update

    @patch("app.services.character_consistency.SongRepository")
    @patch("app.services.character_consistency.get_settings")
    def test_skips_when_no_reference_image(self, mock_get_settings, mock_repo):
        """Test that job is skipped when no reference image exists."""
        song_id = uuid4()
        
        song = Song(
            id=song_id,
            character_reference_image_s3_key=None,
        )
        mock_repo.get_by_id.return_value = song

        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        result = generate_character_image_job(song_id)

        assert result["status"] == "skipped"
        assert result["reason"] == "No reference image"

    @patch("app.services.character_consistency.SongRepository")
    @patch("app.services.character_consistency.download_bytes_from_s3")
    @patch("app.services.character_consistency.generate_presigned_get_url")
    @patch("app.services.character_consistency.interrogate_reference_image")
    @patch("app.services.character_consistency.generate_consistent_character_image")
    @patch("app.services.character_consistency.get_settings")
    def test_handles_generation_failure(
        self,
        mock_get_settings,
        mock_generate,
        mock_interrogate,
        mock_presigned,
        mock_download,
        mock_repo,
    ):
        """Test handling of character image generation failure."""
        song_id = uuid4()
        
        song = Song(
            id=song_id,
            character_reference_image_s3_key="songs/test/character_reference.jpg",
            character_consistency_enabled=True,
        )
        mock_repo.get_by_id.return_value = song
        mock_repo.update.return_value = song

        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_download.return_value = b"image bytes"
        mock_presigned.return_value = "https://presigned-url.com/image.jpg"
        mock_interrogate.return_value = {
            "prompt": "test prompt",
            "character_description": "test description",
            "style_notes": "test notes",
        }
        mock_generate.return_value = (False, None, {"error": "Generation failed"})

        result = generate_character_image_job(song_id)

        assert result["status"] == "failed"
        assert result["error"] == "Generation failed"
        assert song.character_consistency_enabled is False

    @patch("app.services.character_consistency.SongRepository")
    @patch("app.services.character_consistency.download_bytes_from_s3")
    @patch("app.services.character_consistency.generate_presigned_get_url")
    @patch("app.services.character_consistency.interrogate_reference_image")
    @patch("app.services.character_consistency.get_settings")
    def test_handles_interrogation_failure(
        self,
        mock_get_settings,
        mock_interrogate,
        mock_presigned,
        mock_download,
        mock_repo,
    ):
        """Test handling of image interrogation failure."""
        song_id = uuid4()
        
        song = Song(
            id=song_id,
            character_reference_image_s3_key="songs/test/character_reference.jpg",
            character_consistency_enabled=True,
        )
        mock_repo.get_by_id.return_value = song
        mock_repo.update.return_value = song

        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_download.return_value = b"image bytes"
        mock_presigned.return_value = "https://presigned-url.com/image.jpg"
        mock_interrogate.side_effect = Exception("Interrogation failed")

        result = generate_character_image_job(song_id)

        assert result["status"] == "failed"
        assert "Interrogation failed" in result["error"]
        assert song.character_consistency_enabled is False

    @patch("app.services.character_consistency.SongRepository")
    @patch("app.services.character_consistency.download_bytes_from_s3")
    @patch("app.services.character_consistency.generate_presigned_get_url")
    @patch("app.services.character_consistency.interrogate_reference_image")
    @patch("app.services.character_consistency.generate_consistent_character_image")
    @patch("app.services.character_consistency.httpx.get")
    @patch("app.services.character_consistency.get_settings")
    def test_handles_http_download_failure(
        self,
        mock_get_settings,
        mock_httpx_get,
        mock_generate,
        mock_interrogate,
        mock_presigned,
        mock_download,
        mock_repo,
    ):
        """Test handling of HTTP download failure."""
        song_id = uuid4()
        
        song = Song(
            id=song_id,
            character_reference_image_s3_key="songs/test/character_reference.jpg",
            character_consistency_enabled=True,
        )
        mock_repo.get_by_id.return_value = song
        mock_repo.update.return_value = song

        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

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
        mock_httpx_get.side_effect = Exception("HTTP error")

        result = generate_character_image_job(song_id)

        assert result["status"] == "failed"
        assert "HTTP error" in result["error"]
        assert song.character_consistency_enabled is False

