from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.clip import SongClip
from app.models.song import DEFAULT_USER_ID, Song
from app.schemas.analysis import BeatAlignedBoundariesResponse, ClipBoundaryMetadata, SongAnalysis
from app.schemas.clip import ClipPlanBatchResponse, SongClipRead
from app.schemas.clip import ClipGenerationSummary, ClipPlanBatchResponse, SongClipRead
from app.schemas.analysis import SongAnalysis
from app.schemas.job import SongAnalysisJobResponse
from app.schemas.song import SongRead, SongUploadResponse
from app.services import preprocess_audio
from app.services.beat_alignment import (
    ACCEPTABLE_ALIGNMENT,
    calculate_beat_aligned_boundaries,
    validate_boundaries,
)
from app.services.clip_generation import get_clip_generation_summary
from app.services.clip_planning import (
    ClipPlanningError,
    persist_clip_plans,
    plan_beat_aligned_clips,
)
from app.services.song_analysis import enqueue_song_analysis, get_latest_analysis
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


@router.post(
    "/{song_id}/analyze",
    response_model=SongAnalysisJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue song analysis job",
)
def analyze_song(song_id: UUID, db: Session = Depends(get_db)) -> SongAnalysisJobResponse:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    if not song.processed_s3_key:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Song is missing processed audio; please re-upload.",
        )

    return enqueue_song_analysis(song_id)


@router.get(
    "/{song_id}/analysis",
    response_model=SongAnalysis,
    summary="Get latest song analysis",
)
def get_song_analysis(song_id: UUID, db: Session = Depends(get_db)) -> SongAnalysis:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    analysis = get_latest_analysis(song_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song analysis not found. Trigger analysis first.",
        )

    return analysis


@router.get("/{song_id}", response_model=SongRead, summary="Get song")
def get_song(song_id: UUID, db: Session = Depends(get_db)) -> Song:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    return song


@router.get(
    "/{song_id}/beat-aligned-boundaries",
    response_model=BeatAlignedBoundariesResponse,
    summary="Get beat-aligned clip boundaries",
)
def get_beat_aligned_boundaries(
    song_id: UUID,
    fps: float = 24.0,
    db: Session = Depends(get_db),
) -> BeatAlignedBoundariesResponse:
    """
    Calculate beat-aligned clip boundaries for a song.

    Returns clip boundaries that align with beats and video frames,
    with each clip between 3-6 seconds in duration.

    Args:
        song_id: Song ID
        fps: Video frames per second (default: 24.0). Higher FPS improves alignment accuracy.
    """
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    analysis = get_latest_analysis(song_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song analysis not found. Trigger analysis first.",
        )

    if not analysis.beat_times:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Song analysis does not contain beat times. Please re-analyze the song.",
        )

    if not analysis.duration_sec or analysis.duration_sec <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid song duration in analysis.",
        )

    # Validate FPS
    if fps <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="FPS must be greater than 0.",
        )

    # Calculate beat-aligned boundaries
    boundaries = calculate_beat_aligned_boundaries(
        beat_times=analysis.beat_times,
        song_duration=analysis.duration_sec,
        fps=fps,
    )

    # Validate boundaries
    is_valid, max_error, avg_error = validate_boundaries(
        boundaries=boundaries,
        beat_times=analysis.beat_times,
        song_duration=analysis.duration_sec,
        max_drift=ACCEPTABLE_ALIGNMENT,
        fps=fps,
    )

    # Convert boundaries to response format
    boundary_metadata = [
        ClipBoundaryMetadata(
            start_time=boundary.start_time,
            end_time=boundary.end_time,
            start_beat_index=boundary.start_beat_index,
            end_beat_index=boundary.end_beat_index,
            start_frame_index=boundary.start_frame_index,
            end_frame_index=boundary.end_frame_index,
            start_alignment_error=boundary.start_alignment_error,
            end_alignment_error=boundary.end_alignment_error,
            duration_sec=boundary.duration_sec,
            beats_in_clip=boundary.beats_in_clip,
        )
        for boundary in boundaries
    ]

    return BeatAlignedBoundariesResponse(
        boundaries=boundary_metadata,
        clip_count=len(boundaries),
        song_duration=analysis.duration_sec,
        bpm=analysis.bpm,
        fps=fps,
        total_beats=len(analysis.beat_times),
        max_alignment_error=max_error,
        avg_alignment_error=avg_error,
        validation_status="valid" if is_valid else "warning",
    )


@router.post(
    "/{song_id}/clips/plan",
    response_model=ClipPlanBatchResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate beat-aligned clip plan for song",
)
def plan_clips_for_song(
    song_id: UUID,
    clip_count: int = Query(4, ge=1, le=32),
    min_clip_sec: float = Query(3.0, ge=0.5),
    max_clip_sec: float = Query(15.0, ge=1.0),
    db: Session = Depends(get_db),
) -> ClipPlanBatchResponse:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    if not song.duration_sec:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Song duration is missing. Upload and analyze the song first.",
        )

    if min_clip_sec >= max_clip_sec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_clip_sec must be less than max_clip_sec",
        )

    analysis = get_latest_analysis(song_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Song analysis not found. Run analysis before planning clips.",
        )

    try:
        plans = plan_beat_aligned_clips(
            duration_sec=song.duration_sec,
            analysis=analysis,
            clip_count=clip_count,
            min_clip_sec=min_clip_sec,
            max_clip_sec=max_clip_sec,
            generator_fps=8,
        )
    except ClipPlanningError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    persisted = persist_clip_plans(
        song_id=song_id,
        plans=plans,
        fps=8,
        source="beat",
        clear_existing=True,
    )

    return ClipPlanBatchResponse(clips_planned=len(persisted))


@router.get(
    "/{song_id}/clips",
    response_model=List[SongClipRead],
    summary="List planned clips for a song",
)
def list_planned_clips(song_id: UUID, db: Session = Depends(get_db)) -> List[SongClipRead]:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    clips = db.exec(
        select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
    ).all()

    return [SongClipRead.model_validate(clip) for clip in clips]


@router.get(
    "/{song_id}/clips/status",
    response_model=ClipGenerationSummary,
    summary="Get clip generation status and aggregate progress",
)
def get_clip_generation_status(song_id: UUID, db: Session = Depends(get_db)) -> ClipGenerationSummary:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    try:
        return get_clip_generation_summary(song_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No clip plans found for this song.",
        ) from exc

