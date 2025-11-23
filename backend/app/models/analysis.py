from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Text
from sqlmodel import Field, SQLModel


class SongAnalysisRecord(SQLModel, table=True):
    __tablename__ = "song_analyses"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    song_id: UUID = Field(foreign_key="songs.id", unique=True, index=True)
    duration_sec: float = Field(default=0.0, ge=0)
    bpm: Optional[float] = Field(default=None, ge=0)
    analysis_json: str = Field(default="", sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class AnalysisJob(SQLModel, table=True):
    __tablename__ = "analysis_jobs"

    id: str = Field(primary_key=True, max_length=128)
    song_id: UUID = Field(foreign_key="songs.id", index=True)
    status: str = Field(default="queued", max_length=32)
    progress: int = Field(default=0, ge=0, le=100)
    analysis_id: Optional[UUID] = Field(default=None, foreign_key="song_analyses.id")
    error: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class ClipGenerationJob(SQLModel, table=True):
    __tablename__ = "clip_generation_jobs"

    id: str = Field(primary_key=True, max_length=128)
    song_id: UUID = Field(foreign_key="songs.id", index=True)
    status: str = Field(default="queued", max_length=32)
    progress: int = Field(default=0, ge=0, le=100)
    total_clips: int = Field(default=0, ge=0)
    completed_clips: int = Field(default=0, ge=0)
    failed_clips: int = Field(default=0, ge=0)
    error: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


