from __future__ import annotations

import logging
import random
import subprocess
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Optional
from uuid import UUID, uuid4
import tempfile

import httpx
from rq.job import Job, get_current_job
from sqlmodel import select

from app.core.config import get_settings
from app.core.constants import DEFAULT_MAX_CONCURRENCY, QUEUE_TIMEOUT_SEC
from app.core.database import session_scope
from app.core.logging import configure_logging
from app.core.queue import get_queue

# Ensure logging is configured for RQ workers
# This is needed because RQ workers don't automatically call configure_logging()
# Without this, logger.info() calls may be filtered out (root logger defaults to WARNING)
try:
    settings = get_settings()
    configure_logging(settings.api_log_level)
except Exception:
    # Fallback to default if settings can't be loaded
    configure_logging("info")
from app.exceptions import (
    ClipGenerationError,
    ClipNotFoundError,
    CompositionError,
    JobNotFoundError,
    SongNotFoundError,
    StorageError,
)
from app.repositories import ClipRepository, SongRepository
from app.models.analysis import ClipGenerationJob
from app.schemas.analysis import SongAnalysis, SongSection
from app.schemas.clip import ClipGenerationSummary, SongClipStatus
from app.schemas.job import ClipGenerationJobResponse, JobStatusResponse
from app.schemas.scene import SceneSpec
from app.services.scene_planner import build_scene_spec, build_clip_scene_spec
from app.services.song_analysis import get_latest_analysis
from app.services.video_generation import generate_section_video
from app.services.storage import (
    check_s3_object_exists,
    download_bytes_from_s3,
    generate_presigned_get_url,
    upload_bytes_to_s3,
)
from app.services.composition_job import update_job_progress
from app.services.video_composition import (
    concatenate_clips,
    generate_video_poster,
    normalize_clip,
)

logger = logging.getLogger(__name__)


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

    settings = get_settings()
    queue = get_queue(
        queue_name=settings.rq_worker_queue,  # Use main queue so worker picks up jobs
        timeout=QUEUE_TIMEOUT_SEC
    )

    logger.info(
        f"[CLIP-GEN] Enqueueing clip generation batch for song {song_id}, "
        f"batch_job_id={batch_job_id}, max_parallel={max_parallel}, queue={queue.name}"
    )

    # Get clips using repository
    all_clips = ClipRepository.get_by_song_id(song_id)
    
    if clip_ids is not None:
        clip_ids = list(clip_ids)
        if not clip_ids:
            raise ValueError("clip_ids cannot be empty when provided")
        clips = [clip for clip in all_clips if clip.id in clip_ids]
    else:
        clips = all_clips
    
    if not clips:
        raise ValueError("No clips found to enqueue")

    logger.info(f"[CLIP-GEN] Found {len(clips)} clips to enqueue for song {song_id}")

    jobs: list[Job] = []
    with session_scope() as session:
        for idx, clip in enumerate(clips):
            depends_on = jobs[idx - max_parallel] if idx >= max_parallel else None
            job_id = f"clip-gen-{clip.id}"
            meta = {"song_id": str(song_id), "clip_index": clip.clip_index}
            if batch_job_id:
                meta["batch_job_id"] = batch_job_id

            logger.info(
                f"[CLIP-GEN] Enqueueing clip {clip.id} (index {clip.clip_index}) "
                f"as job {job_id}, depends_on={depends_on.id if depends_on else None}"
            )
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
            logger.info(f"[CLIP-GEN] Successfully enqueued job {job.id} for clip {clip.id}")

        session.commit()

    job_ids = [job.id for job in jobs]
    logger.info(
        f"[CLIP-GEN] Enqueued {len(job_ids)} clip generation jobs for song {song_id}, "
        f"batch_job_id={batch_job_id}, job_ids={job_ids[:5]}{'...' if len(job_ids) > 5 else ''}"
    )

    if batch_job_id:
        _update_clip_generation_job(
            batch_job_id,
            status="processing" if jobs else "queued",
        )

    return [job.id for job in jobs]


def retry_clip_generation(clip_id: UUID) -> SongClipStatus:
    """Reset clip state and enqueue a new generation job."""
    settings = get_settings()
    queue = get_queue(
        queue_name=settings.rq_worker_queue,  # Use main queue so worker picks up jobs
        timeout=QUEUE_TIMEOUT_SEC
    )

    try:
        clip = ClipRepository.get_by_id(clip_id)
    except ClipNotFoundError:
        raise ValueError(f"Clip {clip_id} not found")

    if clip.status in {"processing", "queued"}:
        raise RuntimeError("Clip is already queued or processing")

    song_id = clip.song_id
    clip_index = clip.clip_index
    clip_fps = clip.fps or 8
    num_frames = clip.num_frames
    if num_frames <= 0 and clip.duration_sec:
        num_frames = max(int(round(clip.duration_sec * clip_fps)), 1)

    clip.num_frames = num_frames
    clip.status = "queued"
    clip.error = None
    clip.video_url = None
    clip.replicate_job_id = None
    clip.rq_job_id = None
    ClipRepository.update(clip)

    job = queue.enqueue(
        run_clip_generation_job,
        clip_id,
        job_timeout=QUEUE_TIMEOUT_SEC,
        meta={"song_id": str(song_id), "clip_index": clip_index, "retry": True},
    )

    try:
        clip = ClipRepository.get_by_id(clip_id)
    except ClipNotFoundError:
        raise ValueError(f"Clip {clip_id} disappeared after enqueue")
    
    clip.rq_job_id = job.id
    ClipRepository.update(clip)
    return SongClipStatus.model_validate(clip)


def run_clip_generation_job(clip_id: UUID) -> dict[str, object]:
    """RQ job that generates a video for a single clip via Replicate."""
    logger.info(f"[CLIP-GEN] ===== Starting run_clip_generation_job for clip {clip_id} =====")
    job = get_current_job()
    job_id = job.id if job else None
    batch_job_id = job.meta.get("batch_job_id") if job and isinstance(job.meta, dict) else None
    logger.info(f"[CLIP-GEN] Job ID: {job_id}, Batch Job ID: {batch_job_id}")

    song_id: UUID | None = None
    clip_fps: int = 8
    clip_num_frames: int = 0
    
    try:
        clip = ClipRepository.get_by_id(clip_id)
    except ClipNotFoundError:
        # Handle stale RQ jobs gracefully - clip may have been deleted
        logger.warning(
            "Clip %s not found (likely stale RQ job). Skipping clip generation.",
            clip_id
        )
        if batch_job_id:
            _refresh_clip_generation_job(batch_job_id)
        return {
            "status": "skipped",
            "clipId": str(clip_id),
            "reason": "Clip not found (stale job)",
        }

    song_id = clip.song_id
    clip_fps = clip.fps or 8
    computed_frames = clip.num_frames
    if computed_frames <= 0 and clip.duration_sec:
        computed_frames = max(int(round(clip.duration_sec * clip_fps)), 1)
    clip.num_frames = computed_frames
    clip.status = "processing"
    clip.error = None
    clip.rq_job_id = job_id or clip.rq_job_id
    ClipRepository.update(clip)
    clip_num_frames = clip.num_frames

    if song_id is None:
        raise ClipGenerationError("Song id missing for clip generation job.")

    analysis = get_latest_analysis(song_id)
    if not analysis:
        _mark_clip_failed(clip_id, "Song analysis not found for clip generation.", batch_job_id=batch_job_id)
        raise ClipGenerationError("Song analysis not found for clip generation.")

    scene_spec = _build_scene_spec_for_clip(clip_id, analysis)
    logger.info(f"[CLIP-GEN] Clip {clip_id}: Generated prompt: {scene_spec.prompt}")
    seed = _determine_seed_for_clip(clip_id)

    # Get character image URLs if character consistency is enabled
    character_image_urls = []
    character_image_url = None
    song = None
    
    try:
        song = SongRepository.get_by_id(song_id)
        if song:
            character_image_urls, character_image_url = _get_character_image_urls(song)
            logger.info(
                f"[CLIP-GEN] Clip {clip_id}: character_consistency_enabled={song.character_consistency_enabled}, "
                f"character_image_urls count={len(character_image_urls)}, "
                f"character_image_url={'set' if character_image_url else 'none'}"
            )
        else:
            logger.info(f"[CLIP-GEN] Clip {clip_id}: Song {song_id} not found, no character images")
    except SongNotFoundError:
        logger.warning(f"Song {song_id} not found when checking character consistency")
    except Exception as e:
        logger.warning(f"Error checking character consistency: {e}")

    logger.info(
        f"[CLIP-GEN] Clip {clip_id}: Calling generate_section_video with "
        f"character_image_url={'set' if character_image_url else 'none'}, "
        f"character_image_urls count={len(character_image_urls)}"
    )
    success, video_url, metadata = generate_section_video(
        scene_spec,
        seed=seed,
        num_frames=clip_num_frames,
        fps=clip_fps,
        reference_image_url=character_image_url,  # Fallback single image
        reference_image_urls=character_image_urls if len(character_image_urls) > 0 else None,  # Try multiple
        song_id=song_id,  # Pass song_id for prompt logging
        clip_id=clip_id,  # Pass clip_id for prompt logging
    )
    metadata = metadata or {}
    
    # Track estimated cost for this clip generation
    if song:  # Only track cost if we successfully retrieved the song
        from app.services.cost_tracking import track_video_generation_cost
        from app.core.constants import VIDEO_MODEL
        try:
            track_video_generation_cost(
                song_id=song_id,
                model_name=VIDEO_MODEL,
                num_clips=1,
                has_character_consistency=bool(character_image_url),
            )
        except Exception as e:
            logger.warning(f"Failed to track cost for clip {clip_id}: {e}")

    try:
        clip = ClipRepository.get_by_id(clip_id)
    except ClipNotFoundError:
        # Handle stale RQ jobs gracefully - clip may have been deleted during execution
        logger.warning(
            "Clip %s disappeared during job execution (likely stale RQ job). Skipping.",
            clip_id
        )
        if batch_job_id:
            _refresh_clip_generation_job(batch_job_id)
        return {
            "status": "skipped",
            "clipId": str(clip_id),
            "reason": "Clip disappeared during execution",
        }

    clip.prompt = scene_spec.prompt
    clip.style_seed = str(metadata.get("seed") or seed) if seed is not None else clip.style_seed
    clip.fps = metadata.get("fps", clip_fps) or clip_fps
    clip.replicate_job_id = metadata.get("job_id", clip.replicate_job_id)
    clip.num_frames = metadata.get("num_frames", clip_num_frames) or clip_num_frames

    if success and video_url:
        clip.status = "completed"
        clip.video_url = video_url
        clip.error = None
        ClipRepository.update(clip)
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
    ClipRepository.update(clip)
    if batch_job_id:
        _refresh_clip_generation_job(batch_job_id)
    logger.error("Clip %s generation failed: %s", clip_id, error_message)
    raise ClipGenerationError(error_message)


def get_clip_generation_summary(song_id: UUID) -> ClipGenerationSummary:
    song = SongRepository.get_by_id(song_id)
    clips = ClipRepository.get_by_song_id(song_id)

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
    try:
        clip = ClipRepository.get_by_id(clip_id)
        clip.status = "failed"
        clip.error = message
        ClipRepository.update(clip)
    except ClipNotFoundError:
        # Clip doesn't exist, skip
        pass
    if batch_job_id:
        _refresh_clip_generation_job(batch_job_id)


def _build_scene_spec_for_clip(clip_id: UUID, analysis: SongAnalysis) -> SceneSpec:
    """
    Build scene spec for a clip.
    
    For short-form videos (no sections), uses song-level analysis.
    For long-form videos (with sections), uses section-specific analysis.
    """
    from app.schemas.scene import TemplateType
    from app.services.scene_planner import DEFAULT_TEMPLATE
    
    clip = ClipRepository.get_by_id(clip_id)
    start_sec = clip.start_sec
    end_sec = clip.end_sec or (clip.start_sec + clip.duration_sec)
    duration_sec = clip.duration_sec

    # Get template from song (default to 'abstract' if not set)
    song = SongRepository.get_by_id(clip.song_id)
    template: TemplateType = DEFAULT_TEMPLATE
    if song and song.template:
        # Validate template value
        valid_templates = ["abstract", "environment", "character", "minimal"]
        if song.template in valid_templates:
            template = song.template  # type: ignore
        else:
            logger.warning(f"Invalid template '{song.template}' for song {clip.song_id}, using default 'abstract'")

    # For short-form videos, analysis may not have sections
    # Use build_clip_scene_spec which works with song-level analysis
    if not analysis.sections:
        logger.info(
            f"[CLIP-GEN] Clip {clip_id}: No sections in analysis, using clip scene spec "
            f"(short-form mode) for {start_sec}s-{end_sec}s, template={template}"
        )
        return build_clip_scene_spec(
            start_sec=start_sec,
            end_sec=end_sec,
            analysis=analysis,
            template=template,
        )

    # For long-form videos with sections, use section-specific scene spec
    target_section = _find_section_for_clip(start_sec, analysis.sections)
    scene_spec = build_scene_spec(target_section.id, analysis, template=template)
    return scene_spec.model_copy(update={"duration_sec": duration_sec})


def _find_section_for_clip(start_time: float, sections: List[SongSection]) -> SongSection:
    for section in sections:
        if section.start_sec <= start_time < section.end_sec:
            return section
    return min(sections, key=lambda s: abs(s.start_sec - start_time))


def _get_character_image_urls(song) -> tuple[list[str], Optional[str]]:
    """
    Get character image URLs for video generation.
    
    Returns tuple of (urls_list, fallback_url) where:
    - urls_list: List of all available character image URLs (for multiple image support)
    - fallback_url: Single URL for fallback (first available image)
    
    Priority order:
    1. character_generated_image_s3_key (if available)
    2. character_reference_image_s3_key (pose-a)
    3. character_pose_b_s3_key (pose-b, added to list but not as fallback)
    """
    if not song or not song.character_consistency_enabled:
        return [], None
    
    character_image_urls = []
    character_image_url = None
    settings = get_settings()
    
    # Priority 1: Use generated image if available
    if song.character_generated_image_s3_key:
        try:
            generated_url = generate_presigned_get_url(
                bucket_name=settings.s3_bucket_name,
                key=song.character_generated_image_s3_key,
                expires_in=3600,
            )
            character_image_urls.append(generated_url)
            character_image_url = generated_url
            logger.info(f"Using character generated image for clip generation: {song.character_generated_image_s3_key}")
        except Exception as e:
            logger.warning(f"Failed to generate presigned URL for character generated image: {e}")
    
    # Priority 2: Use reference image (pose-a)
    if song.character_reference_image_s3_key:
        try:
            pose_a_url = generate_presigned_get_url(
                bucket_name=settings.s3_bucket_name,
                key=song.character_reference_image_s3_key,
                expires_in=3600,
            )
            # Only add if not already added (generated image takes priority)
            if not character_image_urls:
                character_image_urls.append(pose_a_url)
                character_image_url = pose_a_url
            logger.info(f"Using character reference image (pose-a) for clip generation: {song.character_reference_image_s3_key}")
        except Exception as e:
            logger.warning(f"Failed to generate presigned URL for character reference image: {e}")
    
    # Priority 3: Add pose-b if available (for multiple image support)
    if song.character_pose_b_s3_key:
        try:
            pose_b_url = generate_presigned_get_url(
                bucket_name=settings.s3_bucket_name,
                key=song.character_pose_b_s3_key,
                expires_in=3600,
            )
            character_image_urls.append(pose_b_url)
            logger.info(f"Using character pose-b image for clip generation: {song.character_pose_b_s3_key}")
        except Exception as e:
            logger.warning(f"Failed to generate presigned URL for character pose-b image: {e}")
    
    # Ensure we have at least one URL for fallback
    if character_image_urls and not character_image_url:
        character_image_url = character_image_urls[0]
    
    return character_image_urls, character_image_url


def _determine_seed_for_clip(clip_id: UUID) -> Optional[int]:
    try:
        clip = ClipRepository.get_by_id(clip_id)
    except ClipNotFoundError:
        return None

    if clip.style_seed is not None:
        try:
            return int(clip.style_seed)
        except ValueError:
            logger.debug("Clip %s style_seed is non-numeric; generating new seed.", clip_id)

    seed = random.randint(0, 2**31 - 1)
    clip.style_seed = str(seed)
    ClipRepository.update(clip)
    return seed


def _verify_url_exists(url: str, timeout: float = 10.0) -> bool:
    """Check if a URL exists and is accessible via HEAD request."""
    try:
        response = httpx.head(url, timeout=timeout, follow_redirects=True)
        return response.status_code == 200
    except Exception:
        # If HEAD fails, try GET with range to avoid downloading the whole file
        try:
            headers = {"Range": "bytes=0-0"}  # Just request first byte
            response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
            return response.status_code in (200, 206)  # 206 = Partial Content
        except Exception:
            return False


def _extract_audio_segment(
    audio_path: Path,
    start_sec: float,
    end_sec: float,
    output_path: Path,
) -> None:
    """Extract audio segment using ffmpeg.
    
    Args:
        audio_path: Path to input audio file
        start_sec: Start time in seconds
        end_sec: End time in seconds
        output_path: Path to output audio file
        
    Raises:
        RuntimeError: If ffmpeg extraction fails
    """
    settings = get_settings()
    ffmpeg_bin = settings.ffmpeg_bin
    
    duration = end_sec - start_sec
    cmd = [
        ffmpeg_bin,
        "-i", str(audio_path),
        "-ss", str(start_sec),
        "-t", str(duration),
        "-acodec", "copy",  # Copy codec to avoid re-encoding
        "-y",  # Overwrite output file
        str(output_path),
    ]
    
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=60.0,
        )
        logger.info(
            f"Extracted audio segment: {start_sec}s - {end_sec}s "
            f"({duration:.2f}s) from {audio_path} to {output_path}"
        )
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg extraction failed: {e.stderr}")
        raise RuntimeError(f"Failed to extract audio segment: {e.stderr}") from e
    except subprocess.TimeoutExpired:
        raise RuntimeError("Audio extraction timed out after 60 seconds") from None


def _download_clip_to_path(url: str, destination: Path, timeout: float = 120.0) -> None:
    # Verify URL exists before attempting download
    if not _verify_url_exists(url, timeout=10.0):
        raise StorageError(
            f"Clip URL is not accessible (404 or connection failed): {url[:200]}"
        )
    
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
        raise StorageError(
            f"Failed to download clip asset from presigned URL (status {exc.response.status_code}): {error_detail}"
        ) from exc
    except httpx.HTTPError as exc:
        raise StorageError(f"Failed to download clip asset from {url}: {exc}") from exc


def compose_song_video(song_id: UUID, job_id: Optional[str] = None) -> tuple[str, Optional[str]]:
    """
    Stitch all completed clips for a song into a single video using the processed audio track.

    Args:
        song_id: Song ID
        job_id: Optional job ID for progress tracking

    Returns:
        Tuple of (video_s3_key, poster_s3_key)
    """
    if job_id:
        update_job_progress(job_id, 10, "processing")

    settings = get_settings()
    bucket = settings.s3_bucket_name
    if not bucket:
        raise StorageError("S3 bucket name is not configured; cannot store composed video.")

    song = SongRepository.get_by_id(song_id)
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
                SongRepository.update(song)
                break
        
        if found_key:
            audio_key = found_key
        else:
            raise StorageError(
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
                SongRepository.update(song)
                break
        
        if found_key:
            audio_key = found_key
        else:
            raise StorageError(
                f"Song audio is unavailable for composition. "
                f"Key in database ({audio_key}) doesn't exist in S3, "
                f"and not found at any expected S3 location: {', '.join(possible_keys)}"
            )

    # Get clips after audio key is validated
    clips = ClipRepository.get_by_song_id(song_id)

    if not clips:
        raise CompositionError("No clips found to compose.")

    completed_clips = [
        clip for clip in clips if clip.status == "completed" and clip.video_url
    ]
    if len(completed_clips) != len(clips):
        raise CompositionError("Cannot compose video until all clips are completed.")

    try:
        song = SongRepository.get_by_id(song_id)
        song_duration = song.duration_sec
    except SongNotFoundError:
        song_duration = None
    if song_duration is None:
        song_duration = sum(clip.duration_sec or 0 for clip in completed_clips)

    if job_id:
        update_job_progress(job_id, 20, "processing")  # Starting download

    with tempfile.TemporaryDirectory(prefix=f"compose-{song_id}-") as tmpdir:
        temp_dir = Path(tmpdir)
        normalized_paths: list[Path] = []

        # Download clips and normalize them
        total_clips = len(completed_clips)
        for idx, clip in enumerate(completed_clips):
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
                    raise StorageError(
                        f"Clip {clip.clip_index} file not found at S3 key {clip_s3_key} and no video_url available. "
                        f"Clips may need to be re-generated or uploaded to S3."
                    )
                # Skip obviously fake/test URLs (like example.com)
                if "example.com" in clip.video_url or "localhost" in clip.video_url:
                    raise StorageError(
                        f"Clip {clip.clip_index} has invalid test URL: {clip.video_url}. "
                        f"Please re-run the preload script to upload clips to S3."
                    )
                try:
                    _download_clip_to_path(clip.video_url, source_path)
                except StorageError as download_err:
                    # Provide more helpful error message for expired/invalid presigned URLs
                    if "404" in str(download_err) or "not found" in str(download_err).lower():
                        raise StorageError(
                            f"Clip {clip.clip_index} presigned URL has expired or file was deleted. "
                            f"Clips need to be re-generated or uploaded to S3 at {clip_s3_key}. "
                            f"Original error: {download_err}"
                        ) from download_err
                    raise
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
                        raise StorageError(
                            f"Clip {clip.clip_index} has no video_url and S3 download failed: {s3_err}"
                        ) from s3_err
                    # Skip obviously fake/test URLs (like example.com)
                    if "example.com" in clip.video_url or "localhost" in clip.video_url:
                        raise StorageError(
                            f"Clip {clip.clip_index} has invalid test URL: {clip.video_url}. "
                            f"Please re-run the preload script to upload clips to S3."
                        )
                    _download_clip_to_path(clip.video_url, source_path)
            
            # Update progress: 20-40% for downloading clips
            if job_id:
                download_progress = 20 + int((idx + 1) / total_clips * 20)
                update_job_progress(job_id, download_progress, "processing")
            
            normalize_clip(str(source_path), str(normalized_path))
            normalized_paths.append(normalized_path)
            
            # Update progress: 40-65% for normalizing clips
            if job_id:
                normalize_progress = 40 + int((idx + 1) / total_clips * 25)
                update_job_progress(job_id, normalize_progress, "processing")

        # Download audio (key has already been validated to exist in S3 above)
        audio_bytes = download_bytes_from_s3(bucket_name=bucket, key=audio_key)
        audio_extension = Path(audio_key).suffix or ".wav"
        full_audio_path = temp_dir / f"song_audio_full{audio_extension}"
        full_audio_path.write_bytes(audio_bytes)

        # Extract audio segment if selection exists
        if song.selected_start_sec is not None and song.selected_end_sec is not None:
            logger.info(
                f"Extracting selected audio segment: {song.selected_start_sec}s - {song.selected_end_sec}s "
                f"(duration: {song.selected_end_sec - song.selected_start_sec}s)"
            )
            audio_path = temp_dir / f"song_audio_selected{audio_extension}"
            _extract_audio_segment(
                audio_path=full_audio_path,
                start_sec=song.selected_start_sec,
                end_sec=song.selected_end_sec,
                output_path=audio_path,
            )
            # Use selected duration for composition
            effective_duration = song.selected_end_sec - song.selected_start_sec
        else:
            audio_path = full_audio_path
            effective_duration = float(song_duration)

        if job_id:
            update_job_progress(job_id, 65, "processing")  # Starting concatenation

        # Get beat times from analysis (for beat-synced visual effects)
        analysis = get_latest_analysis(song_id)
        beat_times = None
        if analysis and hasattr(analysis, 'beat_times') and analysis.beat_times:
            beat_times = analysis.beat_times
            logger.info(f"Found {len(beat_times)} beat times for beat-synced visual effects")
        
        # Get beat effect config
        from app.core.config import get_beat_effect_config
        effect_config = get_beat_effect_config()
        filter_type = effect_config.effect_type if effect_config.enabled else None

        # Concatenate clips with audio
        output_path = temp_dir / "composed_video.mp4"
        composition_result = concatenate_clips(
            [str(path) for path in normalized_paths],
            str(audio_path),
            str(output_path),
            song_duration_sec=effective_duration,
            job_id=job_id,
            beat_times=beat_times if effect_config.enabled else None,  # Only pass if effects enabled
            filter_type=filter_type or "flash",  # Use config or default
            frame_rate=24.0,
        )
        
        if job_id:
            update_job_progress(job_id, 85, "processing")  # Concatenation complete

        # Generate poster frame
        poster_path = temp_dir / "poster.jpg"
        try:
            generate_video_poster(str(output_path), str(poster_path))
            poster_bytes = poster_path.read_bytes()
        except Exception:
            logger.exception("Failed to generate composed video poster for song %s", song_id)
            poster_bytes = None

        video_bytes = output_path.read_bytes()

    if job_id:
        update_job_progress(job_id, 90, "processing")  # Starting upload

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
    
    if job_id:
        update_job_progress(job_id, 95, "processing")  # Upload complete

    song = SongRepository.get_by_id(song_id)
    song.composed_video_s3_key = video_key
    song.composed_video_poster_s3_key = poster_key
    song.composed_video_duration_sec = composition_result.duration_sec
    song.composed_video_fps = composition_result.fps
    SongRepository.update(song)

    if job_id:
        update_job_progress(job_id, 100, "completed")  # Composition complete

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

        try:
            song = SongRepository.get_by_id(song_id)
            song.composed_video_s3_key = None
            song.composed_video_poster_s3_key = None
            song.composed_video_duration_sec = None
            song.composed_video_fps = None
            SongRepository.update(song)
        except SongNotFoundError:
            # Song doesn't exist, skip
            pass

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
            raise ClipGenerationError("Failed to create clip generation job.")
        status = job_record.status

    return ClipGenerationJobResponse(job_id=job_id, song_id=song_id, status=status)


def get_clip_generation_job_status(job_id: str) -> JobStatusResponse:
    with session_scope() as session:
        job_record = session.get(ClipGenerationJob, job_id)
        if not job_record:
            raise JobNotFoundError(f"Job {job_id} not found")
        song_id = job_record.song_id

    summary = _refresh_clip_generation_job(job_id) or get_clip_generation_summary(song_id)
    with session_scope() as session:
        job_record = session.get(ClipGenerationJob, job_id)
        if not job_record:
            raise JobNotFoundError(f"Job {job_id} not found")

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

