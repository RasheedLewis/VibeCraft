# Beat Alignment for Clip Generation

## Overview

The beat alignment system calculates where clip boundaries should be placed so that
**transitions between clips happen on beats**. This ensures smooth, musically-synced video
transitions.

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

---

## Usage Guide

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

When stitching clips, transitions automatically happen on beats because:

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

### Example

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

### API Endpoint Usage

You can also use the API endpoint to get boundaries:

```bash
# Get beat-aligned boundaries for a song
curl "http://localhost:8000/api/v1/songs/{song_id}/beat-aligned-boundaries?fps=8.0" | jq

# Response includes all boundaries with frame indices and alignment metadata
```

---

## Technical Details: Beat-to-Frame Alignment Algorithm

### Problem Statement

Given:

- **Song BPM:** 110 beats per minute
- **Video FPS:** 8 frames per second = 480 frames per minute

Find the optimal alignment between beats and frames for beat-synced video generation.

### Mathematical Setup

#### Constants

- `BPM = 110` beats per minute
- `FPS = 8` frames per second = 480 frames per minute

#### Time Calculations

- **Beat interval:** `beat_interval = 60 / BPM = 60 / 110 ≈ 0.5455 seconds`
- **Frame interval:** `frame_interval = 1 / FPS = 1 / 8 = 0.125 seconds`

#### Beat Times

For beat `i` (starting at 0):

```text
beat_time[i] = i * beat_interval = i * (60 / BPM)
```

#### Frame Times

For frame `j` (starting at 0):

```text
frame_time[j] = j * frame_interval = j / FPS
```

### Important Constraints

- Video generation API outputs at **8 FPS** (frame interval = 0.125 seconds)
- Clip durations must be between 3-6 seconds
- Boundaries should align with beats (within acceptable tolerance)
- Must account for 8 FPS frame intervals when calculating alignment

---

## Alignment Approaches

### Approach 1: Nearest Neighbor Matching

#### Algorithm

For each beat, find the nearest frame.

```python
def nearest_frame_for_beat(beat_index, fps, bpm):
    beat_time = beat_index * (60 / bpm)
    frame_index = round(beat_time * fps)
    return frame_index

# Example:
# Beat 0: time = 0.0s → Frame 0 (0.0s)
# Beat 1: time = 0.545s → Frame 4 (0.5s) or Frame 5 (0.625s)
#   Distance to Frame 4: |0.545 - 0.5| = 0.045s
#   Distance to Frame 5: |0.545 - 0.625| = 0.08s
#   → Choose Frame 4 (closer)
```

#### Pros

- Simple and fast
- Works well when frame rate is high relative to beat rate

#### Cons

- May miss some beats if frame rate is too low
- Doesn't optimize globally

### Approach 2: Optimal Alignment (Dynamic Programming)

#### Algorithm

Find the alignment that minimizes total distance between beats and frames.

```python
def optimal_beat_frame_alignment(beats, frames, max_distance=0.1):
    """
    Find optimal alignment using dynamic programming.
    
    Args:
        beats: List of beat times
        frames: List of frame times
        max_distance: Maximum allowed distance between beat and frame
    
    Returns:
        List of (beat_index, frame_index) pairs
    """
    n_beats = len(beats)
    n_frames = len(frames)
    
    # DP table: dp[i][j] = minimum cost to align first i beats with first j frames
    dp = [[float('inf')] * (n_frames + 1) for _ in range(n_beats + 1)]
    dp[0][0] = 0
    
    # Track path for reconstruction
    path = {}
    
    for i in range(n_beats + 1):
        for j in range(n_frames + 1):
            if i == 0 and j == 0:
                continue
            
            # Option 1: Skip this frame (don't assign to any beat)
            if j > 0:
                cost = dp[i][j-1]
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    path[(i, j)] = (i, j-1)
            
            # Option 2: Match beat i-1 with frame j-1
            if i > 0 and j > 0:
                distance = abs(beats[i-1] - frames[j-1])
                if distance <= max_distance:
                    cost = dp[i-1][j-1] + distance
                    if cost < dp[i][j]:
                        dp[i][j] = cost
                        path[(i, j)] = (i-1, j-1)
            
            # Option 3: Skip this beat (no frame assigned)
            if i > 0:
                cost = dp[i-1][j] + 1.0  # Penalty for unmatched beat
                if cost < dp[i][j]:
                    dp[i][j] = cost
                    path[(i, j)] = (i-1, j)
    
    # Reconstruct alignment
    alignment = []
    i, j = n_beats, n_frames
    while i > 0 or j > 0:
        if (i, j) in path:
            prev_i, prev_j = path[(i, j)]
            if prev_i < i and prev_j < j:
                # Beat i-1 matched with frame j-1
                alignment.append((i-1, j-1))
            i, j = prev_i, prev_j
        else:
            break
    
    return list(reversed(alignment))
```

#### Pros

- Globally optimal alignment
- Handles missing beats/frames gracefully

#### Cons

- More complex
- O(n_beats × n_frames) time complexity

### Approach 3: Phase Offset Optimization

#### Algorithm

Since both beats and frames are periodic, find the phase offset that minimizes total error.

```python
import numpy as np

def find_optimal_phase_offset(bpm, fps, duration_sec):
    """
    Find the phase offset that minimizes beat-frame alignment error.
    
    Returns:
        optimal_offset: Time offset in seconds
        alignment_error: Average distance between beats and nearest frames
    """
    beat_interval = 60 / bpm
    frame_interval = 1 / fps
    
    # Generate beat and frame times
    num_beats = int(duration_sec * bpm / 60)
    num_frames = int(duration_sec * fps)
    
    beat_times = np.arange(num_beats) * beat_interval
    frame_times = np.arange(num_frames) * frame_interval
    
    # Try different phase offsets
    best_offset = 0
    best_error = float('inf')
    
    # Search in range [0, frame_interval)
    for offset in np.linspace(0, frame_interval, 100):
        offset_frame_times = frame_times + offset
        
        # Calculate total distance
        total_error = 0
        for beat_time in beat_times:
            # Find nearest frame
            distances = np.abs(offset_frame_times - beat_time)
            min_distance = np.min(distances)
            total_error += min_distance
        
        avg_error = total_error / len(beat_times)
        
        if avg_error < best_error:
            best_error = avg_error
            best_offset = offset
    
    return best_offset, best_error
```

#### Pros

- Accounts for periodic nature
- Good for long videos
- Can be used to adjust video generation timing

#### Cons

- Assumes uniform beat spacing (may not work for variable tempo)

### Approach 4: Beat-Synced Frame Generation (Recommended)

#### Algorithm

Instead of aligning existing frames, generate frames at beat times (or as close as possible).

```python
def generate_beat_synced_frames(bpm, fps, duration_sec):
    """
    Generate frame indices that best align with beats.
    
    Strategy:
    1. Calculate all beat times
    2. For each beat, find the nearest frame time
    3. Generate frames at those times (or nearest possible)
    """
    beat_interval = 60 / bpm
    frame_interval = 1 / fps
    
    num_beats = int(duration_sec * bpm / 60)
    beat_times = [i * beat_interval for i in range(num_beats)]
    
    # Map beats to frame indices
    beat_to_frame = {}
    for beat_idx, beat_time in enumerate(beat_times):
        # Find nearest frame
        frame_idx = round(beat_time * fps)
        frame_time = frame_idx / fps
        
        # Calculate alignment error
        error = abs(beat_time - frame_time)
        
        beat_to_frame[beat_idx] = {
            'frame_idx': frame_idx,
            'frame_time': frame_time,
            'beat_time': beat_time,
            'error': error
        }
    
    return beat_to_frame

# Example with 110 BPM, 8 FPS:
# Beat 0: 0.000s → Frame 0 (0.000s), error = 0.000s ✓
# Beat 1: 0.545s → Frame 4 (0.500s), error = 0.045s ✓
# Beat 2: 1.091s → Frame 9 (1.125s), error = 0.034s ✓
# Beat 3: 1.636s → Frame 13 (1.625s), error = 0.011s ✓
# Beat 4: 2.182s → Frame 17 (2.125s), error = 0.057s
```

#### For Video Generation

When generating video, you can:

1. **Generate frames at beat times:** Request frames at specific timestamps
2. **Emphasize beat-aligned frames:** Use higher quality/weight for beat frames
3. **Adjust generation timing:** Shift frame generation to align with beats

---

## Practical Implementation

### Step 1: Calculate Beat Times

```python
def get_beat_times(bpm, start_time, end_time):
    """Get all beat times within a section."""
    beat_interval = 60 / bpm
    beats = []
    current_beat = start_time
    while current_beat < end_time:
        beats.append(current_beat)
        current_beat += beat_interval
    return beats
```

### Step 2: Map Beats to Frames

```python
def map_beats_to_frames(beat_times, fps):
    """Map each beat to its nearest frame index."""
    alignment = []
    for beat_time in beat_times:
        frame_idx = round(beat_time * fps)
        frame_time = frame_idx / fps
        error = abs(beat_time - frame_time)
        alignment.append({
            'beat_time': beat_time,
            'frame_idx': frame_idx,
            'frame_time': frame_time,
            'error_sec': error
        })
    return alignment
```

### Step 3: Use for Transitions

Use beat-aligned frames for:

- **Hard cuts:** Cut exactly at beat-aligned frames
- **Transitions:** Start/end transitions at beat-aligned frames
- **Effects:** Apply effects (flares, zooms) at beat times

---

## Example: 110 BPM, 8 FPS

### Beat and Frame Timeline

```text
Time (s)  | 0.000 | 0.125 | 0.250 | 0.375 | 0.500 | 0.625 | 0.750 | 0.875 | 1.000 | 1.125 | 1.250 | 1.375 | 1.500 | 1.625 | 1.750 | 1.875 | 2.000
Frame     |   0   |   1   |   2   |   3   |   4   |   5   |   6   |   7   |   8   |   9   |  10   |  11   |  12   |  13   |  14   |  15   |  16
Beat      |   ✓   |       |       |       |   ✓   |       |       |       |       |   ✓   |       |       |       |   ✓   |       |       |   ✓
Beat Time | 0.000 |       |       |       | 0.545 |       |       |       |       | 1.091 |       |       |       | 1.636 |       |       | 2.182
```

### Alignment Results

- **Beat 0** (0.000s) → **Frame 0** (0.000s), error = 0.000s ✓ Perfect
- **Beat 1** (0.545s) → **Frame 4** (0.500s), error = 0.045s ✓ Good
- **Beat 2** (1.091s) → **Frame 9** (1.125s), error = 0.034s ✓ Good
- **Beat 3** (1.636s) → **Frame 13** (1.625s), error = 0.011s ✓ Excellent
- **Beat 4** (2.182s) → **Frame 17** (2.125s), error = 0.057s ✓ Good

**Average error:** ~0.029 seconds (very good alignment!)

---

## Quality Metrics

### Alignment Quality

- **Excellent:** Error < 0.02s (1 frame at 8fps = 0.125s, so < 16% of frame interval)
- **Good:** Error < 0.05s (< 40% of frame interval)
- **Acceptable:** Error < 0.1s (< 80% of frame interval)
- **Poor:** Error ≥ 0.1s (consider adjusting FPS or using interpolation)

### For 110 BPM, 8 FPS

- Beat interval: 0.545s
- Frame interval: 0.125s
- **Ratio:** 0.545 / 0.125 ≈ 4.36 frames per beat
- This means we have ~4-5 frames per beat, which is good for alignment

---

## Why Frame Alignment Matters

Even though we're snapping to beats, we still need frame alignment because:

1. **Video APIs work in frames**: You can't request "4.364 seconds" - you request "35 frames at
   8 FPS"
2. **Precise transitions**: Knowing the exact frame indices helps ensure transitions happen at
   the right moment
3. **Alignment quality**: The `start_alignment_error` and `end_alignment_error` tell you how
   close you are to perfect beat alignment

---

## Recommendations

1. **Use Approach 4 (Beat-Synced Frame Generation)** for video generation
2. **Store beat-to-frame mappings** in the database for composition
3. **Use beat-aligned frames for transitions** in composition engine
4. **Consider increasing FPS** if alignment quality is poor (but increases cost)
5. **For variable tempo songs**, use actual beat times from analysis, not calculated intervals

---

## Code Integration Points

### Video Generation

- Store beat times with clip metadata
- Optionally request frames at specific beat times (if API supports)

### Composition Engine

- Load beat times from analysis
- Calculate beat-to-frame alignment
- Use aligned frames for cuts and transitions
- Apply effects at beat times
