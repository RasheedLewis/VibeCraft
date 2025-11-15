"""Scene planning API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.scene import SceneSpec, TemplateType
from app.services.scene_planner import build_scene_spec

router = APIRouter(prefix="/scenes", tags=["scenes"])


class BuildSceneRequest(BaseModel):
    """Request body for building a scene spec."""

    section_id: str = Field(..., alias="sectionId")
    template: TemplateType = "abstract"

    model_config = {"populate_by_name": True}


@router.post("/build-scene", response_model=SceneSpec)
async def build_scene(request: BuildSceneRequest) -> SceneSpec:
    """
    Build scene specification for a section.

    This is an internal/debugging endpoint for PR-08.
    In production, this will be called internally by the video generation pipeline.

    Args:
        request: BuildSceneRequest with sectionId and optional template

    Returns:
        SceneSpec with complete scene parameters
    """
    try:
        scene_spec = build_scene_spec(
            section_id=request.section_id,
            analysis=None,  # Uses mock data for now
            template=request.template,
        )
        return scene_spec
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building scene spec: {str(e)}")

