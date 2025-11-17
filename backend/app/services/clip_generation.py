from __future__ import annotations

import logging
import random
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Optional
from uuid import UUID, uuid4
import tempfile

import httpx
import redis
from rq import Queue
from rq.job import Job, get_current_job
from sqlmodel import select

from app.core.config import get_settings
from app.core.database import session_scope
from app.models.analysis import ClipGenerationJob
from app.models.clip import SongClip
from app.models.song import Song
from app.schemas.analysis import SongAnalysis, SongSection
from app.schemas.clip import ClipGenerationSummary, SongClipStatus
from app.schemas.job import ClipGenerationJobResponse, JobStatusResponse
from app.schemas.scene import SceneSpec
from app.services.scene_planner import build_scene_spec
from app.services.song_analysis import get_latest_analysis
from app.services.video_generation import generate_section_video
from app.services.storage import (
    check_s3_object_exists,
    download_bytes_from_s3,
    generate_presigned_get_url,
    upload_bytes_to_s3,
)
from app.services.video_composition import (
    concatenate_clips,
    generate_video_poster,
    normalize_clip,
)

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
        song = session.get(Song, song_id)
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

    composed_video_url: Optional[str] = None
    composed_video_poster_url: Optional[str] = None
    song_duration = float(song.duration_sec) if song and song.duration_sec is not None else None

    if song:
        settings = get_settings()
        bucket = settings.s3_bucket_name
        if song.composed_video_s3_key and bucket:
            # Verify file exists before generating presigned URL
            if check_s3_object_exists(bucket_name=bucket, key=song.composed_video_s3_key):
                try:
                    composed_video_url = generate_presigned_get_url(
                        bucket_name=bucket,
                        key=song.composed_video_s3_key,
                        expires_in=3600 * 24,  # 24 hours for composed videos
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.error(
                        "Failed to generate composed video URL for song %s: %s", song_id, exc
                    )
            else:
                logger.warning(
                    "Composed video S3 key %s does not exist in bucket %s for song %s",
                    song.composed_video_s3_key,
                    bucket,
                    song_id,
                )
        if song.composed_video_poster_s3_key and bucket:
            try:
                composed_video_poster_url = generate_presigned_get_url(
                    bucket_name=bucket,
                    key=song.composed_video_poster_s3_key,
                )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Failed to generate composed poster URL for song %s: %s", song_id, exc
                )

    try:
        analysis = get_latest_analysis(song_id)
    except Exception:
        analysis = None

    return ClipGenerationSummary(
        songId=song_id,
        songDurationSec=song_duration,
        totalClips=total,
        completedClips=completed,
        failedClips=failed,
        processingClips=processing,
        queuedClips=queued,
        progressCompleted=completed,
        progressTotal=total,
        clips=clip_statuses,
        analysis=analysis,
        composedVideoUrl=composed_video_url,
        composedVideoPosterUrl=composed_video_poster_url,
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


def _download_clip_to_path(url: str, destination: Path, timeout: float = 120.0) -> None:
    try:
        with httpx.stream("GET", url, timeout=timeout, follow_redirects=True) as response:
            if response.status_code != 200:
                # Log the response body for debugging
                error_body = ""
                try:
                    error_body = response.read().decode('utf-8', errors='ignore')
                except Exception:
                    pass
                logger.error(
                    "Presigned URL download failed: status=%d, url=%s, error=%s",
                    response.status_code,
                    url[:200],  # Truncate URL for logging
                    error_body[:500],
                )
            response.raise_for_status()
            with destination.open("wb") as output_file:
                for chunk in response.iter_bytes():
                    if chunk:
                        output_file.write(chunk)
    except httpx.HTTPStatusError as exc:
        error_detail = f"HTTP {exc.response.status_code}"
        try:
            error_body = exc.response.read().decode('utf-8', errors='ignore')
            error_detail += f": {error_body[:200]}"
        except Exception:
            pass
        raise RuntimeError(
            f"Failed to download clip asset from presigned URL (status {exc.response.status_code}): {error_detail}"
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Failed to download clip asset from {url}: {exc}") from exc


def compose_song_video(song_id: UUID) -> tuple[str, Optional[str]]:
    """
    Stitch all completed clips for a song into a single video using the processed audio track.

    Returns:
        Tuple of (video_s3_key, poster_s3_key)
    """

    settings = get_settings()
    bucket = settings.s3_bucket_name
    if not bucket:
        raise RuntimeError("S3 bucket name is not configured; cannot store composed video.")

    with session_scope() as session:
        song = session.get(Song, song_id)
        if not song:
            raise ValueError(f"Song {song_id} not found")
        audio_key = song.processed_s3_key or song.original_s3_key
        
        # Validate audio key exists in S3, or try to find it
        if not audio_key:
            # No key in database, try to find audio in S3
            possible_keys = [
                f"songs/{song_id}/original.wav",
                f"songs/{song_id}/original.mp3",
                f"songs/{song_id}/processed.wav",
                f"songs/{song_id}/processed.mp3",
            ]
            found_key = None
            for key in possible_keys:
                if check_s3_object_exists(bucket_name=bucket, key=key):
                    found_key = key
                    logger.info("Found audio at S3 key: %s (not in database)", found_key)
                    # Update database with correct key
                    song.original_s3_key = found_key
                    session.add(song)
                    session.commit()
                    break
            
            if found_key:
                audio_key = found_key
            else:
                raise RuntimeError(
                    f"Song audio is unavailable for composition. "
                    f"No S3 key in database and not found at any expected S3 location: "
                    f"{', '.join(possible_keys)}"
                )
        elif not check_s3_object_exists(bucket_name=bucket, key=audio_key):
            # Key exists in database but file doesn't exist in S3, try to find it
            logger.warning(
                "Audio key %s from database does not exist in S3, trying to find correct key",
                audio_key,
            )
            possible_keys = [
                f"songs/{song_id}/original.wav",
                f"songs/{song_id}/original.mp3",
                f"songs/{song_id}/processed.wav",
                f"songs/{song_id}/processed.mp3",
            ]
            found_key = None
            for key in possible_keys:
                if check_s3_object_exists(bucket_name=bucket, key=key):
                    found_key = key
                    logger.info("Found audio at S3 key: %s, updating database", found_key)
                    # Update database with correct key
                    song.original_s3_key = found_key
                    session.add(song)
                    session.commit()
                    break
            
            if found_key:
                audio_key = found_key
            else:
                raise RuntimeError(
                    f"Song audio is unavailable for composition. "
                    f"Key in database ({audio_key}) doesn't exist in S3, "
                    f"and not found at any expected S3 location: {', '.join(possible_keys)}"
                )

        clips = session.exec(
            select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
        ).all()

    if not clips:
        raise RuntimeError("No clips found to compose.")

    completed_clips = [
        clip for clip in clips if clip.status == "completed" and clip.video_url
    ]
    if len(completed_clips) != len(clips):
        raise RuntimeError("Cannot compose video until all clips are completed.")

    song_duration = None
    with session_scope() as session:
        song = session.get(Song, song_id)
        if song:
            song_duration = song.duration_sec
    if song_duration is None:
        song_duration = sum(clip.duration_sec or 0 for clip in completed_clips)

    with tempfile.TemporaryDirectory(prefix=f"compose-{song_id}-") as tmpdir:
        temp_dir = Path(tmpdir)
        normalized_paths: list[Path] = []

        # Download clips and normalize them
        for clip in completed_clips:
            source_path = temp_dir / f"clip_{clip.clip_index:03}.mp4"
            normalized_path = temp_dir / f"clip_{clip.clip_index:03}_normalized.mp4"

            # Try to download from S3 key first (more reliable than presigned URL)
            # S3 key pattern: songs/{song_id}/clips/{clip_index:03d}.mp4
            clip_s3_key = f"songs/{song_id}/clips/{clip.clip_index:03d}.mp4"
            
            # Check if file exists in S3
            if not check_s3_object_exists(bucket_name=bucket, key=clip_s3_key):
                logger.warning(
                    "Clip file does not exist at S3 key %s, trying presigned URL: %s",
                    clip_s3_key,
                    clip.video_url[:100] if clip.video_url else "None",
                )
                if not clip.video_url:
                    raise RuntimeError(
                        f"Clip {clip.clip_index} file not found at S3 key {clip_s3_key} and no video_url available"
                    )
                _download_clip_to_path(clip.video_url, source_path)
            else:
                try:
                    clip_bytes = download_bytes_from_s3(bucket_name=bucket, key=clip_s3_key)
                    source_path.write_bytes(clip_bytes)
                except Exception as s3_err:
                    # Fallback to presigned URL if S3 key download fails
                    logger.warning(
                        "Failed to download clip from S3 key %s, trying presigned URL: %s",
                        clip_s3_key,
                        s3_err,
                    )
                    if not clip.video_url:
                        raise RuntimeError(
                            f"Clip {clip.clip_index} has no video_url and S3 download failed: {s3_err}"
                        ) from s3_err
                    _download_clip_to_path(clip.video_url, source_path)
            
            normalize_clip(str(source_path), str(normalized_path))
            normalized_paths.append(normalized_path)

        # Download audio (key has already been validated to exist in S3 above)
        audio_bytes = download_bytes_from_s3(bucket_name=bucket, key=audio_key)
        audio_extension = Path(audio_key).suffix or ".wav"
        audio_path = temp_dir / f"song_audio{audio_extension}"
        audio_path.write_bytes(audio_bytes)

        # Concatenate clips with audio
        output_path = temp_dir / "composed_video.mp4"
        composition_result = concatenate_clips(
            [str(path) for path in normalized_paths],
            str(audio_path),
            str(output_path),
            song_duration_sec=float(song_duration),
        )

        # Generate poster frame
        poster_path = temp_dir / "poster.jpg"
        try:
            generate_video_poster(str(output_path), str(poster_path))
            poster_bytes = poster_path.read_bytes()
        except Exception:
            logger.exception("Failed to generate composed video poster for song %s", song_id)
            poster_bytes = None

        video_bytes = output_path.read_bytes()

    # Upload assets
    video_key = f"songs/{song_id}/composed/{uuid4()}.mp4"
    upload_bytes_to_s3(
        bucket_name=bucket,
        key=video_key,
        data=video_bytes,
        content_type="video/mp4",
    )

    poster_key: Optional[str] = None
    if poster_bytes:
        poster_key = f"songs/{song_id}/composed/{uuid4()}.jpg"
        upload_bytes_to_s3(
            bucket_name=bucket,
            key=poster_key,
            data=poster_bytes,
            content_type="image/jpeg",
        )

    with session_scope() as session:
        song = session.get(Song, song_id)
        if not song:
            raise ValueError(f"Song {song_id} disappeared during composition update.")
        song.composed_video_s3_key = video_key
        song.composed_video_poster_s3_key = poster_key
        song.composed_video_duration_sec = composition_result.duration_sec
        song.composed_video_fps = composition_result.fps
        session.add(song)
        session.commit()

    return video_key, poster_key


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

        song = session.get(Song, song_id)
        if song:
            song.composed_video_s3_key = None
            song.composed_video_poster_s3_key = None
            song.composed_video_duration_sec = None
            song.composed_video_fps = None
            session.add(song)

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

