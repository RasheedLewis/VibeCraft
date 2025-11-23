"""Unit tests for character image generation service.

Tests character image generation logic with mocked Replicate client.
Validates core business logic in isolation - fast.

Run with: pytest backend/tests/unit/test_character_image_generation.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.character_image_generation import (  # noqa: E402
    generate_consistent_character_image,
)


class TestGenerateConsistentCharacterImage:
    """Test character image generation with mocked Replicate API."""

    @patch("app.services.character_image_generation.get_settings")
    @patch("app.services.character_image_generation.replicate.Client")
    def test_successful_generation(self, mock_client_class, mock_get_settings):
        """Test successful character image generation."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock model and version
        mock_model = MagicMock()
        mock_version = MagicMock()
        mock_model.latest_version = mock_version
        mock_client.models.get.return_value = mock_model

        # Mock prediction
        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "succeeded"
        mock_prediction.output = "https://replicate.delivery/pbxt/image.jpg"
        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        success, image_url, metadata = generate_consistent_character_image(
            reference_image_url="https://example.com/ref.jpg",
            interrogation_prompt="test prompt",
            character_description="test description",
            max_poll_attempts=1,
        )

        assert success is True
        assert image_url == "https://replicate.delivery/pbxt/image.jpg"
        assert metadata["job_id"] == "pred-123"
        assert metadata["model"] == "stability-ai/sdxl"

    @patch("app.services.character_image_generation.get_settings")
    @patch("app.services.character_image_generation.replicate.Client")
    def test_handles_list_output(self, mock_client_class, mock_get_settings):
        """Test that list output is handled correctly."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_model = MagicMock()
        mock_version = MagicMock()
        mock_model.latest_version = mock_version
        mock_client.models.get.return_value = mock_model

        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "succeeded"
        mock_prediction.output = ["https://replicate.delivery/pbxt/image.jpg"]
        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        success, image_url, metadata = generate_consistent_character_image(
            reference_image_url="https://example.com/ref.jpg",
            interrogation_prompt="test prompt",
            character_description="test description",
            max_poll_attempts=1,
        )

        assert success is True
        assert image_url == "https://replicate.delivery/pbxt/image.jpg"

    @patch("app.services.character_image_generation.get_settings")
    @patch("app.services.character_image_generation.replicate.Client")
    def test_handles_dict_output(self, mock_client_class, mock_get_settings):
        """Test that dict output is handled correctly."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_model = MagicMock()
        mock_version = MagicMock()
        mock_model.latest_version = mock_version
        mock_client.models.get.return_value = mock_model

        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "succeeded"
        mock_prediction.output = {"image": "https://replicate.delivery/pbxt/image.jpg"}
        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        success, image_url, metadata = generate_consistent_character_image(
            reference_image_url="https://example.com/ref.jpg",
            interrogation_prompt="test prompt",
            character_description="test description",
            max_poll_attempts=1,
        )

        assert success is True
        assert image_url == "https://replicate.delivery/pbxt/image.jpg"

    @patch("app.services.character_image_generation.get_settings")
    @patch("app.services.character_image_generation.replicate.Client")
    def test_handles_failed_generation(self, mock_client_class, mock_get_settings):
        """Test handling of failed generation."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_model = MagicMock()
        mock_version = MagicMock()
        mock_model.latest_version = mock_version
        mock_client.models.get.return_value = mock_model

        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "failed"
        mock_prediction.error = "Generation failed"
        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        success, image_url, metadata = generate_consistent_character_image(
            reference_image_url="https://example.com/ref.jpg",
            interrogation_prompt="test prompt",
            character_description="test description",
            max_poll_attempts=1,
        )

        assert success is False
        assert image_url is None
        assert metadata["error"] == "Generation failed"

    @patch("app.services.character_image_generation.get_settings")
    @patch("app.services.character_image_generation.replicate.Client")
    def test_handles_timeout(self, mock_client_class, mock_get_settings):
        """Test handling of timeout."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_model = MagicMock()
        mock_version = MagicMock()
        mock_model.latest_version = mock_version
        mock_client.models.get.return_value = mock_model

        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "processing"
        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        success, image_url, metadata = generate_consistent_character_image(
            reference_image_url="https://example.com/ref.jpg",
            interrogation_prompt="test prompt",
            character_description="test description",
            max_poll_attempts=2,
            poll_interval_sec=0.01,
        )

        assert success is False
        assert image_url is None
        assert "error" in metadata
        assert "Timeout" in metadata["error"]

    @patch("app.services.character_image_generation.get_settings")
    def test_returns_false_when_no_token(self, mock_get_settings):
        """Test that function returns False when Replicate token is not configured."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = None
        mock_get_settings.return_value = mock_settings

        success, image_url, metadata = generate_consistent_character_image(
            reference_image_url="https://example.com/ref.jpg",
            interrogation_prompt="test prompt",
            character_description="test description",
        )

        assert success is False
        assert image_url is None
        assert metadata["error"] == "REPLICATE_API_TOKEN not configured"

    @patch("app.services.character_image_generation.get_settings")
    @patch("app.services.character_image_generation.replicate.Client")
    def test_handles_exception(self, mock_client_class, mock_get_settings):
        """Test handling of exceptions during generation."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.models.get.side_effect = Exception("API error")

        success, image_url, metadata = generate_consistent_character_image(
            reference_image_url="https://example.com/ref.jpg",
            interrogation_prompt="test prompt",
            character_description="test description",
        )

        assert success is False
        assert image_url is None
        assert "error" in metadata
        assert "API error" in metadata["error"]

