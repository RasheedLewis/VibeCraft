"""Minimax Hailuo 2.3 video generation provider."""

import logging
from typing import Optional

from app.schemas.scene import SceneSpec
from app.services.video_providers.base import VideoGenerationProvider

logger = logging.getLogger(__name__)


class MinimaxHailuoProvider(VideoGenerationProvider):
    """Provider for Minimax Hailuo 2.3 video generation via Replicate."""

    @property
    def model_name(self) -> str:
        """Return the Minimax Hailuo 2.3 model name."""
        return "minimax/hailuo-2.3"

    @property
    def supports_image_to_video(self) -> bool:
        """Minimax Hailuo 2.3 supports image-to-video via first_frame_image."""
        return True

    def prepare_text_to_video_params(
        self,
        scene_spec: SceneSpec,
        video_type: Optional[str] = None,
        reference_image_url: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> dict:
        """
        Prepare Minimax Hailuo 2.3 API parameters for text-to-video generation.
        
        API supports: prompt, duration (6 or 10s), resolution ("768p" or "1080p"), 
        prompt_optimizer (bool), first_frame_image (optional)
        
        Note: API only supports 6s (1080p) or 6s/10s (768p)
        """
        # Determine resolution based on video type
        # 1080p for short_form (9:16), 768p for full_length (16:9)
        # Note: 1080p only supports 6s duration
        if video_type == "short_form":
            resolution = "1080p"
            duration = 6  # 1080p only supports 6s
        else:
            resolution = "768p"
            duration = 6  # Use 6s for consistency

        params = {
            "prompt": scene_spec.prompt,  # Should be optimized before calling this
            "duration": duration,
            "resolution": resolution,
            "prompt_optimizer": True,
        }

        if seed is not None:
            params["seed"] = seed

        if reference_image_url:
            params["first_frame_image"] = reference_image_url

        logger.info(
            f"[MINIMAX] Text-to-video params: duration={duration}s, "
            f"resolution={resolution}, video_type={video_type}, "
            f"requested_duration={scene_spec.duration_sec}s"
        )

        return params

    def prepare_image_to_video_params(
        self,
        scene_spec: SceneSpec,
        reference_image_url: str,
        video_type: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> dict:
        """
        Prepare Minimax Hailuo 2.3 API parameters for image-to-video generation.
        
        Uses first_frame_image parameter for character consistency.
        """
        # Determine resolution based on video type
        # 1080p for short_form (9:16), 768p for full_length (16:9)
        # Note: 1080p only supports 6s duration
        if video_type == "short_form":
            resolution = "1080p"
            duration = 6  # 1080p only supports 6s
        else:
            resolution = "768p"
            duration = 6  # Use 6s for consistency

        params = {
            "first_frame_image": reference_image_url,
            "prompt": scene_spec.prompt,  # Should be optimized before calling this
            "duration": duration,
            "resolution": resolution,
            "prompt_optimizer": True,
        }

        if seed is not None:
            params["seed"] = seed

        logger.info(
            f"[MINIMAX] Image-to-video params: duration={duration}s, "
            f"resolution={resolution}, video_type={video_type}, "
            f"requested_duration={scene_spec.duration_sec}s"
        )

        return params

    def extract_metadata_from_params(self, params: dict, seed: Optional[int] = None) -> dict:
        """
        Extract metadata from Minimax API parameters.
        
        Returns duration, resolution, seed, and generation type.
        """
        metadata = {
            "duration": params.get("duration"),
            "resolution": params.get("resolution"),
            "seed": seed,
        }

        if "first_frame_image" in params:
            metadata["generation_type"] = "image-to-video"
            metadata["reference_image_url"] = params["first_frame_image"]
        else:
            metadata["generation_type"] = "text-to-video"

        return metadata

