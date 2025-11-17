"""Song API routes for audio upload and management."""

import asyncio
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import select

from app.api.deps import SessionDep, get_current_user
from app.core.config import get_settings
from app.models.song import Song
from app.models.user import User
from app.schemas.song import SongRead, SongUploadResponse
from app.services.audio_validation import validate_audio_file
from app.services.storage_service import upload_bytes_to_s3

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


@router.post(
    "/",
    response_model=SongUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new song",
)
async def upload_song(
    session: SessionDep,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> SongUploadResponse:
    """Upload an audio file and create a song record.

    Args:
        file: Audio file to upload (MP3, WAV, or M4A)
        session: Database session
        current_user: Current authenticated user

    Returns:
        SongUploadResponse with song ID and metadata

    Raises:
        HTTPException: If file validation fails or upload fails
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing filename",
        )

    # Read file contents
    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty",
        )

    # Validate audio file
    validation_result = await asyncio.to_thread(
        validate_audio_file,
        file_bytes=contents,
        filename=file.filename,
    )

    if not validation_result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation_result.error_message or "Invalid audio file",
        )

    # Generate S3 key
    song_title = Path(file.filename).stem or "Untitled Song"
    # Create song record first to get ID
    song = Song(
        user_id=current_user.id,
        title=song_title,
        duration_sec=validation_result.duration_sec or 0.0,
        audio_s3_key="",  # Will be set after upload
    )
    session.add(song)
    session.commit()
    session.refresh(song)

    # Generate S3 key with song ID
    file_extension = Path(file.filename).suffix or ".mp3"
    s3_key = f"songs/{song.id}/audio{file_extension}"

    # Upload to S3
    try:
        await asyncio.to_thread(
            upload_bytes_to_s3,
            bucket=settings.s3_bucket_name,
            key=s3_key,
            data=contents,
            content_type=file.content_type,
        )
        logger.info(
            "Successfully uploaded audio file to S3",
            extra={
                "song_id": song.id,
                "user_id": current_user.id,
                "s3_bucket": settings.s3_bucket_name,
                "s3_key": s3_key,
                "file_size": len(contents),
                "uploaded_filename": file.filename,
                "duration_sec": validation_result.duration_sec,
            },
        )
    except Exception as exc:
        # Log the actual error for debugging
        logger.error(
            f"Failed to upload audio file to S3: {exc}",
            exc_info=True,
            extra={
                "song_id": song.id,
                "s3_bucket": settings.s3_bucket_name,
                "s3_key": s3_key,
                "file_size": len(contents),
            },
        )
        # Rollback song creation if upload fails
        session.delete(song)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store audio file. Please try again later.",
        ) from exc

    # Update song with S3 key
    song.audio_s3_key = s3_key
    session.add(song)
    session.commit()
    session.refresh(song)

    return SongUploadResponse(
        song_id=song.id,
        status="uploaded",
        title=song.title,
        duration_sec=song.duration_sec,
    )


@router.get(
    "/{song_id}",
    response_model=SongRead,
    summary="Get song details",
)
def get_song(
    song_id: str,
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> SongRead:
    """Get song details by ID.

    Args:
        song_id: Song ID
        session: Database session
        current_user: Current authenticated user

    Returns:
        SongRead with song details

    Raises:
        HTTPException: If song not found or user doesn't own the song
    """
    statement = select(Song).where(Song.id == song_id)
    song = session.exec(statement).first()

    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found",
        )

    # Verify user owns the song
    if song.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this song",
        )

    return SongRead(
        id=song.id,
        user_id=song.user_id,
        title=song.title,
        duration_sec=song.duration_sec,
        audio_s3_key=song.audio_s3_key,
        created_at=song.created_at,
    )


@router.get(
    "/",
    response_model=List[SongRead],
    summary="List user's songs",
)
def list_songs(
    session: SessionDep,
    current_user: User = Depends(get_current_user),
) -> List[SongRead]:
    """List all songs for the current user.

    Args:
        session: Database session
        current_user: Current authenticated user

    Returns:
        List of SongRead objects
    """
    statement = select(Song).where(Song.user_id == current_user.id).order_by(Song.created_at.desc())
    songs = session.exec(statement).all()

    return [
        SongRead(
            id=song.id,
            user_id=song.user_id,
            title=song.title,
            duration_sec=song.duration_sec,
            audio_s3_key=song.audio_s3_key,
            created_at=song.created_at,
        )
        for song in songs
    ]

