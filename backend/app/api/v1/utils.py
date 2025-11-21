"""Common utilities for API endpoints."""

from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.song import Song
from app.services.song_analysis import get_latest_analysis

T = TypeVar("T")


def get_song_or_404(song_id: UUID, db: Session) -> Song:
    """Get song or raise 404.

    Args:
        song_id: Song ID to retrieve
        db: Database session

    Returns:
        Song instance

    Raises:
        HTTPException: 404 if song not found
    """
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found",
        )
    return song


def ensure_no_analysis(song_id: UUID) -> None:
    """Ensure song has no analysis, or raise 409.

    Args:
        song_id: Song ID to check

    Raises:
        HTTPException: 409 if analysis exists
    """
    existing_analysis = get_latest_analysis(song_id)
    if existing_analysis:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change after analysis has been completed. Please upload a new song.",
        )


def update_song_field(
    song: Song,
    field_name: str,
    value: T,
    db: Session,
) -> Song:
    """Update a song field and commit.

    Args:
        song: Song instance to update
        field_name: Name of the field to update
        value: Value to set
        db: Database session

    Returns:
        Updated song instance
    """
    setattr(song, field_name, value)
    db.add(song)
    db.commit()
    db.refresh(song)
    return song

