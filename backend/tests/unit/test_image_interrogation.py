"""Unit tests for image interrogation service.

Tests image interrogation logic with mocked OpenAI and Replicate clients.
Validates core business logic in isolation - fast.

Run with: pytest backend/tests/unit/test_image_interrogation.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.image_interrogation import (  # noqa: E402
    _interrogate_with_openai,
    _interrogate_with_replicate,
    interrogate_reference_image,
)


class TestInterrogateReferenceImage:
    """Test image interrogation with mocked APIs."""

    @patch("app.services.image_interrogation.get_settings")
    @patch("app.services.image_interrogation._interrogate_with_openai")
    def test_uses_openai_when_available(self, mock_openai, mock_get_settings):
        """Test that OpenAI is used when API key is available."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.replicate_api_token = None
        mock_get_settings.return_value = mock_settings

        mock_openai.return_value = {
            "prompt": "test prompt",
            "character_description": "test description",
            "style_notes": "test notes",
        }

        result = interrogate_reference_image("https://example.com/image.jpg")

        assert result["prompt"] == "test prompt"
        assert result["character_description"] == "test description"
        assert result["style_notes"] == "test notes"
        mock_openai.assert_called_once()

    @patch("app.services.image_interrogation.get_settings")
    @patch("app.services.image_interrogation._interrogate_with_openai")
    @patch("app.services.image_interrogation._interrogate_with_replicate")
    def test_falls_back_to_replicate_on_openai_error(
        self, mock_replicate, mock_openai, mock_get_settings
    ):
        """Test that Replicate is used as fallback when OpenAI fails."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_openai.side_effect = Exception("OpenAI error")
        mock_replicate.return_value = {
            "prompt": "replicate prompt",
            "character_description": "replicate description",
            "style_notes": "replicate notes",
        }

        result = interrogate_reference_image("https://example.com/image.jpg")

        assert result["prompt"] == "replicate prompt"
        mock_openai.assert_called_once()
        mock_replicate.assert_called_once()

    @patch("app.services.image_interrogation.get_settings")
    @patch("app.services.image_interrogation._interrogate_with_replicate")
    def test_uses_replicate_when_openai_unavailable(self, mock_replicate, mock_get_settings):
        """Test that Replicate is used when OpenAI key is not available."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_replicate.return_value = {
            "prompt": "replicate prompt",
            "character_description": "replicate description",
            "style_notes": "replicate notes",
        }

        result = interrogate_reference_image("https://example.com/image.jpg")

        assert result["prompt"] == "replicate prompt"
        mock_replicate.assert_called_once()

    @patch("app.services.image_interrogation.get_settings")
    def test_raises_error_when_no_api_available(self, mock_get_settings):
        """Test that error is raised when neither API is available."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = None
        mock_settings.replicate_api_token = None
        mock_get_settings.return_value = mock_settings

        with pytest.raises(RuntimeError, match="Neither OpenAI API key nor Replicate API token"):
            interrogate_reference_image("https://example.com/image.jpg")


class TestInterrogateWithOpenAI:
    """Test OpenAI-based interrogation."""

    @patch("app.services.image_interrogation.get_settings")
    @patch("app.services.image_interrogation.OpenAI")
    def test_successful_interrogation_with_url(self, mock_openai_class, mock_get_settings):
        """Test successful interrogation with image URL."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"detailed_prompt": "test prompt", "character_description": "test desc", "style_notes": "test notes"}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = _interrogate_with_openai("https://example.com/image.jpg")

        assert result["prompt"] == "test prompt"
        assert result["character_description"] == "test desc"
        assert result["style_notes"] == "test notes"
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.services.image_interrogation.get_settings")
    @patch("app.services.image_interrogation.OpenAI")
    def test_successful_interrogation_with_bytes(self, mock_openai_class, mock_get_settings):
        """Test successful interrogation with image bytes."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(
                    content='{"detailed_prompt": "test prompt", "character_description": "test desc", "style_notes": "test notes"}'
                )
            )
        ]
        mock_client.chat.completions.create.return_value = mock_response

        image_bytes = b"fake image bytes"
        result = _interrogate_with_openai("https://example.com/image.jpg", image_bytes=image_bytes)

        assert result["prompt"] == "test prompt"
        # Verify base64 encoding was used
        call_args = mock_client.chat.completions.create.call_args
        content = call_args[1]["messages"][0]["content"]
        assert any(item.get("image_url", {}).get("url", "").startswith("data:image") for item in content)

    @patch("app.services.image_interrogation.get_settings")
    @patch("app.services.image_interrogation.OpenAI")
    def test_handles_missing_fields(self, mock_openai_class, mock_get_settings):
        """Test that missing fields in response are handled gracefully."""
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"detailed_prompt": "test prompt"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        result = _interrogate_with_openai("https://example.com/image.jpg")

        assert result["prompt"] == "test prompt"
        assert result["character_description"] == ""
        assert result["style_notes"] == ""


class TestInterrogateWithReplicate:
    """Test Replicate-based interrogation."""

    @patch("app.services.image_interrogation.get_settings")
    @patch("app.services.image_interrogation.replicate.Client")
    def test_successful_interrogation(self, mock_client_class, mock_get_settings):
        """Test successful interrogation with Replicate."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.run.return_value = "A detailed character description with many features"

        result = _interrogate_with_replicate("https://example.com/image.jpg")

        assert "prompt" in result
        assert "character_description" in result
        assert "style_notes" in result
        assert result["prompt"] == "A detailed character description with many features"
        mock_client.run.assert_called_once()

    @patch("app.services.image_interrogation.get_settings")
    @patch("app.services.image_interrogation.replicate.Client")
    def test_handles_non_string_output(self, mock_client_class, mock_get_settings):
        """Test that non-string output is converted to string."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.run.return_value = ["list", "output"]

        result = _interrogate_with_replicate("https://example.com/image.jpg")

        assert isinstance(result["prompt"], str)
        assert "list" in result["prompt"] or "output" in result["prompt"]

