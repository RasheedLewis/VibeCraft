from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class CompositionJob(SQLModel, table=True):
    __tablename__ = "composition_jobs"

    id: str = Field(primary_key=True, max_length=128)
    song_id: UUID = Field(foreign_key="songs.id", index=True)
    status: str = Field(default="queued", max_length=32)  # queued, processing, completed, failed, cancelled
    progress: int = Field(default=0, ge=0, le=100)
    clip_ids: str = Field(sa_column=Column(Text, nullable=False))  # JSON array of SectionVideo UUIDs
    clip_metadata: str = Field(sa_column=Column(Text, nullable=False))  # JSON array of clip metadata
    composed_video_id: Optional[UUID] = Field(default=None, foreign_key="composed_videos.id")
    error: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )


class ComposedVideo(SQLModel, table=True):
    __tablename__ = "composed_videos"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    song_id: UUID = Field(foreign_key="songs.id", index=True)
    s3_key: str = Field(max_length=1024)
    duration_sec: float = Field(ge=0.0)
    file_size_bytes: int = Field(ge=0)
    resolution_width: int = Field(ge=1)
    resolution_height: int = Field(ge=1)
    fps: int = Field(ge=1)
    clip_ids: str = Field(sa_column=Column(Text, nullable=False))  # JSON array of SectionVideo UUIDs
    status: str = Field(default="processing", max_length=32)  # processing, completed, failed
    error_message: Optional[str] = Field(default=None, max_length=1024)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

