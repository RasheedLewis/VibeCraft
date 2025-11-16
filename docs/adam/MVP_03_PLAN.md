# MVP-03 Plan: Video Composition & Stitching

**Goal:** Rapidly prototype and iterate on FFmpeg-based video stitching to validate the composition pipeline.

## Context for Fresh Start

### What MVP-03 Does
Stitch 3-5 video clips together into a single music video with:
- Audio muxed from original song
- Normalized resolution (1080p) and FPS (30+)
- Basic transitions at clip boundaries
- Beat-aligned cuts (optional, using MVP-02 boundaries)

### What Already Exists

**Video Clips:**
- Clips are stored in `SectionVideo` model (`backend/app/models/section_video.py`)
- Each clip has: `video_url` (Replicate URL), `duration_sec`, `fps`, `resolution_width`, `resolution_height`
- Clips are generated via Replicate API (Zeroscope v2 XL) at 8 FPS, 576x320 resolution
- Clips stored in database with `song_id` and `section_id` for lookup

**Audio:**
- Original song audio stored in S3 (`Song.original_s3_key` or `Song.processed_s3_key`)
- Can download via `app/services/storage.py::download_bytes_from_s3()`
- Song duration available in `Song.duration_sec` or `SongAnalysis.duration_sec`

**Beat Alignment (MVP-02):**
- `GET /api/songs/:id/beat-aligned-boundaries` returns clip boundaries
- Boundaries include beat indices, frame indices, and alignment metadata
- Can use these to ensure transitions happen on beats

**Storage Service:**
- `backend/app/services/storage.py` provides:
  - `download_bytes_from_s3()` - Download files from S3
  - `upload_bytes_to_s3()` - Upload files to S3
  - `generate_presigned_get_url()` - Generate access URLs

**Database Models:**
- `Song` - Song metadata, audio S3 keys, duration
- `SongAnalysis` - Analysis results (BPM, beats, sections, mood, genre)
- `SectionVideo` - Generated video clips with metadata
- `SongAnalysisRecord` - Stored analysis JSON

### Key Files to Understand

1. **`backend/app/models/section_video.py`** - SectionVideo model (clip storage)
2. **`backend/app/models/song.py`** - Song model (audio storage)
3. **`backend/app/services/storage.py`** - S3 upload/download utilities
4. **`backend/app/services/beat_alignment.py`** - Beat-aligned boundaries (MVP-02)
5. **`backend/app/api/v1/routes_videos.py`** - Video generation API (example pattern)
6. **`backend/app/core/config.py`** - Settings (S3 config, FFmpeg path)

### Prerequisites

- FFmpeg installed and available in PATH (or set `FFMPEG_BIN` env var)
- Access to S3 storage (for downloading audio, uploading final video)
  - Bucket name: `ai-music-video` (default, configurable via `S3_BUCKET_NAME` env var)
  - Verify S3 access:
    ```bash
    # Test S3 connection (requires AWS CLI or boto3)
    python -c "from app.core.config import get_settings; from app.services.storage import _get_s3_client; s = get_settings(); client = _get_s3_client(); print('Bucket exists:', client.head_bucket(Bucket=s.s3_bucket_name))"
    ```
- Clips already generated (via MVP-01 or existing SectionVideo records)
- Song analysis complete (for beat alignment data)

### Input Data

**For composition, you'll need:**
- List of `SectionVideo` records (clips to stitch)
- Original song audio file (from S3)
- Optional: Beat-aligned boundaries (from MVP-02) for beat-synced transitions

**Clip metadata available:**
- `video_url` - Direct URL to clip (Replicate CDN)
- `duration_sec` - Clip duration
- `fps` - Frames per second (typically 8 from Zeroscope)
- `resolution_width`, `resolution_height` - Clip dimensions (typically 576x320)
- `start_time`, `end_time` - If using beat-aligned boundaries

### Output

- Single MP4 file (1080p, 30 FPS)
- Audio synced with video
- Uploaded to S3
- Presigned URL for access

## Architecture

### Job Flow
1. **API Endpoint** (`POST /api/songs/:id/compose`) → Creates `CompositionJob` → Enqueues to RQ → Returns job ID
2. **RQ Worker** (`run_composition_job`) → Executes pipeline directly in background worker
3. **Progress Tracking** → Updates `CompositionJob` status/progress at each stage
4. **Result Storage** → Creates `ComposedVideo` record with S3 key and metadata

### Data Models

**New Models:**
- `CompositionJob` (`backend/app/models/composition.py`): Tracks job status, progress, errors, clip IDs, and metadata
- `ComposedVideo` (`backend/app/models/composition.py`): Stores final video metadata, links to song and clips used

**Existing Models Used:**
- `SectionVideo`: Source clips (already have `video_url`, metadata)
- `Song`: Source audio (has `original_s3_key` or `processed_s3_key`)

### Key Services

1. **`video_composition.py`**: Core FFmpeg operations
   - `validate_composition_inputs()`: Pre-flight checks using ffprobe
   - `normalize_clip()`: Scale to 1080p, convert FPS to 24, re-encode to H.264
   - `concatenate_clips()`: Stitch normalized clips, mux audio, handle duration mismatch
   - `extend_last_clip()`: Extend last clip with fadeout if needed
   - `verify_composed_video()`: Quality checks

2. **`composition_job.py`**: Job orchestration
   - `enqueue_composition()`: Create job, store clip IDs and metadata
   - `update_job_progress()`: Update status/progress
   - `get_job_status()`: Query job status
   - `cancel_job()`: Cancel a job
   - `create_composed_video()`: Create final video record

3. **`composition_execution.py`**: Pipeline execution
   - `execute_composition_pipeline()`: Full pipeline orchestration
   - Handles: validation → download → normalize (parallel) → stitch → upload → verify

4. **RQ Worker Function** (`run_composition_job` in `composition_job.py`):
   - Executes pipeline directly in background worker
   - Handles job lifecycle (progress updates, completion, failures)
   - Uses RQ for queue management, retries, and job tracking

### API Endpoints

- `POST /api/songs/:id/compose` - Enqueue composition job (enqueues to RQ)
- `GET /api/songs/:id/compose/:jobId/status` - Get job status
- `POST /api/songs/:id/compose/:jobId/cancel` - Cancel job
- `GET /api/songs/:id/composed-videos/:composedVideoId` - Get composed video details

## Approach: Rapid Iteration

Start simple, iterate quickly. Build a working prototype first, then refine.

## Phase 1: Basic Concatenation

**Goal:** Get 3-5 clips stitched together with audio synced.

### Steps:
1. **Create simple FFmpeg service** (`backend/app/services/video_composition.py`)
   - Function: `concatenate_clips(clip_urls: list[str], output_path: str) -> str`
   - Use FFmpeg concat demuxer (fastest, preserves quality)
   - Input: List of clip URLs (download temporarily or use direct URLs)
   - Output: Single MP4 file

2. **Basic FFmpeg command:**
   ```bash
   # Create concat file
   # file 'clip1.mp4'
   # file 'clip2.mp4'
   # file 'clip3.mp4'
   
   ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp4
   ```

3. **Test with sample clips:**
   - Download 3-5 test clips from Replicate
   - Run concatenation locally
   - Verify output plays correctly

4. **Add audio muxing:**
   ```bash
   ffmpeg -f concat -safe 0 -i concat_list.txt -i song.mp3 -c:v copy -c:a aac -shortest output.mp4
   ```

## Phase 2: Normalization

**Goal:** Ensure all clips have same resolution/FPS before concatenation.

### Steps:
1. **Detect clip properties:**
   - Use `ffprobe` to get resolution, FPS, codec for each clip
   - Log differences for debugging

2. **Normalize resolution to 1080p:**
   ```bash
   ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2" output.mp4
   ```

3. **Normalize FPS (upscale from 8 FPS to 30 FPS):**
   ```bash
   # Frame interpolation using minterpolate filter
   ffmpeg -i input.mp4 -vf "minterpolate=fps=30:mi_mode=mci" output.mp4
   
   # Or simpler (duplicate frames):
   ffmpeg -i input.mp4 -r 30 -c:v libx264 output.mp4
   ```

4. **Pre-process all clips before concatenation:**
   - Normalize each clip individually
   - Then concatenate normalized clips

## Phase 3: Transitions

**Goal:** Add basic transitions at clip boundaries.

### Hard Cuts (Simplest):
- Already works with basic concatenation
- No additional FFmpeg work needed

### Crossfade (Quick to test):
```bash
# Crossfade between clips (0.5 second overlap)
ffmpeg -i clip1.mp4 -i clip2.mp4 -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.5[v]" -map "[v]" output.mp4
```

### Beat-Synced Cuts (If beat metadata available):
- Use beat-aligned boundaries from MVP-02
- Ensure cuts happen exactly at beat times
- May need to trim clips to exact beat boundaries

## Phase 4: Audio Sync & Quality

**Goal:** Ensure audio stays in sync and quality is good.

### Steps:
1. **Audio sync:**
   - Use `-shortest` flag to match video duration
   - Use `-async 1` for audio resampling if needed
   - Test with different song lengths

2. **Audio quality:**
   - Use AAC codec: `-c:a aac -b:a 192k`
   - Or copy original audio if possible: `-c:a copy`

3. **Verify sync:**
   - Test with songs that have clear beats
   - Check that audio aligns with video transitions

## Phase 5: Storage & API

**Goal:** Integrate with storage and create API endpoint.

### Steps:
1. **Upload to S3:**
   - Use existing `storage.py` service
   - Upload final composed video
   - Return presigned URL

2. **Create API endpoint:**
   - `POST /api/songs/:id/compose`
   - Input: List of clip IDs or URLs
   - Output: Job ID (background processing)
   - Store composition job status in database

3. **Background job:**
   - Use RQ worker (like analysis jobs)
   - Track progress: downloading clips → normalizing → concatenating → uploading

## FFmpeg Command Reference

### Basic Concatenation:
```bash
# Method 1: Concat demuxer (fastest, preserves quality)
ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp4

# Method 2: Concat filter (allows transitions)
ffmpeg -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 -filter_complex "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[outv][outa]" -map "[outv]" -map "[outa]" output.mp4
```

### Normalization:
```bash
# Resolution + FPS normalization
ffmpeg -i input.mp4 -vf "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30" -c:v libx264 -preset medium -crf 23 output.mp4
```

### With Audio:
```bash
ffmpeg -f concat -safe 0 -i concat_list.txt -i song.mp3 -c:v libx264 -c:a aac -b:a 192k -shortest output.mp4
```

### Crossfade Transition:
```bash
ffmpeg -i clip1.mp4 -i clip2.mp4 -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.5[v]" -map "[v]" output.mp4
```

## Testing Strategy

1. **Local testing first:**
   - Download sample clips manually
   - Test FFmpeg commands in terminal
   - Verify output quality and sync

2. **Unit test FFmpeg commands:**
   - Create test fixtures (sample clips)
   - Test each FFmpeg operation in isolation
   - Verify output properties (resolution, FPS, duration)

3. **Integration test:**
   - Test full pipeline with real clips from database
   - Verify audio sync with actual song
   - Check file upload to S3

## Key Decisions

1. **FFmpeg vs. Python libraries:**
   - Use FFmpeg directly (via subprocess) for maximum control
   - Python libraries (moviepy, etc.) are slower and less flexible

2. **Frame interpolation:**
   - Start with simple frame duplication (`-r 30`)
   - Upgrade to `minterpolate` if quality is poor
   - Consider `rife` filter for better interpolation (slower)

3. **Transitions:**
   - Start with hard cuts (zero work)
   - Add crossfade if time permits
   - Beat-synced transitions can come later

4. **Error handling:**
   - FFmpeg can fail for many reasons (codec issues, corrupt files, etc.)
   - Log full FFmpeg output for debugging
   - Retry logic for transient failures

## Success Criteria

- [ ] Can concatenate 3-5 clips into single video
- [ ] All clips normalized to 1080p/30fps
- [ ] Audio synced with video (no drift)
- [ ] Final video plays correctly
- [ ] Uploaded to S3 and accessible via URL
- [ ] API endpoint works end-to-end

## Next Steps After MVP-03

- Color grading LUT application
- More sophisticated transitions (flares, zooms)
- Beat-synced transition timing
- Performance optimization (parallel processing)

