# Quick Reference

## Do This

`make dev`

^ or `make start`

`make stop`

```bash
# you can run them individually but may get the venv prefix `((.venv) )` unless you VIRTUAL_ENV_DISABLE_PROMPT=1
# Lint
make lint-all # frontend and backend including format and -fix
make build # frontend only, Python doesn't build
make test
# Terminal 1: Frontend
cd frontend && npm run dev -- --host
# Terminal 2: Backend API
cd backend && source ../.venv/bin/activate && uvicorn app.main:app --reload
# Terminal 3: RQ Worker
cd backend && source ../.venv/bin/activate && rq worker ai_music_video
# Terminal 4: Trigger.dev (optional - only when working on trigger workflows)
npx trigger.dev@latest dev
# Or include Trigger.dev in dev script:
ENABLE_TRIGGER_DEV=1 make dev
```

## 🔴 TODO / Questions to Resolve

### 1. Background Job Architecture

- **Where does the lyrics code run?** (Whisper extraction)
- **Where does the librosa code run?** (BPM, sections, analysis)
- **Decision needed:** Should both go with song analysis background job?
- **Current status:** Lyrics extraction exists but not enqueued to background job yet

### 2. UI/UX - Lyrics Display

- **Where should lyrics be shown in the UI?**
- **Options to consider:**

  - Section cards (already has `lyricSnippet` prop support)
  - Full lyrics view/page
  - Timeline overlay
  - Side panel

- **Current status:** Frontend has `SectionCard` component with lyric snippet support, but needs decision on full implementation

### 3. Song Analysis - Data Persistence & Display

- **Which aspects of song analysis should be persisted to DB?**
  - Decision needed: Full `SongAnalysis` object vs. selected fields only
  - Consider: Storage costs, query performance, future extensibility
  - Current: Analysis computed on-demand, not persisted (PR-04 will add persistence)

- **Which aspects should be shown to the user?**
  - Decision needed: What analysis data to display in UI
  - Considerations:
    - **Mood tags:** Ensure at least 1 mood tag is always generated (currently `compute_mood_tags()` can return empty list)
    - Genre: Show primary + sub-genres, or primary only?
    - Mood vector: Show raw numbers (energy, valence, etc.) or just tags?
    - Sections: Show all sections or filter by confidence threshold?
    - Lyrics: Show full lyrics or snippets only?

- **Current status:** Analysis services exist (PR-05, PR-06), but display decisions pending

---

## Scratchpad

### HIGH PRIORITY: Video APIs Research

- Gotta try out video APIs and get lay of the land for what's fast, and what's pricy

**Test Prompts for Video Generation APIs:**

**Structure:** `[Style], [Camera Motion], [Subject/Action], [Environment], [Mood/Lighting]`

**Example Prompts:**

1. **Energetic/Electronic:**
   - `"Cinematic, dynamic camera movement, neon-lit cityscape at night with pulsing lights, cyberpunk aesthetic, high energy, vibrant colors"`
   - `"Abstract, fast-paced zoom, geometric shapes morphing and pulsing, dark background with neon accents, rhythmic motion"`

2. **Chill/Lo-fi:**
   - `"Dreamy, slow pan, person walking through misty forest at golden hour, soft focus, ambient lighting, peaceful mood"`
   - `"Aesthetic, gentle camera drift, abstract watercolor waves, pastel colors, calm and meditative"`

3. **Rock/Intense:**
   - `"Gritty, handheld camera shake, urban street scene with dramatic shadows, high contrast, intense mood, black and white with color accents"`
   - `"Raw, quick cuts, abstract fire and smoke effects, dark atmosphere, powerful energy"`

4. **Pop/Bright:**
   - `"Vibrant, smooth tracking shot, colorful abstract shapes dancing, bright studio lighting, upbeat and joyful"`
   - `"Stylish, rotating camera, geometric patterns in motion, pastel and neon palette, fun and energetic"`

**Quick Test Prompt (Good Baseline):**

- `"Cinematic, slow camera pan, abstract neon particles floating in dark space, pulsing rhythm, moody lighting, music video aesthetic"`
- `"Otter flying an airplane"`

**Prompt Tips:**

- Include camera motion (pan, zoom, track, rotate)
- Specify style (cinematic, abstract, gritty, dreamy)
- Add mood/energy level
- Mention lighting/color palette
- Keep it concise but descriptive (50-100 words)

### Track Recognition & Analysis Flow

**Branching logic:**

```text
Shazam → determine whether known/unknown track
│
├─ if Known Track:
│  ├─ Spotify API → features
│  └─ ChatGPT → lyrics and song section
│
└─ if Unknown Track:
   └─ Whisper → lyrics
   
└─ maybe in either case:
   └─ Essentia → audio info
```

### Deployment

- **Frontend**: We'll try AWS Amplify to deploy frontend
- **Backend**:
  - **Easiest for MVP**: Railway or Render (see DEPLOYMENT_ANALYSIS.md for details)
  - **Best for Production**: AWS ECS/Fargate
  - **Tricky Issues**: FFmpeg system dependency, librosa native deps, long-running tasks (30+ min), memory requirements, worker process management
  - See `docs/adam/DEPLOYMENT_ANALYSIS.md` for full analysis of ease vs issues
  
  **Backend Components to Deploy:**
  - FastAPI API server (uvicorn)
  - RQ workers (or migrate to Trigger.dev for production)
  - Needs: Postgres (RDS), Redis (ElastiCache), S3 access
  - Dependencies: ffmpeg, librosa, Python packages

---

## PR-08 Summary: Section Scene Planner

**Status:** ✅ Complete

### What Was Built

PR-08 implements the scene planning service that converts song analysis data (mood, genre, section type) into visual specifications for video generation.

### Key Components

1. **SceneSpec Schema** (`backend/app/schemas/scene.py`)
   - `SceneSpec`: Complete scene specification with prompt, colors, camera motion, shot patterns
   - `ColorPalette`: Primary/secondary/accent colors + mood description
   - `CameraMotion`: Motion type, intensity, speed
   - `ShotPattern`: Pattern type, pacing, transitions
   - `TemplateType`: Visual style templates (abstract, environment, character, minimal)

2. **Scene Planner Service** (`backend/app/services/scene_planner.py`)
   - `build_scene_spec(section_id, analysis, template)`: Main function to build scene specs
   - `map_mood_to_color_palette()`: Maps mood tags → color palettes (vibrant, calm, intense, muted)
   - `map_genre_to_camera_motion()`: Maps genre → camera motion presets (fast_zoom, slow_pan, quick_cuts, etc.)
   - `map_section_type_to_shot_pattern()`: Maps section type → shot patterns (wide, medium, close_up, etc.)
   - `build_prompt()`: Combines all features into video generation prompt

3. **API Endpoint** (`backend/app/api/v1/routes_scenes.py`)
   - `POST /api/v1/scenes/build-scene`: Debugging endpoint to test scene planning
   - Request: `{ "sectionId": "section-4", "template": "abstract" }`
   - Response: Complete `SceneSpec` object

### Mappings Implemented

**Mood → Color Palette:**
- Energetic + high valence → Vibrant (pink, yellow, green)
- Energetic + low valence → Intense (dark red, orange, gold)
- Calm/Relaxed → Soft blues
- Melancholic/Sad → Muted grays/greens
- Intense → High contrast (crimson, black, deep pink)

**Genre → Camera Motion:**
- Electronic/EDM → fast_zoom (intensity 0.8, fast)
- Rock/Metal → quick_cuts (intensity 0.9, fast)
- Hip-Hop → slow_pan (intensity 0.6, medium)
- Pop → medium_pan (intensity 0.7, medium)
- Country/Folk → slow_pan (intensity 0.4, slow)
- Ambient → static (intensity 0.2, slow)

**Section Type → Shot Pattern:**
- Intro → wide, slow, fade_in
- Verse → medium, medium, cut
- Chorus → close_up_to_wide, fast, zoom/cut/flash
- Pre-chorus → medium_to_close, medium, zoom_in/cut
- Bridge → wide, slow, fade/crossfade
- Solo → close_up, fast, quick_cut/flash
- Drop → close_up, very_fast, strobe/quick_cut/flash
- Outro → wide, slow, fade_out

### Testing

**Quick Test:**
```bash
cd backend && source ../.venv/bin/activate
python -c "from app.services.scene_planner import build_scene_spec; spec = build_scene_spec('section-4'); print(f'Section: {spec.section_id}, Colors: {spec.color_palette.primary}, Camera: {spec.camera_motion.type}')"
```

**API Test:**
```bash
curl -X POST http://localhost:8000/api/v1/scenes/build-scene \
  -H "Content-Type: application/json" \
  -d '{"sectionId": "section-4", "template": "abstract"}'
```

### Data Flow

```
Input: section_id (+ optional analysis, template)
  ↓
1. Lookup section from SongAnalysis (or use mock data)
  ↓
2. Extract: mood_primary, mood_tags, mood_vector, primary_genre, bpm, section.type, section_lyrics
  ↓
3. Map inputs to visual parameters:
   - mood_primary + mood_vector → ColorPalette
   - primary_genre + bpm → CameraMotion
   - section.type → ShotPattern
   - mood_vector → intensity (energy + tension) / 2
  ↓
4. Build prompt: combine template + colors + mood + genre + shot pattern + camera motion + lyrics motifs
  ↓
5. Calculate duration: section.end_sec - section.start_sec
  ↓
Output: SceneSpec (prompt, color_palette, camera_motion, shot_pattern, intensity, duration_sec)
```

### Integration Notes

- Uses mock `SongAnalysis` data from `app.services.mock_analysis` (until PR-04 complete)
- Prompt builder injects lyrics motifs when available
- Intensity calculated from mood vector (energy + tension) / 2
- Duration derived from section timestamps
- Ready for PR-09 (Section Video Generation Pipeline)
