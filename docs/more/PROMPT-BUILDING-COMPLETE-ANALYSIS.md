# Prompt Building: Complete Analysis and Report

## Executive Summary

This document provides a comprehensive analysis of how video generation prompts are constructed in VibeCraft. Prompts are built through a multi-stage pipeline that transforms song analysis data (mood, genre, BPM, sections, lyrics) into optimized video generation prompts tailored for specific AI models.

The system uses a modular approach with distinct stages:
1. **Scene Specification Building** - Entry point and path selection
2. **Base Prompt Construction** - Core component assembly
3. **Rhythm Enhancement** - BPM-aware motion synchronization
4. **API-Specific Optimization** - Model-tailored final adjustments

---

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Stage 1: Scene Specification Building](#stage-1-scene-specification-building)
3. [Stage 2: Base Prompt Construction](#stage-2-base-prompt-construction)
4. [Stage 3: Rhythm Enhancement](#stage-3-rhythm-enhancement)
5. [Stage 4: API-Specific Optimization](#stage-4-api-specific-optimization)
6. [Component Mapping Functions](#component-mapping-functions)
7. [Complete Examples](#complete-examples)
8. [Known Issues and Observations](#known-issues-and-observations)
9. [Related Systems](#related-systems)

---

## System Architecture Overview

### Entry Point

**Location:** `backend/app/services/clip_generation.py`

The prompt building process begins when `run_clip_generation_job()` is called for a clip. This function:

1. Retrieves the clip and associated song analysis
2. Calls `_build_scene_spec_for_clip()` to construct the scene specification
3. The scene specification contains the final prompt along with visual parameters

### Key Files

- **`clip_generation.py`** - Entry point and job orchestration
- **`scene_planner.py`** - Core prompt building logic and component mapping
- **`prompt_enhancement.py`** - Rhythm enhancement and API optimization
- **`video_generation.py`** - Final prompt usage and API calls

---

## Stage 1: Scene Specification Building

### Entry Point Function

**Function:** `_build_scene_spec_for_clip(clip_id: UUID, analysis: SongAnalysis) -> SceneSpec`

**Location:** `backend/app/services/clip_generation.py:529`

### Path Selection Logic

The system selects one of two paths based on whether the song has sections:

#### Path A: Short-Form Videos (No Sections)

**Function:** `build_clip_scene_spec()`

**When Used:**
- Song analysis has no sections (`analysis.sections` is empty)
- Used for short-form video generation

**Characteristics:**
- Uses **song-level analysis** (entire song mood, genre, BPM)
- No section-specific context
- Default shot pattern: `medium` with `medium` pacing
- No lyrics integration

**Code Reference:**
```476:535:backend/app/services/scene_planner.py
def build_clip_scene_spec(
    start_sec: float,
    end_sec: float,
    analysis: SongAnalysis,
    template: TemplateType = DEFAULT_TEMPLATE,
) -> SceneSpec:
    """
    Build scene specification for a clip (non-section mode).

    Uses song-level analysis instead of section-specific data.
    """
    # ... implementation ...
```

#### Path B: Long-Form Videos (With Sections)

**Function:** `build_scene_spec(section_id: str, analysis: SongAnalysis, template: TemplateType) -> SceneSpec`

**When Used:**
- Song analysis contains sections
- Used for full-length video generation

**Characteristics:**
- Uses **section-specific analysis** (section type, section lyrics)
- Section-aware shot patterns (chorus = dynamic, verse = steady, etc.)
- Lyrics integration for motif extraction
- Section context influences prompt components

**Code Reference:**
```405:473:backend/app/services/scene_planner.py
def build_scene_spec(
    section_id: str,
    analysis: SongAnalysis,
    template: TemplateType = DEFAULT_TEMPLATE,
) -> SceneSpec:
    """
    Build scene specification for a given section.
    """
    # ... implementation ...
```

### Template Selection

Both paths support template types:
- `"abstract"` - Abstract visual style (default)
- `"environment"` - Environmental visual style
- `"character"` - Character-focused visual style
- `"minimal"` - Minimalist visual style

Templates are retrieved from `song.template` field and passed through to prompt building.

---

## Stage 2: Base Prompt Construction

### Core Function

**Function:** `build_prompt()`

**Location:** `backend/app/services/scene_planner.py:286`

**Signature:**
```python
def build_prompt(
    section: Optional[SongSection],
    mood_primary: str,
    mood_tags: list[str],
    genre: Optional[str],
    color_palette: ColorPalette,
    camera_motion: CameraMotion,
    shot_pattern: ShotPattern,
    lyrics: Optional[str] = None,
    bpm: Optional[float] = None,
    motion_type: Optional[str] = None,
    template: TemplateType = DEFAULT_TEMPLATE,
) -> str
```

### Component Assembly Order

The base prompt is constructed by assembling components in a specific order, joined with `", "` (comma-space):

#### 1. Visual Style (Template-Based)

**Source:** Template type parameter

**Mapping:**
```python
template_style_map = {
    "abstract": "Abstract visual style",
    "environment": "Environmental visual style",
    "character": "Character-focused visual style",
    "minimal": "Minimalist visual style",
}
```

**Example:** `"Abstract visual style"`

**Note:** This replaces the previous hardcoded "Abstract visual style" - templates are now fully implemented.

#### 2. Color Palette

**Format:** `"{mood} color palette with {primary}, {secondary}, and {accent}"`

**Source:** `map_mood_to_color_palette()` function

**Example:** `"vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F"`

**Mapping Logic:**
- **Energetic + High Valence (>0.6):** Vibrant colors (pink, yellow, green)
- **Energetic + Low Valence (≤0.6):** Intense colors (dark red, orange, gold)
- **Calm/Relaxed:** Soft cool colors (blues, slate blue, sky blue)
- **Melancholic/Sad:** Muted desaturated colors (grays, olive, khaki)
- **Intense:** High contrast saturated colors (crimson, black, deep pink)
- **Default:** Neutral palette (purples)

**Code Reference:**
```62:125:backend/app/services/scene_planner.py
def map_mood_to_color_palette(mood_primary: str, mood_vector) -> ColorPalette:
    """
    Map mood to color palette.
    """
    # ... implementation ...
```

#### 3. Mood Description

**Format:** `"{tag1}, {tag2}, {tag3} mood"`

**Source:** Top 3 mood tags from `analysis.mood_tags`

**Example:** `"energetic, danceable, upbeat mood"`

#### 4. Genre Aesthetic

**Format:** `"{genre} aesthetic"` (only if genre exists)

**Source:** `analysis.primary_genre`

**Example:** `"Electronic aesthetic"`

#### 5. Shot Pattern

**Format:** `"{pattern} with {pacing} pacing"`

**Source:** `map_section_type_to_shot_pattern()` or default for clips

**Examples:**
- `"medium with medium pacing"` (default/clip)
- `"close_up_to_wide with fast pacing"` (chorus)
- `"wide with slow pacing"` (bridge/intro)

**Section Type Mapping:**
- **Intro:** `wide` / `slow` / `["fade_in"]`
- **Verse:** `medium` / `medium` / `["cut"]`
- **Chorus:** `close_up_to_wide` / `fast` / `["zoom", "cut", "flash"]`
- **Pre-chorus:** `medium_to_close` / `medium` / `["zoom_in", "cut"]`
- **Bridge:** `wide` / `slow` / `["fade", "crossfade"]`
- **Solo:** `close_up` / `fast` / `["quick_cut", "flash"]`
- **Drop:** `close_up` / `very_fast` / `["strobe", "quick_cut", "flash"]`
- **Outro:** `wide` / `slow` / `["fade_out"]`

**Code Reference:**
```204:283:backend/app/services/scene_planner.py
def map_section_type_to_shot_pattern(section_type: str) -> ShotPattern:
    """
    Map section type to shot pattern.
    """
    # ... implementation ...
```

#### 6. Camera Motion

**Format:** `"{type} camera motion ({speed} speed)"`

**Source:** `map_genre_to_camera_motion()` function

**Example:** `"fast_zoom camera motion (fast speed)"`

**Genre Mapping:**
- **Electronic/EDM:** `fast_zoom` / `fast` / intensity `0.8`
- **Rock/Metal:** `quick_cuts` / `fast` / intensity `0.9`
- **Hip-Hop:** `slow_pan` / `medium` / intensity `0.6`
- **Pop:** `medium_pan` / `medium` / intensity `0.7`
- **Country/Folk:** `slow_pan` / `slow` / intensity `0.4`
- **Ambient:** `static` / `slow` / intensity `0.2`
- **Default:** `medium_pan` / BPM-based speed / intensity `0.5`

**Speed Calculation (if BPM provided):**
- BPM < 90: `slow`
- BPM > 130: `fast`
- Otherwise: `medium`

**Code Reference:**
```127:201:backend/app/services/scene_planner.py
def map_genre_to_camera_motion(genre: Optional[str], bpm: Optional[float] = None) -> CameraMotion:
    """
    Map genre to camera motion preset.
    """
    # ... implementation ...
```

#### 7. Dancing Instruction (Always Included)

**Format:** Fixed text

**Content:** `"the figure is dancing dynamically, varying the limbs that they move, and at some point turning around"`

**Purpose:** Ensures dynamic character movement in generated videos

**Note:** This is always appended regardless of template type or other parameters.

#### 8. Section Context (Conditional)

**When:** Only if `section` parameter is provided (long-form videos)

**Mappings:**
- **Chorus:** `"dynamic and energetic"`
- **Verse:** `"steady and narrative"`
- **Bridge:** `"transitional and atmospheric"`

#### 9. Lyrics Motif (Conditional)

**When:** Only if `lyrics` parameter is provided

**Process:**
1. Extract first 10 words from lyrics
2. Filter words with length > 3
3. Take first 3 key words
4. Format: `"inspired by: {word1}, {word2}, {word3}"`

**Example:** If lyrics are "I'm walking down the street tonight", extracts: `"inspired by: walking, down, street"`

### Base Prompt Assembly

All components are joined with `", "` to create the base prompt:

```python
base_prompt = ", ".join(components)
```

**Example Base Prompt:**
```
"Abstract visual style, vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F, energetic, danceable, upbeat mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), the figure is dancing dynamically, varying the limbs that they move, and at some point turning around"
```

---

## Stage 3: Rhythm Enhancement

### Entry Point

**Function:** `enhance_prompt_with_rhythm()`

**Location:** `backend/app/services/prompt_enhancement.py:101`

**When Applied:** Only if `bpm > 0` is provided to `build_prompt()`

### Motion Type Selection

Before rhythm enhancement, the system selects an appropriate motion type using `select_motion_type()`.

**Function:** `select_motion_type()`

**Location:** `backend/app/services/prompt_enhancement.py:180`

**Selection Priority (in order):**

1. **Scene Context** (if section provided)
   - Chorus with intensity > 0.7: `"bouncing"`
   - Chorus with intensity ≤ 0.7: `"pulsing"`
   - Bridge: `"looping"`
   - Verse: `"stepping"`

2. **Mood-Based Selection**
   - Energetic/Intense/Aggressive:
     - BPM > 140: `"pulsing"`
     - Otherwise: `"bouncing"`
   - Calm/Relaxed/Peaceful: `"looping"`
   - Melancholic/Sad/Somber: `"rotating"`

3. **Mood Tags Analysis**
   - Dance-related tags (`dance`, `danceable`, `groovy`, `dancing`): `"dancing"`
   - Electronic/Techno tags: `"pulsing"`
   - Acoustic/Folk tags: `"stepping"`

4. **Genre-Based Selection** (fallback)
   - Electronic: `"pulsing"`
   - Dance/Hip-Hop/Pop: `"dancing"`
   - Rock: `"stepping"`
   - Jazz: `"looping"`
   - Default: `"bouncing"`

5. **BPM-Based Selection** (if no other factors)
   - BPM < 80: `"looping"`
   - BPM < 100: `"rotating"`
   - BPM < 120: `"stepping"`
   - BPM < 140: `"bouncing"`
   - BPM ≥ 140: `"pulsing"`

6. **Default:** `"bouncing"`

### Tempo Classification

**Function:** `get_tempo_classification(bpm: float) -> str`

**BPM Ranges:**
- < 60: `"slow"`
- 60-100: `"medium"`
- 100-140: `"fast"`
- ≥ 140: `"very_fast"`

### Motion Descriptors

**Function:** `get_motion_descriptor(bpm: float, motion_type: str) -> str`

**Motion Types Available:**
- `"bouncing"` - Vertical up-and-down motion
- `"dancing"` - Dance steps and movements
- `"pulsing"` - Expansion and contraction
- `"rotating"` - Circular spinning motion
- `"stepping"` - Side-to-side stepping
- `"looping"` - Repetitive cycles

**Motion Descriptor Examples:**

For **fast tempo** (BPM 100-140):
- Bouncing: `"rapid bouncing, energetic rhythmic motion, quick vertical pulses synchronized to tempo"`
- Dancing: `"energetic dancing, rapid rhythmic dance motion, quick dance steps synchronized to tempo, dynamic dancing"`
- Pulsing: `"rapid pulsing, energetic rhythmic beats, quick expansion-contraction cycles matching tempo"`

For **medium tempo** (BPM 60-100):
- Bouncing: `"bouncing motion, rhythmic pulsing, steady vertical rhythm matching the beat"`
- Dancing: `"dancing motion, rhythmic dance steps, steady dance rhythm matching the beat, clear dance movements"`

For **slow tempo** (BPM < 60):
- Bouncing: `"gentle bouncing motion, slow rhythmic up-and-down movement, smooth vertical oscillation"`
- Dancing: `"gentle dancing motion, slow rhythmic movement, smooth flowing dance steps, graceful swaying"`

**Code Reference:**
```9:40:backend/app/services/prompt_enhancement.py
MOTION_TYPES = {
    "bouncing": {
        "slow": "gentle bouncing motion, slow rhythmic up-and-down movement, smooth vertical oscillation",
        "medium": "bouncing motion, rhythmic pulsing, steady vertical rhythm matching the beat",
        "fast": "rapid bouncing, energetic rhythmic motion, quick vertical pulses synchronized to tempo",
    },
    # ... other motion types ...
}
```

### Tempo Descriptors

**Function:** Uses `TEMPO_DESCRIPTORS` dictionary

**Descriptors:**
- `"slow"`: `"slow, flowing, gentle, relaxed"`
- `"medium"`: `"steady, moderate, balanced, rhythmic"`
- `"fast"`: `"energetic, driving, dynamic, upbeat"`
- `"very_fast"`: `"frenetic, rapid, intense, high-energy"`

**Code Reference:**
```48:53:backend/app/services/prompt_enhancement.py
TEMPO_DESCRIPTORS = {
    "slow": "slow, flowing, gentle, relaxed",
    "medium": "steady, moderate, balanced, rhythmic",
    "fast": "energetic, driving, dynamic, upbeat",
    "very_fast": "frenetic, rapid, intense, high-energy",
}
```

### Rhythm Enhancement Process

**Function:** `enhance_prompt_with_rhythm()`

**Process:**
1. Get motion descriptor based on BPM and motion type
2. Get tempo classification and tempo descriptor
3. Build rhythmic phrase:
   ```python
   rhythmic_phrase = (
       f"{tempo_descriptor} {motion_descriptor} synchronized to {bpm_int} BPM tempo, "
       f"rhythmic motion matching the beat with clear repetitive pattern"
   )
   ```
4. Append to base prompt: `f"{base_prompt}, {rhythmic_phrase}"`

**Example Enhancement:**
```
Base: "Abstract visual style, vibrant color palette..."
Enhanced: "Abstract visual style, vibrant color palette..., energetic, driving, dynamic, upbeat bouncing motion, rhythmic pulsing, steady vertical rhythm matching the beat synchronized to 128 BPM tempo, rhythmic motion matching the beat with clear repetitive pattern"
```

### Known Issue: Repetitive Phrases

**Problem:** The rhythm enhancement can create redundant phrases:

**Example Problematic Output:**
```
"energetic, driving, dynamic, upbeat energetic dancing, rapid rhythmic dance motion, 
quick dance steps synchronized to tempo, dynamic dancing synchronized to 129 BPM tempo, 
rhythmic motion matching the beat with clear repetitive pattern"
```

**Issues Identified:**
- "energetic" appears twice (in tempo descriptor AND motion descriptor)
- "dynamic" appears twice (in tempo descriptor AND motion descriptor)
- "dancing" appears multiple times
- "synchronized to tempo" appears twice (once in motion descriptor, once in rhythmic phrase)

**Recommendation:**
- Simplify motion descriptors to avoid duplication
- Remove "repetitive pattern" or make it optional
- Consider combining tempo and motion descriptors more intelligently

---

## Stage 4: API-Specific Optimization

### Entry Point

**Function:** `optimize_prompt_for_api()`

**Location:** `backend/app/services/prompt_enhancement.py:317`

**When Applied:** Just before sending prompt to Replicate API in `video_generation.py`

### BPM Extraction

**Function:** `_extract_bpm_from_prompt()`

**Process:** Extracts BPM from prompt if not provided, looking for patterns like:
- `"128 BPM"` or `"128BPM"`
- `"at 128 beats per minute"`

### API-Specific Optimizations

#### Minimax Hailuo 2.3 (Current Default)

**Optimization Logic:**
- If BPM not already in prompt: Appends `". Camera: static. Motion: synchronized to {BPM} BPM."`
- If BPM already present: Appends `". Camera: static."`

**Rationale:** Hailuo responds well to concise, directive prompts with clear motion descriptions and explicit tempo references.

**Example:**
```
Input: "Abstract visual style..., bouncing motion... synchronized to 128 BPM tempo..."
Output: "Abstract visual style..., bouncing motion... synchronized to 128 BPM tempo.... Camera: static."
```

**Code Reference:**
```352:366:backend/app/services/prompt_enhancement.py
# Minimax Hailuo 2.3 (current default model)
if "hailuo" in api_lower or "minimax" in api_lower:
    # Hailuo responds well to concise, directive prompts with clear motion descriptions
    # It benefits from explicit tempo references, but avoid duplication if already in prompt
    if f"{bpm_int} BPM" not in prompt:
        optimized = f"{prompt}. Camera: static. Motion: synchronized to {bpm_int} BPM."
        # ... logging ...
        return optimized
    else:
        # BPM already in prompt, just add camera/motion directive
        optimized = f"{prompt}. Camera: static."
        # ... logging ...
        return optimized
```

#### Other APIs (Future Support)

**Runway Gen-3:**
- Adds: `". Camera: static. Motion: {motion_style}."`
- Prefers action-oriented language

**Pika:**
- Adds: `". Style: clean motion graphics. Tempo: {BPM} BPM."` (if BPM not present)
- Benefits from style references and tempo mentions

**Kling:**
- Adds detailed motion description: `". The character moves with consistent {motion_style} at {BPM} beats per minute, creating a rhythmic visual pattern."`
- Prefers detailed motion descriptions with context

---

## Component Mapping Functions

### Color Palette Mapping

**Function:** `map_mood_to_color_palette(mood_primary: str, mood_vector) -> ColorPalette`

**Inputs:**
- `mood_primary`: Primary mood tag (e.g., "energetic", "calm", "melancholic")
- `mood_vector`: Object with `energy`, `valence`, `danceability`, `tension` (0.0-1.0)

**Output:** `ColorPalette` object with:
- `primary`: Hex color code
- `secondary`: Hex color code
- `accent`: Hex color code
- `mood`: Mood descriptor string

**Mapping Rules:**
- High energy + high valence → Vibrant warm colors
- High energy + low valence → Intense dark colors
- Calm/relaxed → Soft cool colors
- Melancholic/sad → Muted desaturated colors
- Intense → High contrast saturated colors
- Default → Neutral purple palette

### Camera Motion Mapping

**Function:** `map_genre_to_camera_motion(genre: Optional[str], bpm: Optional[float] = None) -> CameraMotion`

**Inputs:**
- `genre`: Primary genre string (e.g., "Electronic", "Rock", "Hip-Hop")
- `bpm`: Optional BPM for speed calculation

**Output:** `CameraMotion` object with:
- `type`: Motion type string (e.g., "fast_zoom", "slow_pan")
- `intensity`: Float (0.0-1.0)
- `speed`: String ("slow", "medium", "fast")

**Genre Mappings:**
- Electronic/EDM → Fast, dynamic motion
- Rock/Metal → Aggressive, quick cuts
- Hip-Hop → Smooth, steady motion
- Pop → Balanced, dynamic
- Country/Folk → Slow, gentle motion
- Ambient → Very slow, minimal motion

### Shot Pattern Mapping

**Function:** `map_section_type_to_shot_pattern(section_type: str) -> ShotPattern`

**Input:** Section type string (e.g., "verse", "chorus", "bridge")

**Output:** `ShotPattern` object with:
- `pattern`: String (e.g., "wide", "medium", "close_up")
- `pacing`: String (e.g., "slow", "medium", "fast")
- `transitions`: List of transition strings

**Section Type Mappings:**
- Intro → Wide, slow, fade_in
- Verse → Medium, medium, cut
- Chorus → Close_up_to_wide, fast, zoom/cut/flash
- Pre-chorus → Medium_to_close, medium, zoom_in/cut
- Bridge → Wide, slow, fade/crossfade
- Solo → Close_up, fast, quick_cut/flash
- Drop → Close_up, very_fast, strobe/quick_cut/flash
- Outro → Wide, slow, fade_out

---

## Complete Examples

### Example 1: Short-Form Video (Electronic, Energetic)

#### Input Data

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

#### Stage-by-Stage Prompt Evolution

**Stage 1: Component Mapping**

- **Visual Style:** `"Abstract visual style"` (default template)
- **Color Palette:** `"vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F"` (energetic + high valence)
- **Mood:** `"energetic, danceable, upbeat mood"`
- **Genre:** `"Electronic aesthetic"`
- **Shot Pattern:** `"medium with medium pacing"` (default for clips)
- **Camera Motion:** `"fast_zoom camera motion (fast speed)"` (Electronic genre)
- **Dancing:** `"the figure is dancing dynamically, varying the limbs that they move, and at some point turning around"`

**Base Prompt (Stage 2):**
```
"Abstract visual style, vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F, energetic, danceable, upbeat mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), the figure is dancing dynamically, varying the limbs that they move, and at some point turning around"
```

**Stage 3: Rhythm Enhancement**

- **Motion Type Selection:**
  - Priority 1 (Scene Context): None (no section)
  - Priority 2 (Mood): "energetic" → BPM 128 (< 140) → `"bouncing"`
  - Selected: `"bouncing"`

- **Tempo Classification:** BPM 128 → `"fast"` (100-140 range)

- **Motion Descriptor:** `"rapid bouncing, energetic rhythmic motion, quick vertical pulses synchronized to tempo"`

- **Tempo Descriptor:** `"energetic, driving, dynamic, upbeat"`

- **Rhythmic Phrase:**
```
"energetic, driving, dynamic, upbeat rapid bouncing, energetic rhythmic motion, quick vertical pulses synchronized to tempo synchronized to 128 BPM tempo, rhythmic motion matching the beat with clear repetitive pattern"
```

**Enhanced Prompt (Stage 3):**
```
"Abstract visual style, vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F, energetic, danceable, upbeat mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), the figure is dancing dynamically, varying the limbs that they move, and at some point turning around, energetic, driving, dynamic, upbeat rapid bouncing, energetic rhythmic motion, quick vertical pulses synchronized to tempo synchronized to 128 BPM tempo, rhythmic motion matching the beat with clear repetitive pattern"
```

**Stage 4: API Optimization (Minimax Hailuo 2.3)**

- BPM already present in prompt
- Adds: `". Camera: static."`

**Final Prompt (Sent to Replicate):**
```
"Abstract visual style, vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F, energetic, danceable, upbeat mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), the figure is dancing dynamically, varying the limbs that they move, and at some point turning around, energetic, driving, dynamic, upbeat rapid bouncing, energetic rhythmic motion, quick vertical pulses synchronized to tempo synchronized to 128 BPM tempo, rhythmic motion matching the beat with clear repetitive pattern. Camera: static."
```

---

### Example 2: Long-Form Video (Chorus Section, Electronic, Calm)

#### Input Data

```python
{
    "mood_primary": "calm",
    "mood_tags": ["calm", "danceable"],
    "primary_genre": "Electronic",
    "bpm": 129.0,
    "sections": [
        {
            "id": "section_1",
            "type": "chorus",
            "start_sec": 30.0,
            "end_sec": 60.0
        }
    ],
    "section_lyrics": [
        {
            "section_id": "section_1",
            "text": "I'm walking down the street tonight"
        }
    ],
    "mood_vector": {
        "energy": 0.60,
        "valence": 0.50,
        "danceability": 0.70,
        "tension": 0.30
    }
}
```

#### Stage-by-Stage Prompt Evolution

**Stage 1: Component Mapping**

- **Visual Style:** `"Abstract visual style"` (default template)
- **Color Palette:** `"calm color palette with #4A90E2, #7B68EE, and #87CEEB"` (calm mood)
- **Mood:** `"calm, danceable mood"`
- **Genre:** `"Electronic aesthetic"`
- **Shot Pattern:** `"close_up_to_wide with fast pacing"` (chorus section)
- **Camera Motion:** `"fast_zoom camera motion (fast speed)"` (Electronic genre, BPM > 130)
- **Dancing:** `"the figure is dancing dynamically, varying the limbs that they move, and at some point turning around"`
- **Section Context:** `"dynamic and energetic"` (chorus)
- **Lyrics Motif:** `"inspired by: walking, down, street"` (extracted from lyrics)

**Base Prompt (Stage 2):**
```
"Abstract visual style, calm color palette with #4A90E2, #7B68EE, and #87CEEB, calm, danceable mood, Electronic aesthetic, close_up_to_wide with fast pacing, fast_zoom camera motion (fast speed), the figure is dancing dynamically, varying the limbs that they move, and at some point turning around, dynamic and energetic, inspired by: walking, down, street"
```

**Stage 3: Rhythm Enhancement**

- **Motion Type Selection:**
  - Priority 1 (Scene Context): Chorus section → intensity 0.45 (calculated from mood vector) → `"pulsing"` (intensity ≤ 0.7)
  - Selected: `"pulsing"`

- **Tempo Classification:** BPM 129 → `"fast"` (100-140 range)

- **Motion Descriptor:** `"rapid pulsing, energetic rhythmic beats, quick expansion-contraction cycles matching tempo"`

- **Tempo Descriptor:** `"energetic, driving, dynamic, upbeat"`

- **Rhythmic Phrase:**
```
"energetic, driving, dynamic, upbeat rapid pulsing, energetic rhythmic beats, quick expansion-contraction cycles matching tempo synchronized to 129 BPM tempo, rhythmic motion matching the beat with clear repetitive pattern"
```

**Enhanced Prompt (Stage 3):**
```
"Abstract visual style, calm color palette with #4A90E2, #7B68EE, and #87CEEB, calm, danceable mood, Electronic aesthetic, close_up_to_wide with fast pacing, fast_zoom camera motion (fast speed), the figure is dancing dynamically, varying the limbs that they move, and at some point turning around, dynamic and energetic, inspired by: walking, down, street, energetic, driving, dynamic, upbeat rapid pulsing, energetic rhythmic beats, quick expansion-contraction cycles matching tempo synchronized to 129 BPM tempo, rhythmic motion matching the beat with clear repetitive pattern"
```

**Stage 4: API Optimization (Minimax Hailuo 2.3)**

- BPM already present in prompt
- Adds: `". Camera: static."`

**Final Prompt (Sent to Replicate):**
```
"Abstract visual style, calm color palette with #4A90E2, #7B68EE, and #87CEEB, calm, danceable mood, Electronic aesthetic, close_up_to_wide with fast pacing, fast_zoom camera motion (fast speed), the figure is dancing dynamically, varying the limbs that they move, and at some point turning around, dynamic and energetic, inspired by: walking, down, street, energetic, driving, dynamic, upbeat rapid pulsing, energetic rhythmic beats, quick expansion-contraction cycles matching tempo synchronized to 129 BPM tempo, rhythmic motion matching the beat with clear repetitive pattern. Camera: static."
```

---

### Example 3: Real Database Example

**Source:** Song ID `dea00124-cfd6-49d1-8b29-f31f437c42db`, Clip Index 7

**Actual Prompt from Database:**
```
"Abstract visual style, calm color palette with #4A90E2, #7B68EE, and #87CEEB, calm, danceable mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), rapid looping, energetic repetitive cycles, quick seamless loops synchronized to tempo synchronized to 129 BPM tempo, rhythmic motion matching the beat"
```

**Observations:**

1. **Duplicate BPM Reference:** Notice `"synchronized to tempo synchronized to 129 BPM tempo"` - this suggests a bug where BPM synchronization phrase is appended twice. This is the repetitive phrase issue identified in the analysis report.

2. **Calm Mood with Fast Camera:** The prompt has `"calm"` mood but `"fast_zoom camera motion (fast speed)"` - this is because Electronic genre overrides mood-based camera motion selection.

3. **Motion Type:** Uses `"rapid looping"` which was selected based on genre/BPM combination (likely from genre-based selection fallback).

4. **Missing Dancing Instruction:** This example predates the addition of the dancing instruction component, so it's not present.

---

## Known Issues and Observations

### 1. Repetitive Phrase Duplication

**Issue:** Rhythm enhancement can create redundant phrases with duplicate words.

**Example:**
- "energetic" appears in both tempo descriptor and motion descriptor
- "dynamic" appears in both tempo descriptor and motion descriptor
- "synchronized to tempo" appears twice (once in motion descriptor, once in rhythmic phrase)

**Location:** `backend/app/services/prompt_enhancement.py:135-137`

**Recommendation:**
- Simplify motion descriptors to avoid duplication
- Remove "repetitive pattern" or make it optional
- Consider combining tempo and motion descriptors more intelligently

### 2. Template Implementation Status

**Status:** ✅ **FIXED** - Templates are now fully implemented

**Previous Issue:** The `Prompt-Building-Flow.md` document noted that templates were not implemented, but the code shows they are now working correctly in `build_prompt()` function (lines 322-329).

**Current Implementation:**
- Template types are properly mapped to visual style strings
- Templates are passed through from song configuration
- All four template types are supported: `"abstract"`, `"environment"`, `"character"`, `"minimal"`

### 3. Character Consistency and Prompt Interaction

**Observation:** When character images are provided for character consistency:

- **Image Input:** Character image is passed as `first_frame_image` parameter to Replicate API
- **Prompt:** The prompt itself doesn't explicitly reference the character
- **Interaction:** The model uses the image visually while the prompt describes scene, motion, and action

**Potential Issue:** The prompt may need explicit character/dancer references to generate characters consistently, especially when using abstract visual style.

**Location:** `backend/app/services/video_generation.py:106-109`

### 4. Motion Type Selection Complexity

**Observation:** Motion type selection uses a 5-priority system that can be complex to debug.

**Recommendation:** Add more detailed logging to show which priority level was used and why a specific motion type was selected.

### 5. BPM Duplication Bug

**Issue:** In some cases, BPM synchronization phrase appears twice in the final prompt.

**Example:** `"synchronized to tempo synchronized to 129 BPM tempo"`

**Location:** Likely in `enhance_prompt_with_rhythm()` where motion descriptors may already contain "synchronized to tempo" and the rhythmic phrase also adds it.

**Recommendation:** Check motion descriptors for existing BPM references before appending rhythmic phrase.

---

## Related Systems

### Image Interrogation (Not Part of Prompt Building)

**Location:** `backend/app/services/image_interrogation.py`

**Purpose:** Converts reference images into detailed character descriptions for character image generation (not regular video generation).

**Usage:**
- **ONLY called in:** `character_consistency.py` → `generate_character_image_job()`
- **NOT used during regular video generation**

**Methods:**
1. **Primary:** OpenAI GPT-4 Vision (if `OPENAI_API_KEY` configured)
2. **Fallback:** Replicate's `methexis-inc/img2prompt`

**Output:** JSON with `prompt`, `character_description`, `style_notes`

**Note:** Image interrogation is NOT used during regular video generation. The reference image is passed directly to the video generation model as `first_frame_image` parameter, and the model uses it visually without text description.

### Prompt Logging

**Location:** `backend/app/services/prompt_logger.py`

**Purpose:** Logs prompts to `prompts.log` file for collection and analysis.

**When Logged:**
- After API optimization in `video_generation.py:433-439`
- Logs both original and optimized prompts

---

## Summary

The prompt building system in VibeCraft is a sophisticated multi-stage pipeline that:

1. **Transforms song analysis** into visual parameters (colors, camera motion, shot patterns)
2. **Assembles base prompts** from multiple components in a specific order
3. **Enhances with rhythm** using BPM-aware motion descriptors and tempo classifications
4. **Optimizes for APIs** with model-specific formatting and directives

**Key Strengths:**
- Modular, extensible design
- Comprehensive component mapping (mood → colors, genre → camera, section → shots)
- BPM-aware rhythm synchronization
- API-specific optimizations

**Areas for Improvement:**
- Reduce repetitive phrase duplication in rhythm enhancement
- Add more detailed logging for motion type selection
- Fix BPM duplication bug in some edge cases
- Consider explicit character references in prompts when using character consistency

---

## Code References Summary

### Core Functions

- `_build_scene_spec_for_clip()` - `backend/app/services/clip_generation.py:529`
- `build_scene_spec()` - `backend/app/services/scene_planner.py:405`
- `build_clip_scene_spec()` - `backend/app/services/scene_planner.py:476`
- `build_prompt()` - `backend/app/services/scene_planner.py:286`
- `enhance_prompt_with_rhythm()` - `backend/app/services/prompt_enhancement.py:101`
- `select_motion_type()` - `backend/app/services/prompt_enhancement.py:180`
- `optimize_prompt_for_api()` - `backend/app/services/prompt_enhancement.py:317`

### Mapping Functions

- `map_mood_to_color_palette()` - `backend/app/services/scene_planner.py:62`
- `map_genre_to_camera_motion()` - `backend/app/services/scene_planner.py:127`
- `map_section_type_to_shot_pattern()` - `backend/app/services/scene_planner.py:204`

### Helper Functions

- `get_tempo_classification()` - `backend/app/services/prompt_enhancement.py:56`
- `get_motion_descriptor()` - `backend/app/services/prompt_enhancement.py:76`
- `_extract_bpm_from_prompt()` - `backend/app/services/prompt_enhancement.py:282`

---

*Document generated from analysis of `PROMPT-ANALYSIS-REPORT.md` and `Prompt-Building-Flow.md`*

