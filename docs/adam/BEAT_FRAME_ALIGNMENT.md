# Beat-to-Frame Alignment Algorithm

## Context for MVP-02: Beat Alignment Calculation & Planning

This document provides context and analysis for implementing **MVP-02 — Beat Alignment Calculation & Planning**.

### Goal
Calculate beat-aligned clip boundaries (independent of clip generation). This PR focuses on **calculation and planning only** - it doesn't require clips to exist. Can work in parallel with MVP-01.

### Key Requirements
1. Implement beat-to-frame alignment algorithm
2. Build helper function to calculate optimal clip boundaries from beat grid
3. Account for video generation API FPS (8 FPS) when calculating beat-to-frame alignment
4. Adjust clip durations to match nearest beats (within 3-6s constraints)
5. Create API endpoint: `GET /api/songs/:id/beat-aligned-boundaries` that returns calculated boundaries
6. Store beat alignment metadata (which beats each boundary aligns with)
7. Add validation to ensure boundaries don't drift from beat grid

### Essential Context Files
- **`docs/MVP_ROADMAP.md`** - MVP-02 requirements and goals
- **`backend/app/schemas/analysis.py`** - `SongAnalysis` schema (beat_times, bpm, duration_sec)
- **`backend/app/models/analysis.py`** - `SongAnalysisRecord` model (how analysis is stored)
- **`backend/app/services/song_analysis.py`** - How beat times are calculated and stored (lines 165-167, 197-209)
- **`backend/app/api/v1/__init__.py`** - API router structure (where to add the new endpoint)
- **`backend/app/api/v1/routes_videos.py`** - Example API route implementation pattern

### Key Data Structures
- **Beat times:** Stored in `SongAnalysis.beat_times` (list of floats in seconds)
- **BPM:** Stored in `SongAnalysis.bpm` (optional float)
- **Analysis storage:** `SongAnalysisRecord.analysis_json` (JSON string of `SongAnalysis`)
- **Video FPS:** 8 FPS (Zeroscope v2 XL output)

### Important Constraints
- Video generation API outputs at **8 FPS** (frame interval = 0.125 seconds)
- Clip durations must be between 3-6 seconds
- Boundaries should align with beats (within acceptable tolerance)
- Must account for 8 FPS frame intervals when calculating alignment

---

## Problem Statement

Given:
- **Song BPM:** 110 beats per minute
- **Video FPS:** 8 frames per second = 480 frames per minute

Find the optimal alignment between beats and frames for beat-synced video generation.

---

## Mathematical Setup

### Constants
- `BPM = 110` beats per minute
- `FPS = 8` frames per second = 480 frames per minute

### Time Calculations
- **Beat interval:** `beat_interval = 60 / BPM = 60 / 110 ≈ 0.5455 seconds`
- **Frame interval:** `frame_interval = 1 / FPS = 1 / 8 = 0.125 seconds`

### Beat Times
For beat `i` (starting at 0):
```
beat_time[i] = i * beat_interval = i * (60 / BPM)
```

### Frame Times
For frame `j` (starting at 0):
```
frame_time[j] = j * frame_interval = j / FPS
```

---

## Approach 1: Nearest Neighbor Matching

### Algorithm
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

### Pros
- Simple and fast
- Works well when frame rate is high relative to beat rate

### Cons
- May miss some beats if frame rate is too low
- Doesn't optimize globally

---

## Approach 2: Optimal Alignment (Dynamic Programming)

### Algorithm
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

### Pros
- Globally optimal alignment
- Handles missing beats/frames gracefully

### Cons
- More complex
- O(n_beats × n_frames) time complexity

---

## Approach 3: Phase Offset Optimization

### Algorithm
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

### Pros
- Accounts for periodic nature
- Good for long videos
- Can be used to adjust video generation timing

### Cons
- Assumes uniform beat spacing (may not work for variable tempo)

---

## Approach 4: Beat-Synced Frame Generation (Recommended)

### Algorithm
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

### For Video Generation
When generating video, you can:
1. **Generate frames at beat times:** Request frames at specific timestamps
2. **Emphasize beat-aligned frames:** Use higher quality/weight for beat frames
3. **Adjust generation timing:** Shift frame generation to align with beats

---

## Practical Implementation for VibeCraft

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
In PR-13 (Composition Engine), use beat-aligned frames for:
- **Hard cuts:** Cut exactly at beat-aligned frames
- **Transitions:** Start/end transitions at beat-aligned frames
- **Effects:** Apply effects (flares, zooms) at beat times

---

## Example: 110 BPM, 8 FPS

### Beat and Frame Timeline
```
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

### For 110 BPM, 8 FPS:
- Beat interval: 0.545s
- Frame interval: 0.125s
- **Ratio:** 0.545 / 0.125 ≈ 4.36 frames per beat
- This means we have ~4-5 frames per beat, which is good for alignment

---

## Recommendations

1. **Use Approach 4 (Beat-Synced Frame Generation)** for video generation
2. **Store beat-to-frame mappings** in the database for PR-13
3. **Use beat-aligned frames for transitions** in composition engine
4. **Consider increasing FPS** if alignment quality is poor (but increases cost)
5. **For variable tempo songs**, use actual beat times from analysis, not calculated intervals

---

## Code Integration Points

### PR-09 (Video Generation)
- Store beat times with section video
- Optionally request frames at specific beat times (if API supports)

### PR-13 (Composition Engine)
- Load beat times from analysis
- Calculate beat-to-frame alignment
- Use aligned frames for cuts and transitions
- Apply effects at beat times

