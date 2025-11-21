# Beat Synchronization Implementation Plan

**Section 3 from High-Level Plan: Beat Synchronization**

This document provides a comprehensive implementation plan for the three-phase Beat Synchronization feature, which ensures video clips are rhythmically synchronized with the musical beats of the song.

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 3.1: Prompt Engineering](#phase-31-prompt-engineering)
3. [Phase 3.2: Audio-Reactive FFmpeg Filters](#phase-32-audio-reactive-ffmpeg-filters)
4. [Phase 3.3: Structural Sync](#phase-33-structural-sync)
5. [Integration Architecture](#integration-architecture)
6. [Testing Strategy](#testing-strategy)
7. [Timeline & Dependencies](#timeline--dependencies)
8. [Success Metrics](#success-metrics)

---

## Overview

### Goal

Implement a three-phase beat synchronization system that:
1. **Biases video generation** toward rhythmic motion through prompt engineering
2. **Adds visual beat cues** through post-processing FFmpeg filters
3. **Aligns clip transitions** to occur precisely on musical beats

### Current State

- Beat detection is already implemented (`song_analysis` contains `beat_times` array)
- Video composition pipeline exists (`video_composition.py`, `composition_execution.py`)
- Beat alignment utilities exist (`beat_alignment.py`) for calculating boundaries
- Clip generation happens via Replicate API

### Target State

After implementation:
- Generated clips have natural rhythmic motion (Phase 3.1)
- Visual effects flash/pulse on every major beat (Phase 3.2)
- All clip transitions occur exactly on beat boundaries (Phase 3.3)
- Combined effect creates strong perception of beat synchronization

### Success Criteria

- **Phase 3.1**: 40%+ of generated clips show periodic motion aligned with beats (measured via motion analysis)
- **Phase 3.2**: Visual effects trigger within ±20ms of beat timestamps (frame-accurate)
- **Phase 3.3**: 100% of clip transitions occur within ±50ms of beat boundaries
- **Combined**: User perception of strong beat sync in 80%+ of generated videos

---

## Phase 3.1: Prompt Engineering

### Objective

Modify video generation prompts to bias AI models toward producing rhythmic, periodic motion that naturally aligns with musical beats.

### Technical Approach

Enhance the base prompt template with rhythmic motion descriptors based on:
- Song BPM (beats per minute)
- Motion type selection (bouncing, pulsing, rotating, etc.)
- Tempo-appropriate motion descriptors

### Implementation Details

#### 3.1.1: Prompt Enhancement Service

**Location**: `backend/app/services/prompt_enhancement.py` (new file)

**Key Functions**:

```python
def enhance_prompt_with_rhythm(
    base_prompt: str,
    bpm: float,
    motion_type: str = "bouncing",
    style_context: dict | None = None
) -> str:
    """
    Enhance base prompt with rhythmic motion cues.
    
    Args:
        base_prompt: Original user prompt or generated prompt
        bpm: Song BPM from song analysis
        motion_type: Type of rhythmic motion (bouncing, pulsing, rotating, stepping, looping)
        style_context: Optional dict with mood, colors, setting
    
    Returns:
        Enhanced prompt string with rhythmic descriptors
    """
    # Map BPM to tempo descriptors
    tempo_descriptor = get_tempo_descriptor(bpm)
    motion_style = get_motion_style(bpm, motion_type)
    
    # Build rhythmic phrase
    rhythmic_phrase = f"{motion_style} at {int(bpm)} BPM tempo"
    
    # Combine with base prompt
    enhanced = f"{base_prompt}. {rhythmic_phrase}. Clear periodic motion, minimal complexity."
    
    return enhanced

def get_tempo_descriptor(bpm: float) -> str:
    """Map BPM to tempo descriptor."""
    if bpm < 100:
        return "slow, flowing"
    elif 100 <= bpm < 130:
        return "steady, moderate"
    elif 130 <= bpm < 160:
        return "energetic, driving"
    else:  # bpm >= 160
        return "frenetic, rapid"

def get_motion_style(bpm: float, motion_type: str) -> str:
    """Get motion style descriptor based on BPM and motion type."""
    motion_templates = {
        "bouncing": {
            "slow": "gentle swaying",
            "moderate": "steady rhythmic bouncing",
            "fast": "energetic bouncing",
            "very_fast": "rapid pulsing"
        },
        "pulsing": {
            "slow": "slow pulsing",
            "moderate": "rhythmic pulsing",
            "fast": "rapid pulsing",
            "very_fast": "frenetic pulsing"
        },
        # ... other motion types
    }
    
    tempo_key = get_tempo_key(bpm)
    return motion_templates.get(motion_type, {}).get(tempo_key, "rhythmic motion")
```

**Motion Type Templates**:

```python
RHYTHMIC_MOTION_TEMPLATES = {
    "bouncing": [
        "Simple figure bouncing rhythmically up and down",
        "Geometric character with repetitive bouncing motion",
        "Dancing figure with steady bounce"
    ],
    "pulsing": [
        "Pulsing shapes expanding and contracting rhythmically",
        "Character with pulsating motion",
        "Rhythmic pulsing energy"
    ],
    "rotating": [
        "Figure rotating in steady circular motion",
        "Spinning dancer with consistent rotation speed"
    ],
    "stepping": [
        "Figure stepping side to side rhythmically",
        "Character with clear stepping motion"
    ],
    "looping": [
        "Perfectly looping dance animation",
        "Seamless looping motion",
        "Repeating dance pattern"
    ]
}
```

#### 3.1.2: Integration with Clip Generation

**Location**: `backend/app/services/clip_generation.py` (modify existing)

**Changes Required**:

1. Import prompt enhancement service
2. Enhance prompt before sending to Replicate API
3. Add motion_type parameter (can be user-selected or auto-detected)

**Code Changes**:

```python
from app.services.prompt_enhancement import enhance_prompt_with_rhythm
from app.repositories import SongRepository

def generate_clip_prompt(
    scene_description: str,
    song_id: UUID,
    motion_type: str = "bouncing"
) -> str:
    """Generate enhanced prompt with rhythmic cues."""
    # Get song analysis for BPM
    song = SongRepository.get_by_id(song_id)
    bpm = song.analysis.bpm if song.analysis else 120.0  # Default fallback
    
    # Enhance prompt
    enhanced_prompt = enhance_prompt_with_rhythm(
        base_prompt=scene_description,
        bpm=bpm,
        motion_type=motion_type
    )
    
    return enhanced_prompt
```

#### 3.1.3: API-Specific Optimization

**Location**: `backend/app/services/prompt_enhancement.py`

Different video generation APIs respond differently to prompts. Add API-specific optimizations:

```python
def optimize_prompt_for_api(
    prompt: str,
    api_name: str,
    bpm: float
) -> str:
    """
    Tailor prompt structure for specific video generation API.
    
    Different APIs have different prompt parsing and response patterns.
    """
    if api_name == "runway":
        # Runway Gen-3 responds well to concise, directive prompts
        optimized = f"{prompt}. Camera: static. Motion: {get_motion_style(bpm, 'bouncing')}."
    
    elif api_name == "pika":
        # Pika benefits from style references
        optimized = f"{prompt}. Style: clean motion graphics. Tempo: {int(bpm)} BPM."
    
    elif api_name == "kling":
        # Kling prefers detailed motion descriptions
        optimized = (
            f"{prompt}. The character moves with consistent "
            f"{get_motion_style(bpm, 'bouncing')} at {int(bpm)} beats per minute, "
            f"creating a rhythmic visual pattern."
        )
    
    else:
        # Generic optimization
        optimized = prompt
    
    return optimized
```

#### 3.1.4: Motion Type Selection

**Location**: `backend/app/services/scene_planner.py` (modify existing)

Add logic to select appropriate motion type based on:
- Song genre/mood
- Scene context
- User preferences (if available)

```python
def select_motion_type(
    song_analysis: SongAnalysis,
    scene_context: dict
) -> str:
    """
    Select appropriate motion type based on song and scene.
    
    Returns: One of "bouncing", "pulsing", "rotating", "stepping", "looping"
    """
    genre = song_analysis.genre if song_analysis else None
    mood = song_analysis.mood if song_analysis else None
    
    # Genre-based selection
    if genre == "electronic" or genre == "edm":
        return "pulsing"
    elif genre == "hip-hop":
        return "stepping"
    elif genre == "pop":
        return "bouncing"
    
    # Mood-based selection
    if mood and "energetic" in mood.lower():
        return "bouncing"
    elif mood and "calm" in mood.lower():
        return "looping"
    
    # Default
    return "bouncing"
```

### Testing Strategy

1. **Prompt Quality Testing**:
   - Generate 10 clips with enhanced prompts
   - Generate 10 clips with original prompts
   - Compare motion analysis results (periodic motion detection)

2. **BPM Range Testing**:
   - Test with BPM ranges: 60-100 (slow), 100-130 (moderate), 130-160 (fast), 160+ (very fast)
   - Verify appropriate motion descriptors are used

3. **API Compatibility Testing**:
   - Test prompt optimization for each supported API (Runway, Pika, Kling)
   - Measure success rate of rhythmic motion generation per API

4. **Motion Analysis Validation**:
   - Use OpenCV optical flow to detect periodic motion
   - Calculate alignment score between motion peaks and beat times
   - Target: 40%+ of clips show periodic motion aligned with beats

### Success Metrics

- **Prompt Enhancement Rate**: 100% of clips use enhanced prompts
- **Motion Detection Rate**: 40%+ of generated clips show detectable periodic motion
- **Alignment Score**: Average alignment score > 0.4 (motion peaks within 200ms of beats)
- **API Compatibility**: Works with all supported video generation APIs

### Effort Estimate

- **Prompt Enhancement Service**: 1 day
- **Integration with Clip Generation**: 0.5 days
- **API-Specific Optimization**: 1 day
- **Motion Type Selection**: 0.5 days
- **Testing & Validation**: 1 day
- **Total: ~4 days**

---

## Phase 3.2: Audio-Reactive FFmpeg Filters

### Objective

Apply visual effects (flashes, color bursts, zoom pulses) precisely on beat timestamps using FFmpeg filters, creating strong visual cues that the video is synchronized to the music.

### Technical Approach

Use FFmpeg's `select` and `geq` filters to apply effects at exact frame timestamps corresponding to beat times. Effects are applied during the final video composition step.

### Implementation Details

#### 3.2.1: Beat Effect Service

**Location**: `backend/app/services/beat_effects.py` (new file)

**Key Functions**:

```python
def create_beat_effect_filter(
    beat_times: list[float],
    effect_type: str = "flash",
    effect_params: dict | None = None
) -> str:
    """
    Create FFmpeg filter complex for beat-synced visual effects.
    
    Args:
        beat_times: List of beat timestamps in seconds
        effect_type: Type of effect (flash, color_burst, zoom_pulse, glitch)
        effect_params: Optional parameters for effect customization
    
    Returns:
        FFmpeg filter complex string
    """
    fps = 24  # Default FPS (should match video FPS)
    frame_interval = 1.0 / fps
    
    # Convert beat times to frame indices
    beat_frames = [int(beat_time * fps) for beat_time in beat_times]
    
    if effect_type == "flash":
        return create_flash_filter(beat_frames, effect_params or {})
    elif effect_type == "color_burst":
        return create_color_burst_filter(beat_frames, effect_params or {})
    elif effect_type == "zoom_pulse":
        return create_zoom_pulse_filter(beat_frames, effect_params or {})
    elif effect_type == "glitch":
        return create_glitch_filter(beat_frames, effect_params or {})
    else:
        raise ValueError(f"Unknown effect type: {effect_type}")

def create_flash_filter(beat_frames: list[int], params: dict) -> str:
    """
    Create white flash effect on beat frames.
    
    Effect: Single frame white flash (1 frame duration)
    """
    flash_intensity = params.get("intensity", 0.8)  # 0.0-1.0
    flash_color = params.get("color", "white")  # white, red, blue, etc.
    
    # Build boolean expression for beat frames
    # Format: "if(eq(n,FRAME1)+eq(n,FRAME2)+...,FLASH_COLOR,ORIGINAL)"
    beat_conditions = "+".join([f"eq(n,{frame})" for frame in beat_frames])
    
    # Create flash filter using geq (generic equation)
    if flash_color == "white":
        flash_expr = f"if({beat_conditions},{flash_intensity}*255,0)"
        filter_str = f"geq=r='if({beat_conditions},255,p(X,Y))':g='if({beat_conditions},255,p(X,Y))':b='if({beat_conditions},255,p(X,Y))'"
    else:
        # Custom color flash (simplified - would need RGB values)
        filter_str = f"geq=r='if({beat_conditions},255,p(X,Y))':g='if({beat_conditions},255,p(X,Y))':b='if({beat_conditions},255,p(X,Y))'"
    
    return filter_str

def create_color_burst_filter(beat_frames: list[int], params: dict) -> str:
    """
    Create color burst effect (saturated color flash).
    
    Effect: 2-3 frame color saturation burst
    """
    burst_duration = params.get("duration_frames", 2)  # Number of frames
    color_hue = params.get("hue", 0)  # 0-360 degrees
    
    # For each beat frame, create burst window
    burst_conditions = []
    for beat_frame in beat_frames:
        for offset in range(burst_duration):
            burst_conditions.append(f"eq(n,{beat_frame + offset})")
    
    condition_expr = "+".join(burst_conditions)
    
    # Use curves filter for color saturation boost
    # Simplified - would use hsv/hue filters for precise color control
    filter_str = f"curves=all='0/0 0.5/0.7 1/1',geq=r='if({condition_expr},r(X,Y)*1.5,r(X,Y))':g='if({condition_expr},g(X,Y)*1.5,g(X,Y))':b='if({condition_expr},b(X,Y)*1.5,b(X,Y))'"
    
    return filter_str

def create_zoom_pulse_filter(beat_frames: list[int], params: dict) -> str:
    """
    Create zoom pulse effect on beats.
    
    Effect: Subtle zoom in/out pulse (3-5 frames)
    """
    pulse_duration = params.get("duration_frames", 3)
    zoom_amount = params.get("zoom", 1.05)  # 5% zoom
    
    # Build zoom expression
    zoom_conditions = []
    for beat_frame in beat_frames:
        for i in range(pulse_duration):
            frame_offset = i - (pulse_duration // 2)  # Center pulse around beat
            zoom_factor = 1.0 + (zoom_amount - 1.0) * (1.0 - abs(frame_offset) / (pulse_duration / 2))
            zoom_conditions.append((beat_frame + frame_offset, zoom_factor))
    
    # Use zoompan filter
    # Note: This is simplified - actual implementation would need more complex filter chain
    filter_str = f"zoompan=z='if(eq(n,BEAT_FRAME),{zoom_amount},1)':d=1"
    
    return filter_str

def create_glitch_filter(beat_frames: list[int], params: dict) -> str:
    """
    Create digital glitch effect on beats.
    
    Effect: RGB channel shift + scanline effect (2-3 frames)
    """
    glitch_intensity = params.get("intensity", 0.3)
    
    # RGB channel shift on beat frames
    beat_condition = "+".join([f"eq(n,{frame})" for frame in beat_frames])
    
    # Shift red channel left, blue channel right
    filter_str = (
        f"geq=r='p(X+{int(glitch_intensity*10)},Y)':"
        f"g='p(X,Y)':"
        f"b='p(X-{int(glitch_intensity*10)},Y)'"
    )
    
    return filter_str
```

#### 3.2.2: Integration with Video Composition

**Location**: `backend/app/services/video_composition.py` (modify existing)

**Changes Required**:

1. Add beat effect application step in `concatenate_clips` function
2. Accept `beat_times` and `effect_config` parameters
3. Apply effects before final audio muxing

**Code Changes**:

```python
from app.services.beat_effects import create_beat_effect_filter

def concatenate_clips(
    normalized_clip_paths: list[str | Path],
    audio_path: str | Path,
    output_path: str | Path,
    song_duration_sec: float,
    beat_times: list[float] | None = None,  # NEW
    beat_effect_config: dict | None = None,  # NEW
    ffmpeg_bin: str | None = None,
    job_id: str | None = None,
) -> CompositionResult:
    """
    Concatenate normalized clips, apply beat effects, and mux with audio.
    
    Args:
        ... existing args ...
        beat_times: List of beat timestamps for effect synchronization
        beat_effect_config: Configuration dict for beat effects
            {
                "enabled": bool,
                "effect_type": "flash" | "color_burst" | "zoom_pulse" | "glitch",
                "effect_params": dict
            }
    """
    # ... existing concatenation logic ...
    
    # After concatenation, before audio muxing, apply beat effects
    if beat_times and beat_effect_config and beat_effect_config.get("enabled"):
        if job_id:
            update_job_progress(job_id, 82, "processing")  # Applying beat effects
        
        logger.info(f"Applying beat effects: {beat_effect_config['effect_type']}")
        
        # Create effect filter
        effect_filter = create_beat_effect_filter(
            beat_times=beat_times,
            effect_type=beat_effect_config["effect_type"],
            effect_params=beat_effect_config.get("effect_params", {})
        )
        
        # Apply effect to concatenated video
        temp_effected_path = temp_video_path.parent / "temp_effected.mp4"
        apply_beat_effects_to_video(
            input_path=temp_video_path,
            output_path=temp_effected_path,
            effect_filter=effect_filter,
            ffmpeg_bin=ffmpeg_bin
        )
        
        # Replace temp_video_path with effected version
        temp_video_path.unlink(missing_ok=True)
        temp_effected_path.rename(temp_video_path)
    
    # ... continue with audio muxing ...
```

**New Helper Function**:

```python
def apply_beat_effects_to_video(
    input_path: Path,
    output_path: Path,
    effect_filter: str,
    ffmpeg_bin: str | None = None
) -> None:
    """
    Apply beat effect filter to video.
    
    Args:
        input_path: Path to input video
        output_path: Path to output video
        effect_filter: FFmpeg filter complex string
        ffmpeg_bin: Path to ffmpeg binary
    """
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin
    
    try:
        (
            ffmpeg.input(str(input_path))
            .output(
                str(output_path),
                vf=effect_filter,
                vcodec=DEFAULT_VIDEO_CODEC,
                preset="medium",
                crf=DEFAULT_CRF,
            )
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"Failed to apply beat effects: {stderr}") from e
```

#### 3.2.3: Effect Configuration

**Location**: `backend/app/core/config.py` (add configuration)

**Configuration Options**:

```python
class BeatEffectConfig(BaseSettings):
    """Configuration for beat-synced visual effects."""
    
    enabled: bool = True
    effect_type: str = "flash"  # flash, color_burst, zoom_pulse, glitch
    flash_intensity: float = 0.8
    flash_color: str = "white"
    color_burst_hue: int = 0
    zoom_pulse_amount: float = 1.05
    glitch_intensity: float = 0.3
```

#### 3.2.4: Frame-Accurate Timing

**Critical Requirement**: Effects must trigger within ±20ms of beat timestamps (frame-accurate at 24 FPS).

**Implementation**:

```python
def convert_beat_times_to_frames(
    beat_times: list[float],
    video_fps: float = 24.0,
    video_start_time: float = 0.0
) -> list[int]:
    """
    Convert beat times to frame indices with frame-accurate precision.
    
    Args:
        beat_times: Beat timestamps in seconds (relative to song start)
        video_fps: Video frame rate
        video_start_time: Offset of video start relative to song start
    
    Returns:
        List of frame indices where effects should trigger
    """
    frame_indices = []
    frame_interval = 1.0 / video_fps
    
    for beat_time in beat_times:
        # Adjust beat time relative to video start
        relative_beat_time = beat_time - video_start_time
        
        if relative_beat_time < 0:
            continue  # Beat occurs before video starts
        
        # Calculate frame index (round to nearest frame)
        frame_index = round(relative_beat_time * video_fps)
        frame_indices.append(frame_index)
    
    return frame_indices
```

### Testing Strategy

1. **Frame Accuracy Testing**:
   - Generate test video with known beat times
   - Apply flash effect
   - Extract frames at beat timestamps
   - Verify flash occurs on correct frames (±1 frame tolerance)

2. **Effect Visibility Testing**:
   - Test each effect type (flash, color_burst, zoom_pulse, glitch)
   - Verify effects are visible but not overwhelming
   - Test with different BPM ranges (slow vs fast beats)

3. **Performance Testing**:
   - Measure processing time for effect application
   - Target: < 5 seconds for 30-second video
   - Verify no quality degradation

4. **Edge Case Testing**:
   - Very high BPM (> 160) - effects may overlap
   - Very low BPM (< 60) - sparse effects
   - Missing beat_times array - graceful fallback

### Success Metrics

- **Frame Accuracy**: 100% of effects trigger within ±1 frame of beat timestamps
- **Effect Visibility**: Effects are clearly visible in 90%+ of test videos
- **Processing Time**: Effect application adds < 5 seconds to composition time
- **User Perception**: 80%+ of users notice beat synchronization in test videos

### Effort Estimate

- **Beat Effect Service**: 2-3 days
- **Integration with Video Composition**: 1 day
- **Frame-Accurate Timing**: 1 day
- **Effect Configuration**: 0.5 days
- **Testing & Validation**: 1-2 days
- **Total: ~6-8 days**

---

## Phase 3.3: Structural Sync

### Objective

Ensure all clip transitions (cuts between clips) occur precisely on musical beat boundaries, creating rhythmic editing that reinforces beat synchronization.

### Technical Approach

Modify the video composition pipeline to:
1. Align clip boundaries to nearest beat timestamps
2. Trim/extend clips to match beat-aligned boundaries
3. Ensure transitions occur exactly on beat frames

### Implementation Details

#### 3.3.1: Beat-Aligned Boundary Calculation

**Location**: `backend/app/services/beat_alignment.py` (enhance existing)

**Current State**: The file already has `calculate_beat_aligned_boundaries` function.

**Enhancements Needed**:

1. Ensure boundaries are frame-accurate
2. Handle edge cases (very short clips, very long clips)
3. Support user-selected clip segments (30-second selection feature)

**Code Enhancements**:

```python
def calculate_beat_aligned_clip_boundaries(
    beat_times: list[float],
    song_duration: float,
    num_clips: int = 6,
    min_clip_duration: float = 3.0,
    max_clip_duration: float = 6.0,
    fps: float = 24.0,
    user_selection_start: float | None = None,  # NEW: 30s selection support
    user_selection_end: float | None = None,    # NEW: 30s selection support
) -> list[ClipBoundary]:
    """
    Calculate clip boundaries aligned to beats, with optional user selection.
    
    Args:
        beat_times: List of beat timestamps
        song_duration: Total song duration
        num_clips: Target number of clips
        min_clip_duration: Minimum clip duration
        max_clip_duration: Maximum clip duration
        fps: Video frame rate
        user_selection_start: Optional start time for user-selected segment
        user_selection_end: Optional end time for user-selected segment
    
    Returns:
        List of ClipBoundary objects with beat-aligned timestamps
    """
    # Filter beats to user selection if provided
    if user_selection_start is not None and user_selection_end is not None:
        filtered_beats = [
            beat for beat in beat_times
            if user_selection_start <= beat <= user_selection_end
        ]
        effective_duration = user_selection_end - user_selection_start
        effective_start = user_selection_start
    else:
        filtered_beats = beat_times
        effective_duration = song_duration
        effective_start = 0.0
    
    # Calculate boundaries using existing algorithm
    boundaries = calculate_beat_aligned_boundaries(
        beat_times=filtered_beats,
        song_duration=effective_duration,
        min_duration=min_clip_duration,
        max_duration=max_clip_duration,
        fps=fps
    )
    
    # Adjust boundaries for user selection offset
    if user_selection_start is not None:
        adjusted_boundaries = []
        for boundary in boundaries:
            adjusted_boundaries.append(
                ClipBoundary(
                    start_time=boundary.start_time + effective_start,
                    end_time=boundary.end_time + effective_start,
                    start_beat_index=boundary.start_beat_index,
                    end_beat_index=boundary.end_beat_index,
                    start_frame_index=boundary.start_frame_index,
                    end_frame_index=boundary.end_frame_index,
                    start_alignment_error=boundary.start_alignment_error,
                    end_alignment_error=boundary.end_alignment_error,
                    duration_sec=boundary.duration_sec,
                    beats_in_clip=boundary.beats_in_clip,
                )
            )
        boundaries = adjusted_boundaries
    
    return boundaries
```

#### 3.3.2: Clip Trimming/Extension for Beat Alignment

**Location**: `backend/app/services/video_composition.py` (new functions)

**New Functions**:

```python
def trim_clip_to_beat_boundary(
    clip_path: str | Path,
    output_path: str | Path,
    target_start_time: float,
    target_end_time: float,
    beat_start_time: float,
    beat_end_time: float,
    fps: float = 24.0,
    ffmpeg_bin: str | None = None,
) -> None:
    """
    Trim clip to align with beat boundaries.
    
    Args:
        clip_path: Path to input clip
        output_path: Path to output clip
        target_start_time: Desired start time (may not be on beat)
        target_end_time: Desired end time (may not be on beat)
        beat_start_time: Nearest beat-aligned start time
        beat_end_time: Nearest beat-aligned end time
        fps: Video frame rate
        ffmpeg_bin: Path to ffmpeg binary
    """
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin
    
    # Calculate trim parameters
    # Start: trim from beginning to beat_start_time
    trim_start = beat_start_time - target_start_time
    # End: trim from end to beat_end_time
    trim_end = target_end_time - beat_end_time
    
    # Build trim filter
    # Format: trim=start=X:end=Y,setpts=PTS-STARTPTS
    video_filter = f"trim=start={trim_start:.3f}:end={target_end_time - target_start_time - trim_end:.3f},setpts=PTS-STARTPTS"
    
    try:
        (
            ffmpeg.input(str(clip_path))
            .output(
                str(output_path),
                vf=video_filter,
                vcodec=DEFAULT_VIDEO_CODEC,
                preset="medium",
                crf=DEFAULT_CRF,
                **{"an": None},  # Remove audio
            )
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"Failed to trim clip to beat boundary: {stderr}") from e

def extend_clip_to_beat_boundary(
    clip_path: str | Path,
    output_path: str | Path,
    target_duration: float,
    beat_end_time: float,
    fadeout_duration: float = 0.5,
    ffmpeg_bin: str | None = None,
) -> None:
    """
    Extend clip to align with beat boundary using frame freeze + fadeout.
    
    Args:
        clip_path: Path to input clip
        output_path: Path to output clip
        target_duration: Current clip duration
        beat_end_time: Target beat-aligned end time
        fadeout_duration: Fadeout duration in seconds
        ffmpeg_bin: Path to ffmpeg binary
    """
    extension_needed = beat_end_time - target_duration
    
    if extension_needed <= 0:
        # No extension needed, just add fadeout
        trim_last_clip(clip_path, output_path, target_duration, fadeout_duration, ffmpeg_bin)
        return
    
    # Use tpad to extend by freezing last frame
    # Then add fadeout
    video_filter = (
        f"tpad=stop_mode=clone:stop_duration={extension_needed:.3f},"
        f"fade=t=out:st={beat_end_time - fadeout_duration:.3f}:d={fadeout_duration:.3f}"
    )
    
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin
    
    try:
        (
            ffmpeg.input(str(clip_path))
            .output(
                str(output_path),
                vf=video_filter,
                vcodec=DEFAULT_VIDEO_CODEC,
                preset="medium",
                crf=DEFAULT_CRF,
                **{"an": None},
            )
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"Failed to extend clip to beat boundary: {stderr}") from e
```

#### 3.3.3: Integration with Composition Pipeline

**Location**: `backend/app/services/composition_execution.py` (modify existing)

**Changes Required**:

1. Calculate beat-aligned boundaries before clip normalization
2. Trim/extend clips to match boundaries
3. Ensure transitions occur on beat frames

**Code Changes**:

```python
from app.services.beat_alignment import calculate_beat_aligned_clip_boundaries
from app.services.video_composition import (
    trim_clip_to_beat_boundary,
    extend_clip_to_beat_boundary
)

def execute_composition_pipeline(
    job_id: str,
    song_id: UUID,
    clip_ids: list[UUID],
    clip_metadata: list[dict[str, Any]],
    beat_aligned: bool = True,  # NEW: Feature flag
) -> dict[str, Any]:
    """
    Execute composition pipeline with optional beat alignment.
    """
    # ... existing validation logic ...
    
    # Get song analysis for beat times
    song = SongRepository.get_by_id(song_id)
    beat_times = song.analysis.beat_times if song.analysis else None
    
    # Calculate beat-aligned boundaries if enabled
    if beat_aligned and beat_times:
        logger.info("Calculating beat-aligned clip boundaries")
        boundaries = calculate_beat_aligned_clip_boundaries(
            beat_times=beat_times,
            song_duration=song.duration_sec,
            num_clips=len(clip_ids),
            fps=24.0
        )
        
        # Adjust clip metadata to match boundaries
        for i, boundary in enumerate(boundaries):
            if i < len(clip_metadata):
                clip_metadata[i]["beat_start_time"] = boundary.start_time
                clip_metadata[i]["beat_end_time"] = boundary.end_time
                clip_metadata[i]["start_frame"] = boundary.start_frame_index
                clip_metadata[i]["end_frame"] = boundary.end_frame_index
    
    # ... continue with download and normalization ...
    
    # After normalization, trim/extend clips to beat boundaries
    if beat_aligned and beat_times:
        logger.info("Aligning clips to beat boundaries")
        aligned_clip_paths = []
        
        for i, (clip_path, metadata) in enumerate(zip(normalized_clip_paths, clip_metadata)):
            if "beat_start_time" in metadata and "beat_end_time" in metadata:
                aligned_path = temp_dir / f"aligned_clip_{i}.mp4"
                
                # Get original clip duration
                current_duration = metadata.get("duration_sec", 5.0)
                target_duration = metadata["beat_end_time"] - metadata["beat_start_time"]
                
                if current_duration < target_duration:
                    # Extend clip
                    extend_clip_to_beat_boundary(
                        clip_path=clip_path,
                        output_path=aligned_path,
                        target_duration=current_duration,
                        beat_end_time=metadata["beat_end_time"],
                        ffmpeg_bin=ffmpeg_bin
                    )
                elif current_duration > target_duration:
                    # Trim clip
                    trim_clip_to_beat_boundary(
                        clip_path=clip_path,
                        output_path=aligned_path,
                        target_start_time=0.0,
                        target_end_time=current_duration,
                        beat_start_time=0.0,
                        beat_end_time=target_duration,
                        fps=24.0,
                        ffmpeg_bin=ffmpeg_bin
                    )
                else:
                    # No adjustment needed
                    aligned_path = clip_path
                
                aligned_clip_paths.append(aligned_path)
            else:
                aligned_clip_paths.append(clip_path)
        
        normalized_clip_paths = aligned_clip_paths
    
    # ... continue with concatenation ...
```

#### 3.3.4: Transition Verification

**Location**: `backend/app/services/beat_alignment.py` (new function)

**Function to Verify Transitions**:

```python
def verify_beat_aligned_transitions(
    boundaries: list[ClipBoundary],
    beat_times: list[float],
    tolerance_sec: float = 0.05
) -> tuple[bool, list[float]]:
    """
    Verify that all clip transitions occur on beat boundaries.
    
    Args:
        boundaries: List of clip boundaries
        beat_times: List of beat timestamps
        tolerance_sec: Maximum allowed deviation from beat (default: 50ms)
    
    Returns:
        Tuple of (all_aligned, list of alignment errors)
    """
    errors = []
    
    for i in range(len(boundaries) - 1):
        # Transition occurs at end of current clip = start of next clip
        transition_time = boundaries[i].end_time
        
        # Find nearest beat
        nearest_beat = min(beat_times, key=lambda x: abs(x - transition_time))
        error = abs(transition_time - nearest_beat)
        errors.append(error)
    
    all_aligned = all(error <= tolerance_sec for error in errors)
    return all_aligned, errors
```

### Testing Strategy

1. **Boundary Alignment Testing**:
   - Generate test composition with known beat times
   - Verify all transitions occur within ±50ms of beats
   - Test with various BPM ranges

2. **Clip Trimming/Extension Testing**:
   - Test clips that need trimming (too long)
   - Test clips that need extension (too short)
   - Verify no visual artifacts from trimming/extension

3. **Edge Case Testing**:
   - Very short clips (< 2 seconds)
   - Very long clips (> 8 seconds)
   - Missing beat_times (graceful fallback)
   - User-selected 30-second segment

4. **Performance Testing**:
   - Measure time added by beat alignment
   - Target: < 10 seconds for 6 clips

### Success Metrics

- **Transition Accuracy**: 100% of transitions occur within ±50ms of beat boundaries
- **Boundary Alignment**: All clip boundaries align to beat frames
- **Visual Quality**: No visible artifacts from trimming/extension
- **Processing Time**: Beat alignment adds < 10 seconds to composition time

### Effort Estimate

- **Boundary Calculation Enhancements**: 1 day
- **Clip Trimming/Extension Functions**: 2 days
- **Integration with Composition Pipeline**: 1-2 days
- **Transition Verification**: 0.5 days
- **Testing & Validation**: 1-2 days
- **Total: ~6-8 days**

---

## Integration Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Clip Generation Layer                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Prompt Enhancement Service (Phase 3.1)               │  │
│  │  - enhance_prompt_with_rhythm()                      │  │
│  │  - optimize_prompt_for_api()                         │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Video Generation API (Replicate)                     │  │
│  │  - Generates clips with rhythmic prompts            │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                  Composition Execution Layer                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Beat Alignment Service (Phase 3.3)                  │  │
│  │  - calculate_beat_aligned_clip_boundaries()          │  │
│  │  - verify_beat_aligned_transitions()                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Video Composition Service                             │  │
│  │  - trim_clip_to_beat_boundary()                       │  │
│  │  - extend_clip_to_beat_boundary()                     │  │
│  │  - concatenate_clips() (with beat alignment)          │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Beat Effects Service (Phase 3.2)                    │  │
│  │  - create_beat_effect_filter()                       │  │
│  │  - apply_beat_effects_to_video()                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Final Composed Video                                 │  │
│  │  - Rhythmic motion (Phase 3.1)                       │  │
│  │  - Beat-aligned transitions (Phase 3.3)               │  │
│  │  - Visual beat effects (Phase 3.2)                   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Song Analysis** → Provides `beat_times` array and `bpm`
2. **Prompt Enhancement** → Uses `bpm` to enhance prompts
3. **Clip Generation** → Generates clips with enhanced prompts
4. **Beat Alignment** → Uses `beat_times` to calculate boundaries
5. **Clip Trimming/Extension** → Aligns clips to boundaries
6. **Beat Effects** → Uses `beat_times` to apply effects
7. **Final Composition** → Combines all elements

### Feature Flags

All three phases should be feature-flagged for gradual rollout:

```python
# backend/app/core/config.py
class BeatSyncConfig(BaseSettings):
    """Configuration for beat synchronization features."""
    
    # Phase 3.1: Prompt Engineering
    prompt_enhancement_enabled: bool = True
    
    # Phase 3.2: Audio-Reactive Filters
    beat_effects_enabled: bool = True
    beat_effect_type: str = "flash"  # flash, color_burst, zoom_pulse, glitch
    
    # Phase 3.3: Structural Sync
    beat_aligned_transitions_enabled: bool = True
```

### API Changes

**New Endpoints** (if needed):

- `GET /api/v1/config/beat-sync` - Get beat sync configuration
- `POST /api/v1/config/beat-sync` - Update beat sync configuration (admin)

**Existing Endpoints** (modifications):

- `POST /api/v1/compositions` - Accept `beat_sync_enabled` parameter
- `GET /api/v1/compositions/{id}` - Return beat sync metadata in response

---

## Testing Strategy

### Unit Tests

**Phase 3.1: Prompt Engineering**
- Test `enhance_prompt_with_rhythm()` with various BPM values
- Test `get_motion_style()` returns correct descriptors
- Test `optimize_prompt_for_api()` for each supported API

**Phase 3.2: Beat Effects**
- Test `create_beat_effect_filter()` generates valid FFmpeg filters
- Test `convert_beat_times_to_frames()` accuracy
- Test effect filter syntax correctness

**Phase 3.3: Structural Sync**
- Test `calculate_beat_aligned_clip_boundaries()` with various inputs
- Test `trim_clip_to_beat_boundary()` and `extend_clip_to_beat_boundary()`
- Test `verify_beat_aligned_transitions()` accuracy

### Integration Tests

1. **End-to-End Composition Test**:
   - Generate composition with all three phases enabled
   - Verify beat alignment, effects, and prompt enhancement
   - Measure processing time

2. **Phase Interaction Test**:
   - Test each phase independently
   - Test combinations of phases
   - Verify no conflicts between phases

3. **Edge Case Tests**:
   - Missing beat_times (graceful fallback)
   - Very high/low BPM
   - Very short/long songs
   - User-selected 30-second segment

### Performance Tests

- **Prompt Enhancement**: < 10ms overhead per clip
- **Beat Effects**: < 5 seconds for 30-second video
- **Beat Alignment**: < 10 seconds for 6 clips
- **Total Overhead**: < 20 seconds for full composition

### User Acceptance Tests

1. Generate 10 test videos with beat sync enabled
2. Generate 10 test videos with beat sync disabled
3. User survey: Which videos feel more synchronized?
4. Target: 80%+ prefer beat-synced videos

---

## Timeline & Dependencies

### Phase 3.1: Prompt Engineering (Week 1)

**Days 1-2**: Implement prompt enhancement service
- Create `prompt_enhancement.py`
- Implement core functions
- Add motion type templates

**Day 3**: Integration with clip generation
- Modify `clip_generation.py`
- Add motion type selection logic

**Day 4**: API-specific optimization
- Test with each API
- Tune prompt formats

**Day 5**: Testing & validation
- Unit tests
- Motion analysis validation

### Phase 3.2: Audio-Reactive Filters (Week 2)

**Days 1-2**: Implement beat effects service
- Create `beat_effects.py`
- Implement effect filter generation
- Test FFmpeg filter syntax

**Day 3**: Integration with video composition
- Modify `concatenate_clips()`
- Add effect application step

**Day 4**: Frame-accurate timing
- Implement frame conversion
- Verify timing accuracy

**Days 5-6**: Testing & validation
- Frame accuracy tests
- Effect visibility tests
- Performance tests

### Phase 3.3: Structural Sync (Week 3)

**Day 1**: Enhance beat alignment service
- Add user selection support
- Improve boundary calculation

**Days 2-3**: Implement clip trimming/extension
- Create trim/extend functions
- Test with various clip lengths

**Day 4**: Integration with composition pipeline
- Modify `composition_execution.py`
- Add beat alignment step

**Days 5-6**: Testing & validation
- Boundary alignment tests
- Transition verification
- Edge case tests

### Integration & Polish (Week 4)

**Days 1-2**: End-to-end integration
- Test all three phases together
- Fix any conflicts or issues

**Day 3**: Feature flags & configuration
- Add configuration options
- Implement feature flags

**Days 4-5**: Documentation & final testing
- Update API documentation
- User acceptance testing
- Performance optimization

### Dependencies

- **Phase 3.1** has no dependencies (can start immediately)
- **Phase 3.2** depends on Phase 3.1 completion (uses BPM from song analysis)
- **Phase 3.3** can run in parallel with Phase 3.2 (independent)
- **Integration** requires all three phases complete

### Total Timeline

- **Phase 3.1**: 5 days
- **Phase 3.2**: 6 days
- **Phase 3.3**: 6 days
- **Integration**: 5 days
- **Total: ~22 days (~4.5 weeks)**

---

## Success Metrics

### Technical Metrics

1. **Prompt Enhancement**:
   - 100% of clips use enhanced prompts
   - 40%+ show detectable periodic motion
   - Average alignment score > 0.4

2. **Beat Effects**:
   - 100% of effects trigger within ±1 frame
   - Effects visible in 90%+ of videos
   - Processing overhead < 5 seconds

3. **Structural Sync**:
   - 100% of transitions within ±50ms of beats
   - All boundaries align to beat frames
   - Processing overhead < 10 seconds

### User Experience Metrics

1. **Perception of Sync**:
   - 80%+ of users notice beat synchronization
   - 70%+ prefer beat-synced videos in A/B tests

2. **Video Quality**:
   - No degradation in visual quality
   - Effects enhance rather than distract
   - Smooth, professional transitions

3. **Performance**:
   - Total composition time increase < 20 seconds
   - No increase in failure rate
   - No increase in API costs

### Business Metrics

1. **Adoption**:
   - 90%+ of users enable beat sync (if optional)
   - Positive feedback in user surveys

2. **Quality Improvement**:
   - Reduced re-generation requests
   - Higher user satisfaction scores

---

## Appendix: FFmpeg Filter Reference

### Flash Effect Filter

```bash
geq=r='if(eq(n,FRAME1)+eq(n,FRAME2)+...,255,p(X,Y))':g='if(eq(n,FRAME1)+eq(n,FRAME2)+...,255,p(X,Y))':b='if(eq(n,FRAME1)+eq(n,FRAME2)+...,255,p(X,Y))'
```

### Color Burst Filter

```bash
curves=all='0/0 0.5/0.7 1/1',geq=r='if(BEAT_CONDITION,r(X,Y)*1.5,r(X,Y))':g='if(BEAT_CONDITION,g(X,Y)*1.5,g(X,Y))':b='if(BEAT_CONDITION,b(X,Y)*1.5,b(X,Y))'
```

### Zoom Pulse Filter

```bash
zoompan=z='if(eq(n,BEAT_FRAME),1.05,1)':d=3
```

### Glitch Effect Filter

```bash
geq=r='p(X+3,Y)':g='p(X,Y)':b='p(X-3,Y)'
```

---

## Conclusion

This implementation plan provides a comprehensive roadmap for implementing the three-phase Beat Synchronization feature. Each phase builds upon the previous to create a cohesive, professional beat-synced video generation system.

The phased approach allows for:
- **Gradual rollout** with feature flags
- **Independent testing** of each component
- **Flexible configuration** for different use cases
- **Measurable success** through defined metrics

Total implementation time: **~4.5 weeks** with proper testing and validation.

