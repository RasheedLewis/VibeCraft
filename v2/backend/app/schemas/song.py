"""Song schemas for API requests and responses."""

from datetime import datetime

from pydantic import BaseModel, Field


class SongCreate(BaseModel):
    """Schema for creating a song (internal use)."""

    user_id: str
    title: str = Field(max_length=256)
    duration_sec: float = Field(ge=0)
    audio_s3_key: str = Field(max_length=1024)


class SongRead(BaseModel):
    """Schema for reading song information."""

    id: str
    user_id: str
    title: str
    duration_sec: float
    audio_s3_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SongUploadResponse(BaseModel):
    """Schema for song upload response."""

    song_id: str
    status: str = "uploaded"
    title: str
    duration_sec: float

