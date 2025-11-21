Nice, let’s turn all that theory into an actual **Python helper** you can drop into your backend.

We’ll write a function:

```python
infer_section_types(audjust_sections, energy_per_section, vocals_per_section)
```

that returns a list of rich `Section` objects with fields like:

* `type_soft` → `"chorus_like"`, `"verse_like"`, `"intro_like"`, `"outro_like"`, `"bridge_like"`, `"other"`
* `display_name` → `"Chorus 1"`, `"Verse 2"`, etc.
* `confidence` → 0–1

You can later map `type_soft` to your canonical names in prompts/UI.

---

## 1. Data structures

```python
from dataclasses import dataclass
from typing import List, Literal, Optional, Dict
import math
from collections import defaultdict, Counter

SectionSoftType = Literal[
    "intro_like",
    "verse_like",
    "chorus_like",
    "bridge_like",
    "outro_like",
    "other",
]

@dataclass
class Section:
    id: str
    index: int
    start_sec: float
    end_sec: float
    duration_sec: float
    label_raw: int  # from Audjust
    type_soft: SectionSoftType
    confidence: float
    display_name: str
```

---

## 2. Helper: normalize values

```python
def _normalize(values: List[float]) -> List[float]:
    if not values:
        return []
    vmin, vmax = min(values), max(values)
    if math.isclose(vmin, vmax):
        return [0.5 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]
```

---

## 3. Core function: `infer_section_types`

```python
def infer_section_types(
    audjust_sections: List[Dict],
    energy_per_section: List[float],
    vocals_per_section: Optional[List[float]] = None,
) -> List[Section]:
    """
    Infer soft section types (intro/verse/chorus/bridge/outro/other) from:
      - Audjust structure segments: [{'startMs', 'endMs', 'label'}, ...]
      - Per-section average energy (e.g. RMS)
      - Optional per-section vocal activity (0.0–1.0)

    Returns a list of Section objects with type_soft + display_name.
    """

    n = len(audjust_sections)
    if n == 0:
        return []

    if len(energy_per_section) != n:
        raise ValueError("energy_per_section length must match audjust_sections length")
    if vocals_per_section is not None and len(vocals_per_section) != n:
        raise ValueError("vocals_per_section length must match audjust_sections length")

    # ---- Step 1: construct basic sections with durations & positions ----
    sections_raw = []
    total_duration_sec = 0.0
    for i, s in enumerate(audjust_sections):
        start_sec = s["startMs"] / 1000.0
        end_sec = s["endMs"] / 1000.0
        dur = max(0.0, end_sec - start_sec)
        total_duration_sec = max(total_duration_sec, end_sec)
        sections_raw.append(
            {
                "index": i,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": dur,
                "label": int(s["label"]),
                "energy": float(energy_per_section[i]),
                "vocals": float(vocals_per_section[i]) if vocals_per_section is not None else None,
            }
        )

    # ---- Step 2: group by label ----
    by_label: Dict[int, List[dict]] = defaultdict(list)
    for seg in sections_raw:
        by_label[seg["label"]].append(seg)

    # label stats
    label_stats = []
    for label, segs in by_label.items():
        occ = len(segs)
        total_dur = sum(s["duration_sec"] for s in segs)
        mean_energy = sum(s["energy"] for s in segs) / occ
        first_start = min(s["start_sec"] for s in segs)
        label_stats.append(
            {
                "label": label,
                "occ": occ,
                "total_dur": total_dur,
                "mean_energy": mean_energy,
                "first_start": first_start,
            }
        )

    # ---- Step 3: find chorus candidate (most repeated & energetic) ----
    # Only consider labels that occur at least twice
    chorus_candidates = [ls for ls in label_stats if ls["occ"] >= 2]

    chorus_label = None
    if chorus_candidates:
        occ_norm = _normalize([c["occ"] for c in chorus_candidates])
        dur_norm = _normalize([c["total_dur"] for c in chorus_candidates])
        energy_norm = _normalize([c["mean_energy"] for c in chorus_candidates])

        best_score = -1.0
        best_label = None
        for i, c in enumerate(chorus_candidates):
            # Penalize sections whose first start is extremely early (< 10s)
            early_penalty = 0.0
            if c["first_start"] < 10.0:
                early_penalty = 0.3

            score = (
                0.5 * occ_norm[i] +
                0.2 * dur_norm[i] +
                0.3 * energy_norm[i] -
                early_penalty
            )
            if score > best_score:
                best_score = score
                best_label = c["label"]

        # only accept if the score is reasonably high and occ >= 2
        if best_score > 0.2:
            chorus_label = best_label

    # ---- Step 4: find verse-like labels ----
    # verse-like: repeated labels that are not chorus
    verse_labels = set()
    for ls in label_stats:
        if ls["label"] == chorus_label:
            continue
        if ls["occ"] >= 2:
            verse_labels.add(ls["label"])

    # ---- Step 5: classify each segment with soft type ----
    sections_with_type: List[Section] = []
    for seg in sections_raw:
        idx = seg["index"]
        label = seg["label"]
        center = (seg["start_sec"] + seg["end_sec"]) / 2.0
        pos_ratio = center / max(1e-6, total_duration_sec)
        base_type: SectionSoftType = "other"
        conf = 0.4  # baseline

        # chorus-like
        if chorus_label is not None and label == chorus_label:
            base_type = "chorus_like"
            conf = 0.7

        # verse-like
        elif label in verse_labels:
            base_type = "verse_like"
            conf = 0.6

        # intro-like: early in song & not chorus
        if base_type == "other" and pos_ratio < 0.2:
            base_type = "intro_like"
            conf = 0.6

        # outro-like: late in song & not chorus
        if base_type == "other" and pos_ratio > 0.8:
            base_type = "outro_like"
            conf = 0.6

        # bridge-like: unique label in middle region
        if (
            base_type == "other"
            and 0.3 < pos_ratio < 0.8
            and next(ls["occ"] for ls in label_stats if ls["label"] == label) == 1
        ):
            base_type = "bridge_like"
            conf = 0.55

        # if nothing fit, leave as "other" with low-ish conf
        # you could also bump confidence using energy/vocals if you want.

        # We’ll assign display names later after we know how many verses/choruses, etc.
        sections_with_type.append(
            Section(
                id=f"sec_{idx}",
                index=idx,
                start_sec=seg["start_sec"],
                end_sec=seg["end_sec"],
                duration_sec=seg["duration_sec"],
                label_raw=label,
                type_soft=base_type,
                confidence=conf,
                display_name="",  # fill after counting
            )
        )

    # ---- Step 6: assign display names (Verse 1, Chorus 2, etc.) ----
    counters: Dict[SectionSoftType, int] = Counter()  # type: ignore
    for sec in sections_with_type:
        counters[sec.type_soft] += 1
        ordinal = counters[sec.type_soft]

        if sec.type_soft == "chorus_like":
            sec.display_name = f"Chorus {ordinal}"
        elif sec.type_soft == "verse_like":
            sec.display_name = f"Verse {ordinal}"
        elif sec.type_soft == "intro_like":
            sec.display_name = "Intro" if ordinal == 1 else f"Intro {ordinal}"
        elif sec.type_soft == "outro_like":
            sec.display_name = "Outro" if ordinal == 1 else f"Outro {ordinal}"
        elif sec.type_soft == "bridge_like":
            sec.display_name = "Bridge" if ordinal == 1 else f"Bridge {ordinal}"
        else:
            # fallback for "other": Section A/B/C...
            letter = chr(ord("A") + sec.index)
            sec.display_name = f"Section {letter}"

    # Sort back in chronological order
    sections_with_type.sort(key=lambda s: s.start_sec)

    return sections_with_type
```

---

## 4. How you’d use this in your pipeline

After you call Audjust and compute per-section energy:

```python
audjust_sections = response["sections"]  # from their API
energy_per_section = compute_energy_per_section(...)
vocals_per_section = compute_vocal_activity_per_section(...)

sections = infer_section_types(
    audjust_sections=audjust_sections,
    energy_per_section=energy_per_section,
    vocals_per_section=vocals_per_section,
)

# Then build your SongAnalysis object
song_analysis.sections = [
    {
        "id": s.id,
        "index": s.index,
        "startSec": s.start_sec,
        "endSec": s.end_sec,
        "durationSec": s.duration_sec,
        "rawLabel": s.label_raw,
        "typeSoft": s.type_soft,
        "displayName": s.display_name,
        "confidence": s.confidence,
    }
    for s in sections
]
```

This gives your **prompt builder** and **Song Profile UI** something much richer than raw cluster labels:

* You can show: “Verse 1, Chorus 1, Bridge, Outro”
* You can still introspect: “this is `chorus_like` with confidence 0.7”
* If the heuristics fail (no repeated labels), you’ll still get sensible “Section A, Section B, …” labels.
