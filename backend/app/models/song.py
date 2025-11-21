from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


DEFAULT_USER_ID = "default-user"
"""Placeholder user id until authentication is implemented."""


class Song(SQLModel, table=True):
    __tablename__ = "songs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(default=DEFAULT_USER_ID, index=True, foreign_key="users.id")
    title: str = Field(default="", max_length=256)
    original_filename: str = Field(max_length=512)
    original_file_size: int = Field(default=0, ge=0)
    original_content_type: Optional[str] = Field(default=None, max_length=128)
    original_s3_key: str = Field(max_length=1024)
    processed_s3_key: Optional[str] = Field(default=None, max_length=1024)
    processed_sample_rate: Optional[int] = Field(default=None, ge=1)
    waveform_json: Optional[str] = Field(default=None)
    duration_sec: Optional[float] = Field(default=None, ge=0)
    description: Optional[str] = Field(default=None)
    attribution: Optional[str] = Field(default=None, max_length=512)
    composed_video_s3_key: Optional[str] = Field(default=None, max_length=1024)
    composed_video_poster_s3_key: Optional[str] = Field(default=None, max_length=1024)
    composed_video_duration_sec: Optional[float] = Field(default=None, ge=0)
    composed_video_fps: Optional[int] = Field(default=None, ge=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

