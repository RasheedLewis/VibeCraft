"""Composition execution service - runs the actual composition pipeline."""

from __future__ import annotations

import concurrent.futures
import logging
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.core.database import session_scope
from app.models.composition import CompositionJob
from app.models.section_video import SectionVideo
from app.models.song import Song
from app.repositories import SongRepository
from app.services.composition_job import (
    complete_job,
    create_composed_video,
    fail_job,
    update_job_progress,
)
from app.services.storage import download_bytes_from_s3, upload_bytes_to_s3
from app.services.video_composition import (
    concatenate_clips,
    extend_last_clip,
    normalize_clip,
    trim_last_clip,
    validate_composition_inputs,
    verify_composed_video,
)

logger = logging.getLogger(__name__)

# Progress milestones
PROGRESS_VALIDATION = 10
PROGRESS_DOWNLOAD_START = 10
PROGRESS_DOWNLOAD_END = 30
PROGRESS_NORMALIZE_START = 30
PROGRESS_NORMALIZE_END = 80
PROGRESS_STITCH = 80
PROGRESS_UPLOAD = 90
PROGRESS_VERIFY = 95
PROGRESS_COMPLETE = 100

MAX_DURATION_SECONDS = 5 * 60  # 5 minutes cap
MAX_DURATION_MISMATCH_SECONDS = 5.0  # Maximum allowed duration mismatch


def execute_composition_pipeline(
    job_id: str,
    song_id: UUID,
    clip_ids: list[UUID],
    clip_metadata: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Execute the full composition pipeline.

    Args:
        job_id: Composition job ID
        song_id: Song ID
        clip_ids: List of SectionVideo IDs
        clip_metadata: List of metadata dicts with clipId, startFrame, endFrame

    Raises:
        RuntimeError: If composition fails
    """
    settings = get_settings()

    try:
        # Check if job was cancelled
        with session_scope() as session:
            job = session.get(CompositionJob, job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            if job.status == "cancelled":
                logger.info(f"Job {job_id} was cancelled, aborting")
                return

        update_job_progress(job_id, PROGRESS_VALIDATION, "processing")

        # Step 1: Validate inputs
        logger.info(f"Validating composition inputs for job {job_id}")
        song = SongRepository.get_by_id(song_id)

        if song.duration_sec and song.duration_sec > MAX_DURATION_SECONDS:
            raise ValueError(
                f"Song duration ({song.duration_sec}s) exceeds maximum ({MAX_DURATION_SECONDS}s)"
            )

        # Get clips
        clips = []
        clip_urls = []
        with session_scope() as session:
            for clip_id in clip_ids:
                clip = session.get(SectionVideo, clip_id)
                if not clip:
                    raise ValueError(f"SectionVideo {clip_id} not found")
                if not clip.video_url:
                    raise ValueError(f"SectionVideo {clip_id} has no video_url")
                clips.append(clip)
                clip_urls.append(clip.video_url)

        # Validate clip URLs
        clip_metadata_list = validate_composition_inputs(clip_urls)
        logger.info(f"Validated {len(clip_metadata_list)} clips")

        # Step 2: Download clips and audio
        logger.info(f"Downloading clips and audio for job {job_id}")
        update_job_progress(job_id, PROGRESS_DOWNLOAD_START, "processing")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Download audio
            audio_key = song.processed_s3_key or song.original_s3_key
            if not audio_key:
                raise ValueError("Song has no audio file")
            audio_bytes = download_bytes_from_s3(bucket_name=settings.s3_bucket_name, key=audio_key)
            audio_path = temp_path / "song_audio.mp3"
            audio_path.write_bytes(audio_bytes)
            logger.info(f"Downloaded audio: {len(audio_bytes)} bytes")

            # Download clips
            clip_paths = []
            download_progress_per_clip = (PROGRESS_DOWNLOAD_END - PROGRESS_DOWNLOAD_START) / len(clip_urls)

            for i, (clip_url, clip) in enumerate(zip(clip_urls, clips)):
                # Check cancellation
                with session_scope() as session:
                    job = session.get(CompositionJob, job_id)
                    if job and job.status == "cancelled":
                        logger.info(f"Job {job_id} was cancelled during download")
                        return

                clip_path = temp_path / f"clip_{i}.mp4"
                try:
                    # Download clip from URL
                    response = httpx.get(clip_url, timeout=60.0, follow_redirects=True)
                    response.raise_for_status()
                    clip_path.write_bytes(response.content)
                    clip_paths.append(clip_path)
                    logger.info(f"Downloaded clip {i + 1}/{len(clip_urls)}: {len(response.content)} bytes")

                    progress = PROGRESS_DOWNLOAD_START + int((i + 1) * download_progress_per_clip)
                    update_job_progress(job_id, progress, "processing")
                except Exception as e:
                    raise RuntimeError(f"Failed to download clip {i + 1} from {clip_url}: {e}") from e

            # Step 3: Normalize clips (parallel)
            logger.info(f"Normalizing {len(clip_paths)} clips for job {job_id}")
            update_job_progress(job_id, PROGRESS_NORMALIZE_START, "processing")

            normalized_paths = []
            normalize_progress_per_clip = (PROGRESS_NORMALIZE_END - PROGRESS_NORMALIZE_START) / len(clip_paths)

            def normalize_single_clip(i: int, clip_path: Path) -> Path:
                """Normalize a single clip."""
                # Check cancellation
                with session_scope() as session:
                    job = session.get(CompositionJob, job_id)
                    if job and job.status == "cancelled":
                        raise RuntimeError("Job cancelled")

                normalized_path = temp_path / f"normalized_{i}.mp4"
                try:
                    normalize_clip(clip_path, normalized_path)
                    logger.info(f"Normalized clip {i + 1}/{len(clip_paths)}")
                    return normalized_path
                except Exception as e:
                    raise RuntimeError(f"Failed to normalize clip {i + 1}: {e}") from e

            # Normalize in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                future_to_index = {
                    executor.submit(normalize_single_clip, i, clip_path): i
                    for i, clip_path in enumerate(clip_paths)
                }

                for future in concurrent.futures.as_completed(future_to_index):
                    i = future_to_index[future]
                    try:
                        normalized_path = future.result(timeout=300)  # 5 minute timeout per clip
                        normalized_paths.append(normalized_path)
                        progress = PROGRESS_NORMALIZE_START + int(
                            len(normalized_paths) * normalize_progress_per_clip
                        )
                        update_job_progress(job_id, progress, "processing")
                    except Exception as e:
                        raise RuntimeError(f"Normalization failed for clip {i + 1}: {e}") from e

            # Sort normalized paths by original order
            normalized_paths.sort(key=lambda p: int(p.stem.split("_")[1]))

            # Step 4: Handle duration mismatch
            total_clip_duration = sum(m.duration_sec for m in clip_metadata_list)
            song_duration = song.duration_sec or 0

            if song_duration > 0:
                duration_diff = total_clip_duration - song_duration

                # Check for large mismatches (fail if > 5 seconds either way)
                if abs(duration_diff) > MAX_DURATION_MISMATCH_SECONDS:
                    raise ValueError(
                        f"Duration mismatch too large: clips={total_clip_duration:.2f}s, "
                        f"song={song_duration:.2f}s, difference={abs(duration_diff):.2f}s "
                        f"(max allowed: {MAX_DURATION_MISMATCH_SECONDS}s)"
                    )

                # Handle small mismatches
                if duration_diff < 0:
                    # Clips are shorter: extend last clip
                    logger.info(
                        f"Extending last clip: clips={total_clip_duration:.2f}s, "
                        f"song={song_duration:.2f}s, diff={duration_diff:.2f}s"
                    )
                    last_clip_path = normalized_paths[-1]
                    extended_path = temp_path / "last_clip_extended.mp4"
                    extend_last_clip(
                        last_clip_path,
                        extended_path,
                        target_duration_sec=song_duration - total_clip_duration + clip_metadata_list[-1].duration_sec,
                    )
                    normalized_paths[-1] = extended_path
                elif duration_diff > 0:
                    # Clips are longer: trim last clip
                    logger.info(
                        f"Trimming last clip: clips={total_clip_duration:.2f}s, "
                        f"song={song_duration:.2f}s, diff={duration_diff:.2f}s"
                    )
                    last_clip_path = normalized_paths[-1]
                    trimmed_path = temp_path / "last_clip_trimmed.mp4"
                    # Calculate how much to trim from the last clip
                    last_clip_original_duration = clip_metadata_list[-1].duration_sec
                    last_clip_target_duration = last_clip_original_duration - duration_diff
                    trim_last_clip(
                        last_clip_path,
                        trimmed_path,
                        target_duration_sec=last_clip_target_duration,
                    )
                    normalized_paths[-1] = trimmed_path

            # Step 5: Concatenate clips with audio
            logger.info(f"Stitching {len(normalized_paths)} clips for job {job_id}")
            update_job_progress(job_id, PROGRESS_STITCH, "processing")

            output_path = temp_path / "composed.mp4"
            composition_result = concatenate_clips(
                normalized_clip_paths=normalized_paths,
                audio_path=audio_path,
                output_path=output_path,
                song_duration_sec=song_duration,
            )
            logger.info(
                f"Composed video: {composition_result.duration_sec:.2f}s, "
                f"{composition_result.width}x{composition_result.height} @ {composition_result.fps}fps"
            )

            # Step 6: Upload to S3
            logger.info(f"Uploading composed video to S3 for job {job_id}")
            update_job_progress(job_id, PROGRESS_UPLOAD, "processing")

            video_bytes = output_path.read_bytes()
            s3_key = f"composed/{song_id}/{job_id}/final.mp4"
            upload_bytes_to_s3(
                bucket_name=settings.s3_bucket_name,
                key=s3_key,
                data=video_bytes,
                content_type="video/mp4",
            )
            logger.info(f"Uploaded composed video: {len(video_bytes)} bytes to {s3_key}")

            # Step 7: Verify output
            logger.info(f"Verifying composed video for job {job_id}")
            update_job_progress(job_id, PROGRESS_VERIFY, "processing")

            # Re-verify using the uploaded file (or keep using local)
            verify_result = verify_composed_video(output_path)
            logger.info("Verification passed")

            # Step 8: Create ComposedVideo record
            composed_video = create_composed_video(
                song_id=song_id,
                s3_key=s3_key,
                duration_sec=verify_result.duration_sec,
                file_size_bytes=verify_result.file_size_bytes,
                resolution_width=verify_result.width,
                resolution_height=verify_result.height,
                fps=verify_result.fps,
                clip_ids=clip_ids,
            )

            # Step 9: Complete job
            complete_job(job_id, composed_video.id)
            update_job_progress(job_id, PROGRESS_COMPLETE, "completed")

            logger.info(f"Composition job {job_id} completed successfully")

            return {
                "status": "completed",
                "job_id": job_id,
                "composed_video_id": str(composed_video.id),
            }

    except Exception as e:
        logger.exception(f"Composition pipeline failed for job {job_id}")
        error_message = str(e)
        fail_job(job_id, error_message)
        raise

