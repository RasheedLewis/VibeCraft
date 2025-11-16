# MVP-04 Plan: Prompt Experimentation + Consistent Visual Style

**Goal:** Maintain visual coherence across all clips in a song through systematic prompt engineering and experimentation.

## Experimentation Scratchpad

Use this section to document experiments, commands, and results.

### Replicate Playground experiments + notes

Use this section to document experiments run directly in the Replicate web playground (https://replicate.com) before implementing in code.

```
Experiment: _

Command: _

Notes: __
```

---

### Experiments

```
Experiment: _

Command: _

Notes: __
```

---

## Context for Fresh Start

### What MVP-04 Does
Systematically experiment with prompt engineering to achieve consistent visual style across multiple video clips for the same song. This involves:
- Testing different prompt templates and variations
- Experimenting with different Replicate models
- Cataloging prompt → video mappings
- Developing style consistency techniques (seed inheritance, style tokens, etc.)
- Creating a prompt library and best practices guide

### What Already Exists

**Scene Planner (`backend/app/services/scene_planner.py`):**
- `build_scene_spec()` - Generates scene specifications from song analysis
- `build_prompt()` - Combines mood, genre, color palette, camera motion, shot pattern into a prompt
- Template system with `TemplateType` (currently defaults to "abstract")
- Color palette mapping from mood (`map_mood_to_color_palette()`)
- Camera motion mapping from genre (`map_genre_to_camera_motion()`)
- Shot pattern mapping from section type (`map_section_type_to_shot_pattern()`)

**Template Definitions:**
- Frontend templates defined in `frontend/src/pages/SongProfilePage.tsx` (`const templates`):
  - `abstract` - "Abstract Visualizer" (Floating shapes • Violet & neon gradients)
  - `cozy` - "Mood Environment" (Foggy forest • Dream pop ambience)
  - `city` - "Neon City Run" (Hyperlapse skyline • Vaporwave glow)
- Scene planner templates are currently hardcoded in Python (only "abstract" is implemented)
- Backend `build_scene_spec()` accepts a `template` parameter but only "abstract" is fully implemented

**Current Prompt Structure:**
Prompts are built from components:
- Visual style (currently hardcoded as "Abstract visual style")
- Color palette (mood-based, e.g., "vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F")
- Mood description (from mood tags)
- Genre aesthetic
- Shot pattern and pacing
- Camera motion and speed
- Section type context (chorus/verse/bridge)
- Lyrics motif (optional, extracts key words)

**Video Generation (`backend/app/services/video_generation.py`):**
- `generate_section_video()` - Generates video via Replicate API
- Currently uses `anotherjesse/zeroscope-v2-xl` model
- Supports optional `seed` parameter (for style consistency)
- Supports `num_frames` and `fps` parameters
- Polls Replicate API for completion

**Replicate API:**
- Model: `anotherjesse/zeroscope-v2-xl` (8 FPS, 576x320 output)
- Input: `prompt` (text), `num_frames` (default 24), `fps` (default 8), `seed` (optional)
- Output: Video URL (MP4)
- See `docs/adam/REPLICATE_VIDEO_MODELS.md` for alternative models

**Clip Generation (`backend/app/services/clip_generation.py`):**
- `enqueue_clip_generation_batch()` - Enqueues multiple clip generation jobs
- `run_clip_generation_job()` - Generates a single clip
- Uses scene planner to generate prompts for each clip
- Stores results in `SectionVideo` model

**Database Models:**
- `Song` - Song metadata, audio S3 keys, duration
- `SongAnalysis` - Analysis results (BPM, beats, sections, mood, genre, lyrics)
- `SectionVideo` - Generated video clips with metadata (prompt, video_url, duration, fps, resolution)
- `SongClip` - Planned clips with boundaries (from MVP-01)

**Current Limitations:**
- No style seed inheritance across clips
- No shared style tokens or context persistence
- Hardcoded "Abstract visual style" in prompts
- Frontend defines 3 templates (`abstract`, `cozy`, `city`) in `SongProfilePage.tsx` but backend only implements "abstract"
- Template system exists in backend but templates are hardcoded in Python code
- No prompt catalog or library
- No systematic testing of prompt variations

### Key Files to Understand

1. **`backend/app/services/scene_planner.py`** - Scene planning and prompt building
2. **`backend/app/services/video_generation.py`** - Replicate API integration
3. **`backend/app/services/clip_generation.py`** - Batch clip generation
4. **`backend/app/schemas/scene.py`** - SceneSpec, ColorPalette, CameraMotion, ShotPattern schemas
5. **`backend/app/schemas/analysis.py`** - SongAnalysis, MoodVector schemas
6. **`docs/adam/REPLICATE_VIDEO_MODELS.md`** - Alternative Replicate models
7. **`scripts/generate_test_clips.py`** - Example script for generating test clips
8. **`backend/app/models/section_video.py`** - SectionVideo model (stores generated clips)
9. **`frontend/src/pages/SongProfilePage.tsx`** - Frontend template definitions (`const templates`: abstract, cozy, city)

### Prerequisites

- Replicate API token configured (`REPLICATE_API_TOKEN` env var)
- Access to generated clips (via MVP-01) or ability to generate test clips
- Song analysis data (mood, genre, BPM, sections) - can use mock data
- Python environment with dependencies installed
- Ability to view generated videos (for visual inspection)

### Input Data

**For experimentation, you'll need:**
- Song analysis data (mood, genre, sections, lyrics)
- Or use mock analysis: `get_mock_analysis_by_song_id()` from `app/services/mock_analysis.py`
- Test songs in various genres (electronic, country, hip-hop, etc.)

**Current prompt components available:**
- Mood: `analysis.mood_primary`, `analysis.mood_tags`, `analysis.mood_vector`
- Genre: `analysis.primary_genre`
- Sections: `analysis.sections` (with type, start_sec, end_sec)
- Lyrics: `analysis.section_lyrics` (optional)
- BPM: `analysis.bpm`

### Output

**Expected deliverables:**
- Prompt catalog/database (prompt → video results mapping)
- Template library (tested templates for different genres/moods)
- Style consistency guidelines and best practices
- Updated scene planner with style consistency features
- Documentation of successful techniques and limitations

### Experimentation Areas

1. **Template Variations:**
   - Implement the frontend-defined templates (`cozy`, `city`) in the backend scene planner
   - Test different visual styles (abstract, realistic, cinematic, etc.)
   - Create genre-specific templates
   - Test mood-specific templates
   - Test template switching and template-specific prompt variations
   - Consider creating external template configuration files (JSON/YAML) for easier experimentation

2. **Prompt Component Testing:**
   - Test impact of individual components (color palette, camera motion, etc.)
   - Test prompt ordering and structure
   - Test prompt length and detail level

3. **Replicate Model Testing:**
   - Compare `zeroscope-v2-xl` with alternatives
   - Test model-specific features (seed support, style tokens)
   - Document model capabilities and limitations

4. **Style Consistency Techniques:**
   - Test seed inheritance across clips
   - Test shared style tokens/descriptors
   - Test prompt chaining and context persistence
   - Test style reference approaches

5. **Prompt Engineering Patterns:**
   - Test incremental modifications (single word/phrase changes)
   - Test prompt component combinations
   - Test prompt tuning workflows
