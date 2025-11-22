"""Unit tests for character image storage functions.

Tests storage helper functions for character images.

Run with: pytest backend/tests/unit/test_storage_character.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.storage import (  # noqa: E402
    get_character_image_s3_key,
    upload_consistent_character_image,
)


class TestGetCharacterImageS3Key:
    """Test S3 key generation for character images."""

    def test_reference_image_key(self):
        """Test generating key for reference image."""
        song_id = str(uuid4())
        key = get_character_image_s3_key(song_id, "reference")

        assert key == f"songs/{song_id}/character_reference.jpg"

    def test_generated_image_key(self):
        """Test generating key for generated image."""
        song_id = str(uuid4())
        key = get_character_image_s3_key(song_id, "generated")

        assert key == f"songs/{song_id}/character_generated.jpg"

    def test_invalid_image_type(self):
        """Test that invalid image type raises error."""
        song_id = str(uuid4())

        with pytest.raises(ValueError, match="Unknown image_type"):
            get_character_image_s3_key(song_id, "invalid")


class TestUploadConsistentCharacterImage:
    """Test uploading consistent character images."""

    @patch("app.services.storage.get_settings")
    @patch("app.services.storage.get_character_image_s3_key")
    @patch("app.services.storage.upload_bytes_to_s3")
    def test_successful_upload(
        self, mock_upload, mock_get_key, mock_get_settings
    ):
        """Test successful upload of consistent character image."""
        song_id = str(uuid4())
        image_bytes = b"fake image bytes"

        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_get_key.return_value = f"songs/{song_id}/character_generated.jpg"

        s3_key = upload_consistent_character_image(
            song_id=song_id,
            image_bytes=image_bytes,
            content_type="image/jpeg",
        )

        assert s3_key == f"songs/{song_id}/character_generated.jpg"
        mock_get_key.assert_called_once_with(song_id, image_type="generated")
        mock_upload.assert_called_once_with(
            bucket_name="test-bucket",
            key=f"songs/{song_id}/character_generated.jpg",
            data=image_bytes,
            content_type="image/jpeg",
        )

    @patch("app.services.storage.get_settings")
    @patch("app.services.storage.get_character_image_s3_key")
    @patch("app.services.storage.upload_bytes_to_s3")
    def test_upload_with_default_content_type(
        self, mock_upload, mock_get_key, mock_get_settings
    ):
        """Test upload uses default content type when not specified."""
        song_id = str(uuid4())
        image_bytes = b"fake image bytes"

        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_get_key.return_value = f"songs/{song_id}/character_generated.jpg"

        upload_consistent_character_image(
            song_id=song_id,
            image_bytes=image_bytes,
        )

        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args.kwargs["content_type"] == "image/jpeg"

