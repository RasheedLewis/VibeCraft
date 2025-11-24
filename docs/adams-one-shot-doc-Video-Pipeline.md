# VibeCraft Video Pipeline

## Overview

The VibeCraft video pipeline transforms audio files into beat-synchronized music videos through three main stages: **Planning**, **Generation**, and **Composition**. The system supports two video types: **full_length** (16:9) and **short_form** (9:16).

## Pipeline Stages

### 1. Planning (`clip_planning.py`)

**Clip Planning** calculates beat-aligned clip boundaries from music analysis:
- Snaps clip boundaries to beat grid using `beat_times` from `SongAnalysis`
- Generates `ClipPlan` objects with `start_sec`, `end_sec`, `duration_sec`, and frame counts
- Supports audio selection for short-form videos (9-30 second segments)
- Default clip duration: 3-6 seconds, aligned to frame intervals (8fps generator)
- Falls back to uniform distribution if no beats detected

**Scene Planning** (`scene_planner.py`) converts analysis data into visual prompts:
- Maps mood → color palettes (vibrant, intense, calm, melancholic)
- Maps genre → camera motions (slow pan, dynamic tracking, static)
- Selects visual templates (abstract, environment, character, minimal)
- Builds `SceneSpec` objects with prompts, colors, camera motion, and shot patterns
- Incorporates lyrics and section context for full-length videos

### 2. Generation (`clip_generation.py`, `video_generation.py`)

**Clip Generation** orchestrates parallel video creation via Replicate API:

**Workflow:**
1. Enqueues clip generation jobs with controlled concurrency (default: 4 parallel)
2. For each clip:
   - Builds `SceneSpec` from clip timing and song analysis
   - Selects character images (template characters or user-uploaded with consistency)
   - Generates video via `generate_section_video()`:
     - **Text-to-video**: Pure prompt-based generation
     - **Image-to-video**: Character consistency using reference images (Minimax Hailuo 2.3)
   - Polls Replicate API for completion (max 180 attempts, 5s intervals)
   - Downloads generated video and uploads to S3
   - Stores metadata: `SongClip` records with S3 keys, prompts, seeds, costs

**Video Provider Pattern** (`video_providers/`):
- Abstract `VideoGenerationProvider` base class for extensibility
- `MinimaxHailuoProvider` implementation
- Handles aspect ratio selection: 768p (16:9) or 1080p (9:16)
- Supports both generation modes with provider-specific parameter mapping

**Character Consistency** (optional):
- Image interrogation via OpenAI GPT-4o Vision (falls back to Replicate)
- Consistent character generation using Replicate SDXL
- Pose selection (A/B) for character variations
- 9:16 image padding for short-form videos

### 3. Composition (`video_composition.py`, `clip_generation.py`)

**Video Composition** stitches clips into final video:

**Process:**
1. Retrieves all completed `SongClip` records for the song
2. Downloads clips from S3 (parallel normalization with ThreadPoolExecutor)
3. Normalizes clips: FPS (24fps full-length, 30fps short-form), resolution, codec
4. Concatenates clips with beat-aligned cuts using FFmpeg
5. Applies beat-synced visual effects via `BeatFilterApplicator`:
   - **Flash**: Brightness pulse on beats
   - **Color Burst**: Hue/saturation shift
   - **Zoom Pulse**: Scale animation
   - **Glitch**: Digital artifacts
   - **Brightness Pulse**: Smooth fade
   - Effects aligned to beat times with configurable tolerance windows
6. Muxes with original audio track (or selected segment for short-form)
7. Encodes final video: H.264/AAC, 1920×1080 (16:9) or 1080×1920 (9:16), CRF 23
8. Generates poster frame and uploads both to S3
9. Updates `Song` model with `composed_video_s3_key`, duration, FPS

**Beat Synchronization:**
- Uses `beat_times` from `SongAnalysis` for effect timing
- Tolerance windows (default: 50ms) match effects to nearest beats
- Configurable effect frequency (every Nth beat)
- Test mode available for exaggerated effects (3x intensity)

## Video Types

**Full-Length (`full_length`):**
- 16:9 aspect ratio (1920×1080)
- Section-based generation (uses entire track)
- Section segmentation required (intro, verse, chorus, bridge, outro)
- 24fps output

**Short-Form (`short_form`):**
- 9:16 aspect ratio (1080×1920)
- Clip-based generation with audio selection (9-30 seconds)
- No section segmentation required
- 30fps output, optimized encoding for social media (6M bitrate)

## Key Components

- **`ClipPlan`**: Beat-aligned clip boundaries with timing metadata
- **`SceneSpec`**: Visual prompt specification (colors, camera, template, prompt)
- **`SongClip`**: Generated clip metadata (S3 key, prompt, seed, status, cost)
- **`SongAnalysis`**: Music analysis (BPM, beats, sections, genre, mood, lyrics)
- **RQ Job Queue**: Async processing with Redis Queue (timeout: 20-30 min)
- **S3 Storage**: Audio files, video clips, final compositions, character images
- **Cost Tracking**: Per-song generation cost aggregation

## Data Flow

```
Audio Upload → Analysis → Clip Planning → Scene Planning → 
Video Generation (Replicate) → S3 Storage → Composition → 
Beat Effects → Final Video (S3) → User Download
```

## Technical Details

- **Video Codec**: H.264 (libx264) with CRF 23
- **Audio Codec**: AAC at 192k bitrate
- **Frame Rates**: 24fps (full-length), 30fps (short-form)
- **Generator FPS**: 8fps (Minimax Hailuo 2.3)
- **Concurrency**: 4 parallel clip generations (configurable)
- **Polling**: 5s intervals, max 15 minutes per clip
- **Storage Pattern**: `songs/{song_id}/clips/{clip_index:03d}.mp4`

