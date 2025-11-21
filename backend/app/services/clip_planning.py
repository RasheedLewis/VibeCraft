from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from typing import Iterable, List, Optional
from uuid import UUID

from sqlmodel import select

from app.core.database import session_scope
from app.exceptions import ClipPlanningError
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
    tolerance = 1e-3
    duration_tolerance = max(frame_interval, 1e-3)
    raw_beats = getattr(analysis, "beat_times", []) or []
    beat_times = sorted(_unique_floats(raw_beats))
    beat_times = [beat for beat in beat_times if -tolerance <= beat <= duration_sec + tolerance]
    beat_times = [beat for beat in beat_times if 0.0 <= beat <= duration_sec]

    if not beat_times:
        return _plan_without_beats(
            duration_sec=duration_sec,
            clip_count=clip_count,
            min_clip_sec=min_clip_sec,
            max_clip_sec=max_clip_sec,
            generator_fps=generator_fps,
        )

    plans: list[ClipPlan] = []
    current_start = 0.0
    start_beat_index: Optional[int] = _find_beat_index_at_time(beat_times, current_start)
    beat_search_idx = bisect_right(beat_times, current_start + tolerance)

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

        if is_last_clip:
            last_duration = remaining_time
            if last_duration > max_clip_sec + duration_tolerance:
                raise ClipPlanningError(
                    f"Planned clip {index} exceeds max duration ({last_duration:.2f}s > {max_clip_sec}s)"
                )
            min_end = current_start + min_possible
            max_end = duration_sec
            raw_end = duration_sec
            end_beat_index = _find_beat_index_at_time(beat_times, raw_end)
        else:
            max_allowable_for_remaining = (
                remaining_time - min_remaining_needed if trailing_clips > 0 else remaining_time
            )
            max_possible = min(max_clip_sec, max_allowable_for_remaining)

            if max_possible < min_possible - 1e-3:
                raise ClipPlanningError("Not enough duration remaining to satisfy clip constraints")

            min_end = current_start + min_possible
            max_end = current_start + max_possible
            max_end = min(max_end, duration_sec)

            target_length = remaining_time / clips_left
            target_length = max(min(target_length, max_possible), min_possible)
            target_end = current_start + target_length

            candidate_start = bisect_left(beat_times, min_end - tolerance, lo=beat_search_idx)
            candidate_end = bisect_right(beat_times, max_end + tolerance, lo=beat_search_idx)

            raw_end: float
            end_beat_index = None

            if candidate_start < candidate_end:
                candidate_range = range(candidate_start, candidate_end)
                best_index = min(
                    candidate_range,
                    key=lambda idx: abs(beat_times[idx] - target_end),
                )
                raw_end = beat_times[best_index]
                end_beat_index = best_index
            else:
                raw_end = target_end

            raw_end = min(max(raw_end, min_end), max_end)

        snapped_end = _snap_to_frame(raw_end, frame_interval, duration_sec)

        if snapped_end < min_end - 1e-3:
            snapped_end = _snap_to_frame(min_end, frame_interval, duration_sec)
            if snapped_end < min_end - 1e-3:
                snapped_end = min(min_end, duration_sec)

        if not is_last_clip and snapped_end > max_end + 1e-3:
            snapped_end = max_end
            end_beat_index = None

        if is_last_clip:
            snapped_end = duration_sec
        else:
            remaining_after = duration_sec - snapped_end

            if remaining_after > max_remaining_allowed + 1e-3:
                target_end = duration_sec - max_remaining_allowed
                snapped_end = _snap_to_frame(target_end, frame_interval, duration_sec)
                if snapped_end < min_end:
                    snapped_end = min(_snap_to_frame(min_end, frame_interval, duration_sec), max_end)
                if snapped_end > max_end:
                    snapped_end = max_end
                remaining_after = duration_sec - snapped_end
                end_beat_index = None

            if remaining_after < min_remaining_needed - 1e-3:
                raise ClipPlanningError(
                    "Unable to balance clip durations within constraints. "
                    "Consider increasing clip_count or adjusting clip duration bounds."
                )

        duration = max(snapped_end - current_start, frame_interval)
        if not is_last_clip and duration > (max_end - current_start) + duration_tolerance:
            raise ClipPlanningError(
                f"Planned clip {index} exceeds max duration ({duration:.2f}s > {(max_end - current_start):.2f}s)"
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
        beat_search_idx = bisect_right(beat_times, current_start + tolerance, lo=beat_search_idx)

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


def _find_beat_index_at_time(
    beat_times: list[float],
    time: float,
    tolerance: float = 1e-3,
) -> Optional[int]:
    if not beat_times:
        return None

    idx = bisect_left(beat_times, time - tolerance)
    if idx < len(beat_times) and abs(beat_times[idx] - time) <= tolerance:
        return idx
    if idx > 0 and abs(beat_times[idx - 1] - time) <= tolerance:
        return idx - 1
    return None


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

