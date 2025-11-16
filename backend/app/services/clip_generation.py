from __future__ import annotations

import logging
import random
from collections import Counter
from typing import Iterable, List, Optional
from uuid import UUID, uuid4

import redis
from rq import Queue
from rq.job import Job, get_current_job
from sqlmodel import select

from app.core.config import get_settings
from app.core.database import session_scope
from app.models.analysis import ClipGenerationJob
from app.models.clip import SongClip
from app.schemas.analysis import SongAnalysis, SongSection
from app.schemas.clip import ClipGenerationSummary, SongClipStatus
from app.schemas.job import ClipGenerationJobResponse, JobStatusResponse
from app.schemas.scene import SceneSpec
from app.services.scene_planner import build_scene_spec
from app.services.song_analysis import get_latest_analysis
from app.services.video_generation import generate_section_video

logger = logging.getLogger(__name__)

DEFAULT_MAX_CONCURRENCY = 2
QUEUE_TIMEOUT_SEC = 20 * 60  # 20 minutes per clip generation


def _get_clip_queue() -> Queue:
    settings = get_settings()
    connection = redis.from_url(settings.redis_url)
    queue_name = f"{settings.rq_worker_queue}:clip-generation"
    return Queue(queue_name, connection=connection, default_timeout=QUEUE_TIMEOUT_SEC)


def enqueue_clip_generation_batch(
    *,
    song_id: UUID,
    clip_ids: Optional[Iterable[UUID]] = None,
    max_parallel: int = DEFAULT_MAX_CONCURRENCY,
    batch_job_id: Optional[str] = None,
) -> List[str]:
    """Enqueue clip generation jobs with controlled concurrency."""
    if max_parallel < 1:
        raise ValueError("max_parallel must be at least 1")

    queue = _get_clip_queue()

    with session_scope() as session:
        statement = select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
        if clip_ids is not None:
            clip_ids = list(clip_ids)
            if not clip_ids:
                raise ValueError("clip_ids cannot be empty when provided")
            statement = statement.where(SongClip.id.in_(clip_ids))

        clips: list[SongClip] = session.exec(statement).all()
        if not clips:
            raise ValueError("No clips found to enqueue")

        jobs: list[Job] = []
        for idx, clip in enumerate(clips):
            depends_on = jobs[idx - max_parallel] if idx >= max_parallel else None
            job_id = f"clip-gen-{clip.id}"
            meta = {"song_id": str(song_id), "clip_index": clip.clip_index}
            if batch_job_id:
                meta["batch_job_id"] = batch_job_id

            job = queue.enqueue(
                run_clip_generation_job,
                clip.id,
                job_id=job_id,
                depends_on=depends_on,
                job_timeout=QUEUE_TIMEOUT_SEC,
                meta=meta,
            )

            clip.status = "queued"
            clip.error = None
            clip.rq_job_id = job.id
            session.add(clip)
            jobs.append(job)

        session.commit()

    if batch_job_id:
        _update_clip_generation_job(
            batch_job_id,
            status="processing" if jobs else "queued",
        )

    return [job.id for job in jobs]


def run_clip_generation_job(clip_id: UUID) -> dict[str, object]:
    """RQ job that generates a video for a single clip via Replicate."""
    job = get_current_job()
    job_id = job.id if job else None
    batch_job_id = job.meta.get("batch_job_id") if job and isinstance(job.meta, dict) else None

    song_id: UUID | None = None
    clip_fps: int = 8
    clip_num_frames: int = 0
    with session_scope() as session:
        clip = session.get(SongClip, clip_id)
        if not clip:
            raise ValueError(f"Clip {clip_id} not found")

        song_id = clip.song_id
        clip_fps = clip.fps or 8
        computed_frames = clip.num_frames
        if computed_frames <= 0 and clip.duration_sec:
            computed_frames = max(int(round(clip.duration_sec * clip_fps)), 1)
        clip.num_frames = computed_frames
        clip.status = "processing"
        clip.error = None
        clip.rq_job_id = job_id or clip.rq_job_id
        session.add(clip)
        session.commit()
        clip_num_frames = clip.num_frames

    if song_id is None:
        raise RuntimeError("Song id missing for clip generation job.")

    analysis = get_latest_analysis(song_id)
    if not analysis:
        _mark_clip_failed(clip_id, "Song analysis not found for clip generation.", batch_job_id=batch_job_id)
        raise RuntimeError("Song analysis not found for clip generation.")

    scene_spec = _build_scene_spec_for_clip(clip_id, analysis)
    seed = _determine_seed_for_clip(clip_id)

    success, video_url, metadata = generate_section_video(
        scene_spec, seed=seed, num_frames=clip_num_frames, fps=clip_fps
    )
    metadata = metadata or {}

    with session_scope() as session:
        clip = session.get(SongClip, clip_id)
        if not clip:
            raise ValueError(f"Clip {clip_id} disappeared during job execution")

        clip.prompt = scene_spec.prompt
        clip.style_seed = str(metadata.get("seed") or seed) if seed is not None else clip.style_seed
        clip.fps = metadata.get("fps", clip_fps) or clip_fps
        clip.replicate_job_id = metadata.get("job_id", clip.replicate_job_id)
        clip.num_frames = metadata.get("num_frames", clip_num_frames) or clip_num_frames

        if success and video_url:
            clip.status = "completed"
            clip.video_url = video_url
            clip.error = None
            session.add(clip)
            session.commit()
            if batch_job_id:
                _refresh_clip_generation_job(batch_job_id)
            logger.info("Clip %s generation completed with video %s", clip_id, video_url)
            return {
                "status": "completed",
                "clipId": str(clip_id),
                "videoUrl": video_url,
                "replicateJobId": clip.replicate_job_id,
            }

        error_message = metadata.get("error") or "Video generation failed."
        clip.status = "failed"
        clip.error = error_message
        session.add(clip)
        session.commit()
        if batch_job_id:
            _refresh_clip_generation_job(batch_job_id)
        logger.error("Clip %s generation failed: %s", clip_id, error_message)
        raise RuntimeError(error_message)


def get_clip_generation_summary(song_id: UUID) -> ClipGenerationSummary:
    with session_scope() as session:
        clips = session.exec(
            select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
        ).all()

    if not clips:
        raise ValueError("No planned clips found for song.")

    status_counts = Counter(clip.status for clip in clips)
    total = len(clips)
    completed = status_counts.get("completed", 0)
    failed = status_counts.get("failed", 0)
    processing = status_counts.get("processing", 0)
    queued = status_counts.get("queued", 0)

    clip_statuses = [SongClipStatus.model_validate(clip) for clip in clips]

    return ClipGenerationSummary(
        songId=song_id,
        totalClips=total,
        completedClips=completed,
        failedClips=failed,
        processingClips=processing,
        queuedClips=queued,
        progressCompleted=completed,
        progressTotal=total,
        clips=clip_statuses,
    )


def _mark_clip_failed(clip_id: UUID, message: str, *, batch_job_id: Optional[str] = None) -> None:
    with session_scope() as session:
        clip = session.get(SongClip, clip_id)
        if not clip:
            return
        clip.status = "failed"
        clip.error = message
        session.add(clip)
        session.commit()
    if batch_job_id:
        _refresh_clip_generation_job(batch_job_id)


def _build_scene_spec_for_clip(clip_id: UUID, analysis: SongAnalysis) -> SceneSpec:
    with session_scope() as session:
        clip = session.get(SongClip, clip_id)
        if not clip:
            raise ValueError(f"Clip {clip_id} not found when building scene spec")
        start_sec = clip.start_sec
        duration_sec = clip.duration_sec

    if not analysis.sections:
        raise RuntimeError("Song analysis has no sections to build scene spec.")

    target_section = _find_section_for_clip(start_sec, analysis.sections)
    scene_spec = build_scene_spec(target_section.id, analysis)
    return scene_spec.model_copy(update={"duration_sec": duration_sec})


def _find_section_for_clip(start_time: float, sections: List[SongSection]) -> SongSection:
    for section in sections:
        if section.start_sec <= start_time < section.end_sec:
            return section
    return min(sections, key=lambda s: abs(s.start_sec - start_time))


def _determine_seed_for_clip(clip_id: UUID) -> Optional[int]:
    with session_scope() as session:
        clip = session.get(SongClip, clip_id)
        if not clip:
            return None

        if clip.style_seed is not None:
            try:
                return int(clip.style_seed)
            except ValueError:
                logger.debug("Clip %s style_seed is non-numeric; generating new seed.", clip_id)

        seed = random.randint(0, 2**31 - 1)
        clip.style_seed = str(seed)
        session.add(clip)
        session.commit()
        return seed


def _update_clip_generation_job(
    job_id: str,
    *,
    status: Optional[str] = None,
    error: Optional[str] = None,
    progress: Optional[int] = None,
    total_clips: Optional[int] = None,
    completed_clips: Optional[int] = None,
    failed_clips: Optional[int] = None,
) -> None:
    with session_scope() as session:
        job_record = session.get(ClipGenerationJob, job_id)
        if not job_record:
            return
        if status is not None:
            job_record.status = status
        if error is not None:
            job_record.error = error
        if progress is not None:
            job_record.progress = max(0, min(progress, 100))
        if total_clips is not None:
            job_record.total_clips = total_clips
        if completed_clips is not None:
            job_record.completed_clips = completed_clips
        if failed_clips is not None:
            job_record.failed_clips = failed_clips
        session.add(job_record)
        session.commit()


def _refresh_clip_generation_job(job_id: str) -> Optional[ClipGenerationSummary]:
    with session_scope() as session:
        job_record = session.get(ClipGenerationJob, job_id)
        if not job_record:
            return None
        song_id = job_record.song_id
        previous_status = job_record.status

    summary = get_clip_generation_summary(song_id)

    progress = (
        int(round((summary.progress_completed / summary.progress_total) * 100))
        if summary.progress_total
        else 0
    )

    if summary.failed_clips > 0:
        status = "failed"
        error_message = "One or more clips failed."
    elif summary.completed_clips == summary.total_clips and summary.total_clips > 0:
        status = "completed"
        progress = 100
        error_message = None
    elif summary.processing_clips > 0:
        status = "processing"
        error_message = None
    else:
        status = "queued"
        error_message = None

    if (
        status == "queued"
        and previous_status in {"processing", "queued"}
        and summary.total_clips > 0
        and summary.completed_clips < summary.total_clips
        and summary.failed_clips == 0
    ):
        status = "processing"

    _update_clip_generation_job(
        job_id,
        status=status,
        error=error_message,
        progress=progress,
        total_clips=summary.total_clips,
        completed_clips=summary.completed_clips,
        failed_clips=summary.failed_clips,
    )

    return summary


def start_clip_generation_job(
    song_id: UUID,
    *,
    max_parallel: int = DEFAULT_MAX_CONCURRENCY,
) -> ClipGenerationJobResponse:
    try:
        summary = get_clip_generation_summary(song_id)
    except ValueError as exc:
        raise ValueError("No planned clips available for this song.") from exc

    if summary.total_clips == 0:
        raise ValueError("No clips to generate for this song.")

    job_id = f"clip-batch-{uuid4()}"

    with session_scope() as session:
        existing = session.exec(
            select(ClipGenerationJob)
            .where(ClipGenerationJob.song_id == song_id)
            .where(ClipGenerationJob.status.in_(["queued", "processing"]))
        ).first()
        if existing:
            raise ValueError("A clip generation job is already in progress for this song.")

        job_record = ClipGenerationJob(
            id=job_id,
            song_id=song_id,
            status="queued",
            progress=0,
            total_clips=summary.total_clips,
            completed_clips=summary.completed_clips,
            failed_clips=summary.failed_clips,
        )
        session.add(job_record)
        session.commit()

    enqueue_clip_generation_batch(
        song_id=song_id,
        max_parallel=max_parallel,
        batch_job_id=job_id,
    )

    _refresh_clip_generation_job(job_id)

    with session_scope() as session:
        job_record = session.get(ClipGenerationJob, job_id)
        if not job_record:
            raise RuntimeError("Failed to create clip generation job.")
        status = job_record.status

    return ClipGenerationJobResponse(job_id=job_id, song_id=song_id, status=status)


def get_clip_generation_job_status(job_id: str) -> JobStatusResponse:
    with session_scope() as session:
        job_record = session.get(ClipGenerationJob, job_id)
        if not job_record:
            raise ValueError(f"Job {job_id} not found")
        song_id = job_record.song_id

    summary = _refresh_clip_generation_job(job_id) or get_clip_generation_summary(song_id)
    with session_scope() as session:
        job_record = session.get(ClipGenerationJob, job_id)
        if not job_record:
            raise ValueError(f"Job {job_id} not found")

    progress = job_record.progress
    return JobStatusResponse(
        job_id=job_record.id,
        song_id=job_record.song_id,
        status=job_record.status,
        progress=progress,
        analysis_id=None,
        error=job_record.error,
        result=summary,
    )

