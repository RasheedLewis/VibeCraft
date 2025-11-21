from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import select

from app.core.database import init_db, session_scope
from app.main import create_app
from app.models.analysis import SongAnalysisRecord
from app.models.clip import SongClip
from app.models.song import DEFAULT_USER_ID, Song
from app.schemas.analysis import SongAnalysis
from app.services.clip_planning import (
    ClipPlanningError,
    persist_clip_plans,
    plan_beat_aligned_clips,
)


init_db()


def make_analysis(beat_times: list[float]) -> SongAnalysis:
    return SongAnalysis(
        durationSec=max(beat_times) + 0.5 if beat_times else 30.0,
        bpm=120.0,
        beatTimes=beat_times,
        sections=[],
        moodPrimary="energetic",
        moodTags=[],
        moodVector={"energy": 0.8, "valence": 0.6, "danceability": 0.7, "tension": 0.4},
        primaryGenre="Test",
        subGenres=[],
        lyricsAvailable=False,
        sectionLyrics=[],
    )


def test_plan_clips_snaps_to_beats_and_frames():
    beat_times = [i * 0.5 for i in range(120)]  # every 0.5 seconds
    analysis = make_analysis(beat_times)
    duration = beat_times[-1] + 0.5

    plans = plan_beat_aligned_clips(
        duration_sec=duration,
        analysis=analysis,
        clip_count=4,
        min_clip_sec=3.0,
        max_clip_sec=15.0,
        generator_fps=8,
    )

    assert len(plans) == 4

    prev_end = 0.0
    for plan in plans:
        assert plan.start_sec == pytest.approx(prev_end, abs=1e-2)
        assert plan.end_sec % 0.125 == pytest.approx(0.0, abs=1e-6)
        assert plan.duration_sec >= 3.0 - 1e-3
        assert plan.duration_sec <= 15.0 + 1e-3
        assert plan.num_frames == int(round(plan.duration_sec * 8))
        prev_end = plan.end_sec

    assert prev_end == pytest.approx(duration, abs=0.25)


def test_plan_clips_handles_sparse_beats():
    analysis = make_analysis([0.0, 5.0, 10.0, 15.0, 20.0])
    duration = 22.0

    plans = plan_beat_aligned_clips(
        duration_sec=duration,
        analysis=analysis,
        clip_count=3,
        min_clip_sec=3.0,
        max_clip_sec=12.0,
        generator_fps=8,
    )

    assert len(plans) == 3
    assert plans[-1].end_sec == pytest.approx(duration, abs=0.25)


def test_plan_clips_splits_long_intervals_when_no_mid_beats():
    analysis = make_analysis([0.0, 10.0, 20.0])
    duration = 22.0

    plans = plan_beat_aligned_clips(
        duration_sec=duration,
        analysis=analysis,
        clip_count=4,
        min_clip_sec=3.0,
        max_clip_sec=6.0,
        generator_fps=8,
    )

    assert len(plans) == 4
    assert plans[-1].end_sec == pytest.approx(duration, abs=0.25)
    assert sum(plan.duration_sec for plan in plans) == pytest.approx(duration, abs=0.5)
    for plan in plans:
        assert plan.duration_sec >= 3.0 - 1e-3
        assert plan.duration_sec <= 6.0 + 1e-3

    assert any(plan.end_beat_index is None for plan in plans[:-1])


def test_plan_clips_falls_back_when_beats_missing():
    analysis = make_analysis([])

    plans = plan_beat_aligned_clips(
        duration_sec=24.0,
        analysis=analysis,
        clip_count=4,
        min_clip_sec=3.0,
        max_clip_sec=15.0,
        generator_fps=8,
    )

    assert len(plans) == 4
    for plan in plans:
        assert plan.duration_sec >= 3.0 - 1e-3
        assert plan.duration_sec <= 15.0 + 1e-3


def test_plan_clips_raises_when_exceeds_max_duration():
    analysis = make_analysis([0.0, 30.0])

    with pytest.raises(ClipPlanningError):
        plan_beat_aligned_clips(
            duration_sec=30.0,
            analysis=analysis,
            clip_count=2,
            min_clip_sec=3.0,
            max_clip_sec=5.0,
            generator_fps=8,
        )


def test_persist_clip_plans_creates_records():
    beat_times = [i * 0.5 for i in range(40)]
    analysis = make_analysis(beat_times)
    duration = beat_times[-1] + 0.5

    plans = plan_beat_aligned_clips(
        duration_sec=duration,
        analysis=analysis,
        clip_count=4,
        min_clip_sec=3.0,
        max_clip_sec=12.0,
        generator_fps=8,
    )

    song_id = uuid4()
    with session_scope() as session:
        song = Song(
            id=song_id,
            user_id=DEFAULT_USER_ID,
            title="Persist Test Song",
            original_filename="persist.wav",
            original_file_size=1024,
            original_s3_key="s3://test/persist.wav",
            processed_s3_key="s3://test/persist-processed.wav",
            duration_sec=duration,
        )
        session.add(song)
        session.commit()

    try:
        stored = persist_clip_plans(song_id=song_id, plans=plans, fps=8, source="beat")
        assert len(stored) == len(plans)

        with session_scope() as session:
            rows = session.exec(
                select(SongClip).where(SongClip.song_id == song_id).order_by(SongClip.clip_index)
            ).all()

        assert len(rows) == len(plans)
        for row, plan in zip(rows, plans):
            assert row.status == "queued"
            assert row.source == "beat"
            assert row.fps == 8
            assert row.num_frames == plan.num_frames
            assert row.start_sec == pytest.approx(plan.start_sec)
            assert row.end_sec == pytest.approx(plan.end_sec)
        assert row.prompt is None
        assert row.rq_job_id is None
        assert row.replicate_job_id is None

    finally:
        with session_scope() as session:
            for clip in session.exec(select(SongClip).where(SongClip.song_id == song_id)).all():
                session.delete(clip)
            song = session.get(Song, song_id)
            if song:
                session.delete(song)
            session.commit()


def test_clip_planning_api_flow():
    beat_times = [i * 0.5 for i in range(24)]
    analysis = make_analysis(beat_times)
    song_id = uuid4()

    with session_scope() as session:
        song = Song(
            id=song_id,
            user_id=DEFAULT_USER_ID,
            title="API Clip Song",
            original_filename="api.wav",
            original_file_size=2048,
            original_s3_key="s3://test/api.wav",
            processed_s3_key="s3://test/api-processed.wav",
            duration_sec=analysis.duration_sec,
        )
        session.add(song)
        session.commit()

        record = SongAnalysisRecord(
            song_id=song_id,
            analysis_json=analysis.model_dump_json(by_alias=True),
            bpm=analysis.bpm,
            duration_sec=analysis.duration_sec,
        )
        session.add(record)
        session.commit()

    with TestClient(create_app()) as client:
        response = client.post(
            f"/api/v1/songs/{song_id}/clips/plan",
            params={"clip_count": 3, "min_clip_sec": 3.0, "max_clip_sec": 10.0},
        )
        assert response.status_code == 202, response.text
        assert response.json()["clipsPlanned"] == 3

        list_response = client.get(f"/api/v1/songs/{song_id}/clips")
        assert list_response.status_code == 200, list_response.text
        clips = list_response.json()
        assert len(clips) == 3
        assert clips[0]["clipIndex"] == 0
        assert clips[-1]["clipIndex"] == 2
        assert clips[-1]["endSec"] == pytest.approx(analysis.duration_sec, abs=0.5)
        assert clips[0]["prompt"] is None
        assert clips[0]["rqJobId"] is None
        assert clips[0]["numFrames"] > 0

    with session_scope() as session:
        for clip in session.exec(select(SongClip).where(SongClip.song_id == song_id)).all():
            session.delete(clip)
        records = session.exec(
            select(SongAnalysisRecord).where(SongAnalysisRecord.song_id == song_id)
        ).all()
        for record in records:
            session.delete(record)
        song = session.get(Song, song_id)
        if song:
            session.delete(song)
        session.commit()


def test_plan_clips_with_selection_uses_effective_duration():
    """Test that clip planning uses selected range duration."""
    beat_times = [i * 0.5 for i in range(120)]  # 60 seconds of beats
    analysis = make_analysis(beat_times)
    
    # Selection: 10s to 40s (30s effective duration)
    selected_start = 10.0
    selected_end = 40.0
    effective_duration = selected_end - selected_start  # 30s

    plans = plan_beat_aligned_clips(
        duration_sec=effective_duration,  # Use effective duration, not full
        analysis=analysis,
        clip_count=4,
        min_clip_sec=3.0,
        max_clip_sec=12.0,
        generator_fps=8,
    )

    assert len(plans) == 4
    # Plans should cover the effective duration (30s), not full duration
    assert plans[-1].end_sec == pytest.approx(effective_duration, abs=0.5)
    assert plans[0].start_sec == pytest.approx(0.0, abs=0.1)  # Relative to selection start


def test_plan_clips_with_selection_applies_time_offset():
    """Test that clips are offset by selection start time."""
    beat_times = [i * 0.5 for i in range(120)]  # 60 seconds
    analysis = make_analysis(beat_times)
    
    # Selection: 20s to 50s (30s effective duration)
    selected_start = 20.0
    selected_end = 50.0
    effective_duration = selected_end - selected_start  # 30s
    time_offset = selected_start  # 20s

    # Plan clips for effective duration (as if selection starts at 0)
    plans = plan_beat_aligned_clips(
        duration_sec=effective_duration,
        analysis=analysis,
        clip_count=3,
        min_clip_sec=3.0,
        max_clip_sec=12.0,
        generator_fps=8,
    )

    # Apply time offset (this is what the API endpoint does)
    for plan in plans:
        plan.start_sec = round(plan.start_sec + time_offset, 4)
        plan.end_sec = round(plan.end_sec + time_offset, 4)

    # Verify clips are within selected range
    assert plans[0].start_sec >= selected_start
    assert plans[-1].end_sec <= selected_end
    
    # Verify first clip starts near selection start
    assert plans[0].start_sec == pytest.approx(selected_start, abs=1.0)
    # Verify last clip ends near selection end
    assert plans[-1].end_sec == pytest.approx(selected_end, abs=1.0)


def test_plan_clips_without_selection_uses_full_duration():
    """Test backward compatibility - no selection uses full duration."""
    beat_times = [i * 0.5 for i in range(80)]  # 40 seconds
    analysis = make_analysis(beat_times)
    full_duration = beat_times[-1] + 0.5  # ~40s

    plans = plan_beat_aligned_clips(
        duration_sec=full_duration,  # No selection = full duration
        analysis=analysis,
        clip_count=4,
        min_clip_sec=3.0,
        max_clip_sec=12.0,
        generator_fps=8,
    )

    assert len(plans) == 4
    # Plans should cover full duration
    assert plans[-1].end_sec == pytest.approx(full_duration, abs=0.5)
    assert plans[0].start_sec == pytest.approx(0.0, abs=0.1)


def test_plan_clips_selection_boundary_at_start():
    """Test selection starting at 0 seconds."""
    beat_times = [i * 0.5 for i in range(120)]  # 60 seconds
    analysis = make_analysis(beat_times)
    
    # Selection: 0s to 30s
    selected_start = 0.0
    selected_end = 30.0
    effective_duration = selected_end - selected_start  # 30s

    plans = plan_beat_aligned_clips(
        duration_sec=effective_duration,
        analysis=analysis,
        clip_count=3,
        min_clip_sec=3.0,
        max_clip_sec=12.0,
        generator_fps=8,
    )

    assert len(plans) == 3
    assert plans[0].start_sec == pytest.approx(0.0, abs=0.1)
    assert plans[-1].end_sec == pytest.approx(effective_duration, abs=0.5)


def test_plan_clips_selection_boundary_at_end():
    """Test selection ending at song duration."""
    beat_times = [i * 0.5 for i in range(120)]  # 60 seconds
    analysis = make_analysis(beat_times)
    full_duration = beat_times[-1] + 0.5  # ~60s
    
    # Selection: 30s to 60s (last 30s)
    selected_start = 30.0
    selected_end = full_duration
    effective_duration = selected_end - selected_start  # ~30s
    time_offset = selected_start  # 30s

    plans = plan_beat_aligned_clips(
        duration_sec=effective_duration,
        analysis=analysis,
        clip_count=3,
        min_clip_sec=3.0,
        max_clip_sec=12.0,
        generator_fps=8,
    )

    # Apply time offset
    for plan in plans:
        plan.start_sec = round(plan.start_sec + time_offset, 4)
        plan.end_sec = round(plan.end_sec + time_offset, 4)

    assert len(plans) == 3
    assert plans[0].start_sec >= selected_start
    assert plans[-1].end_sec == pytest.approx(selected_end, abs=0.5)


def test_plan_clips_selection_exactly_30s():
    """Test selection at exactly 30 seconds."""
    beat_times = [i * 0.5 for i in range(120)]  # 60 seconds
    analysis = make_analysis(beat_times)
    
    # Selection: 15s to 45s (exactly 30s)
    selected_start = 15.0
    selected_end = 45.0
    effective_duration = 30.0  # Exactly 30s
    time_offset = selected_start  # 15s

    plans = plan_beat_aligned_clips(
        duration_sec=effective_duration,
        analysis=analysis,
        clip_count=4,
        min_clip_sec=3.0,
        max_clip_sec=12.0,
        generator_fps=8,
    )

    # Apply time offset
    for plan in plans:
        plan.start_sec = round(plan.start_sec + time_offset, 4)
        plan.end_sec = round(plan.end_sec + time_offset, 4)

    assert len(plans) == 4
    assert plans[0].start_sec >= selected_start
    assert plans[-1].end_sec <= selected_end
    # Total duration should be approximately 30s
    total_duration = plans[-1].end_sec - plans[0].start_sec
    assert total_duration == pytest.approx(30.0, abs=1.0)


def test_plan_clips_selection_short_song():
    """Test selection on song shorter than 30 seconds."""
    beat_times = [i * 0.5 for i in range(30)]  # 15 seconds
    analysis = make_analysis(beat_times)
    full_duration = beat_times[-1] + 0.5  # ~15s
    
    # Selection: entire song (0s to 15s)
    selected_start = 0.0
    selected_end = full_duration
    effective_duration = selected_end - selected_start  # ~15s

    plans = plan_beat_aligned_clips(
        duration_sec=effective_duration,
        analysis=analysis,
        clip_count=3,
        min_clip_sec=3.0,
        max_clip_sec=6.0,
        generator_fps=8,
    )

    assert len(plans) == 3
    assert plans[0].start_sec == pytest.approx(0.0, abs=0.1)
    assert plans[-1].end_sec == pytest.approx(effective_duration, abs=0.5)
    # All clips should be within the short selection
    for plan in plans:
        assert plan.end_sec <= effective_duration


def test_clip_planning_api_with_selection():
    """Test clip planning API endpoint with selection."""
    beat_times = [i * 0.5 for i in range(120)]  # 60 seconds
    analysis = make_analysis(beat_times)
    song_id = uuid4()

    with session_scope() as session:
        song = Song(
            id=song_id,
            user_id=DEFAULT_USER_ID,
            title="Selection Test Song",
            original_filename="selection.wav",
            original_file_size=2048,
            original_s3_key="s3://test/selection.wav",
            processed_s3_key="s3://test/selection-processed.wav",
            duration_sec=analysis.duration_sec,
            selected_start_sec=10.0,  # Selection: 10s to 40s
            selected_end_sec=40.0,
        )
        session.add(song)
        session.commit()

        record = SongAnalysisRecord(
            song_id=song_id,
            analysis_json=analysis.model_dump_json(by_alias=True),
            bpm=analysis.bpm,
            duration_sec=analysis.duration_sec,
        )
        session.add(record)
        session.commit()

    try:
        with TestClient(create_app()) as client:
            response = client.post(
                f"/api/v1/songs/{song_id}/clips/plan",
                params={"clip_count": 3, "min_clip_sec": 3.0, "max_clip_sec": 12.0},
            )
            assert response.status_code == 202, response.text
            assert response.json()["clipsPlanned"] == 3

            list_response = client.get(f"/api/v1/songs/{song_id}/clips")
            assert list_response.status_code == 200, list_response.text
            clips = list_response.json()
            assert len(clips) == 3
            
            # Verify clips are within selected range (10s to 40s)
            assert clips[0]["startSec"] >= 10.0
            assert clips[-1]["endSec"] <= 40.0
            
            # Verify first clip starts near selection start
            assert clips[0]["startSec"] == pytest.approx(10.0, abs=2.0)
            # Verify last clip ends near selection end
            assert clips[-1]["endSec"] == pytest.approx(40.0, abs=2.0)
    finally:
        with session_scope() as session:
            for clip in session.exec(select(SongClip).where(SongClip.song_id == song_id)).all():
                session.delete(clip)
            records = session.exec(
                select(SongAnalysisRecord).where(SongAnalysisRecord.song_id == song_id)
            ).all()
            for record in records:
                session.delete(record)
            song = session.get(Song, song_id)
            if song:
                session.delete(song)
            session.commit()

