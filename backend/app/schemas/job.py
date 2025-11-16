from __future__ import annotations

from typing import Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.analysis import SongAnalysis
from app.schemas.clip import ClipGenerationSummary

JobStatus = Literal["queued", "processing", "completed", "failed"]


class SongAnalysisJobResponse(BaseModel):
    job_id: str = Field(..., alias="jobId")
    song_id: UUID = Field(..., alias="songId")
    status: JobStatus

    model_config = {"populate_by_name": True}


class ClipGenerationJobResponse(BaseModel):
    job_id: str = Field(..., alias="jobId")
    song_id: UUID = Field(..., alias="songId")
    status: JobStatus

    model_config = {"populate_by_name": True}


class JobStatusResponse(BaseModel):
    job_id: str = Field(..., alias="jobId")
    song_id: UUID = Field(..., alias="songId")
    status: JobStatus
    progress: int = Field(default=0, ge=0, le=100)
    analysis_id: Optional[UUID] = Field(default=None, alias="analysisId")
    error: Optional[str] = None
    result: Optional[Union[SongAnalysis, ClipGenerationSummary]] = None

    model_config = {"populate_by_name": True}

