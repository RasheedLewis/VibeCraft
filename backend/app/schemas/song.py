from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SongUploadResponse(BaseModel):
    song_id: UUID = Field(serialization_alias="songId")
    audio_url: str = Field(serialization_alias="audioUrl")
    s3_key: str = Field(serialization_alias="s3Key")
    status: str

    model_config = {"populate_by_name": True}

