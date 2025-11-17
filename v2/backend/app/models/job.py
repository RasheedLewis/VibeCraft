"""Job model for tracking background job status."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import Field, SQLModel


class Job(SQLModel, table=True):
    """Job model for tracking background job status and progress.

    Used for:
    - Analysis jobs (song_id set, video_id None)
    - Generation jobs (song_id set, video_id None)
    - Composition jobs (song_id set, video_id None)
    - Regeneration jobs (video_id set, song_id None)
    """

    __tablename__ = "jobs"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    song_id: Optional[UUID] = Field(default=None, foreign_key="songs.id", index=True)
    video_id: Optional[UUID] = Field(default=None, foreign_key="videos.id", index=True)
    job_type: str = Field(
        description="Type of job: analysis, generation, composition, regeneration"
    )
    status: str = Field(
        default="queued",
        description="Job status: queued, processing, completed, failed",
    )
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Job progress percentage (0-100)",
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if job failed"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships (will be defined when Song and Video models are created)
    # song: Optional["Song"] = Relationship(back_populates="jobs")
    # video: Optional["Video"] = Relationship(back_populates="jobs")

