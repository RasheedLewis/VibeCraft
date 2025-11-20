"""Composition job orchestration service."""

from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID, uuid4

from rq.job import Job, get_current_job
from sqlmodel import select

from app.core.constants import COMPOSITION_QUEUE_TIMEOUT_SEC
from app.core.database import session_scope
from app.core.queue import get_queue
from app.exceptions import (
    ClipNotFoundError,
    CompositionError,
    JobNotFoundError,
    JobStateError,
)
from app.repositories import ClipRepository, SongRepository
from app.models.composition import ComposedVideo, CompositionJob
from app.models.section_video import SectionVideo
from app.schemas.composition import CompositionJobStatusResponse

logger = logging.getLogger(__name__)


def enqueue_composition(
    song_id: UUID,
    clip_ids: list[UUID],
    clip_metadata: list[dict[str, Any]],
) -> tuple[str, CompositionJob]:
    """
    Create a composition job, enqueue to RQ, and return job ID.

    Args:
        song_id: Song ID
        clip_ids: List of SectionVideo IDs to compose
        clip_metadata: List of metadata dicts with clipId, startFrame, endFrame

    Returns:
        Tuple of (job_id, CompositionJob record)

    Raises:
        ValueError: If song or clips not found
    """
    # Verify song exists
    SongRepository.get_by_id(song_id)

    # Verify all clips exist and belong to the song
    # Note: SectionVideo is not in repositories yet, so we keep direct access for now
    with session_scope() as session:
        for clip_id in clip_ids:
            clip = session.get(SectionVideo, clip_id)
            if not clip:
                raise ClipNotFoundError(f"SectionVideo {clip_id} not found")
            if clip.song_id != song_id:
                raise CompositionError(f"SectionVideo {clip_id} does not belong to song {song_id}")
            if clip.status != "completed" or not clip.video_url:
                raise CompositionError(f"SectionVideo {clip_id} is not ready (status: {clip.status})")

        # Store clip IDs and metadata as JSON
        clip_ids_json = json.dumps([str(clip_id) for clip_id in clip_ids])
        clip_metadata_json = json.dumps(clip_metadata)

        # Enqueue to RQ
        queue = get_queue(timeout=COMPOSITION_QUEUE_TIMEOUT_SEC)
        job_id = f"composition-{uuid4()}"
        job: Job = queue.enqueue(
            run_composition_job,
            song_id,
            clip_ids,
            clip_metadata,
            job_id=job_id,
            meta={"progress": 0},
        )

        # Create job record
        composition_job = CompositionJob(
            id=job.id,
            song_id=song_id,
            status="queued",
            progress=0,
            clip_ids=clip_ids_json,
            clip_metadata=clip_metadata_json,
        )
        session.add(composition_job)
        session.commit()
        session.refresh(composition_job)

        logger.info(f"Enqueued composition job {job.id} for song {song_id} with {len(clip_ids)} clips")

        return job.id, composition_job


def run_composition_job(
    song_id: UUID,
    clip_ids: list[UUID],
    clip_metadata: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    RQ worker function to run composition job.

    Args:
        song_id: Song ID
        clip_ids: List of SectionVideo IDs
        clip_metadata: List of metadata dicts

    Returns:
        Dict with job result
    """
    current_job = get_current_job()
    job_id = current_job.id if current_job else None

    if job_id is None:
        raise CompositionError("Cannot run composition job: no RQ job context")

    try:
        from app.services.composition_execution import execute_composition_pipeline

        execute_composition_pipeline(
            job_id=job_id,
            song_id=song_id,
            clip_ids=clip_ids,
            clip_metadata=clip_metadata,
        )
        return {"status": "completed", "song_id": str(song_id)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Composition failed for song_id=%s", song_id)
        fail_job(job_id, str(exc))
        raise


def enqueue_song_clip_composition(song_id: UUID) -> tuple[str, CompositionJob]:
    """
    Create a composition job for SongClips, enqueue to RQ, and return job ID.
    
    This function automatically gets all completed SongClips for the song.

    Args:
        song_id: Song ID

    Returns:
        Tuple of (job_id, CompositionJob record)

    Raises:
        ValueError: If song not found or no completed clips available
    """
    # Verify song exists
    SongRepository.get_by_id(song_id)

    # Get all completed SongClips for this song
    clips = ClipRepository.get_completed_by_song_id(song_id)

    if not clips:
        raise CompositionError(f"No completed clips found for song {song_id}")

    # Store clip IDs as JSON (no metadata needed for SongClip composition)
    clip_ids_json = json.dumps([str(clip.id) for clip in clips])
    clip_metadata_json = json.dumps([])  # Empty metadata for SongClip-based composition

    # Enqueue to RQ
    queue = get_queue(timeout=COMPOSITION_QUEUE_TIMEOUT_SEC)
    job_id = f"composition-songclip-{uuid4()}"
    job: Job = queue.enqueue(
        run_song_clip_composition_job,
        song_id,
        job_id=job_id,
        meta={"progress": 0},
    )

    # Create job record
    with session_scope() as session:
        composition_job = CompositionJob(
            id=job.id,
            song_id=song_id,
            status="queued",
            progress=0,
            clip_ids=clip_ids_json,
            clip_metadata=clip_metadata_json,
        )
        session.add(composition_job)
        session.commit()
        session.refresh(composition_job)

    logger.info(
        f"Enqueued SongClip composition job {job.id} for song {song_id} with {len(clips)} clips"
    )

    return job.id, composition_job


def run_song_clip_composition_job(song_id: UUID) -> dict[str, Any]:
    """
    RQ worker function to run SongClip-based composition job.

    Args:
        song_id: Song ID

    Returns:
        Dict with job result
    """
    current_job = get_current_job()
    job_id = current_job.id if current_job else None

    if job_id is None:
        raise CompositionError("Cannot run composition job: no RQ job context")

    try:
        from app.services.clip_generation import compose_song_video

        compose_song_video(song_id, job_id=job_id)
        return {"status": "completed", "song_id": str(song_id)}
    except Exception as exc:  # noqa: BLE001
        logger.exception("SongClip composition failed for song_id=%s", song_id)
        fail_job(job_id, str(exc))
        raise


def get_job_status(job_id: str) -> CompositionJobStatusResponse:
    """
    Get composition job status.

    Args:
        job_id: Job ID

    Returns:
        CompositionJobStatusResponse

    Raises:
        ValueError: If job not found
    """
    with session_scope() as session:
        job_record = session.get(CompositionJob, job_id)
        if not job_record:
            raise JobNotFoundError(f"Composition job {job_id} not found")

        return CompositionJobStatusResponse(
            job_id=job_record.id,
            song_id=str(job_record.song_id),
            status=job_record.status,
            progress=job_record.progress,
            composed_video_id=str(job_record.composed_video_id) if job_record.composed_video_id else None,
            error=job_record.error,
            created_at=job_record.created_at.isoformat(),
            updated_at=job_record.updated_at.isoformat(),
        )


def update_job_progress(job_id: str, progress: int, status: str | None = None) -> None:
    """
    Update job progress and optionally status.

    Args:
        job_id: Job ID
        progress: Progress percentage (0-100)
        status: Optional status to update
    """
    with session_scope() as session:
        job_record = session.get(CompositionJob, job_id)
        if not job_record:
            logger.warning(f"Job {job_id} not found for progress update")
            return

        # Ensure progress only increases (never decreases) to prevent UI from showing backward progress
        job_record.progress = max(job_record.progress, min(100, progress))
        if status:
            job_record.status = status
        elif job_record.status == "queued":
            job_record.status = "processing"

        session.add(job_record)
        session.commit()


def complete_job(job_id: str, composed_video_id: UUID) -> None:
    """
    Mark job as completed and link to composed video.

    Args:
        job_id: Job ID
        composed_video_id: ComposedVideo ID
    """
    with session_scope() as session:
        job_record = session.get(CompositionJob, job_id)
        if not job_record:
            logger.warning(f"Job {job_id} not found for completion")
            return

        job_record.status = "completed"
        job_record.progress = 100
        job_record.composed_video_id = composed_video_id

        session.add(job_record)
        session.commit()


def fail_job(job_id: str, error_message: str) -> None:
    """
    Mark job as failed with error message.

    Args:
        job_id: Job ID
        error_message: Error message
    """
    with session_scope() as session:
        job_record = session.get(CompositionJob, job_id)
        if not job_record:
            logger.warning(f"Job {job_id} not found for failure")
            return

        job_record.status = "failed"
        job_record.error = error_message
        # Don't reset progress, keep it at current value

        session.add(job_record)
        session.commit()


def cancel_job(job_id: str) -> None:
    """
    Cancel a composition job.

    Args:
        job_id: Job ID

    Raises:
        ValueError: If job not found or cannot be cancelled
    """
    with session_scope() as session:
        job_record = session.get(CompositionJob, job_id)
        if not job_record:
            raise JobNotFoundError(f"Composition job {job_id} not found")

        if job_record.status in ("completed", "failed", "cancelled"):
            raise JobStateError(f"Job {job_id} cannot be cancelled (status: {job_record.status})")

        job_record.status = "cancelled"
        session.add(job_record)
        session.commit()

        logger.info(f"Cancelled composition job {job_id}")


def create_composed_video(
    song_id: UUID,
    s3_key: str,
    duration_sec: float,
    file_size_bytes: int,
    resolution_width: int,
    resolution_height: int,
    fps: int,
    clip_ids: list[UUID],
) -> ComposedVideo:
    """
    Create a ComposedVideo record.

    Args:
        song_id: Song ID
        s3_key: S3 key for the composed video
        duration_sec: Video duration in seconds
        file_size_bytes: File size in bytes
        resolution_width: Video width
        resolution_height: Video height
        fps: Frames per second
        clip_ids: List of SectionVideo IDs used

    Returns:
        ComposedVideo record
    """
    with session_scope() as session:
        composed_video = ComposedVideo(
            song_id=song_id,
            s3_key=s3_key,
            duration_sec=duration_sec,
            file_size_bytes=file_size_bytes,
            resolution_width=resolution_width,
            resolution_height=resolution_height,
            fps=fps,
            clip_ids=json.dumps([str(clip_id) for clip_id in clip_ids]),
            status="completed",
        )
        session.add(composed_video)
        session.commit()
        session.refresh(composed_video)

        logger.info(f"Created ComposedVideo {composed_video.id} for song {song_id}")

        return composed_video


def get_composed_video(composed_video_id: UUID) -> ComposedVideo | None:
    """
    Get a ComposedVideo record.

    Args:
        composed_video_id: ComposedVideo ID

    Returns:
        ComposedVideo record or None if not found
    """
    with session_scope() as session:
        return session.get(ComposedVideo, composed_video_id)


def get_composed_videos_for_song(song_id: UUID) -> list[ComposedVideo]:
    """
    Get all composed videos for a song.

    Args:
        song_id: Song ID

    Returns:
        List of ComposedVideo records
    """
    with session_scope() as session:
        statement = (
            select(ComposedVideo)
            .where(ComposedVideo.song_id == song_id)
            .order_by(ComposedVideo.created_at.desc())
        )
        return list(session.exec(statement).all())

