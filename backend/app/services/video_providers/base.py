"""Base classes for video generation providers.

This module provides an abstraction layer for video generation APIs/models,
making it easy to swap out different providers (e.g., Minimax, Runway, etc.).

To add a new provider:
1. Create a new class inheriting from VideoGenerationProvider
2. Implement all abstract methods
3. Update get_video_provider() in video_generation.py to return your provider
   (or use set_video_provider() for runtime switching)
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.schemas.scene import SceneSpec


class VideoGenerationProvider(ABC):
    """Abstract base class for video generation providers.
    
    Subclasses should implement API-specific parameter preparation and metadata extraction.
    This allows the video generation service to work with different models/APIs without
    tight coupling to specific parameter formats.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name/identifier for this provider."""
        pass

    @property
    @abstractmethod
    def supports_image_to_video(self) -> bool:
        """Return whether this provider supports image-to-video generation."""
        pass

    @abstractmethod
    def prepare_text_to_video_params(
        self,
        scene_spec: SceneSpec,
        video_type: Optional[str] = None,
        reference_image_url: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> dict:
        """
        Prepare API-specific parameters for text-to-video generation.
        
        Args:
            scene_spec: Scene specification with prompt and parameters
            video_type: Optional video type ("short_form" or "full_length")
            reference_image_url: Optional reference image URL for image-to-video
            seed: Optional seed for reproducibility
        
        Returns:
            Dictionary of API-specific parameters
        """
        pass

    @abstractmethod
    def prepare_image_to_video_params(
        self,
        scene_spec: SceneSpec,
        reference_image_url: str,
        video_type: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> dict:
        """
        Prepare API-specific parameters for image-to-video generation.
        
        Args:
            scene_spec: Scene specification with prompt and parameters
            reference_image_url: URL to reference image
            video_type: Optional video type ("short_form" or "full_length")
            seed: Optional seed for reproducibility
        
        Returns:
            Dictionary of API-specific parameters
        """
        pass

    @abstractmethod
    def extract_metadata_from_params(self, params: dict, seed: Optional[int] = None) -> dict:
        """
        Extract metadata from API parameters for logging/storage.
        
        Args:
            params: API parameters dictionary
            seed: Optional seed value
        
        Returns:
            Dictionary of metadata (duration, resolution, etc.)
        """
        pass

    def should_pad_image_for_9_16(
        self,
        video_type: Optional[str],
        has_reference_image: bool,
    ) -> bool:
        """
        Determine if image should be padded to 9:16 aspect ratio.
        
        Override in subclasses if needed.
        
        Args:
            video_type: Optional video type ("short_form" or "full_length")
            has_reference_image: Whether a reference image is provided
        
        Returns:
            True if image should be padded to 9:16
        """
        return video_type == "short_form" and has_reference_image

    def should_create_9_16_placeholder(
        self,
        video_type: Optional[str],
        has_reference_image: bool,
    ) -> bool:
        """
        Determine if a 9:16 placeholder image should be created for text-to-video.
        
        Override in subclasses if needed.
        
        Args:
            video_type: Optional video type ("short_form" or "full_length")
            has_reference_image: Whether a reference image is provided
        
        Returns:
            True if placeholder should be created
        """
        return video_type == "short_form" and not has_reference_image

