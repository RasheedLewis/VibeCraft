from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator


class SongBase(BaseModel):
    title: str
    audio_url: HttpUrl
    description: Optional[str] = None
    duration_sec: Optional[float] = None
    # Attribution (optional, for royalty-free music credits)
    attribution: Optional[str] = None

    @field_validator("duration_sec")
    @classmethod
    def validate_duration(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and value < 0:
            raise ValueError("duration_sec must be positive")
        return value


class SongCreate(SongBase):
    pass


class SongUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_sec: Optional[float] = None
    attribution: Optional[str] = None


class SongRead(SongBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

