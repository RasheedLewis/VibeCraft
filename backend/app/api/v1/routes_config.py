"""Configuration API routes."""

from fastapi import APIRouter

from app.core.config import is_sections_enabled

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/features")
async def get_feature_flags() -> dict[str, bool]:
    """
    Get enabled feature flags.

    Returns:
        Dict with feature flag states
    """
    return {
        "sections": is_sections_enabled(),
    }

