"""Schemas for video composition requests and responses."""

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ClipMetadata(BaseModel):
    """Metadata for a single clip in composition (legacy, not used in MVP)."""

    clip_id: UUID = Field(..., alias="clipId", description="SongClip UUID")
    start_frame: int = Field(..., alias="startFrame", description="Start frame number (0-indexed)")
    end_frame: int = Field(..., alias="endFrame", description="End frame number (0-indexed)")

    model_config = {"populate_by_name": True}


class ComposeVideoResponse(BaseModel):
    """Response after enqueuing a composition job."""

    job_id: str = Field(..., alias="jobId", description="Composition job ID")
    status: str = Field(..., description="Job status (queued, processing, etc.)")
    song_id: str = Field(..., alias="songId", description="Song ID")

    model_config = {"populate_by_name": True}


class CompositionJobStatusResponse(BaseModel):
    """Response for composition job status query."""

    job_id: str = Field(..., alias="jobId", description="Composition job ID")
    song_id: str = Field(..., alias="songId", description="Song ID")
    status: str = Field(..., description="Job status: queued, processing, completed, failed, cancelled")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    composed_video_id: Optional[str] = Field(None, alias="composedVideoId", description="ComposedVideo ID if completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: str = Field(..., alias="createdAt", description="Job creation timestamp")
    updated_at: str = Field(..., alias="updatedAt", description="Job last update timestamp")

    model_config = {"populate_by_name": True}


class ComposedVideoResponse(BaseModel):
    """Response with composed video details."""

    id: str = Field(..., description="ComposedVideo ID")
    song_id: str = Field(..., alias="songId", description="Song ID")
    video_url: str = Field(..., alias="videoUrl", description="Presigned URL to access the video")
    duration_sec: float = Field(..., alias="durationSec", description="Video duration in seconds")
    file_size_bytes: int = Field(..., alias="fileSizeBytes", description="File size in bytes")
    resolution_width: int = Field(..., alias="resolutionWidth", description="Video width in pixels")
    resolution_height: int = Field(..., alias="resolutionHeight", description="Video height in pixels")
    fps: int = Field(..., description="Frames per second")
    clip_ids: List[str] = Field(..., alias="clipIds", description="List of SongClip IDs used")
    status: str = Field(..., description="Video status: processing, completed, failed")
    created_at: str = Field(..., alias="createdAt", description="Creation timestamp")

    model_config = {"populate_by_name": True}

