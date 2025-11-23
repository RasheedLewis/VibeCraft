You're right to zoom in on this, because "what is a chorus vs verse vs bridge?" is *not*
something the Audjust API will hand you for free.

Short version:

* Audjust gives you **segments + similarity labels**, not semantic names.
* You can use those labels + some audio heuristics (energy, repetition, position) to infer
  **"this is probably a chorus / verse / intro / bridge / outro"**.
* And you should have a **graceful fallback** for weird/edge-case song forms.

Let’s walk through a concrete strategy you can actually implement.

---

## 1. What Audjust is giving you

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

> The label values will be between 0 and 1000 and can be used to identify similar sections in
> the song. When the numbers are closer together, the sections are more similar in terms of
> audio characteristics. ([audjust.com][1])

So those **labels are cluster IDs / similarity codes**, *not* “chorus / verse” names. Your job is to:

1. Group segments by label (or by label similarity).
2. See which patterns repeat, where, and with what energy.
3. Map patterns → human-friendly section types.

---

## 2. Core idea for labeling

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

And: if the heuristics aren't confident, you just fall back to **A/B/C sections** or
"Section 1, Section 2…" – which is still usable for your video prompts.

---

## 3. Practical pipeline with Audjust

Assume you have:

* Audjust `sections[]` with `(startMs, endMs, label)` ([audjust.com][1])
* Optional extra features per frame/segment (from your own analysis):

  * RMS loudness / energy
  * Spectral centroid / brightness
  * Vocal activity (from vocal stem or ASR)
  * Lyrics alignment

### Step 1: Normalize sections

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

### Step 2: Group by label / similarity

Group segments by `label`:

```python
groups = { label: [segments_with_that_label] }
```

For each group:

* `occurrence_count`
* `total_duration`
* `mean_energy`

You can also treat labels "close" in value as similar if you want, since Audjust says closer
label numbers = more similar audio ([audjust.com][1]), but starting with strict equality is
fine.

### Step 3: Pick a **chorus candidate**

Heuristic:

1. Candidate labels must appear **≥ 2 times**.
2. Exclude groups whose first instance starts too early (e.g., first 10–15 seconds) – usually not
   the chorus.
3. Score each candidate label:

```python
score = (
  w_occ * normalized_occurrence_count +
  w_dur * normalized_total_duration +
  w_energy * normalized_mean_energy
)
```

1. The highest scoring group → **chorus**.

This aligns with MIR research that chorus regions are typically the most repeated,
high-energy passages. ([ACM Digital Library][2])

If there is **no label with ≥ 2 occurrences** → maybe the song is through-composed /
strophic / ambient. In that case, skip chorus labeling and just keep neutral labels (A/B/C).
([Wikipedia][3])

### Step 4: Pick **verse** candidates

Once you have `chorus_label`:

* Look for another label (or set of labels) that:

  * Appears ≥ 2 times
  * Often occurs **before** the first chorus instance
  * Has lower or medium energy relative to the chorus

That cluster becomes **verse**.

If there's still ambiguity, you can even tag them as `section_type = "verse_like"` internally
and only display "Verse" in the UI when you're above some confidence threshold.

### Step 5: Intro & Outro

Given the labeled verse/chorus clusters:

* `intro`:

  * First segment(s) **before** first verse/chorus
  * Only if they total under some length threshold, e.g., `< 0.20 * song_length`
  * If there’s just one short, unique segment at the top, very likely intro.

* `outro`:

  * Last segment(s) **after** last chorus/verse
  * If unique and/or with fading energy, label as outro.

If none of that fits, just mark them as "Section 1 / Section N" in the UI and use
"opening shot / ending shot" semantics in your prompt builder (which is often enough for your
music video context).

### Step 6: Bridge / middle special sections (optional)

Look in the **middle third** of the track:

* Unique label (occurs once)
* Surrounded by chorus/verse instances
* Possibly changed harmony or timbre (if you have harmonic features)

This is your **bridge / drop / solo / breakdown** candidate.

You don't have to get this perfectly right. For video prompts, it can just be "experimental
middle section where visuals take a twist."

### Step 7: Confidence and fallbacks

You definitely don't want to hallucinate full pop structure on ambient / jazz / classical
pieces. So keep a simple "confidence" estimate per label:

* If:

  * chorus candidate score is high,
  * plus at least 2 distinct groups repeat,
    then you show **Verse/Chorus** labels.

* Else:

  * Just label them generically: A, B, C, D… and in prompts talk about:

    * “first main motif”,
    * “repeating hook section”,
    * “final resolving section”, etc.

That still gives your visual planner enough structure to work with.

---

## 4. You don’t *have* to force canonical labels

Given your use case (AI music videos), there are two levels of naming:

1. **Internal, soft labels** for your engine:

   * chorus_like, verse_like, intro_like, bridge_like, outro_like, other

2. **User-facing labels**:

   * “Chorus”, “Verse 1”, “Verse 2” when confidence > threshold
   * Otherwise “Section A, B, C” or “Part 1, Part 2, Part 3”

Your prompt builder doesn’t actually *need* to know “this is a textbook bridge,” it just needs:

* Whether the section is:

  * **repeated and hook-y**,
  * **narrative / evolving**,
  * **intro**, **ending**, or **detour**.

You can deduce that robustly from **repetition patterns + position + energy** even if
theoretical labels are fuzzy.

---

## 5. Alternatives / complements

If you want more out-of-the-box labeling:

* **Music.AI "song sections" workflow** advertises directly labeled intro/verse/chorus/etc
  with lyrics alignment. ([Music AI][4])
* **Moises.ai "Song Parts"** also auto-detects sections for practice (they don't expose an
  open API AFAIK, but conceptually similar). ([Moises][5])
* Recent research like **MuSFA** explicitly predicts verse/chorus labels from audio using
  supervised training. ([arXiv][6])

These confirm that what you're trying to do is essentially Music Structure Analysis (MSA) with
semantic labels, not just boundaries. ([PLOS][7])

---

## 6. What I’d do *for VibeCraft specifically*

For your current stack & timeline, I’d implement:

1. **Boundary + cluster from Audjust** (you get that “for free”). ([audjust.com][1])
2. **Compute basic features per segment** (RMS energy, maybe vocal activity from your lyrics engine).
3. **Heuristic labeler**:

   * Determine `chorus_like`, `verse_like`, `intro_like`, `outro_like`, `bridge_like`, `other`
     using the rules above.
4. **Expose both**:

   * `section.type_soft` (those heuristics)
   * `section.label_raw` (Audjust numeric label)
5. In your UI and prompts:

   * Use human names when confident,
   * Otherwise fall back to neutral "Section A/B/C" and rely on "opening / middle / climax /
     ending" in the prompt language.

[1]: https://www.audjust.com/api/examples/find-chorus-verse-sections-of-song "Audjust - Break Down a Song into Sections like Chorus and Verse"
[2]: https://dl.acm.org/doi/10.1145/1178723.1178733?utm_source=chatgpt.com "Music structure analysis by finding repeated parts"
[3]: https://en.wikipedia.org/wiki/Strophic_form?utm_source=chatgpt.com "Strophic form"
[4]: https://music.ai/workflows/transcription-and-alignment/song-sections/?utm_source=chatgpt.com "How To Segment Song Sections And Align Lyrics"
[5]: https://moises.ai/features/song-parts/?utm_source=chatgpt.com "Transform your Music Practice with our Song Parts feature"
[6]: https://arxiv.org/abs/2211.15787?utm_source=chatgpt.com "MuSFA: Improving Music Structural Function Analysis with Partially Labeled Data"
[7]: https://journals.plos.org/plosone/article/file?id=10.1371%2Fjournal.pone.0312608&type=printable&utm_source=chatgpt.com "A music structure analysis method based on beat feature and ..."
