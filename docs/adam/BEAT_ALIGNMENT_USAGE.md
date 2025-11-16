# How to Use Beat-Aligned Boundaries for Clip Generation

## Overview

The beat alignment helper calculates where clip boundaries should be placed so that **transitions between clips happen on beats**. This ensures smooth, musically-synced video transitions.

## The Problem

Video generation APIs (like Replicate's Zeroscope) let you specify:
- `num_frames`: Number of frames to generate
- `fps`: Frames per second

Together, these give you exact timing: `duration = num_frames / fps`

**Example:** 48 frames at 8 FPS = 6 seconds exactly

The challenge: We want clip transitions to happen **on beats**, not at arbitrary times.

## The Solution

Use `calculate_beat_aligned_boundaries()` to:
1. Find beat-aligned boundaries (where clips should start/end)
2. Calculate exact `num_frames` for each clip based on boundary duration
3. Generate clips with those exact frame counts
4. When stitching, transitions automatically happen on beats

## Workflow

### Step 1: Get Beat-Aligned Boundaries

```python
from app.services.beat_alignment import calculate_beat_aligned_boundaries
from app.services.song_analysis import get_latest_analysis

# Get song analysis (contains beat_times)
analysis = get_latest_analysis(song_id)

# Calculate boundaries aligned to beats
# fps should match your video generation API (e.g., 8 for Zeroscope)
boundaries = calculate_beat_aligned_boundaries(
    beat_times=analysis.beat_times,
    song_duration=analysis.duration_sec,
    fps=8.0,  # Match your video generation API FPS
)
```

**Result:** List of `ClipBoundary` objects, each with:
- `start_time`, `end_time`: Beat-aligned timestamps
- `start_beat_index`, `end_beat_index`: Which beats this clip spans
- `start_frame_index`, `end_frame_index`: Frame indices for alignment
- `duration_sec`: Clip duration (3-6 seconds)

### Step 2: Calculate num_frames for Each Clip

```python
fps = 8.0  # Your video generation API FPS

for boundary in boundaries:
    # Calculate exact number of frames needed
    num_frames = int(boundary.duration_sec * fps)
    
    # Example: 4.5 seconds * 8 fps = 36 frames
    # This ensures the clip ends exactly at the beat boundary
```

### Step 3: Generate Video Clips

```python
from app.services.video_generation import generate_section_video
from app.services.scene_planner import build_scene_spec

for i, boundary in enumerate(boundaries):
    # Build scene spec for this clip
    scene_spec = build_scene_spec(
        section_id=f"clip-{i}",
        analysis=analysis,
        template="abstract",
    )
    
    # Override duration to match boundary
    scene_spec.duration_sec = boundary.duration_sec
    
    # Generate video with exact frame count
    num_frames = int(boundary.duration_sec * fps)
    
    # Call video generation API with num_frames
    # (You'll need to modify generate_section_video to accept num_frames)
    success, video_url, metadata = generate_section_video(
        scene_spec=scene_spec,
        num_frames=num_frames,  # Exact frame count for beat alignment
        fps=fps,
    )
    
    # Store clip with boundary metadata
    clip = {
        "video_url": video_url,
        "start_time": boundary.start_time,
        "end_time": boundary.end_time,
        "start_beat_index": boundary.start_beat_index,
        "end_beat_index": boundary.end_beat_index,
        "num_frames": num_frames,
        "fps": fps,
    }
```

### Step 4: Stitch Clips Together

When stitching clips (MVP-03), transitions automatically happen on beats because:
- Each clip ends at a beat boundary (`boundary.end_time` aligns with a beat)
- The next clip starts at the next beat boundary (`boundary.start_time` aligns with a beat)
- No need to calculate transition timing - it's already beat-aligned!

```python
# When stitching clips together
clips = [clip1, clip2, clip3, ...]

# Transitions happen at:
# - clip1.end_time (beat-aligned)
# - clip2.start_time (same beat, so seamless transition)
# - clip2.end_time (beat-aligned)
# - clip3.start_time (same beat, so seamless transition)
# etc.
```

## Example

**Song:** 30 seconds, 110 BPM
**Video API:** 8 FPS

```python
# Step 1: Get boundaries
boundaries = calculate_beat_aligned_boundaries(
    beat_times=[0.0, 0.545, 1.091, 1.636, ...],  # Beat times from analysis
    song_duration=30.0,
    fps=8.0,
)

# Result might be:
# Boundary 0: start=0.0s, end=4.364s, duration=4.364s
# Boundary 1: start=4.364s, end=8.727s, duration=4.363s
# Boundary 2: start=8.727s, end=13.091s, duration=4.364s
# ... etc

# Step 2: Calculate frames
# Clip 0: 4.364s * 8 fps = 34.912 → 35 frames (rounds to nearest)
# Clip 1: 4.363s * 8 fps = 34.904 → 35 frames
# Clip 2: 4.364s * 8 fps = 34.912 → 35 frames

# Step 3: Generate clips
# Generate clip 0: num_frames=35, fps=8 → 4.375 seconds (very close to 4.364s)
# Generate clip 1: num_frames=35, fps=8 → 4.375 seconds
# Generate clip 2: num_frames=35, fps=8 → 4.375 seconds

# Step 4: Stitch
# Transition at 4.364s (beat-aligned) between clip 0 and clip 1
# Transition at 8.727s (beat-aligned) between clip 1 and clip 2
# etc.
```

## Why Frame Alignment Matters

Even though we're snapping to beats, we still need frame alignment because:

1. **Video APIs work in frames**: You can't request "4.364 seconds" - you request "35 frames at 8 FPS"
2. **Precise transitions**: Knowing the exact frame indices helps ensure transitions happen at the right moment
3. **Alignment quality**: The `start_alignment_error` and `end_alignment_error` tell you how close you are to perfect beat alignment

## API Endpoint Usage

You can also use the API endpoint to get boundaries:

```bash
# Get beat-aligned boundaries for a song
curl "http://localhost:8000/api/v1/songs/{song_id}/beat-aligned-boundaries?fps=8.0" | jq

# Response includes all boundaries with frame indices and alignment metadata
```

Then use those boundaries in your clip generation workflow.

