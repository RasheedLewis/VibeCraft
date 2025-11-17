"""Song model for audio file storage and management."""

from datetime import UTC, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class Song(SQLModel, table=True):
    """Song model for audio file storage and management."""

    __tablename__ = "songs"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        max_length=128,
    )
    user_id: str = Field(
        index=True,
        foreign_key="users.id",
        max_length=128,
    )
    title: str = Field(max_length=256)
    duration_sec: float = Field(ge=0)
    audio_s3_key: str = Field(max_length=1024)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationship to User (optional, for SQLModel relationships)
    # user: Optional["User"] = Relationship(back_populates="songs")

