"""Unit tests for Audjust API client.

Tests external API integration with mocked HTTP requests - no network calls needed.
Covers configuration validation, critical error handling, and response parsing.

Run with: pytest backend/tests/unit/test_audjust_client.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import httpx  # noqa: E402
import pytest  # noqa: E402
from app.services.audjust_client import (  # noqa: E402
    AudjustConfigurationError,
    AudjustRequestError,
    fetch_structure_segments,
)


class TestConfigurationErrors:
    """Test configuration validation."""

    @patch("app.services.audjust_client.get_settings")
    def test_missing_credentials(self, mock_get_settings):
        """Test that missing credentials raises AudjustConfigurationError."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = None
        mock_settings.audjust_api_key = None
        mock_get_settings.return_value = mock_settings

        with pytest.raises(AudjustConfigurationError, match="credentials are not configured"):
            fetch_structure_segments(Path("/tmp/test.mp3"))


class TestUploadUrlRequest:
    """Test upload URL request handling."""

    @patch("app.services.audjust_client.get_settings")
    @patch("app.services.audjust_client.httpx.get")
    def test_upload_url_http_error(self, mock_get, mock_get_settings):
        """Test that HTTP error on upload URL raises AudjustRequestError."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = "https://api.audjust.com"
        mock_settings.audjust_api_key = "test-key"
        mock_settings.audjust_timeout_sec = 30.0
        mock_get_settings.return_value = mock_settings

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("Connection error")
        mock_get.return_value = mock_response

        with pytest.raises(AudjustRequestError, match="Failed to obtain Audjust upload URL"):
            fetch_structure_segments(Path("/tmp/test.mp3"))

    @patch("app.services.audjust_client.get_settings")
    @patch("app.services.audjust_client.httpx.get")
    def test_missing_storage_url(self, mock_get, mock_get_settings):
        """Test that missing storageUrl raises AudjustRequestError."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = "https://api.audjust.com"
        mock_settings.audjust_api_key = "test-key"
        mock_settings.audjust_timeout_sec = 30.0
        mock_get_settings.return_value = mock_settings

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "retrievalUrl": "https://storage.example.com/retrieve",
            # Missing storageUrl
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with pytest.raises(AudjustRequestError, match="did not return storage/retrieval URLs"):
            fetch_structure_segments(Path("/tmp/test.mp3"))


class TestFileUpload:
    """Test file upload handling."""

    @patch("app.services.audjust_client.Path.open")
    @patch("app.services.audjust_client.get_settings")
    @patch("app.services.audjust_client.httpx.put")
    @patch("app.services.audjust_client.httpx.get")
    def test_upload_http_error(self, mock_get, mock_put, mock_get_settings, mock_path_open):
        """Test that HTTP error on upload raises AudjustRequestError."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = "https://api.audjust.com"
        mock_settings.audjust_api_key = "test-key"
        mock_settings.audjust_timeout_sec = 30.0
        mock_get_settings.return_value = mock_settings

        upload_response = MagicMock()
        upload_response.json.return_value = {
            "storageUrl": "https://storage.example.com/upload",
            "retrievalUrl": "https://storage.example.com/retrieve",
        }
        upload_response.raise_for_status = MagicMock()
        mock_get.return_value = upload_response

        put_response = MagicMock()
        put_response.raise_for_status.side_effect = httpx.HTTPError("Upload failed")
        mock_put.return_value = put_response

        # Mock file opening
        mock_file_handle = MagicMock()
        mock_file_handle.read.return_value = b"fake audio data"
        mock_path_open.return_value.__enter__.return_value = mock_file_handle

        with pytest.raises(AudjustRequestError, match="Failed to upload audio to Audjust storage"):
            fetch_structure_segments(Path("/tmp/test.mp3"))


class TestStructureApiCall:
    """Test structure API call handling."""

    @patch("app.services.audjust_client.Path.open")
    @patch("app.services.audjust_client.get_settings")
    @patch("app.services.audjust_client.httpx.post")
    @patch("app.services.audjust_client.httpx.put")
    @patch("app.services.audjust_client.httpx.get")
    def test_structure_success(self, mock_get, mock_put, mock_post, mock_get_settings, mock_path_open):
        """Test successful structure API call."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = "https://api.audjust.com"
        mock_settings.audjust_api_key = "test-key"
        mock_settings.audjust_upload_path = "/upload"
        mock_settings.audjust_structure_path = "/structure"
        mock_settings.audjust_timeout_sec = 30.0
        mock_get_settings.return_value = mock_settings

        upload_response = MagicMock()
        upload_response.json.return_value = {
            "storageUrl": "https://storage.example.com/upload",
            "retrievalUrl": "https://storage.example.com/retrieve",
        }
        upload_response.raise_for_status = MagicMock()
        mock_get.return_value = upload_response

        put_response = MagicMock()
        put_response.raise_for_status = MagicMock()
        mock_put.return_value = put_response

        structure_response = MagicMock()
        structure_response.status_code = 200
        structure_response.json.return_value = {
            "sections": [
                {"startMs": 0, "endMs": 5000, "label": 100},
                {"startMs": 5000, "endMs": 10000, "label": 200},
            ]
        }
        mock_post.return_value = structure_response

        # Mock file opening
        mock_file_handle = MagicMock()
        mock_file_handle.read.return_value = b"fake audio data"
        mock_path_open.return_value.__enter__.return_value = mock_file_handle

        result = fetch_structure_segments(Path("/tmp/test.mp3"))
        assert len(result) == 2
        assert result[0]["label"] == 100
        assert result[1]["label"] == 200

    @patch("app.services.audjust_client.Path.open")
    @patch("app.services.audjust_client.get_settings")
    @patch("app.services.audjust_client.httpx.post")
    @patch("app.services.audjust_client.httpx.put")
    @patch("app.services.audjust_client.httpx.get")
    def test_structure_http_error(self, mock_get, mock_put, mock_post, mock_get_settings, mock_path_open):
        """Test that HTTP error on structure call raises AudjustRequestError."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = "https://api.audjust.com"
        mock_settings.audjust_api_key = "test-key"
        mock_settings.audjust_timeout_sec = 30.0
        mock_get_settings.return_value = mock_settings

        upload_response = MagicMock()
        upload_response.json.return_value = {
            "storageUrl": "https://storage.example.com/upload",
            "retrievalUrl": "https://storage.example.com/retrieve",
        }
        upload_response.raise_for_status = MagicMock()
        mock_get.return_value = upload_response

        put_response = MagicMock()
        put_response.raise_for_status = MagicMock()
        mock_put.return_value = put_response

        mock_post.side_effect = httpx.HTTPError("Structure API error")

        # Mock file opening
        mock_file_handle = MagicMock()
        mock_file_handle.read.return_value = b"fake audio data"
        mock_path_open.return_value.__enter__.return_value = mock_file_handle

        with pytest.raises(AudjustRequestError, match="Failed to call Audjust structure endpoint"):
            fetch_structure_segments(Path("/tmp/test.mp3"))

    @patch("app.services.audjust_client.Path.open")
    @patch("app.services.audjust_client.get_settings")
    @patch("app.services.audjust_client.httpx.post")
    @patch("app.services.audjust_client.httpx.put")
    @patch("app.services.audjust_client.httpx.get")
    def test_structure_status_400(self, mock_get, mock_put, mock_post, mock_get_settings, mock_path_open):
        """Test that status code >= 400 raises AudjustRequestError."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = "https://api.audjust.com"
        mock_settings.audjust_api_key = "test-key"
        mock_settings.audjust_timeout_sec = 30.0
        mock_get_settings.return_value = mock_settings

        upload_response = MagicMock()
        upload_response.json.return_value = {
            "storageUrl": "https://storage.example.com/upload",
            "retrievalUrl": "https://storage.example.com/retrieve",
        }
        upload_response.raise_for_status = MagicMock()
        mock_get.return_value = upload_response

        put_response = MagicMock()
        put_response.raise_for_status = MagicMock()
        mock_put.return_value = put_response

        structure_response = MagicMock()
        structure_response.status_code = 400
        structure_response.text = "Bad Request"
        mock_post.return_value = structure_response

        # Mock file opening
        mock_file_handle = MagicMock()
        mock_file_handle.read.return_value = b"fake audio data"
        mock_path_open.return_value.__enter__.return_value = mock_file_handle

        with pytest.raises(AudjustRequestError, match="status 400"):
            fetch_structure_segments(Path("/tmp/test.mp3"))


class TestResponseParsing:
    """Test response parsing logic."""

    @patch("app.services.audjust_client.Path.open")
    @patch("app.services.audjust_client.get_settings")
    @patch("app.services.audjust_client.httpx.post")
    @patch("app.services.audjust_client.httpx.put")
    @patch("app.services.audjust_client.httpx.get")
    def test_sections_nested_in_result(self, mock_get, mock_put, mock_post, mock_get_settings, mock_path_open):
        """Test parsing sections from nested result structure (both formats)."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = "https://api.audjust.com"
        mock_settings.audjust_api_key = "test-key"
        mock_settings.audjust_timeout_sec = 30.0
        mock_get_settings.return_value = mock_settings

        upload_response = MagicMock()
        upload_response.json.return_value = {
            "storageUrl": "https://storage.example.com/upload",
            "retrievalUrl": "https://storage.example.com/retrieve",
        }
        upload_response.raise_for_status = MagicMock()
        mock_get.return_value = upload_response

        put_response = MagicMock()
        put_response.raise_for_status = MagicMock()
        mock_put.return_value = put_response

        # Test nested format
        structure_response = MagicMock()
        structure_response.status_code = 200
        structure_response.json.return_value = {
            "result": {
                "sections": [{"startMs": 0, "endMs": 5000, "label": 100}]
            }
        }
        mock_post.return_value = structure_response

        # Mock file opening
        mock_file_handle = MagicMock()
        mock_file_handle.read.return_value = b"fake audio data"
        mock_path_open.return_value.__enter__.return_value = mock_file_handle

        result = fetch_structure_segments(Path("/tmp/test.mp3"))
        assert len(result) == 1

    @patch("app.services.audjust_client.Path.open")
    @patch("app.services.audjust_client.get_settings")
    @patch("app.services.audjust_client.httpx.post")
    @patch("app.services.audjust_client.httpx.put")
    @patch("app.services.audjust_client.httpx.get")
    def test_invalid_json(self, mock_get, mock_put, mock_post, mock_get_settings, mock_path_open):
        """Test that invalid JSON raises AudjustRequestError."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = "https://api.audjust.com"
        mock_settings.audjust_api_key = "test-key"
        mock_settings.audjust_timeout_sec = 30.0
        mock_get_settings.return_value = mock_settings

        upload_response = MagicMock()
        upload_response.json.return_value = {
            "storageUrl": "https://storage.example.com/upload",
            "retrievalUrl": "https://storage.example.com/retrieve",
        }
        upload_response.raise_for_status = MagicMock()
        mock_get.return_value = upload_response

        put_response = MagicMock()
        put_response.raise_for_status = MagicMock()
        mock_put.return_value = put_response

        structure_response = MagicMock()
        structure_response.status_code = 200
        structure_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = structure_response

        # Mock file opening
        mock_file_handle = MagicMock()
        mock_file_handle.read.return_value = b"fake audio data"
        mock_path_open.return_value.__enter__.return_value = mock_file_handle

        with pytest.raises(AudjustRequestError, match="not valid JSON"):
            fetch_structure_segments(Path("/tmp/test.mp3"))

    @patch("app.services.audjust_client.Path.open")
    @patch("app.services.audjust_client.get_settings")
    @patch("app.services.audjust_client.httpx.post")
    @patch("app.services.audjust_client.httpx.put")
    @patch("app.services.audjust_client.httpx.get")
    def test_missing_sections(self, mock_get, mock_put, mock_post, mock_get_settings, mock_path_open):
        """Test that missing sections raises AudjustRequestError."""
        mock_settings = MagicMock()
        mock_settings.audjust_base_url = "https://api.audjust.com"
        mock_settings.audjust_api_key = "test-key"
        mock_settings.audjust_timeout_sec = 30.0
        mock_get_settings.return_value = mock_settings

        upload_response = MagicMock()
        upload_response.json.return_value = {
            "storageUrl": "https://storage.example.com/upload",
            "retrievalUrl": "https://storage.example.com/retrieve",
        }
        upload_response.raise_for_status = MagicMock()
        mock_get.return_value = upload_response

        put_response = MagicMock()
        put_response.raise_for_status = MagicMock()
        mock_put.return_value = put_response

        structure_response = MagicMock()
        structure_response.status_code = 200
        structure_response.json.return_value = {}  # No sections
        mock_post.return_value = structure_response

        # Mock file opening
        mock_file_handle = MagicMock()
        mock_file_handle.read.return_value = b"fake audio data"
        mock_path_open.return_value.__enter__.return_value = mock_file_handle

        with pytest.raises(AudjustRequestError, match="did not include sections"):
            fetch_structure_segments(Path("/tmp/test.mp3"))
