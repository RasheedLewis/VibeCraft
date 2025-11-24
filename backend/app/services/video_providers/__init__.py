"""Video generation providers for different APIs/models."""

from app.services.video_providers.base import VideoGenerationProvider
from app.services.video_providers.minimax_provider import MinimaxHailuoProvider

__all__ = ["VideoGenerationProvider", "MinimaxHailuoProvider"]

