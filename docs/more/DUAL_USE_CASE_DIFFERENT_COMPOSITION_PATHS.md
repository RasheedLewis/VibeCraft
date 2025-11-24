# Why Two Composition Code Paths?

## Overview

There are two separate composition pipelines because the app supports two different video types with different data models and requirements. However, the implementation has evolved and both paths now share more similarities than differences.

## The Two Paths

### Path 1: SongClip Composition (Short Form Videos)

- **Endpoint**: `/songs/{song_id}/clips/compose/async`
- **Function Chain**: `enqueue_song_clip_composition` → `run_song_clip_composition_job` → `compose_song_video`
- **Data Model**: `SongClip` (simple clip model with clip_index, start_sec, end_sec)
- **Use Case**: Short-form videos (30-second clips)
- **Behavior**:
  - Automatically gets all completed SongClips for the song via `ClipRepository.get_completed_by_song_id()`
  - No metadata needed (clips are already positioned by clip_index)
  - Simpler, straightforward composition
  - Stores result directly on `Song` model:
    - `song.composed_video_s3_key`
    - `song.composed_video_poster_s3_key`
    - `song.composed_video_duration_sec`
    - `song.composed_video_fps`
  - **Does NOT create** a `ComposedVideo` record
  - **Does NOT support** beat-aligned clip boundaries
- **Features**:
  - ✅ Beat-synced visual effects (via `concatenate_clips()` with beat_times)
  - ✅ Audio selection support (uses `song.selected_start_sec` and `song.selected_end_sec` if present)
  - ✅ Parallel clip normalization (ThreadPoolExecutor with 4 workers)
  - ✅ Downloads clips from S3 keys (pattern: `songs/{song_id}/clips/{clip_index:03d}.mp4`) with fallback to presigned URLs
  - ✅ Generates video poster/thumbnail
  - ✅ Progress tracking via `CompositionJob` (10% → 100%)
- **Frontend Usage**: ✅ Currently used by frontend

### Path 2: SectionVideo Composition (Full Length Videos)

- **Endpoint**: `/songs/{song_id}/compose`
- **Function Chain**: `enqueue_composition` → `run_composition_job` → `execute_composition_pipeline`
- **Data Model**: `SectionVideo` (section-based clips) OR `SongClip` (via `clip_model_selector` based on `video_type`)
- **Use Case**: Full-length videos with sections (or explicit clip selection)
- **Behavior**:
  - Requires explicit clip IDs and metadata (startFrame/endFrame) in request
  - Uses `clip_model_selector.get_clips_for_composition()` which:
    - Determines model type via `should_use_sections_for_song(song)`
    - Supports both `SectionVideo` and `SongClip` models based on `song.video_type`
  - Creates a `ComposedVideo` record (separate from Song model)
  - More complex pipeline with detailed progress tracking
- **Features**:
  - ✅ Beat-aligned clip boundaries (feature flag `beat_aligned = True` in `execute_composition_pipeline`)
    - Uses `calculate_beat_aligned_clip_boundaries()` to adjust clip durations
    - Trims or extends clips to match beat boundaries
  - ✅ Beat-synced visual effects (via `concatenate_clips()` with beat_times)
  - ✅ Parallel clip downloads (ThreadPoolExecutor with 4 workers)
  - ✅ Parallel clip normalization (ThreadPoolExecutor with 4 workers)
  - ✅ Duration mismatch handling (extends/trims last clip if within 5s tolerance)
  - ✅ Detailed progress milestones (validation → download → normalize → stitch → upload → verify)
  - ✅ Job cancellation support (checks job status periodically)
  - ✅ Cost tracking logging
  - ❌ **Does NOT support** audio selection (uses full song audio)
  - ❌ **Does NOT generate** video poster/thumbnail
- **Frontend Usage**: Not currently used (for future full-length video feature)

## Key Differences

### Data Storage
- **Path 1**: Stores composed video metadata directly on `Song` model
- **Path 2**: Creates separate `ComposedVideo` record linked via `CompositionJob.composed_video_id`

### Clip Discovery
- **Path 1**: Auto-discovers all completed SongClips (no user input needed)
- **Path 2**: Requires explicit clip IDs and metadata in API request

### Beat Alignment
- **Path 1**: No beat-aligned clip boundary adjustment
- **Path 2**: Supports beat-aligned clip boundaries (trims/extends clips to beat times)

### Audio Handling
- **Path 1**: Supports audio selection (`selected_start_sec`/`selected_end_sec`)
- **Path 2**: Always uses full song audio

### Output Artifacts
- **Path 1**: Generates both video and poster/thumbnail
- **Path 2**: Only generates video (no poster)

### Model Flexibility
- **Path 1**: Only works with `SongClip` model
- **Path 2**: Works with both `SectionVideo` and `SongClip` via `clip_model_selector` (determined by `video_type`)

## Why They Exist

The split exists because:

1. **Different use cases**: 
   - Path 1: Simple "compose all clips" for short-form videos
   - Path 2: Explicit clip selection with metadata for full-length videos
2. **Different data storage**: Song model vs ComposedVideo record
3. **Different complexity**: Path 2 has beat alignment, duration mismatch handling, cancellation support
4. **Feature flag**: `should_use_sections_for_song()` determines which model Path 2 uses:
   - `short_form` → Uses `SongClip` model
   - `full_length` → Uses `SectionVideo` model

## Current State

- **Frontend uses**: Path 1 (`/clips/compose/async`) for short-form videos
- **Both paths support**: 
  - Beat-synced visual effects (via `concatenate_clips()`)
  - Parallel processing (downloads and normalization)
  - Progress tracking via `CompositionJob`
- **Shared code**: Both use `concatenate_clips()`, `normalize_clip()`, and `video_composition` utilities
- **Issue**: Significant code duplication - both paths do similar work but separately

## Potential Consolidation

Both paths could potentially be unified since they:

- Use the same `concatenate_clips()` function
- Both support beat-synced visual effects
- Both normalize clips the same way (parallel processing)
- Both use `CompositionJob` for progress tracking
- Both download clips similarly (Path 2 uses URLs, Path 1 uses S3 keys with URL fallback)

The main differences are:

- **Clip discovery**: Auto vs explicit
- **Beat alignment**: Path 2 only
- **Data storage**: Song model vs ComposedVideo record
- **Audio selection**: Path 1 only
- **Poster generation**: Path 1 only

## Recommendation

Consider consolidating into a single pipeline that:

1. Detects video type and use case
2. Gets clips appropriately (auto vs explicit) based on endpoint/request
3. Uses unified composition logic with optional features (beat alignment, audio selection, poster generation)
4. Stores results consistently (either always use ComposedVideo or always use Song model)

This would reduce maintenance burden and ensure both paths stay in sync, especially for shared features like beat-synced effects.
