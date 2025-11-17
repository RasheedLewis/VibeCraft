from __future__ import annotations

from typing import Optional
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from app.core.config import get_settings
from app.core.database import init_db, session_scope
from app.main import create_app
from app.models.analysis import ClipGenerationJob, SongAnalysisRecord
from app.models.clip import SongClip
from app.models.song import DEFAULT_USER_ID, Song
from app.schemas.analysis import SongAnalysis
from app.services.clip_generation import (
    enqueue_clip_generation_batch,
    get_clip_generation_job_status,
    get_clip_generation_summary,
    run_clip_generation_job,
    start_clip_generation_job,
)
from app.services.clip_planning import persist_clip_plans, plan_beat_aligned_clips

init_db()


class DummyJob:
    def __init__(self, clip_id: UUID, job_id: str, depends_on: Optional["DummyJob"], meta: Optional[dict]):
        self.clip_id = clip_id
        self.id = job_id
        self.depends_on = depends_on
        self.meta = meta or {}


class DummyQueue:
    def __init__(self) -> None:
        self.jobs: list[DummyJob] = []

    def enqueue(
        self,
        func,
        clip_id,
        job_id=None,
        depends_on=None,
        job_timeout=None,
        meta=None,
    ):
        job = DummyJob(clip_id, job_id, depends_on, meta)
        self.jobs.append(job)
        return job


def make_analysis(beat_times: list[float]) -> SongAnalysis:
    return SongAnalysis(
        durationSec=max(beat_times) + 0.5 if beat_times else 20.0,
        bpm=128.0,
        beatTimes=beat_times,
        sections=[
            {
                "id": "intro",
                "type": "intro",
                "startSec": 0.0,
                "endSec": 5.0,
                "confidence": 0.8,
            },
            {
                "id": "verse",
                "type": "verse",
                "startSec": 5.0,
                "endSec": 12.0,
                "confidence": 0.8,
            },
            {
                "id": "chorus",
                "type": "chorus",
                "startSec": 12.0,
                "endSec": 20.0,
                "confidence": 0.8,
            },
            {
                "id": "outro",
                "type": "outro",
                "startSec": 20.0,
                "endSec": 24.0,
                "confidence": 0.8,
            },
        ],
        moodPrimary="energetic",
        moodTags=["energetic", "uplifting", "cinematic"],
        moodVector={"energy": 0.8, "valence": 0.7, "danceability": 0.6, "tension": 0.5},
        primaryGenre="Electronic",
        subGenres=["EDM"],
        lyricsAvailable=False,
        sectionLyrics=[],
    )


def _insert_song_and_clips(
    *,
    beat_times: list[float],
    clip_count: int,
) -> tuple[UUID, SongAnalysis]:
    analysis = make_analysis(beat_times)
    song_id = uuid4()

    with session_scope() as session:
        song = Song(
            id=song_id,
            user_id=DEFAULT_USER_ID,
            title="Generation Song",
            original_filename="gen.wav",
            original_file_size=1024,
            original_s3_key="s3://test/gen.wav",
            processed_s3_key="s3://test/gen-processed.wav",
            duration_sec=analysis.duration_sec,
        )
        session.add(song)
        session.commit()

    plans = plan_beat_aligned_clips(
        duration_sec=analysis.duration_sec,
        analysis=analysis,
        clip_count=clip_count,
        min_clip_sec=3.0,
        max_clip_sec=10.0,
        generator_fps=8,
    )
    persist_clip_plans(song_id=song_id, plans=plans, fps=8, source="beat")

    with session_scope() as session:
        record = SongAnalysisRecord(
            song_id=song_id,
            analysis_json=analysis.model_dump_json(by_alias=True),
            bpm=analysis.bpm,
            duration_sec=analysis.duration_sec,
        )
        session.add(record)
        session.commit()

    return song_id, analysis


def _cleanup_song(song_id: UUID) -> None:
    with session_scope() as session:
        clips = session.exec(select(SongClip).where(SongClip.song_id == song_id)).all()
        for clip in clips:
            session.delete(clip)

        records = session.exec(
            select(SongAnalysisRecord).where(SongAnalysisRecord.song_id == song_id)
        ).all()
        for record in records:
            session.delete(record)

        jobs = session.exec(
            select(ClipGenerationJob).where(ClipGenerationJob.song_id == song_id)
        ).all()
        for job in jobs:
            session.delete(job)

        song = session.get(Song, song_id)
        if song:
            session.delete(song)
        session.commit()


def test_enqueue_clip_generation_batch_controls_concurrency(monkeypatch):
    song_id, _ = _insert_song_and_clips(beat_times=[i * 0.5 for i in range(32)], clip_count=5)

    dummy_queue = DummyQueue()
    monkeypatch.setattr(
        "app.services.clip_generation._get_clip_queue",
        lambda: dummy_queue,
    )

    job_ids = enqueue_clip_generation_batch(song_id=song_id, max_parallel=2)
    assert len(job_ids) == 5
    assert dummy_queue.jobs[2].depends_on is dummy_queue.jobs[0]
    assert dummy_queue.jobs[3].depends_on is dummy_queue.jobs[1]

    with session_scope() as session:
        clips = session.exec(
            select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
        ).all()

    for clip, job in zip(clips, dummy_queue.jobs):
        assert clip.status == "queued"
        assert clip.rq_job_id == job.id
        assert clip.error is None
        assert clip.num_frames > 0

    _cleanup_song(song_id)


def test_run_clip_generation_job_success(monkeypatch):
    song_id, _ = _insert_song_and_clips(beat_times=[i * 0.5 for i in range(24)], clip_count=3)

    with session_scope() as session:
        clip = session.exec(
            select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
        ).first()
    assert clip is not None
    clip_id = clip.id

    captured = {}

    def _mock_generate(scene_spec, seed=None, num_frames=None, fps=None):
        captured["num_frames"] = num_frames
        captured["fps"] = fps
        return True, "https://video.example.com/clip.mp4", {"fps": fps, "job_id": "rep-123", "seed": seed or 42}

    monkeypatch.setattr("app.services.clip_generation.generate_section_video", _mock_generate)

    # Ensure deterministic seed
    monkeypatch.setattr("random.randint", lambda *_: 42)

    result = run_clip_generation_job(clip_id)
    assert result["status"] == "completed"

    with session_scope() as session:
        updated_clip = session.get(SongClip, clip_id)
        assert updated_clip is not None
        assert updated_clip.status == "completed"
        assert updated_clip.video_url == "https://video.example.com/clip.mp4"
        assert updated_clip.replicate_job_id == "rep-123"
        assert updated_clip.prompt
        assert updated_clip.error is None
        assert captured["num_frames"] == updated_clip.num_frames
        assert captured["fps"] == updated_clip.fps

    _cleanup_song(song_id)


def test_run_clip_generation_job_failure(monkeypatch):
    song_id, _ = _insert_song_and_clips(beat_times=[i * 0.5 for i in range(20)], clip_count=2)

    with session_scope() as session:
        clip = session.exec(
            select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
        ).first()
    assert clip is not None
    clip_id = clip.id

    def _fail_generation(scene_spec, seed=None, num_frames=None, fps=None):
        return False, None, {"error": "replicate error", "job_id": "rep-err"}

    monkeypatch.setattr("app.services.clip_generation.generate_section_video", _fail_generation)

    with pytest.raises(RuntimeError):
        run_clip_generation_job(clip_id)

    with session_scope() as session:
        updated_clip = session.get(SongClip, clip_id)
        assert updated_clip is not None
        assert updated_clip.status == "failed"
        assert updated_clip.error == "replicate error"
        assert updated_clip.video_url is None

    _cleanup_song(song_id)


def test_get_clip_generation_summary():
    song_id, _ = _insert_song_and_clips(beat_times=[i * 0.5 for i in range(30)], clip_count=3)

    with session_scope() as session:
        clips = session.exec(
            select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
        ).all()
        clips[0].status = "completed"
        clips[0].video_url = "https://example.com/video0.mp4"
        clips[1].status = "processing"
        clips[2].status = "failed"
        clips[2].error = "generation failed"
        session.add_all(clips)
        session.commit()

    summary = get_clip_generation_summary(song_id)
    assert summary.progress_total == 3
    assert summary.progress_completed == 1
    assert summary.failed_clips == 1
    assert summary.processing_clips == 1
    assert len(summary.clips) == 3
    assert summary.composed_video_url is None

    with TestClient(create_app()) as client:
        response = client.get(f"/api/v1/songs/{song_id}/clips/status")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["progressTotal"] == 3
        assert data["progressCompleted"] == 1
        statuses = {clip["status"] for clip in data["clips"]}
        assert statuses == {"completed", "processing", "failed"}

    _cleanup_song(song_id)


def test_compose_endpoint_generates_urls(monkeypatch):
    song_id, _ = _insert_song_and_clips(beat_times=[i * 0.5 for i in range(16)], clip_count=2)

    with session_scope() as session:
        clips = session.exec(
            select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
        ).all()
        for clip in clips:
            clip.status = "completed"
            clip.video_url = f"https://example.com/clip{clip.clip_index}.mp4"
            session.add(clip)
        session.commit()

    composed_called: dict[str, bool] = {}

    def _fake_compose(target_song_id: UUID) -> tuple[str, Optional[str]]:
        composed_called["called"] = True
        with session_scope() as session:
            song = session.get(Song, target_song_id)
            assert song is not None
            song.composed_video_s3_key = "composed/video.mp4"
            song.composed_video_poster_s3_key = "composed/poster.jpg"
            song.composed_video_duration_sec = 42.0
            song.composed_video_fps = 24
            session.add(song)
            session.commit()
        return "composed/video.mp4", "composed/poster.jpg"

    monkeypatch.setattr("app.services.clip_generation.compose_song_video", _fake_compose)
    monkeypatch.setattr("app.api.v1.routes_songs.compose_song_video", _fake_compose)

    def _fake_presigned(*, bucket_name: str, key: str, expires_in: int = 3600) -> str:
        return f"https://cdn/{key}"

    monkeypatch.setattr(
        "app.services.clip_generation.generate_presigned_get_url",
        _fake_presigned,
    )

    def _fake_check_s3_object_exists(*, bucket_name: str, key: str) -> bool:
        # In tests, assume objects exist if they're in the expected format
        return True

    monkeypatch.setattr(
        "app.services.clip_generation.check_s3_object_exists",
        _fake_check_s3_object_exists,
    )

    settings = get_settings()
    monkeypatch.setattr(settings, "s3_bucket_name", "unit-test-bucket", raising=False)

    with TestClient(create_app()) as client:
        response = client.post(f"/api/v1/songs/{song_id}/clips/compose")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["composedVideoUrl"] == "https://cdn/composed/video.mp4"
        assert data["composedVideoPosterUrl"] == "https://cdn/composed/poster.jpg"

    assert composed_called.get("called") is True

    with session_scope() as session:
        song = session.get(Song, song_id)
        assert song is not None
        assert song.composed_video_s3_key == "composed/video.mp4"
        assert song.composed_video_poster_s3_key == "composed/poster.jpg"

    _cleanup_song(song_id)


def test_start_clip_generation_job_and_status(monkeypatch):
    song_id, _ = _insert_song_and_clips(beat_times=[i * 0.5 for i in range(24)], clip_count=3)

    dummy_queue = DummyQueue()
    monkeypatch.setattr("app.services.clip_generation._get_clip_queue", lambda: dummy_queue)

    response = start_clip_generation_job(song_id)
    assert response.song_id == song_id
    assert response.job_id.startswith("clip-batch-")

    with session_scope() as session:
        job_record = session.get(ClipGenerationJob, response.job_id)
        assert job_record is not None
        assert job_record.total_clips == 3

    status = get_clip_generation_job_status(response.job_id)
    assert status.song_id == song_id
    assert status.result is not None
    assert status.result.total_clips == 3

    api_queue = DummyQueue()
    monkeypatch.setattr("app.services.clip_generation._get_clip_queue", lambda: api_queue)
    other_song_id, _ = _insert_song_and_clips(beat_times=[i * 0.5 for i in range(16)], clip_count=2)

    with TestClient(create_app()) as client:
        resp = client.post(f"/api/v1/songs/{other_song_id}/clips/generate")
        assert resp.status_code == 202, resp.text
        payload = resp.json()
        assert payload["songId"] == str(other_song_id)
        assert payload["jobId"].startswith("clip-batch-")

        status_resp = client.get(f"/api/v1/songs/{other_song_id}/clips/status")
        assert status_resp.status_code == 200

        job_status_resp = client.get(f"/api/v1/jobs/{payload['jobId']}")
        assert job_status_resp.status_code == 200

    _cleanup_song(song_id)
    _cleanup_song(other_song_id)

