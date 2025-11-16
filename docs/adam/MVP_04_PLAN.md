# MVP-04 Plan: Prompt Experimentation + Consistent Visual Style

**Goal:** Set up an efficient manual test process to iterate on generating videos. **Primary objective: Get a video that looks cool!** Then learn about different APIs, experiment with prompts, and finally integrate findings back into the repo.

## Phase 1: Manual Test Process Setup (FIRST GOAL)

**Objective:** Create an efficient workflow for manually testing video generation outside the main codebase.

### Manual Test Workflow

Use this section to document manual experiments, commands, and results.

```
Experiment: _

Command: _

API/Model Used: _

Prompt: _

Result: _

Notes: __
```

---

## Context for Fresh Start

### What MVP-04 Does (Updated Approach)

**Phase 1: Manual Experimentation (Current Focus)**
- Set up efficient manual test process for video generation
- Goal: Generate videos that look cool!
- Learn about different video generation APIs and their capabilities
- Experiment with different prompts, models, and parameters
- Document what works and what doesn't

**Phase 2: Integration (After Learning)**
- Integrate successful techniques back into the codebase
- Update scene planner with tested prompt patterns
- Implement style consistency features based on learnings
- Create prompt library and best practices guide

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

**Phase 1 Deliverables (Manual Experimentation):**
- Efficient manual test workflow/process
- Collection of cool-looking videos generated
- API comparison and capabilities documentation
- Prompt experimentation results and catalog
- Notes on what works and what doesn't

**Phase 2 Deliverables (Integration - After Learning):**
- Prompt catalog/database (prompt → video results mapping)
- Template library (tested templates for different genres/moods)
- Style consistency guidelines and best practices
- Updated scene planner with style consistency features
- Documentation of successful techniques and limitations

### Experimentation Areas (Phase 1 Focus)

**1. API & Model Exploration:**
   - Test different video generation APIs (Replicate, Runway, etc.)
   - Compare different models within each API
   - Document model capabilities, limitations, and costs
   - Test model-specific features (seed support, style tokens, resolution, FPS)
   - Find which APIs/models produce the coolest results

**2. Prompt Engineering:**
   - Test different prompt styles and structures
   - Experiment with visual style descriptors
   - Test prompt length and detail level
   - Try different prompt ordering and component combinations
   - Test incremental modifications (single word/phrase changes)
   - Find prompts that consistently produce cool-looking videos

**3. Parameter Tuning:**
   - Test different seeds for style consistency
   - Experiment with frame counts, FPS, resolution
   - Test other model-specific parameters
   - Document parameter impact on output quality

**4. Visual Style Exploration:**
   - Test different visual styles (abstract, realistic, cinematic, etc.)
   - Experiment with color palettes and mood expressions
   - Test camera motion and shot patterns
   - Find styles that look cool and work well for music videos

### Integration Areas (Phase 2 - After Learning)

**1. Template Implementation:**
   - Implement successful templates in backend scene planner
   - Implement frontend-defined templates (`cozy`, `city`) based on learnings
   - Create genre-specific and mood-specific templates
   - Consider external template configuration files (JSON/YAML)

**2. Style Consistency:**
   - Implement seed inheritance across clips
   - Implement shared style tokens/descriptors
   - Test prompt chaining and context persistence
   - Integrate style reference approaches

**3. Prompt Library:**
   - Build prompt catalog/database from Phase 1 learnings
   - Create prompt templates for different genres/moods
   - Document prompt engineering patterns and best practices
