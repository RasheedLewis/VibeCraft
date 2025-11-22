"""Scene specification schemas for video generation."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# Template types for visual styles
TemplateType = Literal["abstract", "environment", "character", "minimal"]


class ColorPalette(BaseModel):
    """Color palette for a scene."""

    primary: str = Field(..., description="Primary color (hex or name)")
    secondary: str = Field(..., description="Secondary color (hex or name)")
    accent: str = Field(..., description="Accent color (hex or name)")
    mood: str = Field(..., description="Mood description (e.g., 'vibrant', 'muted', 'dark')")


class CameraMotion(BaseModel):
    """Camera motion preset for a scene."""

    type: str = Field(..., description="Motion type (e.g., 'slow_pan', 'fast_zoom', 'static')")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Motion intensity (0-1)")
    speed: str = Field(..., description="Speed description (e.g., 'slow', 'medium', 'fast')")


class ShotPattern(BaseModel):
    """Shot pattern for a section type."""

    pattern: str = Field(..., description="Pattern type (e.g., 'close_up', 'wide', 'medium')")
    pacing: str = Field(..., description="Pacing (e.g., 'slow', 'medium', 'fast')")
    transitions: List[str] = Field(default_factory=list, description="Transition types")


class SceneSpec(BaseModel):
    """Complete scene specification for video generation."""

    section_id: Optional[str] = Field(None, alias="sectionId")
    template: TemplateType
    prompt: str = Field(..., description="Full prompt for video generation")
    color_palette: ColorPalette = Field(..., alias="colorPalette")
    camera_motion: CameraMotion = Field(..., alias="cameraMotion")
    shot_pattern: ShotPattern = Field(..., alias="shotPattern")
    intensity: float = Field(..., ge=0.0, le=1.0, description="Visual intensity (0-1)")
    duration_sec: float = Field(..., alias="durationSec", description="Section duration in seconds")

    model_config = {"populate_by_name": True}

