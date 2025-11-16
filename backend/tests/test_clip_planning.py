from __future__ import annotations

from uuid import uuid4

import pytest
from sqlmodel import select

from app.core.database import session_scope
from app.models.clip import SongClip
from app.models.song import DEFAULT_USER_ID, Song
from app.schemas.analysis import SongAnalysis
from app.services.clip_planning import (
    ClipPlanningError,
    persist_clip_plans,
    plan_beat_aligned_clips,
)


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
        assert plan.frame_count == int(round(plan.duration_sec * 8))
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
            assert row.frame_count == plan.frame_count
            assert row.start_sec == pytest.approx(plan.start_sec)
            assert row.end_sec == pytest.approx(plan.end_sec)

    finally:
        with session_scope() as session:
            for clip in session.exec(select(SongClip).where(SongClip.song_id == song_id)).all():
                session.delete(clip)
            song = session.get(Song, song_id)
            if song:
                session.delete(song)
            session.commit()

