"""Unit tests for template characters service.

Tests template character management logic including character retrieval,
image fetching, and S3 operations. Mocks S3 operations for fast execution.

Run with: pytest backend/tests/unit/test_template_characters.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.template_characters import (  # noqa: E402
    copy_template_pose_to_song,
    get_template_character,
    get_template_character_image,
    get_template_characters,
)


class TestGetTemplateCharacters:
    """Test get_template_characters function."""

    @patch("app.services.template_characters.get_settings")
    @patch("app.services.template_characters.generate_presigned_get_url")
    def test_get_template_characters_success(self, mock_presigned_url, mock_get_settings):
        """Test successful retrieval of template characters with presigned URLs."""
        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_presigned_url.return_value = "https://s3.example.com/presigned-url"

        characters = get_template_characters()

        assert len(characters) == 4
        assert all("id" in char for char in characters)
        assert all("name" in char for char in characters)
        assert all("poses" in char for char in characters)
        assert all("default_pose" in char for char in characters)

        # Verify first character structure
        char1 = characters[0]
        assert char1["id"] == "character-1"
        assert len(char1["poses"]) == 2
        assert all("id" in pose for pose in char1["poses"])
        assert all("thumbnail_url" in pose for pose in char1["poses"])
        assert all("image_url" in pose for pose in char1["poses"])

    @patch("app.services.template_characters.get_settings")
    @patch("app.services.template_characters.generate_presigned_get_url")
    def test_get_template_characters_presigned_url_failure(self, mock_presigned_url, mock_get_settings):
        """Test handling of presigned URL generation failures."""
        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_presigned_url.side_effect = Exception("S3 error")

        # Should still return characters but without URLs
        characters = get_template_characters()

        # Should return empty list if all presigned URLs fail
        assert len(characters) == 0


class TestGetTemplateCharacter:
    """Test get_template_character function."""

    def test_get_template_character_success(self):
        """Test successful retrieval of character by ID."""
        char = get_template_character("character-1")

        assert char is not None
        assert char["id"] == "character-1"
        assert "name" in char
        assert "poses" in char
        assert "default_pose" in char

    def test_get_template_character_not_found(self):
        """Test retrieval of non-existent character."""
        char = get_template_character("character-999")

        assert char is None

    def test_get_template_character_all_ids(self):
        """Test retrieval of all defined characters."""
        for i in range(1, 5):
            char = get_template_character(f"character-{i}")
            assert char is not None
            assert char["id"] == f"character-{i}"


class TestGetTemplateCharacterImage:
    """Test get_template_character_image function."""

    @patch("app.services.template_characters.get_settings")
    @patch("app.services.template_characters.download_bytes_from_s3")
    def test_get_template_character_image_success(self, mock_download, mock_get_settings):
        """Test successful image download."""
        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_download.return_value = b"fake-image-bytes"

        image_bytes = get_template_character_image("character-1", "pose-a")

        assert image_bytes == b"fake-image-bytes"
        mock_download.assert_called_once()
        call_args = mock_download.call_args
        assert call_args.kwargs["bucket_name"] == "test-bucket"
        assert "character1-pose1.png" in call_args.kwargs["key"]

    @patch("app.services.template_characters.get_settings")
    @patch("app.services.template_characters.download_bytes_from_s3")
    def test_get_template_character_image_pose_b(self, mock_download, mock_get_settings):
        """Test downloading pose-b image."""
        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_download.return_value = b"fake-image-bytes"

        image_bytes = get_template_character_image("character-1", "pose-b")

        assert image_bytes == b"fake-image-bytes"
        call_args = mock_download.call_args
        assert "character1-pose2.png" in call_args.kwargs["key"]

    def test_get_template_character_image_invalid_character(self):
        """Test image download with invalid character ID."""
        image_bytes = get_template_character_image("character-999", "pose-a")

        assert image_bytes is None

    def test_get_template_character_image_invalid_pose(self):
        """Test image download with invalid pose."""
        image_bytes = get_template_character_image("character-1", "pose-invalid")

        assert image_bytes is None

    @patch("app.services.template_characters.get_settings")
    @patch("app.services.template_characters.download_bytes_from_s3")
    def test_get_template_character_image_s3_error(self, mock_download, mock_get_settings):
        """Test handling of S3 download errors."""
        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_download.side_effect = Exception("S3 download failed")

        image_bytes = get_template_character_image("character-1", "pose-a")

        assert image_bytes is None


class TestCopyTemplatePoseToSong:
    """Test copy_template_pose_to_song function."""

    @patch("app.services.template_characters.get_settings")
    @patch("app.services.template_characters.upload_bytes_to_s3")
    @patch("app.services.template_characters.get_template_character_image")
    def test_copy_template_pose_to_song_success(
        self, mock_get_image, mock_upload, mock_get_settings
    ):
        """Test successful copy of template pose to song."""
        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_get_image.return_value = b"fake-image-bytes"

        result = copy_template_pose_to_song("character-1", "pose-a", "songs/test/pose_a.jpg")

        assert result is True
        mock_get_image.assert_called_once_with("character-1", "pose-a")
        mock_upload.assert_called_once()
        call_args = mock_upload.call_args
        assert call_args.kwargs["bucket_name"] == "test-bucket"
        assert call_args.kwargs["key"] == "songs/test/pose_a.jpg"
        assert call_args.kwargs["data"] == b"fake-image-bytes"
        assert call_args.kwargs["content_type"] == "image/jpeg"

    @patch("app.services.template_characters.get_template_character_image")
    def test_copy_template_pose_to_song_image_not_found(self, mock_get_image):
        """Test copy when template image is not found."""
        mock_get_image.return_value = None

        result = copy_template_pose_to_song("character-1", "pose-a", "songs/test/pose_a.jpg")

        assert result is False

    @patch("app.services.template_characters.get_settings")
    @patch("app.services.template_characters.upload_bytes_to_s3")
    @patch("app.services.template_characters.get_template_character_image")
    def test_copy_template_pose_to_song_upload_failure(
        self, mock_get_image, mock_upload, mock_get_settings
    ):
        """Test handling of S3 upload failures."""
        mock_settings = MagicMock()
        mock_settings.s3_bucket_name = "test-bucket"
        mock_get_settings.return_value = mock_settings

        mock_get_image.return_value = b"fake-image-bytes"
        mock_upload.side_effect = Exception("S3 upload failed")

        result = copy_template_pose_to_song("character-1", "pose-a", "songs/test/pose_a.jpg")

        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

