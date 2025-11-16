from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ClipPlanBatchResponse(BaseModel):
    clips_planned: int = Field(..., alias="clipsPlanned", ge=0)

    model_config = {"populate_by_name": True}


class SongClipRead(BaseModel):
    id: UUID
    song_id: UUID = Field(..., alias="songId")
    clip_index: int = Field(..., alias="clipIndex", ge=0)
    start_sec: float = Field(..., alias="startSec", ge=0.0)
    end_sec: float = Field(..., alias="endSec", ge=0.0)
    duration_sec: float = Field(..., alias="durationSec", ge=0.0)
    start_beat_index: Optional[int] = Field(None, alias="startBeat")
    end_beat_index: Optional[int] = Field(None, alias="endBeat")
    frame_count: int = Field(..., alias="frameCount", ge=0)
    fps: int = Field(..., ge=1)
    status: str
    source: str
    video_url: Optional[str] = Field(None, alias="videoUrl")
    style_seed: Optional[str] = Field(None, alias="styleSeed")
    error: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}

