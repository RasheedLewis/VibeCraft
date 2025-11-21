from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class SongClip(SQLModel, table=True):
    __tablename__ = "song_clips"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    song_id: UUID = Field(foreign_key="songs.id", index=True)
    clip_index: int = Field(index=True)

    start_sec: float = Field(ge=0)
    end_sec: float = Field(ge=0)
    duration_sec: float = Field(ge=0)

    start_beat_index: Optional[int] = Field(default=None)
    end_beat_index: Optional[int] = Field(default=None)

    num_frames: int = Field(default=0, ge=0)
    fps: int = Field(default=8, ge=1)

    status: str = Field(default="queued", max_length=32)
    source: str = Field(default="auto", max_length=32)

    video_url: Optional[str] = Field(default=None, max_length=2048)
    prompt: Optional[str] = Field(default=None, max_length=2048)
    style_seed: Optional[str] = Field(default=None, max_length=128)
    rq_job_id: Optional[str] = Field(default=None, max_length=128)
    replicate_job_id: Optional[str] = Field(default=None, max_length=256)
    error: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

