from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class SectionVideo(SQLModel, table=True):
    __tablename__ = "section_videos"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    song_id: UUID = Field(foreign_key="songs.id", index=True)
    section_id: str = Field(index=True, max_length=128)
    template: str = Field(max_length=64)  # e.g., "abstract", "environment"
    prompt: str = Field(max_length=2048)
    duration_sec: float = Field(ge=0.0)
    video_url: Optional[str] = Field(default=None, max_length=2048)
    s3_key: Optional[str] = Field(default=None, max_length=1024)
    fps: Optional[int] = Field(default=None, ge=1)
    resolution_width: Optional[int] = Field(default=None, ge=1)
    resolution_height: Optional[int] = Field(default=None, ge=1)
    seed: Optional[int] = Field(default=None)
    replicate_job_id: Optional[str] = Field(default=None, max_length=256)
    status: str = Field(default="pending", max_length=32)  # pending, processing, completed, failed
    error_message: Optional[str] = Field(default=None, max_length=1024)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )

