from __future__ import annotations

import asyncio
import json
import logging
import math
import re
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.clip import SongClip
from app.models.song import DEFAULT_USER_ID, Song
from app.schemas.analysis import BeatAlignedBoundariesResponse, ClipBoundaryMetadata, SongAnalysis
from app.schemas.clip import (
    ClipGenerationSummary,
    ClipPlanBatchResponse,
    SongClipRead,
    SongClipStatus,
)
from app.schemas.job import ClipGenerationJobResponse, SongAnalysisJobResponse
from app.schemas.song import SongRead, SongUploadResponse
from app.services import preprocess_audio
from app.services.beat_alignment import (
    ACCEPTABLE_ALIGNMENT,
    calculate_beat_aligned_boundaries,
    validate_boundaries,
)
from app.services.clip_generation import (
    DEFAULT_MAX_CONCURRENCY,
    compose_song_video,
    get_clip_generation_summary,
    retry_clip_generation,
    start_clip_generation_job,
)
from app.services.clip_planning import (
    ClipPlanningError,
    persist_clip_plans,
    plan_beat_aligned_clips,
)
from app.services.composition_job import (
    cancel_job,
    enqueue_composition,
    enqueue_song_clip_composition,
    get_composed_video,
    get_job_status,
)
from app.services.song_analysis import enqueue_song_analysis, get_latest_analysis
from app.services.storage import generate_presigned_get_url, upload_bytes_to_s3
from app.schemas.composition import (
    ComposeVideoRequest,
    ComposeVideoResponse,
    ComposedVideoResponse,
    CompositionJobStatusResponse,
)

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

logger = logging.getLogger(__name__)


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
        logger.exception(
            "Failed to upload audio assets to storage (bucket=%s, song_id=%s, filename=%s)",
            settings.s3_bucket_name,
            song.id,
            sanitized_filename,
        )
        db.delete(song)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store audio file. Verify storage configuration and try again.",
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
        logger.exception(
            "Failed to generate presigned URL for uploaded audio (bucket=%s, key=%s)",
            settings.s3_bucket_name,
            original_s3_key,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate access URL for uploaded audio. Verify storage configuration.",
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
    clip_count: Optional[int] = Query(None, ge=1, le=64),
    min_clip_sec: float = Query(3.0, ge=0.5),
    max_clip_sec: float = Query(6.0, ge=1.0),
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

    min_required_clips = max(1, int(math.ceil(song.duration_sec / max_clip_sec)))

    effective_clip_count = clip_count if clip_count is not None else min_required_clips
    effective_clip_count = max(3, min(64, effective_clip_count))

    if effective_clip_count < min_required_clips:
        effective_clip_count = min(64, min_required_clips)

    min_total_required = min_clip_sec * effective_clip_count
    if song.duration_sec < min_total_required - 1e-3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unable to plan clips: song duration is shorter than minimum total clip "
                "duration. Reduce clip_count or lower min_clip_sec."
            ),
        )

    try:
        plans = plan_beat_aligned_clips(
            duration_sec=song.duration_sec,
            analysis=analysis,
            clip_count=effective_clip_count,
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


@router.post(
    "/{song_id}/clips/generate",
    response_model=ClipGenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start clip generation job",
)
def generate_clip_batch(
    song_id: UUID,
    max_parallel: int = Query(DEFAULT_MAX_CONCURRENCY, ge=1, le=8),
    db: Session = Depends(get_db),
) -> ClipGenerationJobResponse:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    try:
        return start_clip_generation_job(song_id, max_parallel=max_parallel)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{song_id}/clips/{clip_id}/retry",
    response_model=SongClipStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry generation for a single clip",
)
def retry_clip_generation_route(
    song_id: UUID,
    clip_id: UUID,
    db: Session = Depends(get_db),
) -> SongClipStatus:
    clip = db.get(SongClip, clip_id)
    if not clip or clip.song_id != song_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found for song")

    if clip.status in {"processing", "queued"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clip is already queued or processing.",
        )

    try:
        refreshed = retry_clip_generation(clip_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return refreshed


@router.post(
    "/{song_id}/clips/compose",
    response_model=ClipGenerationSummary,
    summary="Compose completed clips into a single video",
)
async def compose_completed_clips(
    song_id: UUID,
    db: Session = Depends(get_db),
) -> ClipGenerationSummary:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    try:
        summary = get_clip_generation_summary(song_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No clip plans found for this song.",
        ) from exc

    if summary.total_clips == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No clips available for composition.",
        )
    if summary.failed_clips > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolve failed clips before composing.",
        )
    if summary.completed_clips != summary.total_clips:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clip generation must be complete before composing.",
        )

    if summary.composed_video_url:
        return summary

    try:
        await asyncio.to_thread(compose_song_video, song_id)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to compose video for song %s", song_id)
        # Include the actual error message for debugging
        error_detail = str(exc) if exc else "Failed to compose video. Please try again later."
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compose video: {error_detail}",
        ) from exc

    return get_clip_generation_summary(song_id)


@router.post(
    "/{song_id}/clips/compose/async",
    response_model=ComposeVideoResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue async composition job for SongClips",
)
def compose_song_clips_async(
    song_id: UUID,
    db: Session = Depends(get_db),
) -> ComposeVideoResponse:
    """
    Enqueue an async composition job to stitch all completed SongClips into a single video.
    
    This endpoint automatically uses all completed SongClips for the song and returns
    a job ID that can be polled for progress.

    Args:
        song_id: Song ID

    Returns:
        ComposeVideoResponse with job ID for polling
    """
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    try:
        summary = get_clip_generation_summary(song_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No clip plans found for this song.",
        ) from exc

    if summary.total_clips == 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No clips available for composition.",
        )
    if summary.failed_clips > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolve failed clips before composing.",
        )
    if summary.completed_clips != summary.total_clips:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clip generation must be complete before composing.",
        )

    if summary.composed_video_url:
        # Already composed, but we'll still return a job ID for consistency
        # In practice, the frontend should check for composed_video_url first
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Video already composed. Refresh to see the result.",
        )

    try:
        job_id, _ = enqueue_song_clip_composition(song_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return ComposeVideoResponse(
        job_id=job_id,
        status="queued",
        song_id=str(song_id),
    )


@router.post(
    "/{song_id}/compose",
    response_model=ComposeVideoResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Enqueue video composition job",
)
def compose_video(
    song_id: UUID,
    request: ComposeVideoRequest,
    db: Session = Depends(get_db),
) -> ComposeVideoResponse:
    """
    Enqueue a video composition job to stitch clips together.

    Args:
        song_id: Song ID
        request: Composition request with clip IDs and metadata

    Returns:
        ComposeVideoResponse with job ID
    """
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    # Validate clip IDs match metadata
    if len(request.clip_ids) != len(request.clip_metadata):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Number of clip IDs must match number of clip metadata entries",
        )

    # Convert clip metadata to dict format
    clip_metadata_dicts = [
        {
            "clipId": str(meta.clip_id),
            "startFrame": meta.start_frame,
            "endFrame": meta.end_frame,
        }
        for meta in request.clip_metadata
    ]

    # Create job and enqueue to RQ
    try:
        job_id, _ = enqueue_composition(
            song_id=song_id,
            clip_ids=request.clip_ids,
            clip_metadata=clip_metadata_dicts,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return ComposeVideoResponse(
        job_id=job_id,
        status="queued",
        song_id=str(song_id),
    )


@router.get(
    "/{song_id}/compose/{job_id}/status",
    response_model=CompositionJobStatusResponse,
    summary="Get composition job status",
)
def get_composition_job_status(
    song_id: UUID,
    job_id: str,
    db: Session = Depends(get_db),
) -> CompositionJobStatusResponse:
    """
    Get the status of a composition job.

    Args:
        song_id: Song ID
        job_id: Composition job ID

    Returns:
        CompositionJobStatusResponse with job status and progress
    """
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    try:
        return get_job_status(job_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/{song_id}/compose/{job_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel a composition job",
)
def cancel_composition_job(
    song_id: UUID,
    job_id: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Cancel a composition job.

    Args:
        song_id: Song ID
        job_id: Composition job ID

    Returns:
        Dict with status message
    """
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    try:
        cancel_job(job_id)
        return {"status": "cancelled", "job_id": job_id}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.get(
    "/{song_id}/composed-videos/{composed_video_id}",
    response_model=ComposedVideoResponse,
    summary="Get composed video details",
)
def get_composed_video_endpoint(
    song_id: UUID,
    composed_video_id: UUID,
    db: Session = Depends(get_db),
) -> ComposedVideoResponse:
    """
    Get details of a composed video.

    Args:
        song_id: Song ID
        composed_video_id: ComposedVideo ID

    Returns:
        ComposedVideoResponse with video details and presigned URL
    """
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    composed_video = get_composed_video(composed_video_id)
    if not composed_video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Composed video not found"
        )
    if composed_video.song_id != song_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Composed video does not belong to this song",
        )

    # Generate presigned URL
    settings = get_settings()
    try:
        video_url = generate_presigned_get_url(
            bucket_name=settings.s3_bucket_name,
            key=composed_video.s3_key,
            expires_in=3600,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate video URL: {e}",
        ) from e

    # Parse clip IDs from JSON
    clip_ids = json.loads(composed_video.clip_ids)

    return ComposedVideoResponse(
        id=str(composed_video.id),
        song_id=str(composed_video.song_id),
        video_url=video_url,
        duration_sec=composed_video.duration_sec,
        file_size_bytes=composed_video.file_size_bytes,
        resolution_width=composed_video.resolution_width,
        resolution_height=composed_video.resolution_height,
        fps=composed_video.fps,
        clip_ids=clip_ids,
        status=composed_video.status,
        created_at=composed_video.created_at.isoformat(),
    )

