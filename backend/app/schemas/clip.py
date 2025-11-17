from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.analysis import SongAnalysis


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
    num_frames: int = Field(..., alias="numFrames", ge=0)
    fps: int = Field(..., ge=1)
    status: str
    source: str
    video_url: Optional[str] = Field(None, alias="videoUrl")
    prompt: Optional[str] = None
    style_seed: Optional[str] = Field(None, alias="styleSeed")
    rq_job_id: Optional[str] = Field(None, alias="rqJobId")
    replicate_job_id: Optional[str] = Field(None, alias="replicateJobId")
    error: Optional[str] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = {"from_attributes": True, "populate_by_name": True}


class SongClipStatus(BaseModel):
    id: UUID
    clip_index: int = Field(..., alias="clipIndex", ge=0)
    start_sec: float = Field(..., alias="startSec", ge=0.0)
    end_sec: float = Field(..., alias="endSec", ge=0.0)
    duration_sec: float = Field(..., alias="durationSec", ge=0.0)
    start_beat_index: Optional[int] = Field(None, alias="startBeat")
    end_beat_index: Optional[int] = Field(None, alias="endBeat")
    status: str
    source: str
    num_frames: int = Field(..., alias="numFrames", ge=0)
    fps: int = Field(..., ge=1)
    video_url: Optional[str] = Field(None, alias="videoUrl")
    rq_job_id: Optional[str] = Field(None, alias="rqJobId")
    replicate_job_id: Optional[str] = Field(None, alias="replicateJobId")
    error: Optional[str] = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class ClipGenerationSummary(BaseModel):
    song_id: UUID = Field(..., alias="songId")
    song_duration_sec: Optional[float] = Field(None, alias="songDurationSec", ge=0)
    total_clips: int = Field(..., alias="totalClips", ge=0)
    completed_clips: int = Field(..., alias="completedClips", ge=0)
    failed_clips: int = Field(..., alias="failedClips", ge=0)
    processing_clips: int = Field(..., alias="processingClips", ge=0)
    queued_clips: int = Field(..., alias="queuedClips", ge=0)
    progress_completed: int = Field(..., alias="progressCompleted", ge=0)
    progress_total: int = Field(..., alias="progressTotal", ge=0)
    clips: List[SongClipStatus]
    analysis: Optional[SongAnalysis] = None
    composed_video_url: Optional[str] = Field(None, alias="composedVideoUrl")
    composed_video_poster_url: Optional[str] = Field(None, alias="composedVideoPosterUrl")

    model_config = {"populate_by_name": True, "from_attributes": True}

