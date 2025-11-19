"""Repository for clip data access."""

from uuid import UUID

from sqlmodel import select

from app.core.database import session_scope
from app.exceptions import ClipNotFoundError
from app.models.clip import SongClip


class ClipRepository:
    """Repository for clip data access operations."""

    @staticmethod
    def get_by_id(clip_id: UUID) -> SongClip:
        """
        Get a clip by ID.

        Args:
            clip_id: Clip ID

        Returns:
            SongClip object

        Raises:
            ClipNotFoundError: If clip not found
        """
        with session_scope() as session:
            clip = session.get(SongClip, clip_id)
            if not clip:
                raise ClipNotFoundError(f"Clip {clip_id} not found")
            return clip

    @staticmethod
    def get_by_song_id(song_id: UUID) -> list[SongClip]:
        """
        Get all clips for a song.

        Args:
            song_id: Song ID

        Returns:
            List of clips ordered by clip_index
        """
        with session_scope() as session:
            statement = (
                select(SongClip)
                .where(SongClip.song_id == song_id)
                .order_by(SongClip.clip_index)
            )
            return list(session.exec(statement).all())

    @staticmethod
    def get_completed_by_song_id(song_id: UUID) -> list[SongClip]:
        """
        Get all completed clips for a song.

        Args:
            song_id: Song ID

        Returns:
            List of completed clips ordered by clip_index
        """
        with session_scope() as session:
            statement = (
                select(SongClip)
                .where(SongClip.song_id == song_id)
                .where(SongClip.status == "completed")
                .where(SongClip.video_url.isnot(None))  # type: ignore[attr-defined]
                .order_by(SongClip.clip_index)
            )
            return list(session.exec(statement).all())

    @staticmethod
    def create(clip: SongClip) -> SongClip:
        """
        Create a new clip.

        Args:
            clip: SongClip object to create

        Returns:
            Created clip with ID
        """
        with session_scope() as session:
            session.add(clip)
            session.commit()
            session.refresh(clip)
            return clip

    @staticmethod
    def update(clip: SongClip) -> SongClip:
        """
        Update an existing clip.

        Args:
            clip: SongClip object to update

        Returns:
            Updated clip
        """
        with session_scope() as session:
            session.add(clip)
            session.commit()
            session.refresh(clip)
            return clip

