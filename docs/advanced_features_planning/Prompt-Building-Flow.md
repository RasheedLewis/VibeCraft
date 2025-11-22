# Prompt Building Flow

## Overview

Prompts are constructed through a multi-stage pipeline that transforms song analysis data into optimized video generation prompts. The flow is as follows:

## Stage 1: Scene Specification Building (`clip_generation.py` → `scene_planner.py`)

**Entry Point:** `run_clip_generation_job()` in `clip_generation.py` calls `_build_scene_spec_for_clip()`

**Path Selection:**
- **Short-form videos (no sections):** Calls `build_clip_scene_spec()` which uses song-level analysis
- **Long-form videos (with sections):** Calls `build_scene_spec()` which uses section-specific analysis

**Both paths call `build_prompt()` with:**
- Song analysis data (mood, genre, BPM, mood tags)
- Mapped visual parameters (color palette, camera motion, shot pattern)
- Optional section context and lyrics

## Stage 2: Base Prompt Construction (`scene_planner.py::build_prompt()`)

**Components assembled in order:**

1. **Visual Style:** Always starts with "Abstract visual style"
   - **Note:** The `TemplateType` schema defines four options: `"abstract"`, `"environment"`, `"character"`, `"minimal"`
   - However, the `build_prompt()` function currently hardcodes "Abstract visual style" regardless of the template parameter
   - The template parameter is passed through `build_scene_spec()` and `build_clip_scene_spec()` but is not used in prompt construction
   - This is a known limitation: template types exist in the schema but are not yet implemented in the prompt building logic
2. **Color Palette:** `"{mood} color palette with {primary}, {secondary}, and {accent}"` (e.g., "vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F")
3. **Mood Description:** Top 3 mood tags joined (e.g., "energetic, danceable, upbeat mood")
4. **Genre Aesthetic:** If genre exists, adds `"{genre} aesthetic"` (e.g., "Electronic aesthetic")
5. **Shot Pattern:** `"{pattern} with {pacing} pacing"` (e.g., "medium with medium pacing")
6. **Camera Motion:** `"{type} camera motion ({speed} speed)"` (e.g., "fast_zoom camera motion (fast speed)")
7. **Section Context (if section provided):**
   - Chorus: "dynamic and energetic"
   - Verse: "steady and narrative"
   - Bridge: "transitional and atmospheric"
8. **Lyrics Motif (if available):** Extracts first 3 key words (length > 3) from first 10 words, adds `"inspired by: {word1}, {word2}, {word3}"`

**Base prompt:** All components joined with `", "` (comma-space)

## Stage 3: Rhythm Enhancement (`scene_planner.py::build_prompt()` → `prompt_enhancement.py`)

**If BPM > 0:**

1. **Motion Type Selection:** Calls `select_motion_type()` with priority:
   - Priority 1: Scene context (section type, intensity)
   - Priority 2: Mood-based selection
   - Priority 3: Mood tags analysis
   - Priority 4: Genre-based selection
   - Priority 5: BPM-based selection
   - Default: "bouncing"

2. **Rhythm Enhancement:** Calls `enhance_prompt_with_rhythm()` which:
   - Gets motion descriptor based on BPM and motion type (e.g., "bouncing motion, rhythmic pulsing, steady vertical rhythm matching the beat")
   - Appends: `", {motion_descriptor} synchronized to {bpm_int} BPM tempo, rhythmic motion matching the beat"`

## Stage 4: API-Specific Optimization (`video_generation.py::generate_section_video()` → `prompt_enhancement.py`)

**Before sending to Replicate API:**

Calls `optimize_prompt_for_api()` which tailors the prompt based on API/model:

**For Minimax Hailuo 2.3 (current default):**
- If BPM not already in prompt: Appends `". Camera: static. Motion: synchronized to {BPM} BPM."`
- If BPM already present: Appends `". Camera: static."`

**For other APIs (Runway, Pika, Kling):** Similar optimizations with API-specific formatting

## Stage 5: Final Prompt Usage

The optimized prompt is sent to Replicate API along with:
- Image input (if character consistency enabled)
- Frame count, FPS, dimensions
- Seed (for reproducibility)

---

## Example Prompts

### Example 1: Synthetic Example

**Note:** This is a constructed example for demonstration purposes.

#### Input Data (Song Analysis)

```python
{
    "mood_primary": "energetic",
    "mood_tags": ["energetic", "danceable", "upbeat", "groovy"],
    "primary_genre": "Electronic",
    "bpm": 128.0,
    "sections": [],  # Short-form video
    "mood_vector": {
        "energy": 0.85,
        "valence": 0.75,
        "danceability": 0.90,
        "tension": 0.60
    }
}
```

### Stage-by-Stage Prompt Evolution

**Stage 1: Base Components**
```
"Abstract visual style, vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F, energetic, danceable, upbeat mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed)"
```

**Stage 2: Rhythm Enhancement**
- Motion type selected: "bouncing" (based on genre="Electronic" → priority 4)
- Motion descriptor: "bouncing motion, rhythmic pulsing, steady vertical rhythm matching the beat" (BPM 128 = "fast" tempo)
- Enhanced prompt:
```
"Abstract visual style, vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F, energetic, danceable, upbeat mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), bouncing motion, rhythmic pulsing, steady vertical rhythm matching the beat synchronized to 128 BPM tempo, rhythmic motion matching the beat"
```

**Stage 3: API Optimization (Minimax Hailuo 2.3)**
- BPM already present, adds camera directive:
```
"Abstract visual style, vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F, energetic, danceable, upbeat mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), bouncing motion, rhythmic pulsing, steady vertical rhythm matching the beat synchronized to 128 BPM tempo, rhythmic motion matching the beat. Camera: static."
```

### Final Prompt (Sent to Replicate)

```
"Abstract visual style, vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F, energetic, danceable, upbeat mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), bouncing motion, rhythmic pulsing, steady vertical rhythm matching the beat synchronized to 128 BPM tempo, rhythmic motion matching the beat. Camera: static."
```

---

### Example 2: Real Database Example

**Note:** This is an actual prompt from the database (Song ID: `dea00124-cfd6-49d1-8b29-f31f437c42db`, Clip Index: 7).

#### Actual Prompt from Database

```
"Abstract visual style, calm color palette with #4A90E2, #7B68EE, and #87CEEB, calm, danceable mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), rapid looping, energetic repetitive cycles, quick seamless loops synchronized to tempo synchronized to 129 BPM tempo, rhythmic motion matching the beat"
```

#### Observations from Real Example

1. **Duplicate BPM reference:** Notice "synchronized to tempo synchronized to 129 BPM tempo" - this suggests a bug in the rhythm enhancement logic where BPM is appended twice
2. **Calm mood with fast camera:** The prompt has "calm" mood but "fast_zoom camera motion (fast speed)" - this may be a mismatch between mood and camera motion mapping
3. **Electronic genre:** Uses "Electronic aesthetic" which maps to fast camera motion regardless of mood
4. **Motion type:** Uses "rapid looping" which was selected based on the genre/BPM combination

---

### Key Observations

1. **No explicit character/dancer mention:** The prompt focuses on abstract visuals, colors, mood, and motion patterns, but does not explicitly request a "dancing character" or "person dancing"
2. **Abstract visual style:** Starts with "Abstract visual style" which may bias the model away from character-based generation
3. **Motion descriptors:** Focus on motion patterns (bouncing, pulsing) rather than character actions
4. **Character consistency:** When character images are provided, they are passed as image inputs to the API, but the prompt itself doesn't reference the character

### Potential Issues

- The prompt may need explicit character/dancer references to generate characters consistently
- "Abstract visual style" may conflict with character-based generation goals
- Motion descriptors describe patterns but not character actions (e.g., "person dancing" vs "bouncing motion")

