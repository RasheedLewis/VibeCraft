"""Repository for song data access."""

from uuid import UUID

from sqlmodel import select

from app.core.database import session_scope
from app.exceptions import SongNotFoundError
from app.models.song import Song


class SongRepository:
    """Repository for song data access operations."""

    @staticmethod
    def get_by_id(song_id: UUID) -> Song:
        """
        Get a song by ID.

        Args:
            song_id: Song ID

        Returns:
            Song object

        Raises:
            SongNotFoundError: If song not found
        """
        with session_scope() as session:
            song = session.get(Song, song_id)
            if not song:
                raise SongNotFoundError(f"Song {song_id} not found")
            return song

    @staticmethod
    def get_all() -> list[Song]:
        """
        Get all songs.

        Returns:
            List of songs ordered by creation date (newest first)
        """
        with session_scope() as session:
            statement = select(Song).order_by(Song.created_at.desc())
            return list(session.exec(statement).all())

    @staticmethod
    def create(song: Song) -> Song:
        """
        Create a new song.

        Args:
            song: Song object to create

        Returns:
            Created song with ID
        """
        with session_scope() as session:
            session.add(song)
            session.commit()
            session.refresh(song)
            return song

    @staticmethod
    def update(song: Song) -> Song:
        """
        Update an existing song.

        Args:
            song: Song object to update

        Returns:
            Updated song
        """
        with session_scope() as session:
            session.add(song)
            session.commit()
            session.refresh(song)
            return song

