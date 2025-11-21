from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional


SectionSoftType = Literal[
    "intro_like",
    "verse_like",
    "chorus_like",
    "bridge_like",
    "outro_like",
    "other",
]


@dataclass(slots=True)
class SectionInference:
    id: str
    index: int
    start_sec: float
    end_sec: float
    duration_sec: float
    label_raw: int
    type_soft: SectionSoftType
    confidence: float
    display_name: str


def _normalize(values: Iterable[float]) -> List[float]:
    values = list(values)
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if abs(vmin - vmax) < 1e-9:
        return [0.5 for _ in values]
    return [(value - vmin) / (vmax - vmin) for value in values]


def infer_section_types(
    audjust_sections: List[dict],
    energy_per_section: List[float],
    vocals_per_section: Optional[List[float]] = None,
) -> List[SectionInference]:
    """
    Infer soft section types from Audjust segments and per-segment features.

    Args:
        audjust_sections: List of dicts with at least startMs, endMs, label.
        energy_per_section: Average energy value per section, aligned with audjust_sections.
        vocals_per_section: Optional vocal activity metrics per section.
    """

    n = len(audjust_sections)
    if n == 0:
        return []

    if len(energy_per_section) != n:
        raise ValueError("energy_per_section length must match audjust_sections length")
    if vocals_per_section is not None and len(vocals_per_section) != n:
        raise ValueError("vocals_per_section length must match audjust_sections length")

    # Step 1: Basic section payload
    sections_raw: List[dict] = []
    total_duration_sec = 0.0
    for i, section in enumerate(audjust_sections):
        start_ms = float(section.get("startMs", 0))
        end_ms = float(section.get("endMs", start_ms))
        label = int(section.get("label", -1))
        start_sec = max(0.0, start_ms / 1000.0)
        end_sec = max(start_sec, end_ms / 1000.0)
        duration_sec = max(0.0, end_sec - start_sec)
        total_duration_sec = max(total_duration_sec, end_sec)
        sections_raw.append(
            {
                "index": i,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": duration_sec,
                "label": label,
                "energy": float(energy_per_section[i]),
                "vocals": (
                    float(vocals_per_section[i]) if vocals_per_section is not None else None
                ),
            }
        )

    if total_duration_sec <= 0:
        total_duration_sec = sum(section["duration_sec"] for section in sections_raw)

    # Step 2: stats per label
    by_label: Dict[int, List[dict]] = defaultdict(list)
    for seg in sections_raw:
        by_label[seg["label"]].append(seg)

    label_stats = []
    for label, slices in by_label.items():
        occ = len(slices)
        total_dur = sum(s["duration_sec"] for s in slices)
        mean_energy = (
            sum(s["energy"] for s in slices) / occ if occ else 0.0
        )
        first_start = min(s["start_sec"] for s in slices)
        label_stats.append(
            {
                "label": label,
                "occ": occ,
                "total_dur": total_dur,
                "mean_energy": mean_energy,
                "first_start": first_start,
            }
        )

    # Step 3: chorus label heuristics
    chorus_label = None
    chorus_candidates = [stat for stat in label_stats if stat["occ"] >= 2]
    if chorus_candidates:
        occ_norm = _normalize(stat["occ"] for stat in chorus_candidates)
        dur_norm = _normalize(stat["total_dur"] for stat in chorus_candidates)
        energy_norm = _normalize(stat["mean_energy"] for stat in chorus_candidates)

        best_score = -1.0
        best_label = None
        for idx, stat in enumerate(chorus_candidates):
            early_penalty = 0.3 if stat["first_start"] < 10.0 else 0.0
            score = (
                0.5 * occ_norm[idx]
                + 0.2 * dur_norm[idx]
                + 0.3 * energy_norm[idx]
                - early_penalty
            )
            if score > best_score:
                best_score = score
                best_label = stat["label"]

        if best_score > 0.2:
            chorus_label = best_label

    # Step 4: verse-like label set
    verse_labels = {
        stat["label"]
        for stat in label_stats
        if stat["label"] != chorus_label and stat["occ"] >= 2
    }

    # Step 5: section typing
    inferred_sections: List[SectionInference] = []
    for segment in sections_raw:
        idx = segment["index"]
        label = segment["label"]
        center = (segment["start_sec"] + segment["end_sec"]) / 2.0
        pos_ratio = center / max(total_duration_sec, 1e-6)
        base_type: SectionSoftType = "other"
        conf = 0.45

        if chorus_label is not None and label == chorus_label:
            base_type = "chorus_like"
            conf = 0.7
        elif label in verse_labels:
            base_type = "verse_like"
            conf = 0.6
        elif pos_ratio < 0.2:
            base_type = "intro_like"
            conf = 0.6
        elif pos_ratio > 0.8:
            base_type = "outro_like"
            conf = 0.6
        elif 0.3 < pos_ratio < 0.8 and next(
            stat["occ"] for stat in label_stats if stat["label"] == label
        ) == 1:
            base_type = "bridge_like"
            conf = 0.55

        inferred_sections.append(
            SectionInference(
                id=f"sec-{idx}",
                index=idx,
                start_sec=segment["start_sec"],
                end_sec=segment["end_sec"],
                duration_sec=segment["duration_sec"],
                label_raw=label,
                type_soft=base_type,
                confidence=conf,
                display_name="",  # filled later
            )
        )

    # Step 6: assign display names
    counters: Dict[SectionSoftType, int] = Counter()
    for section in inferred_sections:
        counters[section.type_soft] += 1
        ordinal = counters[section.type_soft]
        if section.type_soft == "chorus_like":
            section.display_name = f"Chorus {ordinal}"
        elif section.type_soft == "verse_like":
            section.display_name = f"Verse {ordinal}"
        elif section.type_soft == "intro_like":
            section.display_name = "Intro" if ordinal == 1 else f"Intro {ordinal}"
        elif section.type_soft == "outro_like":
            section.display_name = "Outro" if ordinal == 1 else f"Outro {ordinal}"
        elif section.type_soft == "bridge_like":
            section.display_name = "Bridge" if ordinal == 1 else f"Bridge {ordinal}"
        else:
            section.display_name = f"Section {chr(ord('A') + section.index)}"

    inferred_sections.sort(key=lambda s: s.start_sec)
    return inferred_sections

