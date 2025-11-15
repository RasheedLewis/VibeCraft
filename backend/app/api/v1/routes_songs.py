from __future__ import annotations

import asyncio
import os
import re
import tempfile
from pathlib import Path
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.song import DEFAULT_USER_ID, Song
from app.schemas.song import SongRead, SongUploadResponse
from app.services import preprocess_audio
from app.services.storage import generate_presigned_get_url, upload_bytes_to_s3

ALLOWED_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/webm",
    "audio/flac",
    "audio/x-flac",
    "audio/aac",
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
}
MAX_DURATION_SECONDS = 7 * 60  # 7 minutes


def _sanitize_filename(filename: str) -> str:
    candidate = Path(filename).name
    candidate = re.sub(r"[^a-zA-Z0-9._-]", "_", candidate)
    if not candidate or candidate in {".", ".."}:
        return "audio_upload"
    return candidate


router = APIRouter()


@router.get("/", response_model=List[SongRead], summary="List songs")
def list_songs(db: Session = Depends(get_db)) -> List[Song]:
    statement = select(Song).order_by(Song.created_at.desc())
    return db.exec(statement).all()


@router.post(
    "/",
    response_model=SongUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new song",
)
async def upload_song(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> SongUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename")

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio content type: {file.content_type}",
        )

    sanitized_filename = _sanitize_filename(file.filename)
    suffix = Path(sanitized_filename).suffix or ".mp3"

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    try:
        preprocess_result = await asyncio.to_thread(
            preprocess_audio,
            file_bytes=contents,
            original_suffix=suffix,
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to preprocess audio. Please upload a valid audio file.",
        ) from exc

    if preprocess_result.duration_sec > MAX_DURATION_SECONDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Audio duration must be 7 minutes or less.",
        )

    settings = get_settings()
    song_title = Path(sanitized_filename).stem or "Untitled Song"

    song = Song(
        user_id=DEFAULT_USER_ID,
        title=song_title,
        original_filename=sanitized_filename,
        original_file_size=len(contents),
        original_content_type=file.content_type,
        duration_sec=preprocess_result.duration_sec,
        original_s3_key="",
        processed_s3_key=None,
        processed_sample_rate=preprocess_result.sample_rate,
        waveform_json=preprocess_result.waveform_json,
    )
    db.add(song)
    db.commit()
    db.refresh(song)

    original_s3_key = f"songs/{song.id}/original{suffix}"
    processed_s3_key = f"songs/{song.id}/processed{preprocess_result.processed_extension}"

    try:
        await asyncio.to_thread(
            upload_bytes_to_s3,
            bucket_name=settings.s3_bucket_name,
            key=original_s3_key,
            data=contents,
            content_type=file.content_type,
        )
        await asyncio.to_thread(
            upload_bytes_to_s3,
            bucket_name=settings.s3_bucket_name,
            key=processed_s3_key,
            data=preprocess_result.processed_bytes,
            content_type=preprocess_result.content_type,
        )
    except Exception as exc:  # noqa: BLE001
        db.delete(song)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store audio file. Please try again later.",
        ) from exc

    song.original_s3_key = original_s3_key
    song.processed_s3_key = processed_s3_key
    song.duration_sec = preprocess_result.duration_sec
    db.add(song)
    db.commit()
    db.refresh(song)

    try:
        audio_url = await asyncio.to_thread(
            generate_presigned_get_url,
            bucket_name=settings.s3_bucket_name,
            key=original_s3_key,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate access URL for uploaded audio.",
        ) from exc

    return SongUploadResponse(
        song_id=song.id,
        audio_url=audio_url,
        s3_key=original_s3_key,
        status="uploaded",
    )


@router.get("/{song_id}", response_model=SongRead, summary="Get song")
def get_song(song_id: UUID, db: Session = Depends(get_db)) -> Song:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    return song

