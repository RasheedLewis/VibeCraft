from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional
from uuid import UUID

from sqlmodel import select

from app.core.database import session_scope
from app.models.clip import SongClip
from app.schemas.analysis import SongAnalysis


@dataclass(slots=True)
class ClipPlan:
    index: int
    start_sec: float
    end_sec: float
    duration_sec: float
    start_beat_index: Optional[int]
    end_beat_index: Optional[int]
    frame_count: int


class ClipPlanningError(RuntimeError):
    """Raised when clip planning cannot generate a valid set of boundaries."""


def plan_beat_aligned_clips(
    *,
    duration_sec: float,
    analysis: SongAnalysis,
    clip_count: int,
    min_clip_sec: float = 3.0,
    max_clip_sec: float = 15.0,
    generator_fps: int = 8,
) -> List[ClipPlan]:
    """Plan clip boundaries snapped to beat grid and frame intervals.

    Args:
        duration_sec: Total song duration in seconds.
        analysis: SongAnalysis including beatTimes.
        clip_count: Desired number of clips to produce.
        min_clip_sec: Minimum allowed clip duration.
        max_clip_sec: Maximum allowed clip duration (limited by generation API).
        generator_fps: Frame rate of the generation model (defaults to 8 for Zeroscope).

    Returns:
        A list of ClipPlan entries ordered by the clip index.

    Raises:
        ClipPlanningError: If planning fails to generate a valid set of clips.
    """

    if clip_count <= 0:
        raise ValueError("clip_count must be positive")
    if duration_sec <= 0:
        raise ValueError("duration_sec must be positive")
    if min_clip_sec <= 0 or max_clip_sec <= 0:
        raise ValueError("clip durations must be positive")
    if min_clip_sec >= max_clip_sec:
        raise ValueError("min_clip_sec must be less than max_clip_sec")

    frame_interval = 1.0 / generator_fps
    beat_times = sorted(_unique_floats(getattr(analysis, "beat_times", []) or []))
    target_length = max(min(max_clip_sec, duration_sec / clip_count), min_clip_sec)

    plans: list[ClipPlan] = []
    current_start = 0.0
    start_beat_index: Optional[int] = None

    for index in range(clip_count):
        is_last_clip = index == clip_count - 1

        if is_last_clip:
            raw_end = duration_sec
        else:
            desired_end = current_start + target_length
            min_end = min(duration_sec, current_start + min_clip_sec)
            max_end = min(duration_sec, current_start + max_clip_sec)
            raw_end, end_beat_index = _pick_boundary_from_beats(
                beat_times=beat_times,
                desired_end=desired_end,
                min_end=min_end,
                max_end=max_end,
            )
            if raw_end is None:
                raw_end = max(min(desired_end, max_end), min_end)
                end_beat_index = None
        raw_end = min(raw_end, duration_sec)
        snapped_end = _snap_to_frame(raw_end, frame_interval, duration_sec)

        if snapped_end - current_start < min_clip_sec - 1e-3:
            snapped_end = min(
                _snap_to_frame(current_start + min_clip_sec, frame_interval, duration_sec),
                duration_sec,
            )

        duration = max(snapped_end - current_start, frame_interval)

        if duration > max_clip_sec + 1e-3:
            raise ClipPlanningError(
                f"Planned clip {index} exceeds max duration ({duration:.2f}s > {max_clip_sec}s)"
            )

        frame_count = max(int(round(duration * generator_fps)), 1)

        plan = ClipPlan(
            index=index,
            start_sec=round(current_start, 4),
            end_sec=round(snapped_end, 4),
            duration_sec=round(duration, 4),
            start_beat_index=start_beat_index,
            end_beat_index=end_beat_index if not is_last_clip else None,
            frame_count=frame_count,
        )
        plans.append(plan)

        current_start = snapped_end
        start_beat_index = end_beat_index

    if abs(plans[-1].end_sec - duration_sec) > max(frame_interval, 0.25):
        raise ClipPlanningError(
            f"Clip plan did not cover song duration ({plans[-1].end_sec:.3f}s / {duration_sec:.3f}s)"
        )

    return plans


def persist_clip_plans(
    *,
    song_id: UUID,
    plans: List[ClipPlan],
    fps: int = 8,
    source: str = "auto",
    clear_existing: bool = True,
) -> List[SongClip]:
    """Persist planned clips to the database and return the stored records."""

    with session_scope() as session:
        if clear_existing:
            existing = session.exec(select(SongClip).where(SongClip.song_id == song_id)).all()
            for clip in existing:
                session.delete(clip)
            session.commit()

        song_clips: list[SongClip] = []
        for plan in plans:
            clip = SongClip(
                song_id=song_id,
                clip_index=plan.index,
                start_sec=plan.start_sec,
                end_sec=plan.end_sec,
                duration_sec=plan.duration_sec,
                start_beat_index=plan.start_beat_index,
                end_beat_index=plan.end_beat_index,
                frame_count=plan.frame_count,
                fps=fps,
                status="queued",
                source=source,
            )
            session.add(clip)
            song_clips.append(clip)

        session.commit()

        for clip in song_clips:
            session.refresh(clip)

        return song_clips


def _pick_boundary_from_beats(
    *,
    beat_times: list[float],
    desired_end: float,
    min_end: float,
    max_end: float,
) -> tuple[Optional[float], Optional[int]]:
    if not beat_times:
        return None, None

    candidates = [
        (idx, beat)
        for idx, beat in enumerate(beat_times)
        if min_end - 1e-6 <= beat <= max_end + 1e-6
    ]
    if not candidates:
        return None, None

    best_idx, best_time = min(candidates, key=lambda item: abs(item[1] - desired_end))
    return best_time, best_idx


def _snap_to_frame(value: float, interval: float, max_value: float) -> float:
    snapped = round(value / interval) * interval
    if snapped > max_value:
        snapped = max_value
    return max(snapped, 0.0)


def _unique_floats(values: Iterable[float], tolerance: float = 1e-4) -> list[float]:
    unique: list[float] = []
    for value in values:
        if not unique or abs(unique[-1] - value) > tolerance:
            unique.append(value)
    return unique

