"""Unit tests for video generation service.

Tests logic for generating videos via Replicate API - mocks Replicate client, fast (~0.1s).
Validates generate_section_video() and poll_video_generation_status() in isolation.

Run with: pytest backend/tests/unit/test_video_generation.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas.scene import CameraMotion, ColorPalette, SceneSpec, ShotPattern  # noqa: E402
from app.services.video_generation import (  # noqa: E402
    generate_section_video,
    poll_video_generation_status,
)


class TestGenerateSectionVideo:
    """Test video generation with mocked Replicate API."""

    @patch("app.services.video_generation.get_settings")
    @patch("app.services.video_generation.replicate.Client")
    def test_successful_generation(self, mock_client_class, mock_get_settings):
        """Test successful video generation."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock prediction object
        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "succeeded"
        mock_prediction.output = "https://replicate.delivery/pbxt/video.mp4"

        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        # Create scene spec
        scene_spec = SceneSpec(
            sectionId="section-1",
            template="abstract",
            prompt="Test prompt",
            colorPalette=ColorPalette(primary="#FF0000", secondary="#00FF00", accent="#0000FF", mood="vibrant"),
            cameraMotion=CameraMotion(type="slow_pan", intensity=0.5, speed="medium"),
            shotPattern=ShotPattern(pattern="wide", pacing="slow", transitions=["fade"]),
            intensity=0.5,
            durationSec=5.0,
        )

        # Call function
        success, video_url, metadata = generate_section_video(scene_spec, seed=42, max_poll_attempts=1)

        # Assertions
        assert success is True
        assert video_url == "https://replicate.delivery/pbxt/video.mp4"
        assert metadata["job_id"] == "pred-123"
        assert metadata["seed"] == 42
        assert metadata["fps"] == 8
        # Resolution values are implementation details - just verify they exist
        assert "resolution_width" in metadata
        assert "resolution_height" in metadata

        # Verify API calls
        mock_client.predictions.create.assert_called_once()
        mock_client.predictions.get.assert_called_once_with("pred-123")

    @patch("app.services.video_generation.get_settings")
    @patch("app.services.video_generation.replicate.Client")
    def test_failed_generation(self, mock_client_class, mock_get_settings):
        """Test failed video generation."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock failed prediction
        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "failed"
        mock_prediction.error = "Generation failed"

        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        scene_spec = SceneSpec(
            sectionId="section-1",
            template="abstract",
            prompt="Test prompt",
            colorPalette=ColorPalette(primary="#FF0000", secondary="#00FF00", accent="#0000FF", mood="vibrant"),
            cameraMotion=CameraMotion(type="slow_pan", intensity=0.5, speed="medium"),
            shotPattern=ShotPattern(pattern="wide", pacing="slow", transitions=["fade"]),
            intensity=0.5,
            durationSec=5.0,
        )

        success, video_url, metadata = generate_section_video(scene_spec, max_poll_attempts=1)

        assert success is False
        assert video_url is None
        assert metadata["error"] == "Generation failed"

    @patch("app.services.video_generation.get_settings")
    def test_no_api_token(self, mock_get_settings):
        """Test error when API token is not configured."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = None
        mock_get_settings.return_value = mock_settings

        scene_spec = SceneSpec(
            sectionId="section-1",
            template="abstract",
            prompt="Test prompt",
            colorPalette=ColorPalette(primary="#FF0000", secondary="#00FF00", accent="#0000FF", mood="vibrant"),
            cameraMotion=CameraMotion(type="slow_pan", intensity=0.5, speed="medium"),
            shotPattern=ShotPattern(pattern="wide", pacing="slow", transitions=["fade"]),
            intensity=0.5,
            durationSec=5.0,
        )

        success, video_url, metadata = generate_section_video(scene_spec)

        assert success is False
        assert video_url is None
        assert metadata is None

    @patch("app.services.video_generation.get_settings")
    @patch("app.services.video_generation.replicate.Client")
    def test_video_url_from_list_output(self, mock_client_class, mock_get_settings):
        """Test handling video URL from list output format."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "succeeded"
        mock_prediction.output = ["https://replicate.delivery/pbxt/video.mp4"]

        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        scene_spec = SceneSpec(
            sectionId="section-1",
            template="abstract",
            prompt="Test prompt",
            colorPalette=ColorPalette(primary="#FF0000", secondary="#00FF00", accent="#0000FF", mood="vibrant"),
            cameraMotion=CameraMotion(type="slow_pan", intensity=0.5, speed="medium"),
            shotPattern=ShotPattern(pattern="wide", pacing="slow", transitions=["fade"]),
            intensity=0.5,
            durationSec=5.0,
        )

        success, video_url, metadata = generate_section_video(scene_spec, max_poll_attempts=1)

        assert success is True
        assert video_url == "https://replicate.delivery/pbxt/video.mp4"

    @patch("app.services.video_generation.get_settings")
    @patch("app.services.video_generation.replicate.Client")
    def test_generation_with_single_reference_image(self, mock_client_class, mock_get_settings):
        """Test generation with single reference image (existing behavior)."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "succeeded"
        mock_prediction.output = "https://replicate.delivery/pbxt/video.mp4"

        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        scene_spec = SceneSpec(
            sectionId="section-1",
            template="abstract",
            prompt="Test prompt",
            colorPalette=ColorPalette(primary="#FF0000", secondary="#00FF00", accent="#0000FF", mood="vibrant"),
            cameraMotion=CameraMotion(type="slow_pan", intensity=0.5, speed="medium"),
            shotPattern=ShotPattern(pattern="wide", pacing="slow", transitions=["fade"]),
            intensity=0.5,
            durationSec=5.0,
        )

        success, video_url, metadata = generate_section_video(
            scene_spec,
            reference_image_url="https://example.com/image.jpg",
            max_poll_attempts=1,
        )

        assert success is True
        assert video_url == "https://replicate.delivery/pbxt/video.mp4"
        # Verify image parameter was passed
        call_args = mock_client.predictions.create.call_args
        assert call_args.kwargs["input"]["image"] == "https://example.com/image.jpg"

    @patch("app.services.video_generation.get_settings")
    @patch("app.services.video_generation.replicate.Client")
    def test_generation_with_multiple_reference_images(self, mock_client_class, mock_get_settings):
        """Test generation with multiple reference images."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "succeeded"
        mock_prediction.output = "https://replicate.delivery/pbxt/video.mp4"

        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        scene_spec = SceneSpec(
            sectionId="section-1",
            template="abstract",
            prompt="Test prompt",
            colorPalette=ColorPalette(primary="#FF0000", secondary="#00FF00", accent="#0000FF", mood="vibrant"),
            cameraMotion=CameraMotion(type="slow_pan", intensity=0.5, speed="medium"),
            shotPattern=ShotPattern(pattern="wide", pacing="slow", transitions=["fade"]),
            intensity=0.5,
            durationSec=5.0,
        )

        image_urls = ["https://example.com/pose-a.jpg", "https://example.com/pose-b.jpg"]

        success, video_url, metadata = generate_section_video(
            scene_spec,
            reference_image_urls=image_urls,
            max_poll_attempts=1,
        )

        assert success is True
        # Verify multiple images were attempted (may fallback to single)
        call_args = mock_client.predictions.create.call_args
        input_params = call_args.kwargs["input"]
        # Should have either "images" or "image" parameter
        assert "images" in input_params or "image" in input_params

    @patch("app.services.video_generation.get_settings")
    @patch("app.services.video_generation.replicate.Client")
    def test_generation_prioritizes_reference_image_urls_over_single(
        self, mock_client_class, mock_get_settings
    ):
        """Test that reference_image_urls takes priority over reference_image_url."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_prediction = MagicMock()
        mock_prediction.id = "pred-123"
        mock_prediction.status = "succeeded"
        mock_prediction.output = "https://replicate.delivery/pbxt/video.mp4"

        mock_client.predictions.create.return_value = mock_prediction
        mock_client.predictions.get.return_value = mock_prediction

        scene_spec = SceneSpec(
            sectionId="section-1",
            template="abstract",
            prompt="Test prompt",
            colorPalette=ColorPalette(primary="#FF0000", secondary="#00FF00", accent="#0000FF", mood="vibrant"),
            cameraMotion=CameraMotion(type="slow_pan", intensity=0.5, speed="medium"),
            shotPattern=ShotPattern(pattern="wide", pacing="slow", transitions=["fade"]),
            intensity=0.5,
            durationSec=5.0,
        )

        # Provide both single and multiple
        success, video_url, metadata = generate_section_video(
            scene_spec,
            reference_image_url="https://example.com/single.jpg",
            reference_image_urls=["https://example.com/pose-a.jpg", "https://example.com/pose-b.jpg"],
            max_poll_attempts=1,
        )

        assert success is True
        # Verify multiple images were used (not single)
        call_args = mock_client.predictions.create.call_args
        input_params = call_args.kwargs["input"]
        # Should use multiple images, not single
        if "images" in input_params:
            assert len(input_params["images"]) == 2
        elif "image" in input_params:
            # If fallback occurred, should be first image from list
            assert input_params["image"] in ["https://example.com/pose-a.jpg", "https://example.com/pose-b.jpg"]


class TestPollVideoGenerationStatus:
    """Test polling video generation status."""

    @patch("app.services.video_generation.get_settings")
    @patch("app.services.video_generation.replicate.Client")
    def test_poll_completed(self, mock_client_class, mock_get_settings):
        """Test polling completed job."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_prediction = MagicMock()
        mock_prediction.status = "succeeded"
        mock_prediction.output = "https://replicate.delivery/pbxt/video.mp4"

        mock_client.predictions.get.return_value = mock_prediction

        status, video_url, metadata = poll_video_generation_status("pred-123")

        assert status == "completed"
        assert video_url == "https://replicate.delivery/pbxt/video.mp4"
        assert "error" not in metadata

    @patch("app.services.video_generation.get_settings")
    @patch("app.services.video_generation.replicate.Client")
    def test_poll_processing(self, mock_client_class, mock_get_settings):
        """Test polling processing job."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_prediction = MagicMock()
        mock_prediction.status = "processing"

        mock_client.predictions.get.return_value = mock_prediction

        status, video_url, metadata = poll_video_generation_status("pred-123")

        assert status == "processing"
        assert video_url is None

    @patch("app.services.video_generation.get_settings")
    @patch("app.services.video_generation.replicate.Client")
    def test_poll_failed(self, mock_client_class, mock_get_settings):
        """Test polling failed job."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = "test-token"
        mock_get_settings.return_value = mock_settings

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_prediction = MagicMock()
        mock_prediction.status = "failed"
        mock_prediction.error = "Generation error"

        mock_client.predictions.get.return_value = mock_prediction

        status, video_url, metadata = poll_video_generation_status("pred-123")

        assert status == "failed"
        assert video_url is None
        assert metadata["error"] == "Generation error"

    @patch("app.services.video_generation.get_settings")
    def test_poll_no_api_token(self, mock_get_settings):
        """Test polling without API token."""
        mock_settings = MagicMock()
        mock_settings.replicate_api_token = None
        mock_get_settings.return_value = mock_settings

        status, video_url, metadata = poll_video_generation_status("pred-123")

        assert status == "failed"
        assert video_url is None
        assert "error" in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

