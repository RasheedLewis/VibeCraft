# Why Two Composition Code Paths?

## Overview

There are two separate composition pipelines because the app supports two different video types with different data models and requirements.

## The Two Paths

### Path 1: SongClip Composition (Short Form Videos)
- **Endpoint**: `/songs/{song_id}/clips/compose/async`
- **Function Chain**: `enqueue_song_clip_composition` → `run_song_clip_composition_job` → `compose_song_video`
- **Data Model**: `SongClip` (simple clip model)
- **Use Case**: Short-form videos (30-second clips)
- **Behavior**: 
  - Automatically gets all completed SongClips for the song
  - No metadata needed (clips are already positioned)
  - Simpler, straightforward composition
- **Frontend Usage**: ✅ Currently used by frontend

### Path 2: SectionVideo Composition (Full Length Videos)
- **Endpoint**: `/songs/{song_id}/compose`
- **Function Chain**: `enqueue_composition` → `run_composition_job` → `execute_composition_pipeline`
- **Data Model**: `SectionVideo` (section-based clips with metadata)
- **Use Case**: Full-length videos with sections
- **Behavior**:
  - Requires explicit clip IDs and metadata (startFrame/endFrame)
  - Supports beat-aligned clip boundaries
  - More complex pipeline with beat alignment logic
- **Frontend Usage**: Not currently used (for future full-length video feature)

## Why They Exist

The split exists because:
1. **Different data models**: `SongClip` vs `SectionVideo` have different structures
2. **Different complexity**: Full-length videos need beat alignment, section metadata, etc.
3. **Feature flag**: `should_use_sections_for_song()` determines which path based on `video_type`:
   - `short_form` → SongClip path
   - `full_length` → SectionVideo path

## Current State

- **Frontend uses**: SongClip path (`/clips/compose/async`)
- **Both paths now support**: Beat-synced visual effects (fixed today)
- **Issue**: Code duplication - both paths do similar work but separately

## Potential Consolidation

Both paths could potentially be unified since they:
- Use the same `concatenate_clips()` function
- Both support beat filters (now)
- Both normalize clips the same way

The main difference is:
- SongClip path: Auto-discovers clips
- SectionVideo path: Requires explicit clip selection with metadata

## Recommendation

Consider consolidating into a single pipeline that:
1. Detects video type
2. Gets clips appropriately (auto vs explicit)
3. Uses unified composition logic

This would reduce maintenance burden and ensure both paths stay in sync.

