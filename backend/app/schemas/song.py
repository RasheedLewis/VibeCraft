from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.core.constants import (
    MAX_AUDIO_SELECTION_DURATION_SEC,
    MIN_AUDIO_SELECTION_DURATION_SEC,
    VALID_VIDEO_TYPES,
)


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
    video_type: Optional[str] = None
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
        # Note: Full validation with song duration happens in the endpoint
        # This validates basic constraints only
        if self.end_sec <= self.start_sec:
            raise ValueError("end_sec must be greater than start_sec")
        duration = self.end_sec - self.start_sec
        if duration > MAX_AUDIO_SELECTION_DURATION_SEC:
            raise ValueError(
                f"Selection duration ({duration}s) exceeds maximum ({MAX_AUDIO_SELECTION_DURATION_SEC}s)"
            )
        if duration < MIN_AUDIO_SELECTION_DURATION_SEC:
            raise ValueError(
                f"Selection duration ({duration}s) is below minimum ({MIN_AUDIO_SELECTION_DURATION_SEC}s)"
            )
        return self


class VideoTypeUpdate(BaseModel):
    video_type: str = Field(description="Video type: 'full_length' or 'short_form'")
    
    @model_validator(mode='after')
    def validate_video_type(self) -> 'VideoTypeUpdate':
        if self.video_type not in VALID_VIDEO_TYPES:
            raise ValueError(f"video_type must be one of {VALID_VIDEO_TYPES}")
        return self

