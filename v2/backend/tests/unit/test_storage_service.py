"""Unit tests for storage service.

Tests S3 operations with mocked boto3 client - no real AWS needed, fast (~0.1s).
Validates upload, download, presigned URLs, and delete operations with error handling.

Run with: pytest backend/tests/unit/test_storage_service.py -v
Or from backend/: pytest tests/unit/test_storage_service.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import BotoCoreError, ClientError

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Mock settings before importing modules that use get_settings()
mock_settings = MagicMock()
mock_settings.aws_access_key_id = "test-key"
mock_settings.aws_secret_access_key = "test-secret"
mock_settings.s3_bucket_name = "test-bucket"
with patch("app.core.config.get_settings", return_value=mock_settings):
    from app.services.storage_service import (  # noqa: E402
        delete_from_s3,
        download_bytes_from_s3,
        generate_presigned_get_url,
        generate_presigned_put_url,
        upload_bytes_to_s3,
    )


class TestUploadBytesToS3:
    """Test S3 upload functionality."""

    @patch("app.services.storage_service._get_s3_client")
    def test_upload_success_without_content_type(self, mock_get_client):
        """Test successful upload without content type."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        upload_bytes_to_s3(
            bucket="test-bucket",
            key="test/key.mp3",
            data=b"audio content",
        )

        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/key.mp3",
            Body=b"audio content",
        )

    @patch("app.services.storage_service._get_s3_client")
    def test_upload_success_with_content_type(self, mock_get_client):
        """Test successful upload with content type."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        upload_bytes_to_s3(
            bucket="test-bucket",
            key="test/key.mp3",
            data=b"audio content",
            content_type="audio/mpeg",
        )

        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/key.mp3",
            Body=b"audio content",
            ContentType="audio/mpeg",
        )

    @patch("app.services.storage_service._get_s3_client")
    def test_upload_failure_boto_error(self, mock_get_client):
        """Test upload failure with BotoCoreError."""
        mock_client = MagicMock()
        mock_client.put_object.side_effect = BotoCoreError()
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to upload object"):
            upload_bytes_to_s3(
                bucket="test-bucket",
                key="test/key.mp3",
                data=b"audio content",
            )

    @patch("app.services.storage_service._get_s3_client")
    def test_upload_failure_client_error(self, mock_get_client):
        """Test upload failure with ClientError."""
        mock_client = MagicMock()
        mock_client.put_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "PutObject",
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to upload object"):
            upload_bytes_to_s3(
                bucket="test-bucket",
                key="test/key.mp3",
                data=b"audio content",
            )


class TestDownloadBytesFromS3:
    """Test S3 download functionality."""

    @patch("app.services.storage_service._get_s3_client")
    def test_download_success(self, mock_get_client):
        """Test successful download."""
        mock_client = MagicMock()
        mock_body = MagicMock()
        mock_body.read.return_value = b"downloaded content"
        mock_client.get_object.return_value = {"Body": mock_body}
        mock_get_client.return_value = mock_client

        result = download_bytes_from_s3(bucket="test-bucket", key="test/key.mp3")

        assert result == b"downloaded content"
        mock_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/key.mp3",
        )

    @patch("app.services.storage_service._get_s3_client")
    def test_download_failure_boto_error(self, mock_get_client):
        """Test download failure with BotoCoreError."""
        mock_client = MagicMock()
        mock_client.get_object.side_effect = BotoCoreError()
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to download object"):
            download_bytes_from_s3(bucket="test-bucket", key="test/key.mp3")

    @patch("app.services.storage_service._get_s3_client")
    def test_download_failure_no_body(self, mock_get_client):
        """Test download failure when response has no body."""
        mock_client = MagicMock()
        mock_client.get_object.return_value = {"Body": None}
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="No content returned"):
            download_bytes_from_s3(bucket="test-bucket", key="test/key.mp3")


class TestGeneratePresignedGetUrl:
    """Test presigned GET URL generation."""

    @patch("app.services.storage_service._get_s3_client")
    def test_generate_presigned_get_url_success(self, mock_get_client):
        """Test successful presigned GET URL generation."""
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-bucket/test/key.mp3?signature=abc123"
        mock_get_client.return_value = mock_client

        result = generate_presigned_get_url(
            bucket="test-bucket",
            key="test/key.mp3",
            expires_in=3600,
        )

        assert result == "https://s3.amazonaws.com/test-bucket/test/key.mp3?signature=abc123"
        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test/key.mp3"},
            ExpiresIn=3600,
        )

    @patch("app.services.storage_service._get_s3_client")
    def test_generate_presigned_get_url_default_expiry(self, mock_get_client):
        """Test presigned URL with default expiry."""
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://example.com/url"
        mock_get_client.return_value = mock_client

        generate_presigned_get_url(bucket="test-bucket", key="test/key.mp3")

        mock_client.generate_presigned_url.assert_called_once_with(
            "get_object",
            Params={"Bucket": "test-bucket", "Key": "test/key.mp3"},
            ExpiresIn=3600,  # Default
        )

    @patch("app.services.storage_service._get_s3_client")
    def test_generate_presigned_get_url_failure(self, mock_get_client):
        """Test presigned URL generation failure."""
        mock_client = MagicMock()
        mock_client.generate_presigned_url.side_effect = ClientError(
            {"Error": {"Code": "InvalidRequest", "Message": "Invalid request"}},
            "GeneratePresignedUrl",
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to generate presigned URL"):
            generate_presigned_get_url(bucket="test-bucket", key="test/key.mp3")


class TestGeneratePresignedPutUrl:
    """Test presigned PUT URL generation."""

    @patch("app.services.storage_service._get_s3_client")
    def test_generate_presigned_put_url_success(self, mock_get_client):
        """Test successful presigned PUT URL generation."""
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-bucket/test/key.mp3?signature=xyz789"
        mock_get_client.return_value = mock_client

        result = generate_presigned_put_url(
            bucket="test-bucket",
            key="test/key.mp3",
            expires_in=7200,
        )

        assert result == "https://s3.amazonaws.com/test-bucket/test/key.mp3?signature=xyz789"
        mock_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={"Bucket": "test-bucket", "Key": "test/key.mp3"},
            ExpiresIn=7200,
        )

    @patch("app.services.storage_service._get_s3_client")
    def test_generate_presigned_put_url_failure(self, mock_get_client):
        """Test presigned PUT URL generation failure."""
        mock_client = MagicMock()
        mock_client.generate_presigned_url.side_effect = BotoCoreError()
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to generate presigned PUT URL"):
            generate_presigned_put_url(bucket="test-bucket", key="test/key.mp3")


class TestDeleteFromS3:
    """Test S3 delete functionality."""

    @patch("app.services.storage_service._get_s3_client")
    def test_delete_success(self, mock_get_client):
        """Test successful delete."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        delete_from_s3(bucket="test-bucket", key="test/key.mp3")

        mock_client.delete_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="test/key.mp3",
        )

    @patch("app.services.storage_service._get_s3_client")
    def test_delete_failure_boto_error(self, mock_get_client):
        """Test delete failure with BotoCoreError."""
        mock_client = MagicMock()
        mock_client.delete_object.side_effect = BotoCoreError()
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to delete object"):
            delete_from_s3(bucket="test-bucket", key="test/key.mp3")

    @patch("app.services.storage_service._get_s3_client")
    def test_delete_failure_client_error(self, mock_get_client):
        """Test delete failure with ClientError."""
        mock_client = MagicMock()
        mock_client.delete_object.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied", "Message": "Access denied"}},
            "DeleteObject",
        )
        mock_get_client.return_value = mock_client

        with pytest.raises(RuntimeError, match="Failed to delete object"):
            delete_from_s3(bucket="test-bucket", key="test/key.mp3")

