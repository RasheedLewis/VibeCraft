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
    num_frames: int


class ClipPlanningError(RuntimeError):
    """Raised when clip planning cannot generate a valid set of boundaries."""


def plan_beat_aligned_clips(
    *,
    duration_sec: float,
    analysis: SongAnalysis,
    clip_count: int,
    min_clip_sec: float = 3.0,
    max_clip_sec: float = 6.0,
    generator_fps: int = 8,
) -> List[ClipPlan]:
    """Plan clip boundaries snapped to beat grid and frame intervals.

    Args:
        duration_sec: Total song duration in seconds.
        analysis: SongAnalysis including beatTimes.
        clip_count: Desired number of clips to produce.
        min_clip_sec: Minimum allowed clip duration.
        max_clip_sec: Maximum allowed clip duration (limited by generation API).
        generator_fps: Frame rate of the generation model (defaults to 8 for Minimax Hailuo).

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

    if not beat_times:
        return _plan_without_beats(
            duration_sec=duration_sec,
            clip_count=clip_count,
            min_clip_sec=min_clip_sec,
            max_clip_sec=max_clip_sec,
            generator_fps=generator_fps,
        )

    for index in range(clip_count):
        remaining_time = duration_sec - current_start
        clips_left = clip_count - index
        is_last_clip = clips_left == 1

        if remaining_time < min_clip_sec - 1e-3:
            if plans:
                # merge remainder into previous clip
                plans[-1].end_sec = round(duration_sec, 4)
                plans[-1].duration_sec = round(duration_sec - plans[-1].start_sec, 4)
                plans[-1].num_frames = max(
                    int(round(plans[-1].duration_sec * generator_fps)),
                    1,
                )
                return plans
            raise ClipPlanningError("Song duration is shorter than minimum clip length")

        min_possible = min_clip_sec
        trailing_clips = clips_left - 1
        min_remaining_needed = min_clip_sec * max(0, trailing_clips)
        max_remaining_allowed = max_clip_sec * max(0, trailing_clips)

        max_allowable_for_remaining = (
            remaining_time - min_remaining_needed if trailing_clips > 0 else remaining_time
        )
        max_possible = min(max_clip_sec, max_allowable_for_remaining)

        if max_possible < min_possible - 1e-3:
            raise ClipPlanningError("Not enough duration remaining to satisfy clip constraints")

        desired_length = target_length if not is_last_clip else remaining_time
        desired_length = max(min(desired_length, max_possible), min_possible)

        min_end = current_start + min_possible
        max_end = current_start + max_possible

        raw_end = None
        end_beat_index: Optional[int] = None

        if not is_last_clip and beat_times:
            raw_end, end_beat_index = _pick_boundary_from_beats(
                beat_times=beat_times,
                desired_end=current_start + desired_length,
                min_end=min_end,
                max_end=max_end,
            )

        if raw_end is None:
            raw_end = current_start + desired_length
            end_beat_index = None

        raw_end = max(min(raw_end, max_end), min_end) if not is_last_clip else min(raw_end, duration_sec)
        snapped_end = _snap_to_frame(raw_end, frame_interval, duration_sec)

        if snapped_end < min_end - 1e-3:
            snapped_end = min(_snap_to_frame(min_end, frame_interval, duration_sec), duration_sec)

        if not is_last_clip and snapped_end > max_end + 1e-3:
            snapped_end = max_end

        if not is_last_clip:
            remaining_after = duration_sec - snapped_end
            if remaining_after > max_remaining_allowed + 1e-3:
                target_end = duration_sec - max_remaining_allowed
                snapped_end = _snap_to_frame(target_end, frame_interval, duration_sec)
                if snapped_end < min_end:
                    snapped_end = min_end
                if snapped_end > max_end:
                    snapped_end = max_end
                remaining_after = duration_sec - snapped_end
                end_beat_index = None
            if remaining_after < min_remaining_needed - 1e-3:
                raise ClipPlanningError(
                    "Unable to balance clip durations within constraints. "
                    "Consider increasing clip_count or adjusting clip duration bounds."
                )

        if is_last_clip:
            last_duration = duration_sec - current_start
            if last_duration > max_clip_sec + 1e-3:
                raise ClipPlanningError(
                    f"Planned clip {index} exceeds max duration ({last_duration:.2f}s > {max_clip_sec}s)"
                )
            snapped_end = duration_sec

        duration = max(snapped_end - current_start, frame_interval)
        if not is_last_clip and duration > max_possible + 1e-3:
            raise ClipPlanningError(
                f"Planned clip {index} exceeds max duration ({duration:.2f}s > {max_possible:.2f}s)"
            )

        num_frames = max(int(round(duration * generator_fps)), 1)

        plan = ClipPlan(
            index=index,
            start_sec=round(current_start, 4),
            end_sec=round(snapped_end, 4),
            duration_sec=round(duration, 4),
            start_beat_index=start_beat_index,
            end_beat_index=end_beat_index if not is_last_clip else None,
            num_frames=num_frames,
        )
        plans.append(plan)

        current_start = snapped_end
        start_beat_index = end_beat_index

    if abs(plans[-1].end_sec - duration_sec) > max(frame_interval, 0.25):
        raise ClipPlanningError(
            f"Clip plan did not cover song duration ({plans[-1].end_sec:.3f}s / {duration_sec:.3f}s)"
        )

    return plans


def _plan_without_beats(
    *,
    duration_sec: float,
    clip_count: int,
    min_clip_sec: float,
    max_clip_sec: float,
    generator_fps: int,
) -> List[ClipPlan]:
    frame_interval = 1.0 / generator_fps
    durations = [duration_sec / clip_count for _ in range(clip_count)]

    def clamp_all() -> None:
        for i, d in enumerate(durations):
            if d < min_clip_sec:
                durations[i] = min_clip_sec
            elif d > max_clip_sec:
                durations[i] = max_clip_sec

    clamp_all()

    def adjust_sum(target: float) -> None:
        total = sum(durations)
        if abs(total - target) <= 1e-6:
            return
        if total > target:
            excess = total - target
            while excess > 1e-6:
                changed = False
                share = excess / clip_count
                for i in range(clip_count):
                    reducible = durations[i] - min_clip_sec
                    if reducible <= 1e-6:
                        continue
                    delta = min(reducible, share if share > 0 else excess, frame_interval)
                    if delta <= 1e-6:
                        continue
                    durations[i] -= delta
                    excess -= delta
                    changed = True
                    if excess <= 1e-6:
                        break
                if not changed:
                    break
        else:
            deficit = target - total
            while deficit > 1e-6:
                changed = False
                share = deficit / clip_count
                for i in range(clip_count):
                    growable = max_clip_sec - durations[i]
                    if growable <= 1e-6:
                        continue
                    delta = min(growable, share if share > 0 else deficit, frame_interval)
                    if delta <= 1e-6:
                        continue
                    durations[i] += delta
                    deficit -= delta
                    changed = True
                    if deficit <= 1e-6:
                        break
                if not changed:
                    break

    adjust_sum(duration_sec)
    clamp_all()
    adjust_sum(duration_sec)

    quantized: list[float] = []
    cumulative = 0.0
    for i in range(clip_count - 1):
        desired = durations[i]
        q = max(frame_interval, round(desired / frame_interval) * frame_interval)
        q = min(q, max_clip_sec)
        if q < min_clip_sec:
            q = min_clip_sec
        if cumulative + q + min_clip_sec * (clip_count - i - 1) > duration_sec:
            q = duration_sec - min_clip_sec * (clip_count - i - 1) - cumulative
            q = max(frame_interval, q)
        quantized.append(q)
        cumulative += q

    last_duration = max(frame_interval, duration_sec - cumulative)
    quantized.append(last_duration)

    plans: list[ClipPlan] = []
    current = 0.0
    for index, q in enumerate(quantized):
        end = current + q
        plans.append(
            ClipPlan(
                index=index,
                start_sec=round(current, 4),
                end_sec=round(end, 4),
                duration_sec=round(q, 4),
                start_beat_index=None,
                end_beat_index=None,
                num_frames=max(int(round(q * generator_fps)), 1),
            )
        )
        current = end

    plans[-1].end_sec = round(duration_sec, 4)
    plans[-1].duration_sec = round(plans[-1].end_sec - plans[-1].start_sec, 4)
    plans[-1].num_frames = max(int(round(plans[-1].duration_sec * generator_fps)), 1)

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
                num_frames=plan.num_frames,
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

