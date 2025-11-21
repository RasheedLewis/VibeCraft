from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class SongRead(BaseModel):
    id: UUID
    user_id: str
    title: str
    original_filename: str
    original_file_size: int
    original_content_type: Optional[str] = None
    original_s3_key: str
    processed_s3_key: Optional[str] = None
    processed_sample_rate: Optional[int] = None
    waveform_json: Optional[str] = None
    duration_sec: Optional[float] = None
    description: Optional[str] = None
    attribution: Optional[str] = None
    composed_video_s3_key: Optional[str] = None
    composed_video_poster_s3_key: Optional[str] = None
    composed_video_duration_sec: Optional[float] = None
    composed_video_fps: Optional[int] = None
    selected_start_sec: Optional[float] = None
    selected_end_sec: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SongUploadResponse(BaseModel):
    song_id: UUID = Field(serialization_alias="songId")
    audio_url: str = Field(serialization_alias="audioUrl")
    s3_key: str = Field(serialization_alias="s3Key")
    status: str

    model_config = {"populate_by_name": True}


class AudioSelectionUpdate(BaseModel):
    start_sec: float = Field(ge=0, description="Start time in seconds")
    end_sec: float = Field(gt=0, description="End time in seconds")
    
    @model_validator(mode='after')
    def validate_range(self) -> 'AudioSelectionUpdate':
        if self.end_sec <= self.start_sec:
            raise ValueError("end_sec must be greater than start_sec")
        duration = self.end_sec - self.start_sec
        if duration > 30.0:
            raise ValueError(f"Selection duration ({duration}s) exceeds maximum (30s)")
        if duration < 1.0:
            raise ValueError(f"Selection duration ({duration}s) is below minimum (1s)")
        return self

