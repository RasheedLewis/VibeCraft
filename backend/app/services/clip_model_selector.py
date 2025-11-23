"""Clip model selection service for composition.

Provides helper functions to select and validate clips based on video_type,
supporting both SectionVideo (for full-length videos) and SongClip (for short-form videos).
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from sqlmodel import Session

from app.core.config import should_use_sections_for_song as _should_use_sections_for_song
from app.exceptions import ClipNotFoundError, CompositionError
from app.models.clip import SongClip
from app.models.section_video import SectionVideo
from app.models.song import Song


class ClipModel(Protocol):
    """Protocol for clip models."""

    id: UUID
    song_id: UUID
    status: str
    video_url: str | None


def get_clip_model_class(use_sections: bool) -> type[SongClip] | type[SectionVideo]:
    """Get the appropriate clip model class based on sections flag.

    Args:
        use_sections: Whether to use SectionVideo (True) or SongClip (False)

    Returns:
        SectionVideo class if use_sections is True, SongClip otherwise
    """
    return SectionVideo if use_sections else SongClip


def get_and_validate_clip(
    session: Session,
    clip_id: UUID,
    song_id: UUID,
    use_sections: bool,
) -> SongClip | SectionVideo:
    """
    Get and validate a clip based on video_type.

    Args:
        session: Database session
        clip_id: Clip ID to retrieve
        song_id: Expected song ID
        use_sections: Whether to use SectionVideo or SongClip

    Returns:
        Validated clip instance

    Raises:
        ClipNotFoundError: If clip not found
        CompositionError: If clip doesn't belong to song or isn't ready
    """
    model_class = get_clip_model_class(use_sections)
    clip = session.get(model_class, clip_id)

    if not clip:
        model_name = model_class.__name__
        raise ClipNotFoundError(f"{model_name} {clip_id} not found")

    if clip.song_id != song_id:
        model_name = model_class.__name__
        raise CompositionError(f"{model_name} {clip_id} does not belong to song {song_id}")

    if clip.status != "completed" or not clip.video_url:
        model_name = model_class.__name__
        raise CompositionError(f"{model_name} {clip_id} is not ready (status: {clip.status})")

    return clip


def get_clips_for_composition(
    session: Session,
    clip_ids: list[UUID],
    song: Song,
) -> tuple[list[SongClip | SectionVideo], list[str]]:
    """
    Get and validate all clips for composition.

    Optimized to fetch all clips in a single query instead of N+1 pattern.

    Args:
        session: Database session
        clip_ids: List of clip IDs to retrieve
        song: Song instance to determine video_type

    Returns:
        Tuple of (clips, clip_urls)

    Raises:
        ClipNotFoundError: If any clip not found
        CompositionError: If any clip doesn't belong to song or isn't ready
    """
    use_sections = _should_use_sections_for_song(song)
    model_class = get_clip_model_class(use_sections)
    
    if not clip_ids:
        return [], []
    
    # Fetch all clips in a single query (optimization #2: fix N+1)
    from sqlmodel import select
    statement = select(model_class).where(model_class.id.in_(clip_ids))  # type: ignore[attr-defined]
    clips = list(session.exec(statement).all())
    
    # Create a lookup dict for validation
    clip_dict = {clip.id: clip for clip in clips}
    
    # Validate all clips
    validated_clips = []
    clip_urls = []
    
    for clip_id in clip_ids:
        clip = clip_dict.get(clip_id)
        if not clip:
            model_name = model_class.__name__
            raise ClipNotFoundError(f"{model_name} {clip_id} not found")
        
        if clip.song_id != song.id:
            model_name = model_class.__name__
            raise CompositionError(f"{model_name} {clip_id} does not belong to song {song.id}")
        
        if clip.status != "completed" or not clip.video_url:
            model_name = model_class.__name__
            raise CompositionError(f"{model_name} {clip_id} is not ready (status: {clip.status})")
        
        validated_clips.append(clip)
        clip_urls.append(clip.video_url)
    
    return validated_clips, clip_urls

