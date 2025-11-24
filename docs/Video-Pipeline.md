# VibeCraft Video Pipeline

## Overview

The VibeCraft video pipeline transforms audio files into beat-synchronized music videos through three main stages: **Planning**, **Generation**, and **Composition**. The system supports two video types: **full_length** (16:9) and **short_form** (9:16).

## Pipeline Stages

### 1. Planning (`clip_planning.py`, `scene_planner.py`)

**Clip Planning** calculates beat-aligned clip boundaries from music analysis:
- Snaps boundaries to beat grid using `beat_times` from `SongAnalysis`
- Generates `ClipPlan` objects (3-6 second clips, aligned to 8fps frame intervals)
- Supports audio selection for short-form videos (9-30 second segments)
- Falls back to uniform distribution if no beats detected

**Scene Planning** converts analysis data into visual prompts:
- Maps mood → color palettes (vibrant, intense, calm, melancholic)
- Maps genre → camera motions (slow pan, dynamic tracking, static)
- Selects visual templates (abstract, environment, character, minimal)
- Builds `SceneSpec` objects with prompts, colors, camera motion, and shot patterns
- Incorporates lyrics and section context for full-length videos

### 2. Generation (`clip_generation.py`, `video_generation.py`)

**Clip Generation** orchestrates parallel video creation via Replicate API (4 concurrent by default):

**Workflow:**
1. Enqueues clip generation jobs with controlled concurrency
2. For each clip: builds `SceneSpec`, selects character images, generates video
3. Generation modes:
   - **Text-to-video**: Pure prompt-based generation
   - **Image-to-video**: Character consistency using reference images (Minimax Hailuo 2.3)
4. Polls Replicate API (max 180 attempts, 5s intervals)
5. Downloads generated video, uploads to S3, stores `SongClip` metadata

**Video Provider Pattern** (`video_providers/`): Abstract `VideoGenerationProvider` base with `MinimaxHailuoProvider` implementation. Handles aspect ratios (768p 16:9, 1080p 9:16) and generation modes.

**Character Consistency** (optional): Image interrogation (GPT-4o Vision/Replicate) → consistent character generation (SDXL) → image-to-video with pose selection (A/B). 9:16 image padding for short-form.

### 3. Composition (`video_composition.py`, `clip_generation.py`)

**Video Composition** stitches clips into final video:

**Process:**
1. Retrieves completed `SongClip` records, downloads from S3 (parallel normalization)
2. Normalizes clips: FPS (24fps full-length, 30fps short-form), resolution, codec
3. Concatenates with beat-aligned cuts using FFmpeg
4. Applies beat-synced visual effects via `BeatFilterApplicator`:
   - Flash, Color Burst, Zoom Pulse, Glitch, Brightness Pulse
   - Effects aligned to beat times with configurable tolerance windows (50ms default)
5. Muxes with original audio track (or selected segment for short-form)
6. Encodes final video: H.264/AAC, 1920×1080 (16:9) or 1080×1920 (9:16), CRF 23
7. Generates poster frame, uploads to S3, updates `Song` model

## Video Types

**Full-Length (`full_length`)**: 16:9 (1920×1080), section-based generation, requires section segmentation, 24fps output.

**Short-Form (`short_form`)**: 9:16 (1080×1920), clip-based with audio selection (9-30s), no section segmentation, 30fps output optimized for social media (6M bitrate).

## Key Components & Technical Details

**Data Models**: `ClipPlan` (beat-aligned boundaries), `SceneSpec` (visual prompts), `SongClip` (generated clip metadata), `SongAnalysis` (BPM, beats, sections, genre, mood, lyrics).

**Infrastructure**: RQ Job Queue (Redis, 20-30 min timeout), S3 Storage (audio, clips, compositions, characters), Cost Tracking (per-song aggregation).

**Encoding**: H.264 (libx264) CRF 23, AAC 192k, Generator FPS 8 (Minimax Hailuo 2.3). Storage pattern: `songs/{song_id}/clips/{clip_index:03d}.mp4`.

## Data Flow

```
Audio Upload → Analysis → Clip Planning → Scene Planning → 
Video Generation (Replicate) → S3 Storage → Composition → 
Beat Effects → Final Video (S3) → User Download
```
