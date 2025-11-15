from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.analysis import SongAnalysis


class SongAnalysisJobResponse(BaseModel):
    job_id: str = Field(serialization_alias="jobId")
    status: str

    model_config = {"populate_by_name": True}


class JobStatusResponse(BaseModel):
    job_id: str = Field(serialization_alias="jobId")
    song_id: str = Field(serialization_alias="songId")
    status: str
    progress: int
    analysis_id: Optional[str] = Field(default=None, serialization_alias="analysisId")
    error: Optional[str] = None
    result: Optional[SongAnalysis] = None

    model_config = {"populate_by_name": True}


