from __future__ import annotations

import json
import logging
import tempfile
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import librosa
import numpy as np
import redis
from rq import Queue
from rq.job import Job, get_current_job

from app.core.config import get_settings
from app.core.database import session_scope
from app.models.analysis import AnalysisJob, SongAnalysisRecord
from app.models.song import Song
from app.schemas.analysis import SongAnalysis, SongSection
from app.schemas.job import JobStatusResponse, SongAnalysisJobResponse
from app.services import compute_genre, compute_mood_features, compute_mood_tags, extract_and_align_lyrics
from app.services.storage import download_bytes_from_s3
from sqlmodel import select

logger = logging.getLogger(__name__)


def _get_queue() -> Queue:
    settings = get_settings()
    connection = redis.from_url(settings.redis_url)
    return Queue(settings.rq_worker_queue, connection=connection)


def enqueue_song_analysis(song_id: UUID) -> SongAnalysisJobResponse:
    queue = _get_queue()
    job_id = f"analysis-{uuid4()}"
    job: Job = queue.enqueue(run_song_analysis_job, song_id, job_id=job_id, meta={"progress": 0})

    with session_scope() as session:
        analysis_job = AnalysisJob(
            id=job.id,
            song_id=song_id,
            status="queued",
            progress=0,
        )
        session.add(analysis_job)
        session.commit()

    return SongAnalysisJobResponse(job_id=job.id, status="queued")


def get_job_status(job_id: str) -> JobStatusResponse:
    with session_scope() as session:
        job_record = session.get(AnalysisJob, job_id)
        if not job_record:
            raise ValueError(f"Job {job_id} not found")

        result = None
        if job_record.analysis_id:
            analysis_record = session.get(SongAnalysisRecord, job_record.analysis_id)
            if analysis_record:
                result = SongAnalysis.model_validate_json(analysis_record.analysis_json)

        return JobStatusResponse(
            job_id=job_record.id,
            song_id=str(job_record.song_id),
            status=job_record.status,
            progress=job_record.progress,
            analysis_id=str(job_record.analysis_id) if job_record.analysis_id else None,
            error=job_record.error,
            result=result,
        )


def get_latest_analysis(song_id: UUID) -> SongAnalysis | None:
    with session_scope() as session:
        statement = (
            select(SongAnalysisRecord)
            .where(SongAnalysisRecord.song_id == song_id)
            .order_by(SongAnalysisRecord.updated_at.desc())
        )
        record = session.exec(statement).first()
        if not record:
            return None
        return SongAnalysis.model_validate_json(record.analysis_json)


def _update_job_progress(job_id: str | None, progress: int) -> None:
    if job_id is None:
        return
    with session_scope() as session:
        job_record = session.get(AnalysisJob, job_id)
        if not job_record:
            return
        job_record.progress = progress
        job_record.status = "processing"
        session.add(job_record)
        session.commit()


def _complete_job(job_id: str | None, analysis_record: SongAnalysisRecord) -> None:
    if job_id is None:
        return
    with session_scope() as session:
        job_record = session.get(AnalysisJob, job_id)
        if not job_record:
            return
        job_record.status = "completed"
        job_record.progress = 100
        job_record.analysis_id = analysis_record.id
        session.add(job_record)
        session.commit()


def _fail_job(job_id: str | None, error_message: str) -> None:
    if job_id is None:
        return
    with session_scope() as session:
        job_record = session.get(AnalysisJob, job_id)
        if not job_record:
            return
        job_record.status = "failed"
        job_record.error = error_message
        job_record.progress = min(job_record.progress, 99)
        session.add(job_record)
        session.commit()


def run_song_analysis_job(song_id: UUID) -> dict[str, Any]:
    current_job = get_current_job()
    job_id = current_job.id if current_job else None

    try:
        analysis_payload = _execute_analysis_pipeline(song_id, job_id)
        return analysis_payload
    except Exception as exc:  # noqa: BLE001
        logger.exception("Song analysis failed for song_id=%s", song_id)
        _fail_job(job_id, str(exc))
        raise


def _execute_analysis_pipeline(song_id: UUID, job_id: str | None) -> dict[str, Any]:
    settings = get_settings()

    with session_scope() as session:
        song = session.get(Song, song_id)
        if not song:
            raise ValueError(f"Song {song_id} not found")

        audio_key = song.processed_s3_key or song.original_s3_key
        if not audio_key:
            raise ValueError("Song has no associated audio to analyze")

        audio_bytes = download_bytes_from_s3(bucket_name=settings.s3_bucket_name, key=audio_key)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            audio_path = Path(tmp.name)
            tmp.write(audio_bytes)

    try:
        y, sr = librosa.load(str(audio_path), sr=None, mono=True)
        duration = float(librosa.get_duration(y=y, sr=sr))

        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
        beat_times = [round(time, 4) for time in beat_times]

        _update_job_progress(job_id, 25)

        # onset_env = librosa.onset.onset_strength(y=y, sr=sr)  # Not used yet
        # novelty_curve = _normalize_list(onset_env.tolist())  # Not used yet

        sections = _detect_sections(y, sr, duration)

        _update_job_progress(job_id, 50)

        mood_vector = compute_mood_features(audio_path, tempo if tempo else None)
        primary_mood, mood_tags = compute_mood_tags(mood_vector)
        primary_genre, sub_genres, _ = compute_genre(audio_path, tempo if tempo else None, mood_vector)

        _update_job_progress(job_id, 70)

        lyrics_available = False
        section_lyrics_models = []

        try:
            lyrics_available, aligned = extract_and_align_lyrics(audio_path, sections)
            section_lyrics_models = aligned
        except Exception as lyric_exc:  # noqa: BLE001
            logger.warning("Lyric extraction failed for song %s: %s", song_id, lyric_exc)
            lyrics_available = False
            section_lyrics_models = []

        _update_job_progress(job_id, 85)

        analysis = SongAnalysis(
            durationSec=duration,
            bpm=float(tempo) if tempo else None,
            beatTimes=beat_times,
            sections=sections,
            moodPrimary=primary_mood,
            moodTags=mood_tags,
            moodVector=mood_vector,
            primaryGenre=primary_genre,
            subGenres=sub_genres,
            lyricsAvailable=lyrics_available,
            sectionLyrics=section_lyrics_models,
        )

        analysis_json = analysis.model_dump_json()

        with session_scope() as session:
            statement = select(SongAnalysisRecord).where(SongAnalysisRecord.song_id == song_id)
            record = session.exec(statement).first()

            if record:
                record.analysis_json = analysis_json
                record.bpm = float(tempo) if tempo else None
                record.duration_sec = duration
            else:
                record = SongAnalysisRecord(
                    song_id=song_id,
                    analysis_json=analysis_json,
                    bpm=float(tempo) if tempo else None,
                    duration_sec=duration,
                )
            session.add(record)
            session.commit()
            session.refresh(record)

        _complete_job(job_id, record)

        return json.loads(analysis_json)
    finally:
        try:
            if audio_path.exists():
                audio_path.unlink()
        except FileNotFoundError:
            pass


def _normalize_list(values: list[float]) -> list[float]:
    if not values:
        return []
    max_value = max(values)
    if max_value <= 0:
        return [0.0 for _ in values]
    return [round(v / max_value, 5) for v in values]


def _detect_sections(y: np.ndarray, sr: int, duration: float) -> list[SongSection]:
    hop_length = 512
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop_length)
    chroma = librosa.util.normalize(chroma)

    n_frames = chroma.shape[1]
    if n_frames < 16:
        boundaries = np.array([0, n_frames - 1])
    else:
        k = min(6, max(2, n_frames // 32))
        boundaries = librosa.segment.agglomerative(chroma.T, k=k)
        boundaries = np.pad(boundaries, (0, 1), mode="constant", constant_values=n_frames - 1)
        boundaries[0] = 0

    boundary_times = librosa.frames_to_time(boundaries, sr=sr, hop_length=hop_length)
    boundary_times = np.clip(boundary_times, 0, duration)
    boundary_times = np.unique(boundary_times)

    if boundary_times[-1] < duration:
        boundary_times = np.append(boundary_times, duration)

    sections: list[SongSection] = []
    template_types = ["intro", "verse", "pre_chorus", "chorus", "bridge", "outro"]

    # Compute mean chroma per segment for repetition grouping
    segment_chroma = []
    for idx in range(len(boundary_times) - 1):
        start_frame = int(boundaries[idx])
        end_frame = int(boundaries[idx + 1]) if idx + 1 < len(boundaries) else n_frames - 1
        segment_slice = chroma[:, start_frame:end_frame] if end_frame > start_frame else chroma[:, start_frame:]
        if segment_slice.size == 0:
            segment_chroma.append(np.zeros(chroma.shape[0]))
        else:
            segment_chroma.append(np.mean(segment_slice, axis=1))

    repetition_labels = _assign_repetition_groups(segment_chroma)

    for idx in range(len(boundary_times) - 1):
        start = float(boundary_times[idx])
        end = float(boundary_times[idx + 1])
        section_type = template_types[min(idx, len(template_types) - 1)]
        confidence = 0.6 if repetition_labels[idx] else 0.5

        section = SongSection(
            id=f"section-{idx}",
            type=section_type,
            startSec=round(start, 3),
            endSec=round(end, 3),
            confidence=round(confidence, 3),
            repetitionGroup=repetition_labels[idx],
        )
        sections.append(section)

    return sections


def _assign_repetition_groups(features: list[np.ndarray]) -> list[str | None]:
    if not features:
        return []

    groups: list[str | None] = [None] * len(features)
    if len(features) <= 1:
        return groups

    feature_matrix = np.vstack(features)
    norm = np.linalg.norm(feature_matrix, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    normalized = feature_matrix / norm

    similarity = normalized @ normalized.T
    threshold = 0.85

    group_label = 0
    for i in range(len(features)):
        if groups[i] is not None:
            continue
        groups[i] = f"grp-{group_label}"
        for j in range(i + 1, len(features)):
            if groups[j] is None and similarity[i, j] >= threshold:
                groups[j] = groups[i]
        group_label += 1

    return groups


