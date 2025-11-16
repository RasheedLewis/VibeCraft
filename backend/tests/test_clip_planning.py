from __future__ import annotations

import pytest

from app.schemas.analysis import SongAnalysis
from app.services.clip_planning import ClipPlanningError, plan_beat_aligned_clips


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

