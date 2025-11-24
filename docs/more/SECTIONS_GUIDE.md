# Song Sections Analysis Guide

This guide covers everything you need to know about analyzing song sections using the Audjust API, from environment setup to implementation.

---

## Part 1: Environment Configuration

### Required Environment Variables for Audjust Integration

To enable song section analysis using the Audjust API, you need to configure the following environment variables in your `backend/.env` file:

### Audjust API Configuration

```bash
# Audjust API Base URL (production endpoint)
AUDJUST_BASE_URL=https://api.audjust.com

# Your Audjust API Key
# Get this from: https://www.audjust.com/console
AUDJUST_API_KEY=your_api_key_here

# API endpoints (default values, usually don't need to change)
AUDJUST_UPLOAD_PATH=/upload
AUDJUST_STRUCTURE_PATH=/structure
AUDJUST_TIMEOUT_SEC=30.0
```

### How to Get an Audjust API Key

1. Visit the [Audjust API Console](https://www.audjust.com/console)
2. Sign up or log in
3. Generate a new API key
4. Copy the key and add it to your `.env` file

### Testing Your Configuration

After setting up the environment variables, restart your backend server and check the logs when uploading a song for analysis. You should see:

```text
INFO: Checking Audjust configuration: base_url=https://api.audjust.com, api_key=***
INFO: Audjust is configured, attempting to fetch structure segments for song <song_id>
INFO: fetch_structure_segments called with audio_path=<path>
INFO: Calling Audjust structure API: url=https://api.audjust.com/structure, payload={'sourceFileUrl': '...'}
INFO: Fetched N sections from Audjust for song <song_id>
```

### Troubleshooting

**If you see:** `WARNING: Audjust API not configured`

- Check that both `AUDJUST_BASE_URL` and `AUDJUST_API_KEY` are set in your `.env` file
- Verify there are no extra spaces or quotes in the values
- Make sure the `.env` file is in the `backend/` directory

**If the API call fails:**

- Check that your API key is valid
- Verify you have sufficient API credits
- Check the logs for specific error messages

**If no logs appear at all:**

- Check that your log level is set to `info` or `debug`: `API_LOG_LEVEL=info`
- Ensure the song analysis job is actually running (check Redis/RQ worker logs)

---

## Part 2: Understanding Audjust API Output

### What Audjust Provides

The Audjust API does **not** directly give you semantic section names like "chorus" or "verse". Instead, it provides:

* **Segments with similarity labels**, not semantic names
* You can use those labels + some audio heuristics (energy, repetition, position) to infer **"this is probably a chorus / verse / intro / bridge / outro"**
* And you should have a **graceful fallback** for weird/edge-case song forms

### Audjust API Response Format

From their structure example, the API returns:

```json
{
  "sections": [
    { "startMs": 0, "endMs": 15452, "label": 171 },
    { "startMs": 15452, "endMs": 23161, "label": 264 },
    { "startMs": 23161, "endMs": 44164, "label": 505 },
    ...
  ]
}
```

They explicitly say:

> The label values will be between 0 and 1000 and can be used to identify similar sections in the song. When the numbers are closer together, the sections are more similar in terms of audio characteristics. ([audjust.com][1])

So those **labels are cluster IDs / similarity codes**, *not* "chorus / verse" names. Your job is to:

1. Group segments by label (or by label similarity)
2. See which patterns repeat, where, and with what energy
3. Map patterns → human-friendly section types

### Core Labeling Strategy

At a high level:

* **Chorus**
  * Most repeated section type by *occurrences* or *total time*
  * Often higher **energy/loudness** and **density**
  * Often appears after an initial verse or build, then repeats

* **Verse**
  * Another repeated group distinct from chorus
  * Usually 2–3 copies, often preceding choruses

* **Intro / Outro**
  * At very start / end
  * Often **unique** labels and shorter length

* **Bridge / Drop / Other**
  * Unique or low-frequency label
  * In the middle or 2/3 through the song
  * Different harmony/texture than verse/chorus

And: if the heuristics aren't confident, you just fall back to **A/B/C sections** or "Section 1, Section 2…" – which is still usable for your video prompts.

### Practical Pipeline with Audjust

Assume you have:

* Audjust `sections[]` with `(startMs, endMs, label)` ([audjust.com][1])
* Optional extra features per frame/segment (from your own analysis):
  * RMS loudness / energy
  * Spectral centroid / brightness
  * Vocal activity (from vocal stem or ASR)
  * Lyrics alignment

#### Step 1: Normalize sections

For each raw section:

```python
duration = (endMs - startMs)/1000
idx = index in list
```

Build:

```python
SectionSeg = {
  "idx": i,
  "start": start_sec,
  "end": end_sec,
  "duration": duration,
  "label": label,
  "center_time": (start_sec + end_sec) / 2,
  # plus any features you compute:
  "mean_energy": ...,
  "has_vocals": ...,
}
```

#### Step 2: Group by label / similarity

Group segments by `label`:

```python
groups = { label: [segments_with_that_label] }
```

For each group:
* `occurrence_count`
* `total_duration`
* `mean_energy`

You can also treat labels "close" in value as similar if you want, since Audjust says closer label numbers = more similar audio ([audjust.com][1]), but starting with strict equality is fine.

#### Step 3: Pick a **chorus candidate**

Heuristic:

1. Candidate labels must appear **≥ 2 times**
2. Exclude groups whose first instance starts too early (e.g., first 10–15 seconds) – usually not the chorus
3. Score each candidate label:

```python
score = (
  w_occ * normalized_occurrence_count +
  w_dur * normalized_total_duration +
  w_energy * normalized_mean_energy
)
```

4. The highest scoring group → **chorus**

This aligns with MIR research that chorus regions are typically the most repeated, high-energy passages. ([ACM Digital Library][2])

If there is **no label with ≥ 2 occurrences** → maybe the song is through-composed / strophic / ambient. In that case, skip chorus labeling and just keep neutral labels (A/B/C). ([Wikipedia][3])

#### Step 4: Pick **verse** candidates

Once you have `chorus_label`:

* Look for another label (or set of labels) that:
  * Appears ≥ 2 times
  * Often occurs **before** the first chorus instance
  * Has lower or medium energy relative to the chorus

That cluster becomes **verse**.

If there's still ambiguity, you can even tag them as `section_type = "verse_like"` internally and only display "Verse" in the UI when you're above some confidence threshold.

#### Step 5: Intro & Outro

Given the labeled verse/chorus clusters:

* `intro`:
  * First segment(s) **before** first verse/chorus
  * Only if they total under some length threshold, e.g., `< 0.20 * song_length`
  * If there's just one short, unique segment at the top, very likely intro

* `outro`:
  * Last segment(s) **after** last chorus/verse
  * If unique and/or with fading energy, label as outro

If none of that fits, just mark them as "Section 1 / Section N" in the UI and use "opening shot / ending shot" semantics in your prompt builder (which is often enough for your music video context).

#### Step 6: Bridge / middle special sections (optional)

Look in the **middle third** of the track:

* Unique label (occurs once)
* Surrounded by chorus/verse instances
* Possibly changed harmony or timbre (if you have harmonic features)

This is your **bridge / drop / solo / breakdown** candidate.

You don't have to get this perfectly right. For video prompts, it can just be "experimental middle section where visuals take a twist."

#### Step 7: Confidence and fallbacks

You definitely don't want to hallucinate full pop structure on ambient / jazz / classical pieces. So keep a simple "confidence" estimate per label:

* If:
  * chorus candidate score is high,
  * plus at least 2 distinct groups repeat,
    then you show **Verse/Chorus** labels

* Else:
  * Just label them generically: A, B, C, D… and in prompts talk about:
    * "first main motif",
    * "repeating hook section",
    * "final resolving section", etc.

That still gives your visual planner enough structure to work with.

### You don't *have* to force canonical labels

Given your use case (AI music videos), there are two levels of naming:

1. **Internal, soft labels** for your engine:
   * chorus_like, verse_like, intro_like, bridge_like, outro_like, other

2. **User-facing labels**:
   * "Chorus", "Verse 1", "Verse 2" when confidence > threshold
   * Otherwise "Section A, B, C" or "Part 1, Part 2, Part 3"

Your prompt builder doesn't actually *need* to know "this is a textbook bridge," it just needs:

* Whether the section is:
  * **repeated and hook-y**,
  * **narrative / evolving**,
  * **intro**, **ending**, or **detour**

You can deduce that robustly from **repetition patterns + position + energy** even if theoretical labels are fuzzy.

### Alternatives / Complements

If you want more out-of-the-box labeling:

* **Music.AI "song sections" workflow** advertises directly labeled intro/verse/chorus/etc with lyrics alignment. ([Music AI][4])
* **Moises.ai "Song Parts"** also auto-detects sections for practice (they don't expose an open API AFAIK, but conceptually similar). ([Moises][5])
* Recent research like **MuSFA** explicitly predicts verse/chorus labels from audio using supervised training. ([arXiv][6])

These confirm that what you're trying to do is essentially Music Structure Analysis (MSA) with semantic labels, not just boundaries. ([PLOS][7])

### What to do *for VibeCraft specifically*

For your current stack & timeline, implement:

1. **Boundary + cluster from Audjust** (you get that "for free"). ([audjust.com][1])
2. **Compute basic features per segment** (RMS energy, maybe vocal activity from your lyrics engine)
3. **Heuristic labeler**:
   * Determine `chorus_like`, `verse_like`, `intro_like`, `outro_like`, `bridge_like`, `other` using the rules above
4. **Expose both**:
   * `section.type_soft` (those heuristics)
   * `section.label_raw` (Audjust numeric label)
5. In your UI and prompts:
   * Use human names when confident,
   * Otherwise fall back to neutral "Section A/B/C" and rely on "opening / middle / climax / ending" in the prompt language

---

## Part 3: Python Implementation

Here's a practical Python helper you can drop into your backend.

### Data Structures

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

### Helper: Normalize Values

```python
def _normalize(values: List[float]) -> List[float]:
    if not values:
        return []
    vmin, vmax = min(values), max(values)
    if math.isclose(vmin, vmax):
        return [0.5 for _ in values]
    return [(v - vmin) / (vmax - vmin) for v in values]
```

### Core Function: `infer_section_types`

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

        # We'll assign display names later after we know how many verses/choruses, etc.
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

### Usage in Your Pipeline

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

* You can show: "Verse 1, Chorus 1, Bridge, Outro"
* You can still introspect: "this is `chorus_like` with confidence 0.7"
* If the heuristics fail (no repeated labels), you'll still get sensible "Section A, Section B, …" labels.

---

## References

[1]: https://www.audjust.com/api/examples/find-chorus-verse-sections-of-song "Audjust - Break Down a Song into Sections like Chorus and Verse"
[2]: https://dl.acm.org/doi/10.1145/1178723.1178733?utm_source=chatgpt.com "Music structure analysis by finding repeated parts"
[3]: https://en.wikipedia.org/wiki/Strophic_form?utm_source=chatgpt.com "Strophic form"
[4]: https://music.ai/workflows/transcription-and-alignment/song-sections/?utm_source=chatgpt.com "How To Segment Song Sections And Align Lyrics"
[5]: https://moises.ai/features/song-parts/?utm_source=chatgpt.com "Transform your Music Practice with our Song Parts feature"
[6]: https://arxiv.org/abs/2211.15787?utm_source=chatgpt.com "MuSFA: Improving Music Structural Function Analysis with Partially Labeled Data"
[7]: https://journals.plos.org/plosone/article/file?id=10.1371%2Fjournal.pone.0312608&type=printable&utm_source=chatgpt.com "A music structure analysis method based on beat feature and ..."

