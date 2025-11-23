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
from app.api.v1.utils import ensure_no_analysis, get_song_or_404, update_song_field, verify_song_ownership
from app.core.auth import get_current_user
from app.core.config import get_settings
from app.models.analysis import AnalysisJob, ClipGenerationJob, SongAnalysisRecord
from app.models.clip import SongClip
from app.models.composition import CompositionJob, ComposedVideo
from app.models.section_video import SectionVideo
from app.models.song import Song
from app.models.user import User
from app.schemas.analysis import (
    BeatAlignedBoundariesResponse,
    ClipBoundaryMetadata,
    SongAnalysis,
)
from app.schemas.clip import (
    ClipGenerationSummary,
    ClipPlanBatchResponse,
    SongClipRead,
    SongClipStatus,
)
from app.schemas.job import ClipGenerationJobResponse, SongAnalysisJobResponse
from app.schemas.song import (
    AudioSelectionUpdate,
    SelectedPoseUpdate,
    SongRead,
    SongUploadResponse,
    TemplateUpdate,
    TitleUpdate,
    VideoTypeUpdate,
)
from app.services import preprocess_audio
from app.core.constants import (
    ACCEPTABLE_ALIGNMENT,
    ALLOWED_CONTENT_TYPES,
    DEFAULT_MAX_CONCURRENCY,
    MAX_AUDIO_FILE_SIZE_BYTES,
    MAX_AUDIO_FILE_SIZE_MB,
    MAX_DURATION_SECONDS,
)
from app.services.beat_alignment import (
    calculate_beat_aligned_boundaries,
    validate_boundaries,
)
from app.services.clip_generation import (
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
from app.exceptions import (
    ClipGenerationError,
    ClipNotFoundError,
    CompositionError,
    JobNotFoundError,
    JobStateError,
    SongNotFoundError,
)
from app.services.composition_job import (
    cancel_job,
    enqueue_composition,
    enqueue_song_clip_composition,
    get_composed_video,
    get_job_status,
)
from app.services.song_analysis import enqueue_song_analysis, get_latest_analysis
from app.services.storage import (
    generate_presigned_get_url,
    upload_bytes_to_s3,
    get_character_image_s3_key,
)
from app.services.image_validation import validate_image, normalize_image_format
from app.schemas.composition import (
    ComposeVideoRequest,
    ComposeVideoResponse,
    ComposedVideoResponse,
    CompositionJobStatusResponse,
)

logger = logging.getLogger(__name__)


def _sanitize_filename(filename: str) -> str:
    candidate = Path(filename).name
    candidate = re.sub(r"[^a-zA-Z0-9._-]", "_", candidate)
    if not candidate or candidate in {".", ".."}:
        return "audio_upload"
    return candidate


router = APIRouter()


@router.get("/", response_model=List[SongRead], summary="List songs with analysis (max 5 per user)")
def list_songs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Song]:
    """List user's songs that have analysis, limited to 5 most recent."""
    statement = (
        select(Song)
        .join(SongAnalysisRecord, Song.id == SongAnalysisRecord.song_id)
        .where(Song.user_id == current_user.id)
        .order_by(Song.created_at.desc())
        .limit(5)
    )
    return db.exec(statement).all()


@router.post(
    "/",
    response_model=SongUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new song",
)
async def upload_song(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SongUploadResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing filename"
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio content type: {file.content_type}",
        )

    sanitized_filename = _sanitize_filename(file.filename)
    suffix = Path(sanitized_filename).suffix or ".mp3"

    # Check file size from Content-Length header first (if available)
    # This allows us to reject large files before reading them into memory
    content_length = None
    if hasattr(file, 'headers') and 'content-length' in file.headers:
        try:
            content_length = int(file.headers['content-length'])
            if content_length > MAX_AUDIO_FILE_SIZE_BYTES:
                file_size_mb = content_length / (1024 * 1024)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Audio file size ({file_size_mb:.1f}MB) exceeds maximum ({MAX_AUDIO_FILE_SIZE_MB}MB).",
                )
        except (ValueError, KeyError):
            pass  # If Content-Length is invalid, continue to read file

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty"
        )
    
    # Check file size after reading (in case Content-Length wasn't available)
    file_size_mb = len(contents) / (1024 * 1024)
    if len(contents) > MAX_AUDIO_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Audio file size ({file_size_mb:.1f}MB) exceeds maximum ({MAX_AUDIO_FILE_SIZE_MB}MB).",
        )

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

    # Check if user has reached the 5-project limit
    existing_songs_count = db.exec(
        select(Song).where(Song.user_id == current_user.id)
    ).all()
    if len(existing_songs_count) >= 5:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Limit of 5 reached :( Please delete a video (or create a new account)",
        )

    settings = get_settings()
    song_title = Path(sanitized_filename).stem or "Untitled Song"

    song = Song(
        user_id=current_user.id,
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
    processed_s3_key = (
        f"songs/{song.id}/processed{preprocess_result.processed_extension}"
    )

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
def analyze_song(
    song_id: UUID, db: Session = Depends(get_db)
) -> SongAnalysisJobResponse:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

    analysis = get_latest_analysis(song_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song analysis not found. Trigger analysis first.",
        )

    return analysis


@router.delete(
    "/delete-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete all songs for the current user",
    response_model=None,
)
def delete_all_songs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete all songs and related records for the current user. Includes un-analyzed tracks."""
    # Get all songs for the current user
    all_songs = db.exec(
        select(Song).where(Song.user_id == current_user.id)
    ).all()
    
    if not all_songs:
        # No songs to delete, return early
        return
    
    try:
        # Delete all related records for each song
        for song in all_songs:
            song_id = song.id
            
            # Delete clips
            clips = db.exec(select(SongClip).where(SongClip.song_id == song_id)).all()
            for clip in clips:
                db.delete(clip)
            
            # Get analysis record first (before deleting jobs that reference it)
            analysis_record = db.exec(
                select(SongAnalysisRecord).where(SongAnalysisRecord.song_id == song_id)
            ).first()
            
            # Delete analysis jobs that reference the analysis record by analysis_id
            if analysis_record:
                analysis_jobs_by_analysis_id = db.exec(
                    select(AnalysisJob).where(AnalysisJob.analysis_id == analysis_record.id)
                ).all()
                for job in analysis_jobs_by_analysis_id:
                    db.delete(job)
            
            # Delete analysis jobs by song_id (any remaining ones)
            analysis_jobs = db.exec(
                select(AnalysisJob).where(AnalysisJob.song_id == song_id)
            ).all()
            for job in analysis_jobs:
                db.delete(job)
            
            # Now delete the analysis record (after all jobs referencing it are deleted)
            if analysis_record:
                db.delete(analysis_record)
            
            # Delete clip generation jobs
            clip_jobs = db.exec(
                select(ClipGenerationJob).where(ClipGenerationJob.song_id == song_id)
            ).all()
            for job in clip_jobs:
                db.delete(job)
            
            # Delete composed videos first (get IDs before deletion)
            composed_videos = db.exec(
                select(ComposedVideo).where(ComposedVideo.song_id == song_id)
            ).all()
            composed_video_ids = [video.id for video in composed_videos]
            
            # Delete composition jobs that reference these composed videos
            if composed_video_ids:
                composition_jobs_with_video = db.exec(
                    select(CompositionJob).where(
                        CompositionJob.composed_video_id.in_(composed_video_ids)  # type: ignore
                    )
                ).all()
                for job in composition_jobs_with_video:
                    db.delete(job)
            
            # Delete composition jobs by song_id (any remaining ones)
            composition_jobs = db.exec(
                select(CompositionJob).where(CompositionJob.song_id == song_id)
            ).all()
            for job in composition_jobs:
                db.delete(job)
            
            # Now delete composed videos (after all jobs referencing them are deleted)
            for video in composed_videos:
                db.delete(video)
            
            # Delete section videos
            section_videos = db.exec(
                select(SectionVideo).where(SectionVideo.song_id == song_id)
            ).all()
            for video in section_videos:
                db.delete(video)
            
            # Delete the song itself
            db.delete(song)
        
        db.commit()
        logger.info(f"Deleted all songs for user {current_user.id}")
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to delete all songs for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete all songs: {str(e)}",
        ) from e


@router.get("/{song_id}", response_model=SongRead, summary="Get song")
def get_song(
    song_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Song:
    """Get a song by ID. Only returns songs owned by the current user."""
    song = get_song_or_404(song_id, db)
    verify_song_ownership(song, current_user)
    return song


@router.get("/{song_id}/public", response_model=SongRead, summary="Get song (public, read-only)")
def get_song_public(
    song_id: UUID,
    db: Session = Depends(get_db),
) -> Song:
    """Get a song by ID for public viewing. No authentication required, read-only access."""
    song = get_song_or_404(song_id, db)
    return song


@router.delete(
    "/{song_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a song",
    response_model=None,
)
def delete_song(
    song_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Delete a song and all related records. Only deletes songs owned by the current user."""
    song = get_song_or_404(song_id, db)
    verify_song_ownership(song, current_user)
    
    try:
        # Delete all related records
        # Delete clips
        clips = db.exec(select(SongClip).where(SongClip.song_id == song_id)).all()
        for clip in clips:
            db.delete(clip)
        
        # Get analysis record first (before deleting jobs that reference it)
        analysis_record = db.exec(
            select(SongAnalysisRecord).where(SongAnalysisRecord.song_id == song_id)
        ).first()
        
        # Delete analysis jobs that reference the analysis record by analysis_id
        # (must be deleted before the analysis record due to FK constraint)
        if analysis_record:
            analysis_jobs_by_analysis_id = db.exec(
                select(AnalysisJob).where(AnalysisJob.analysis_id == analysis_record.id)
            ).all()
            for job in analysis_jobs_by_analysis_id:
                db.delete(job)
        
        # Delete analysis jobs by song_id (any remaining ones)
        analysis_jobs = db.exec(
            select(AnalysisJob).where(AnalysisJob.song_id == song_id)
        ).all()
        for job in analysis_jobs:
            db.delete(job)
        
        # Now delete the analysis record (after all jobs referencing it are deleted)
        if analysis_record:
            db.delete(analysis_record)
        
        # Delete clip generation jobs
        clip_jobs = db.exec(
            select(ClipGenerationJob).where(ClipGenerationJob.song_id == song_id)
        ).all()
        for job in clip_jobs:
            db.delete(job)
        
        # Delete composed videos first (get IDs before deletion)
        composed_videos = db.exec(
            select(ComposedVideo).where(ComposedVideo.song_id == song_id)
        ).all()
        composed_video_ids = [video.id for video in composed_videos]
        
        # Delete composition jobs that reference these composed videos
        # (must be deleted before composed videos due to FK constraint)
        if composed_video_ids:
            composition_jobs_with_video = db.exec(
                select(CompositionJob).where(
                    CompositionJob.composed_video_id.in_(composed_video_ids)  # type: ignore
                )
            ).all()
            for job in composition_jobs_with_video:
                db.delete(job)
        
        # Delete composition jobs by song_id (any remaining ones)
        composition_jobs = db.exec(
            select(CompositionJob).where(CompositionJob.song_id == song_id)
        ).all()
        for job in composition_jobs:
            db.delete(job)
        
        # Now delete composed videos (after all jobs referencing them are deleted)
        for video in composed_videos:
            db.delete(video)
        
        # Delete section videos
        section_videos = db.exec(
            select(SectionVideo).where(SectionVideo.song_id == song_id)
        ).all()
        for video in section_videos:
            db.delete(video)
        
        # Delete the song itself
        db.delete(song)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to delete song {song_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete song: {str(e)}",
        ) from e


@router.patch(
    "/{song_id}/video-type",
    response_model=SongRead,
    summary="Set video type for song",
)
def set_video_type(
    song_id: UUID,
    video_type: VideoTypeUpdate,
    db: Session = Depends(get_db),
) -> Song:
    """Set the video type (full-length or short-form) for a song.

    This must be set before analysis runs, as it affects the analysis
    and generation workflow.
    """
    song = get_song_or_404(song_id, db)

    # Prevent changing after analysis has started
    # Note: video_type validation is handled by VideoTypeUpdate schema
    ensure_no_analysis(song_id)

    return update_song_field(song, "video_type", video_type.video_type, db)


@router.patch(
    "/{song_id}/title",
    response_model=SongRead,
    summary="Update song title",
)
def update_song_title(
    song_id: UUID,
    title_update: TitleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Song:
    """Update the title of a song. Only the song owner can update it."""
    song = get_song_or_404(song_id, db)
    verify_song_ownership(song, current_user)
    
    return update_song_field(song, "title", title_update.title, db)


@router.patch(
    "/{song_id}/template",
    response_model=SongRead,
    summary="Set visual style template for song",
)
def set_template(
    song_id: UUID,
    template: TemplateUpdate,
    db: Session = Depends(get_db),
) -> Song:
    """Set the visual style template (abstract, environment, character, minimal) for a song.
    
    This affects the visual style of generated video clips.
    """
    song = get_song_or_404(song_id, db)
    
    return update_song_field(song, "template", template.template, db)


@router.patch(
    "/{song_id}/selection",
    response_model=SongRead,
    summary="Update audio selection range",
)
def update_audio_selection(
    song_id: UUID,
    selection: AudioSelectionUpdate,
    db: Session = Depends(get_db),
) -> Song:
    """Update the selected audio segment for a song."""
    song = get_song_or_404(song_id, db)

    if song.duration_sec is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Song duration not available. Please wait for analysis to complete.",
        )

    # Validate selection using centralized validation service
    from app.services.audio_selection import validate_audio_selection

    try:
        validate_audio_selection(
            start_sec=selection.start_sec,
            end_sec=selection.end_sec,
            song_duration_sec=song.duration_sec,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

    # Update song fields
    song.selected_start_sec = selection.start_sec
    song.selected_end_sec = selection.end_sec
    db.add(song)
    db.commit()
    db.refresh(song)

    return song


@router.post(
    "/{song_id}/character-image",
    status_code=status.HTTP_200_OK,
    summary="Upload character reference image",
)
async def upload_character_image(
    song_id: UUID,
    image: UploadFile = File(...),
    pose: str = "A",  # "A" for pose-a (reference), "B" for pose-b
    db: Session = Depends(get_db),
) -> dict:
    """
    Upload a character reference image for a song.

    Only available for songs with video_type='short_form'.
    The image will be validated, normalized to JPEG, and stored in S3.
    
    Args:
        pose: "A" for pose-a (reference/primary image) or "B" for pose-b (secondary image)
    """
    settings = get_settings()

    # Get song
    song = get_song_or_404(song_id, db)

    # Only allow for short_form videos
    if song.video_type != "short_form":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character consistency only available for short_form videos",
        )

    # Validate pose parameter
    pose_upper = pose.upper()
    if pose_upper not in ("A", "B"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="pose parameter must be 'A' or 'B'",
        )

    # Read image bytes
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Image file is empty"
        )

    # Validate image
    is_valid, error_msg, metadata = validate_image(image_bytes, image.filename)
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg)

    # Normalize to JPEG
    try:
        normalized_bytes = normalize_image_format(image_bytes, "JPEG")
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format: {str(exc)}"
        ) from exc

    # Generate S3 key based on pose
    if pose_upper == "A":
        s3_key = get_character_image_s3_key(str(song_id), "reference")
    else:  # pose_upper == "B"
        s3_key = f"songs/{song_id}/character_pose_b.jpg"

    # Upload to S3
    try:
        await asyncio.to_thread(
            upload_bytes_to_s3,
            bucket_name=settings.s3_bucket_name,
            key=s3_key,
            data=normalized_bytes,
            content_type="image/jpeg",
        )
    except Exception as exc:
        logger.exception(f"Failed to upload character image to S3: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store image. Verify storage configuration.",
        ) from exc

    # Update song record
    if pose_upper == "A":
        song.character_reference_image_s3_key = s3_key
        song.character_consistency_enabled = True
    else:  # pose_upper == "B"
        song.character_pose_b_s3_key = s3_key
    db.add(song)
    db.commit()
    db.refresh(song)

    # Enqueue background job to generate consistent character image (only for Pose A)
    if pose_upper == "A":
        try:
            from app.core.queue import get_queue
            from app.services.character_consistency import generate_character_image_job

            queue = get_queue(
                queue_name=f"{settings.rq_worker_queue}:character-generation",
                timeout=300,  # 5 minutes
            )
            queue.enqueue(
                generate_character_image_job,
                song_id,
                job_timeout=300,
            )
            logger.info(f"Enqueued character image generation job for song {song_id}")
        except Exception as exc:
            # Don't fail the upload if job enqueue fails
            logger.warning(f"Failed to enqueue character image generation job: {exc}")

    # Generate presigned URL
    try:
        image_url = await asyncio.to_thread(
            generate_presigned_get_url,
            bucket_name=settings.s3_bucket_name,
            key=s3_key,
            expires_in=3600,
        )
    except Exception as exc:
        logger.exception(f"Failed to generate presigned URL: {exc}")
        image_url = None

    return {
        "song_id": str(song_id),
        "image_s3_key": s3_key,
        "image_url": image_url,
        "metadata": metadata,
        "status": "uploaded",
        "character_consistency_enabled": True,
    }


@router.get(
    "/{song_id}/character-image/url",
    summary="Get presigned URLs for character images",
)
async def get_character_image_urls(
    song_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get presigned URLs for character reference image and pose-b image.
    
    Returns URLs for both poses if available.
    """
    settings = get_settings()
    song = get_song_or_404(song_id, db)
    
    result: dict = {
        "pose_a_url": None,
        "pose_b_url": None,
        "selected_pose": song.character_selected_pose or "A",
    }
    
    # Get pose-a (reference image) URL
    if song.character_reference_image_s3_key:
        try:
            pose_a_url = await asyncio.to_thread(
                generate_presigned_get_url,
                bucket_name=settings.s3_bucket_name,
                key=song.character_reference_image_s3_key,
                expires_in=3600,
            )
            result["pose_a_url"] = pose_a_url
        except Exception as exc:
            logger.warning(f"Failed to generate presigned URL for pose-a: {exc}")
    
    # Get pose-b URL
    if song.character_pose_b_s3_key:
        try:
            pose_b_url = await asyncio.to_thread(
                generate_presigned_get_url,
                bucket_name=settings.s3_bucket_name,
                key=song.character_pose_b_s3_key,
                expires_in=3600,
            )
            result["pose_b_url"] = pose_b_url
        except Exception as exc:
            logger.warning(f"Failed to generate presigned URL for pose-b: {exc}")
    
    return result


@router.patch(
    "/{song_id}/selected-pose",
    response_model=SongRead,
    summary="Update selected character pose",
)
def update_selected_pose(
    song_id: UUID,
    pose_update: SelectedPoseUpdate,
    db: Session = Depends(get_db),
) -> Song:
    """Update the selected character pose (A or B) for a song."""
    song = get_song_or_404(song_id, db)
    
    # Only allow for short_form videos
    if song.video_type != "short_form":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character pose selection only available for short_form videos",
        )
    
    # Validate that at least one pose exists
    if pose_update.selected_pose == "A" and not song.character_reference_image_s3_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pose A image not available. Please upload a character reference image first.",
        )
    if pose_update.selected_pose == "B" and not song.character_pose_b_s3_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pose B image not available. Please upload a Pose B image first.",
        )
    
    song.character_selected_pose = pose_update.selected_pose
    db.add(song)
    db.commit()
    db.refresh(song)
    
    logger.info(f"Updated selected pose for song {song_id} to {pose_update.selected_pose}")
    
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )
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

    # Determine effective duration and time offset based on selection
    if song.selected_start_sec is not None and song.selected_end_sec is not None:
        effective_duration = song.selected_end_sec - song.selected_start_sec
        time_offset = song.selected_start_sec
        logger.info(
            f"Using selected audio range: {song.selected_start_sec}s - {song.selected_end_sec}s "
            f"(duration: {effective_duration}s) for song {song_id}"
        )
    else:
        effective_duration = song.duration_sec
        time_offset = 0.0
        logger.info(
            f"Using full audio duration: {effective_duration}s for song {song_id}"
        )

    min_required_clips = max(1, int(math.ceil(effective_duration / max_clip_sec)))

    effective_clip_count = clip_count if clip_count is not None else min_required_clips
    effective_clip_count = max(3, min(64, effective_clip_count))

    if effective_clip_count < min_required_clips:
        effective_clip_count = min(64, min_required_clips)

    min_total_required = min_clip_sec * effective_clip_count
    if effective_duration < min_total_required - 1e-3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unable to plan clips: effective duration is shorter than minimum total clip "
                "duration. Reduce clip_count or lower min_clip_sec."
            ),
        )

    try:
        plans = plan_beat_aligned_clips(
            duration_sec=effective_duration,
            analysis=analysis,
            clip_count=effective_clip_count,
            min_clip_sec=min_clip_sec,
            max_clip_sec=max_clip_sec,
            generator_fps=8,
            selection_start_sec=song.selected_start_sec if song.selected_start_sec is not None else None,
            selection_end_sec=song.selected_end_sec if song.selected_end_sec is not None else None,
        )
    except ClipPlanningError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    # Adjust clip start/end times by time offset if selection is active
    # (Note: if selection is used, plans are already relative to selection start,
    # so we need to add the offset to get absolute times)
    if time_offset > 0:
        for plan in plans:
            plan.start_sec = round(plan.start_sec + time_offset, 4)
            plan.end_sec = round(plan.end_sec + time_offset, 4)

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
def list_planned_clips(
    song_id: UUID, db: Session = Depends(get_db)
) -> List[SongClipRead]:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

    clips = db.exec(
        select(SongClip)
        .where(SongClip.song_id == song_id)
        .order_by(SongClip.clip_index)
    ).all()

    return [SongClipRead.model_validate(clip) for clip in clips]


@router.get(
    "/{song_id}/clips/status",
    response_model=ClipGenerationSummary,
    summary="Get clip generation status and aggregate progress",
)
def get_clip_generation_status(
    song_id: UUID, db: Session = Depends(get_db)
) -> ClipGenerationSummary:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

    # get_clip_generation_summary now returns empty summary instead of raising error
    return get_clip_generation_summary(song_id)


@router.get(
    "/{song_id}/clips/job",
    response_model=Optional[ClipGenerationJobResponse],
    summary="Get active clip generation job for a song",
)
def get_active_clip_generation_job(
    song_id: UUID, db: Session = Depends(get_db)
) -> Optional[ClipGenerationJobResponse]:
    """Get the active (queued or processing) clip generation job for a song, if any."""
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

    from sqlmodel import select
    from app.models.analysis import ClipGenerationJob

    job = db.exec(
        select(ClipGenerationJob)
        .where(ClipGenerationJob.song_id == song_id)
        .where(ClipGenerationJob.status.in_(["queued", "processing"]))
        .order_by(ClipGenerationJob.created_at.desc())
    ).first()

    if not job:
        return None

    return ClipGenerationJobResponse(
        job_id=job.id,
        song_id=job.song_id,
        status=job.status,
    )


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

    try:
        return start_clip_generation_job(song_id, max_parallel=max_parallel)
    except ClipGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.post(
    "/{song_id}/clips/job/{job_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel a clip generation job",
)
def cancel_clip_generation_job(
    song_id: UUID,
    job_id: str,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    Cancel a clip generation job.
    
    Args:
        song_id: Song ID
        job_id: Clip generation job ID
        
    Returns:
        Dict with status message
    """
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )
    
    from app.services.clip_generation import cancel_clip_generation_job
    from app.exceptions import JobNotFoundError, JobStateError
    
    try:
        cancel_clip_generation_job(job_id)
        return {"status": "cancelled", "job_id": job_id}
    except JobNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        ) from e
    except JobStateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found for song"
        )

    if clip.status in {"processing", "queued"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clip is already queued or processing.",
        )

    try:
        refreshed = retry_clip_generation(clip_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

    summary = get_clip_generation_summary(song_id)

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
        error_detail = (
            str(exc) if exc else "Failed to compose video. Please try again later."
        )
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

    summary = get_clip_generation_summary(song_id)

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
    except (ValueError, CompositionError, SongNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

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
    except (ValueError, CompositionError, SongNotFoundError, ClipNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e

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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

    try:
        return get_job_status(job_id)
    except (ValueError, JobNotFoundError) as e:
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

    try:
        cancel_job(job_id)
        return {"status": "cancelled", "job_id": job_id}
    except (ValueError, JobNotFoundError, JobStateError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Song not found"
        )

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
