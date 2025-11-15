from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SectionVideoRead(BaseModel):
    id: UUID
    song_id: UUID = Field(..., alias="songId")
    section_id: str = Field(..., alias="sectionId")
    template: str
    prompt: str
    duration_sec: float = Field(..., alias="durationSec")
    video_url: Optional[str] = Field(None, alias="videoUrl")
    s3_key: Optional[str] = Field(None, alias="s3Key")
    fps: Optional[int] = None
    resolution_width: Optional[int] = Field(None, alias="resolutionWidth")
    resolution_height: Optional[int] = Field(None, alias="resolutionHeight")
    seed: Optional[int] = None
    status: str
    error_message: Optional[str] = Field(None, alias="errorMessage")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class SectionVideoCreate(BaseModel):
    song_id: UUID = Field(..., alias="songId")
    section_id: str = Field(..., alias="sectionId")
    template: str
    prompt: str
    duration_sec: float = Field(..., alias="durationSec")
    seed: Optional[int] = None

    model_config = {"populate_by_name": True}


class SectionVideoGenerateRequest(BaseModel):
    section_id: str = Field(..., alias="sectionId")
    template: Optional[str] = "abstract"

    model_config = {"populate_by_name": True}


class SectionVideoGenerateResponse(BaseModel):
    section_video_id: UUID = Field(..., alias="sectionVideoId")
    status: str
    message: str

    model_config = {"populate_by_name": True}

