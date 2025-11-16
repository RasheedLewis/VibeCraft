# Video Composition Testing - Rapid Iteration Workflow

**Goal:** Go from local clips on your Mac Desktop → Final composition video in ONE command.

## Quick Start

```bash
# From project root
source .venv/bin/activate  # Activate virtual environment

# Compose clips - ONE COMMAND!
python scripts/compose_local.py \
  --clips ~/Desktop/clip1.mp4 ~/Desktop/clip2.mp4 ~/Desktop/clip3.mp4 ~/Desktop/clip4.mp4 \
  --audio ~/Desktop/song.mp3 \
  --output ~/Desktop/composed_video.mp4
```

That's it! The script will:
1. Validate all clips
2. Normalize them to 1080p/24fps
3. Stitch them together
4. Mux with audio
5. Output the final video

**Pro tip:** Use shell globbing for multiple clips:
```bash
python scripts/compose_local.py \
  --clips ~/Desktop/clip*.mp4 \
  --audio ~/Desktop/song.mp3 \
  --output ~/Desktop/composed_video.mp4
```

## Prerequisites

```bash
# Make sure FFmpeg is installed
ffmpeg -version

# If not installed:
brew install ffmpeg

# Install Python dependencies (if not already done)
source .venv/bin/activate
pip install -r backend/requirements.txt

# Install Replicate Python client (if not already installed)
pip install replicate
```

## Generate Test Clips

Generate 4 test clips in parallel using the Python script (recommended):

```bash
# Set your Replicate API token
export REPLICATE_API_TOKEN="your_token_here"

# Run the Python script (it will generate all 4 clips in parallel and download them)
python scripts/generate_test_clips.py
```

The script will:
1. Generate all 4 clips in parallel using ThreadPoolExecutor
2. Automatically download them to `~/Desktop/clip1.mp4`, `clip2.mp4`, etc.
3. Print progress for each clip

**Note:** The script uses prompts based on actual examples from your database, with 4 distinct variants. See `scripts/generate_test_clips.py` for the full implementation.

**Cost:** ~$0.14 for 4 clips (4 × $0.035)

## Prepare Audio to Match Clip Duration

After generating clips, trim your audio to match the exact total duration:

```bash
# Step 1: Get total duration of clips (rounded to nearest frame, 1/24s)
python scripts/get_clips_duration.py ~/Desktop/compTest/clip1.mp4 ~/Desktop/compTest/clip2.mp4 ~/Desktop/compTest/clip3.mp4 ~/Desktop/compTest/clip4.mp4

# Output will show: "Use this duration: 16.333333" (example)

# Step 2: Trim audio to that exact duration
python scripts/trim_audio.py ~/Desktop/file.mp3 NUMBER ~/Desktop/compTest/testAudio.mp3
```

The scripts round to the nearest frame (1/24th second) for precise synchronization.

## Full Workflow Examples

### Example 1: Basic Composition
Simply `python scripts/compose_local.py --defaultNames` which expands to the below:

```bash
python scripts/compose_local.py \
  --clips ~/Desktop/clip1.mp4 ~/Desktop/clip2.mp4 ~/Desktop/clip3.mp4 ~/Desktop/clip4.mp4 \
  --audio ~/Desktop/testAudio.mp3 \
  --output ~/Desktop/testComp.mp4
```

### Example 2: With Custom Settings
```bash
python scripts/compose_local.py \
  --clips ~/Desktop/clip*.mp4 \
  --audio ~/Desktop/song.mp3 \
  --output ~/Desktop/composed.mp4 \
  --fps 30 \
  --resolution 1920 1080
```

### Example 3: Verbose Output (see what's happening)
```bash
python scripts/compose_local.py \
  --clips ~/Desktop/clip1.mp4 ~/Desktop/clip2.mp4 \
  --audio ~/Desktop/song.mp3 \
  --output ~/Desktop/result.mp4 \
  --verbose
```

### Example 4: Keep Intermediate Files (for debugging)
```bash
python scripts/compose_local.py \
  --clips ~/Desktop/clip1.mp4 ~/Desktop/clip2.mp4 \
  --audio ~/Desktop/song.mp3 \
  --output ~/Desktop/result.mp4 \
  --keep-temp
```

## Inspecting Normalization

To see what happened during normalization (scaling, letterboxing, FPS conversion):

**Option 1: Keep temporary files**
```bash
python scripts/compose_local.py --defaultNames --keep-temp
```

This keeps the temp directory (path shown in logs) with:
- `normalized_0.mp4`, `normalized_1.mp4`, etc. — the normalized clips
- Compare before/after by playing original clips vs. normalized ones
- Check resolution, FPS, and letterboxing effects

**Option 2: Verbose output**
```bash
python scripts/compose_local.py --defaultNames --verbose --keep-temp
```

Shows detailed FFmpeg commands and progress. The normalized files will be in a temp directory like `/var/folders/.../tmpXXXXXX/` (the path is logged).

**What normalization does:**
- Scales clips to 1080p (1920x1080) with letterboxing if needed (preserves aspect ratio)
- Converts FPS to 24 (from original 8 FPS for Zeroscope clips)
- Re-encodes to H.264
- **Note:** Does NOT do color grading, color correction, or consistency adjustments between clips

## Script Options

```bash
python scripts/compose_local.py --help

Options:
  --clips CLIP [CLIP ...]    Input video clip files (required)
  --audio AUDIO              Input audio file (required)
  --output OUTPUT            Output video file path (required)
  --fps FPS                  Target FPS (default: 24)
  --resolution WIDTH HEIGHT  Target resolution (default: 1920 1080)
  --verbose                  Show detailed progress
  --keep-temp                Keep temporary files after completion
  --ffmpeg-bin PATH          Custom FFmpeg binary path
```

## Testing Individual Steps

### 1. Validate Clips
```bash
python -c "
from app.services.video_composition import validate_composition_inputs
metadata = validate_composition_inputs(['~/Desktop/clip1.mp4', '~/Desktop/clip2.mp4'])
for m in metadata:
    print(f'Clip: {m.width}x{m.height} @ {m.fps}fps, duration={m.duration_sec}s')
"
```

### 2. Normalize a Single Clip
```bash
python -c "
from app.services.video_composition import normalize_clip
normalize_clip('~/Desktop/clip1.mp4', '~/Desktop/clip1_normalized.mp4')
print('Normalized!')
"
```

### 3. Concatenate Clips (already normalized)
```bash
python -c "
from app.services.video_composition import concatenate_clips
result = concatenate_clips(
    normalized_clip_paths=['~/Desktop/clip1_normalized.mp4', '~/Desktop/clip2_normalized.mp4'],
    audio_path='~/Desktop/song.mp3',
    output_path='~/Desktop/result.mp4',
    song_duration_sec=180.0
)
print(f'Composed: {result.duration_sec}s, {result.width}x{result.height} @ {result.fps}fps')
"
```

## Transitions: Hard Cuts vs. Crossfades

**Current implementation:** Hard cuts only (immediate transition from one clip to the next)

**Hard Cuts:**
- Instant transition: clip 1 ends → clip 2 starts immediately
- No overlap or blending
- Fastest to process, preserves all video content
- Current behavior: Uses FFmpeg concat demuxer for direct concatenation

**Crossfades (not yet implemented):**
- Smooth transition: clip 1 fades out while clip 2 fades in
- Overlapping transition (e.g., 0.5 seconds)
- More visually smooth, but requires overlap calculation and FFmpeg xfade filter
- Example: Last 0.5s of clip 1 fades out while first 0.5s of clip 2 fades in

**To test crossfades (future):**
- Will require implementing `concatenate_clips_with_crossfade()` function
- Uses FFmpeg `xfade` filter: `[0:v][1:v]xfade=transition=fade:duration=0.5:offset=4.5[v]`
- Need to handle timing: clips must overlap, so total duration will be slightly shorter

## Testing with Many Clips (40 Clips)

**Before MVP-03 is complete, test with 40 clips:**
- Verify memory usage during normalization (parallel processing)
- Check concatenation performance with many clips
- Ensure duration handling works correctly
- Test with `--keep-temp` to inspect all normalized clips

**Note:** Beat-aligned logic will wait until we have real sections from the database instead of hard-coded test clips. For now, we test with 40 clips using the `--40clips` flag.

**Easy 40-clip test (single command):**
```bash
python scripts/compose_local.py --defaultNames --40clips
```

This automatically:
- Uses clip1.mp4, clip2.mp4, clip3.mp4, clip4.mp4 from `samples/compTest/`
- Creates 9 copies of each (10 total of each = 40 clips)
- Interleaves them: clip1, clip2, clip3, clip4, clip1-copy1, clip2-copy1, clip3-copy1, clip4-copy1, clip1-copy2, clip2-copy2, ...
- Composes all 40 clips with testAudio.mp3
- Outputs to testComp.mp4

**With additional options:**
```bash
python scripts/compose_local.py --defaultNames --40clips --keep-temp --verbose
```

**Manual 40-clip test (if you have 40 different clips):**
```bash
python scripts/compose_local.py \
  --clips clip1.mp4 clip2.mp4 ... clip40.mp4 \
  --audio testAudio.mp3 \
  --output testComp_40clips.mp4 \
  --keep-temp \
  --verbose
```

## Controlling File Size

**Why composed videos are larger than expected:**

When normalizing clips from lower resolution/FPS to 1080p @ 24fps, file size increases significantly:
- **Resolution upscaling**: 576×320 → 1920×1080 = 11.25× more pixels
- **FPS increase**: 8fps → 24fps = 3× more frames
- **Total data increase**: ~33.75× more raw data before compression

Example: 4 clips totaling 3.5MB → 40 clips at 1080p/24fps = ~141MB (compressed)

**Current encoding settings:**
- **CRF**: 23 (medium quality, range 18-28)
- **Preset**: "medium" (encoding speed vs compression tradeoff)
- **Resolution**: 1920×1080 (fixed for MVP)
- **FPS**: 24 (fixed for MVP)

**Options to reduce file size:**

1. **Increase CRF** (smaller file, lower quality):
   - Current: `CRF = 23`
   - Smaller: `CRF = 26-28` (acceptable quality, ~30-50% smaller)
   - Edit: `backend/app/services/video_composition.py` → `DEFAULT_CRF = 23`

2. **Use slower preset** (better compression, slower encoding):
   - Current: `preset = "medium"`
   - Better compression: `preset = "slow"` or `"veryslow"` (~10-20% smaller, 2-5× slower)
   - Edit: `backend/app/services/video_composition.py` → `normalize_clip()` and `concatenate_clips()`

3. **Reduce resolution** (smaller file, lower resolution):
   - Current: 1920×1080
   - Smaller: 1280×720 (~44% fewer pixels, ~40% smaller file)
   - Edit: `backend/app/services/video_composition.py` → `DEFAULT_TARGET_RESOLUTION = (1920, 1080)`

4. **Reduce FPS** (smaller file, less smooth):
   - Current: 24fps
   - Smaller: 20fps (~17% fewer frames, ~15% smaller file)
   - Edit: `backend/app/services/video_composition.py` → `DEFAULT_TARGET_FPS = 24`

**For MVP:** 1080p @ 24fps with CRF 23 is recommended. If file size is a concern, increase CRF to 26-28.

**Note:** These settings apply to both the local test script and the production pipeline.

## Common Issues & Fixes

### "FFmpeg not found"
```bash
# Check if FFmpeg is in PATH
which ffmpeg

# If not, add to PATH or use --ffmpeg-bin
python scripts/compose_local.py ... --ffmpeg-bin /usr/local/bin/ffmpeg
```

### "Clip validation failed"
- Check that clips are valid MP4 files: `ffprobe ~/Desktop/clip1.mp4`
- Make sure clips are readable: `ls -l ~/Desktop/clip*.mp4`

### "Audio sync issues"
- Check audio file: `ffprobe ~/Desktop/song.mp3`
- Try re-encoding audio: `ffmpeg -i ~/Desktop/song.mp3 -c:a aac -b:a 192k ~/Desktop/song_fixed.mp3`

### "Out of memory"
- Process fewer clips at once
- Close other applications
- Use smaller resolution: `--resolution 1280 720`

## Quick Test with Sample Data

```bash
# Create test clips (if you don't have any)
ffmpeg -f lavfi -i testsrc=duration=5:size=576x320:rate=8 -c:v libx264 ~/Desktop/test_clip1.mp4
ffmpeg -f lavfi -i testsrc2=duration=5:size=576x320:rate=8 -c:v libx264 ~/Desktop/test_clip2.mp4

# Create test audio (MP3)
ffmpeg -f lavfi -i "sine=frequency=440:duration=10" -c:a libmp3lame -b:a 192k ~/Desktop/test_audio.mp3
# Alternative (AAC): use -c:a aac and .m4a extension

# Compose
python scripts/compose_local.py \
  --clips ~/Desktop/test_clip1.mp4 ~/Desktop/test_clip2.mp4 \
  --audio ~/Desktop/test_audio.mp3 \
  --output ~/Desktop/test_result.mp4
```

## Performance Tips

- **Parallel normalization**: The script automatically normalizes clips in parallel (4 workers)
- **Fast concatenation**: Uses FFmpeg concat demuxer for fastest stitching
- **Skip validation**: Use `--skip-validation` to skip pre-flight checks (faster, but less safe)

## What Gets Created

```
~/Desktop/
  clip1.mp4          (your input)
  clip2.mp4          (your input)
  song.mp3           (your input)
  composed_video.mp4 (final output)
  
/tmp/compose_XXXXXX/ (temporary directory, auto-cleaned)
  clip_0.mp4         (downloaded/normalized clips)
  clip_1.mp4
  normalized_0.mp4   (normalized clips)
  normalized_1.mp4
  concat_list.txt    (FFmpeg concat file)
  composed.mp4       (final before copy to output)
```

## Next Steps After Testing

Once you're happy with the local workflow:
1. Test with real clips from Replicate (download them first)
2. Test the full API workflow (POST /api/songs/:id/compose)
3. Test with Trigger.dev task

## Troubleshooting

### See FFmpeg commands being run
```bash
export FFMPEG_VERBOSE=1
python scripts/compose_local.py ...
```

### Debug a specific step
```python
# In Python REPL
from app.services.video_composition import *
import logging
logging.basicConfig(level=logging.DEBUG)

# Run your test
validate_composition_inputs(['~/Desktop/clip1.mp4'])
```
