# Beat Synchronization Implementation Plan

**Section 3 from High-Level Plan: Beat Synchronization**

This document provides a comprehensive implementation plan for the three-phase Beat
Synchronization feature, which ensures video clips are rhythmically synchronized with
the musical beats of the song.

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

### Foundation Status (✅ COMPLETE)

**Beat Sync Foundation has been implemented** (see `FOUNDATION-IMPLEMENTATION-GUIDE.md`):

- ✅ **Prompt Enhancement Service** (`prompt_enhancement.py`):
  - `get_tempo_classification()` - Classifies BPM into slow/medium/fast/very_fast
  - `get_motion_descriptor()` - Gets motion descriptors based on BPM and motion type
  - `enhance_prompt_with_rhythm()` - Enhances prompts with rhythmic motion cues
  - `get_motion_type_from_genre()` - Suggests motion type based on genre
  - Integrated into `scene_planner.py` - `build_prompt()` now accepts `bpm` and `motion_type` parameters

- ✅ **Beat Filter Service** (`beat_filters.py`):
  - `generate_beat_filter_expression()` - Generates FFmpeg filter expressions
  - `generate_beat_filter_complex()` - Generates filter_complex expressions
  - Supports: flash, color_burst, zoom_pulse, brightness_pulse filter types
  - Integrated into `video_composition.py` - `concatenate_clips()` now accepts
    `beat_times`, `filter_type`, `frame_rate` parameters

- ✅ **Integration**:
  - BPM flows from analysis → scene planning → prompt enhancement
  - Beat times flow from analysis → composition execution → video composition → beat filters
  - All changes are backward compatible (optional parameters)

**Next Steps**: The foundation enables Phase 3.1 and Phase 3.2 full implementation.
See sections below for remaining work.

### Target State

After implementation:

- Generated clips have natural rhythmic motion (Phase 3.1)
- Visual effects flash/pulse on every major beat (Phase 3.2)
- All clip transitions occur exactly on beat boundaries (Phase 3.3)
- Combined effect creates strong perception of beat synchronization

### Success Criteria

- **Phase 3.1**: 40%+ of generated clips show periodic motion aligned with beats
  (measured via motion analysis)
- **Phase 3.2**: Visual effects trigger within ±20ms of beat timestamps (frame-accurate)
- **Phase 3.3**: 100% of clip transitions occur within ±50ms of beat boundaries
- **Combined**: User perception of strong beat sync in 80%+ of generated videos

---

## Phase 3.1: Prompt Engineering

### Objective

Modify video generation prompts to bias AI models toward producing rhythmic, periodic
motion that naturally aligns with musical beats.

### Technical Approach

Enhance the base prompt template with rhythmic motion descriptors based on:

- Song BPM (beats per minute)
- Motion type selection (bouncing, pulsing, rotating, etc.)
- Tempo-appropriate motion descriptors

### Implementation Details

#### 3.1.1: Prompt Enhancement Service

**Status**: ✅ **FOUNDATION COMPLETE** - Basic implementation done, enhancements needed

**Location**: `backend/app/services/prompt_enhancement.py` (✅ exists)

**Current Implementation** (Foundation):

The service has been implemented with the following functions:

- ✅ `get_tempo_classification(bpm)` - Classifies BPM into "slow", "medium", "fast",
  "very_fast" (boundaries: 60, 100, 140 BPM)
- ✅ `get_motion_descriptor(bpm, motion_type)` - Gets motion descriptors based on BPM
  and motion type
- ✅ `enhance_prompt_with_rhythm(base_prompt, bpm, motion_type)` - Enhances prompts
  with rhythmic motion cues
- ✅ `get_motion_type_from_genre(genre)` - Suggests motion type based on genre

**Integration Status**:

- ✅ Integrated into `scene_planner.py` - `build_prompt()` accepts `bpm` and `motion_type` parameters
- ✅ BPM flows from `SongAnalysis` → `build_scene_spec()` → `build_prompt()` → `enhance_prompt_with_rhythm()`

**Remaining Work** (Full Phase 3.1):

1. **API-Specific Optimization** (not yet implemented):
   - Add `optimize_prompt_for_api()` function for Runway, Pika, Kling-specific prompt formats
   - Test and tune prompt formats for each API

2. **Enhanced Motion Templates** (partially implemented):
   - Current: Basic motion descriptors work
   - Future: Add more detailed motion templates (see `RHYTHMIC_MOTION_TEMPLATES` in plan)

3. **Motion Type Selection Logic** (partially implemented):
   - Current: `get_motion_type_from_genre()` provides basic genre-based selection
   - Future: Add more sophisticated selection based on mood, scene context, user preferences

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

**Status**: ✅ **FOUNDATION COMPLETE** - Integrated at scene planning level

**Current Implementation**:

The prompt enhancement is integrated at the scene planning level:

- ✅ `scene_planner.py` → `build_scene_spec()` passes BPM from analysis to `build_prompt()`
- ✅ `build_prompt()` calls `enhance_prompt_with_rhythm()` when BPM is provided
- ✅ Motion type is auto-selected via `get_motion_type_from_genre()` if not provided

**Remaining Work**:

1. **Direct Integration in Clip Generation** (optional enhancement):
   - Currently prompts are enhanced in `build_scene_spec()` before clip generation
   - Could add direct integration in `clip_generation.py` for more control
   - Would allow user-selected motion types per clip

2. **Motion Type Selection UI** (future):
   - Add UI controls for motion type selection
   - Store user preferences

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

**Foundation (✅ COMPLETE)**:

- ✅ Prompt Enhancement Service: Done
- ✅ Integration with Scene Planning: Done
- ✅ Basic Motion Type Selection: Done

**Remaining Work**:

- **API-Specific Optimization**: 1 day
- **Enhanced Motion Templates**: 0.5 days
- **Advanced Motion Type Selection**: 0.5 days
- **Testing & Validation**: 1 day
- **Total Remaining: ~3 days**

---

## Phase 3.2: Audio-Reactive FFmpeg Filters

### Objective

Apply visual effects (flashes, color bursts, zoom pulses) precisely on beat timestamps
using FFmpeg filters, creating strong visual cues that the video is synchronized to
the music.

### Technical Approach

Use FFmpeg's `select` and `geq` filters to apply effects at exact frame timestamps
corresponding to beat times. Effects are applied during the final video composition
step.

### Implementation Details

#### 3.2.1: Beat Effect Service

**Status**: ✅ **FOUNDATION COMPLETE** - Basic implementation done, enhancements needed

**Location**: `backend/app/services/beat_filters.py` (✅ exists - note: named
`beat_filters.py` not `beat_effects.py`)

**Current Implementation** (Foundation):

The service has been implemented with the following functions:

- ✅ `generate_beat_filter_expression(beat_times, filter_type, frame_rate,
  tolerance_ms)` - Generates FFmpeg filter expressions
- ✅ `generate_beat_filter_complex(beat_times, filter_type, frame_rate,
  tolerance_ms)` - Generates filter_complex expressions
- ✅ Supports filter types: `flash`, `color_burst`, `zoom_pulse`, `brightness_pulse`
- ✅ Frame-accurate timing with tolerance windows

**Integration Status**:

- ✅ Integrated into `video_composition.py` - `concatenate_clips()` accepts
  `beat_times`, `filter_type`, `frame_rate` parameters
- ✅ Beat times flow from `SongAnalysis` → `composition_execution.py` →
  `concatenate_clips()` → beat filter application
- ✅ Basic flash effect implementation using time-based FFmpeg filters

**Remaining Work** (Full Phase 3.2):

1. **Enhanced Effect Implementations** (partially implemented):
   - ✅ Flash effect: Basic implementation done
   - ✅ Color burst: Basic implementation done
   - ⚠️ Zoom pulse: Filter expression generated, but complex filter chain needs refinement
   - ❌ Glitch effect: Not yet implemented

2. **Effect Parameter Customization** (not yet implemented):
   - Current: Fixed effect parameters
   - Future: Add `effect_params` dict for intensity, color, duration customization
   - Add configuration in `config.py` for effect settings

3. **Frame-Accurate Timing Verification** (needs testing):
   - Current: Time-based filters with tolerance windows
   - Future: Add frame-accurate verification and testing
   - Ensure effects trigger within ±20ms of beat timestamps

```python
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
```

```python
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
```

```python
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
```

```python
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

**Status**: ✅ **FOUNDATION COMPLETE** - Basic integration done

**Current Implementation**:

The beat filters are integrated into video composition:

- ✅ `concatenate_clips()` accepts `beat_times`, `filter_type`, `frame_rate` parameters
- ✅ Beat filters are applied before audio muxing
- ✅ Uses `generate_beat_filter_complex()` from `beat_filters.py`
- ✅ Basic flash effect implementation using time-based FFmpeg filters

**Integration Flow**:

- ✅ `composition_execution.py` → Gets `beat_times` from analysis via `get_latest_analysis()`
- ✅ Passes `beat_times` to `concatenate_clips()`
- ✅ `concatenate_clips()` applies filters to concatenated video before muxing

**Remaining Work**:

1. **Effect Configuration** (not yet implemented):
   - Current: Simple `filter_type` string parameter
   - Future: Add `beat_effect_config` dict with enabled flag, effect_params, etc.
   - Add configuration in `config.py`

2. **Enhanced Filter Application** (basic implementation done, needs refinement):
   - Current: Basic time-based filter application
   - Future: Improve filter expression generation for better visual quality
   - Add support for more complex filter chains (zoom_pulse, glitch)
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

```python
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

**New Helper Function:**

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

**Critical Requirement**: Effects must trigger within ±20ms of beat timestamps
(frame-accurate at 24 FPS).

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

**Foundation (✅ COMPLETE)**:

- ✅ Beat Filter Service: Done
- ✅ Integration with Video Composition: Done
- ✅ Basic Frame Timing: Done

**Remaining Work**:

- **Enhanced Effect Implementations** (glitch, improved zoom_pulse): 1-2 days
- **Effect Parameter Customization**: 1 day
- **Frame-Accurate Timing Verification**: 0.5 days
- **Effect Configuration System**: 0.5 days
- **Testing & Validation**: 1-2 days
- **Total Remaining: ~4-6 days**

---

## Phase 3.3: Structural Sync

### Objective

Ensure all clip transitions (cuts between clips) occur precisely on musical beat
boundaries, creating rhythmic editing that reinforces beat synchronization.

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

**Status**: ✅ Foundation components implemented, full architecture pending

```text
┌─────────────────────────────────────────────────────────────┐
│                    Clip Generation Layer                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Prompt Enhancement Service (Phase 3.1) ✅ FOUNDATION   │  │
│  │  ✅ enhance_prompt_with_rhythm()                      │  │
│  │  ✅ get_tempo_classification()                        │  │
│  │  ✅ get_motion_descriptor()                           │  │
│  │  ✅ get_motion_type_from_genre()                      │  │
│  │  ⚠️ optimize_prompt_for_api() (not yet implemented)   │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Scene Planner (✅ INTEGRATED)                        │  │
│  │  ✅ build_prompt() accepts bpm, motion_type          │  │
│  │  ✅ build_scene_spec() passes BPM from analysis      │  │
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
│  │  Composition Execution (✅ INTEGRATED)                 │  │
│  │  ✅ Gets beat_times from analysis                    │  │
│  │  ✅ Passes beat_times to concatenate_clips()         │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Beat Alignment Service (Phase 3.3) ⚠️ NOT STARTED    │  │
│  │  - calculate_beat_aligned_clip_boundaries()          │  │
│  │  - verify_beat_aligned_transitions()                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Video Composition Service (✅ INTEGRATED)             │  │
│  │  ✅ concatenate_clips() accepts beat_times           │  │
│  │  ✅ Applies beat filters before audio muxing        │  │
│  │  ⚠️ trim_clip_to_beat_boundary() (not yet implemented)│ │
│  │  ⚠️ extend_clip_to_beat_boundary() (not yet implemented)││
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Beat Filters Service (Phase 3.2) ✅ FOUNDATION      │  │
│  │  ✅ generate_beat_filter_expression()                │  │
│  │  ✅ generate_beat_filter_complex()                   │  │
│  │  ✅ Supports: flash, color_burst, zoom_pulse,         │  │
│  │     brightness_pulse                                 │  │
│  │  ⚠️ Enhanced effects (glitch, improved zoom) pending  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Final Composed Video                                 │  │
│  │  ✅ Rhythmic motion (Phase 3.1 Foundation)            │  │
│  │  ⚠️ Beat-aligned transitions (Phase 3.3 - pending)    │  │
│  │  ✅ Visual beat effects (Phase 3.2 Foundation)       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**Current Implementation (Foundation)**:

1. ✅ **Song Analysis** → Provides `beat_times` array and `bpm` (via `SongAnalysis` schema)
2. ✅ **Prompt Enhancement** → Uses `bpm` to enhance prompts in `build_prompt()`
3. ✅ **Clip Generation** → Generates clips with enhanced prompts (via `build_scene_spec()`)
4. ✅ **Composition Execution** → Gets `beat_times` from analysis via `get_latest_analysis()`
5. ✅ **Beat Filters** → Uses `beat_times` to apply effects in `concatenate_clips()`
6. ✅ **Final Composition** → Combines clips with beat-reactive effects

**Remaining Work**:

- ⚠️ **Beat Alignment** → Uses `beat_times` to calculate boundaries (Phase 3.3)
- ⚠️ **Clip Trimming/Extension** → Aligns clips to boundaries (Phase 3.3)

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

**Phase 3.1: Prompt Engineering** ✅ **FOUNDATION TESTS COMPLETE**

- ✅ Test `enhance_prompt_with_rhythm()` with various BPM values (27 tests in `test_prompt_enhancement.py`)
- ✅ Test `get_tempo_classification()` boundary values and tempo ranges
- ✅ Test `get_motion_descriptor()` with all motion types and BPM combinations
- ✅ Test `get_motion_type_from_genre()` genre mapping
- ✅ Test BPM integration in `build_prompt()` (3 tests in `test_scene_planner.py`)
- ⚠️ Test `optimize_prompt_for_api()` for each supported API (not yet implemented)

**Phase 3.2: Beat Effects** ✅ **FOUNDATION TESTS COMPLETE**

- ✅ Test `generate_beat_filter_expression()` generates valid FFmpeg filters (16 tests in `test_beat_filters.py`)
- ✅ Test `generate_beat_filter_complex()` filter complex generation
- ✅ Test all filter types (flash, color_burst, zoom_pulse, brightness_pulse)
- ✅ Test edge cases (empty beat_times, invalid filter types, tolerance handling)
- ⚠️ Test `convert_beat_times_to_frames()` accuracy (needs frame-accurate verification tests)

**Phase 3.3: Structural Sync** (Not yet started)

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

**✅ Foundation Complete** (Already Done):

- ✅ Created `prompt_enhancement.py` with core functions
- ✅ Integrated with `scene_planner.py`
- ✅ Basic motion type selection implemented
- ✅ Unit tests written (27 tests)

**Remaining Work**:

- **Day 1**: API-specific optimization
  - Add `optimize_prompt_for_api()` function
  - Test with each API (Runway, Pika, Kling)
  - Tune prompt formats

- **Day 2**: Enhanced motion templates
  - Add more detailed motion templates
  - Improve motion descriptor quality

- **Day 3**: Advanced motion type selection
  - Add mood-based selection
  - Add user preference support
  - Testing & validation

### Phase 3.2: Audio-Reactive Filters (Week 2)

**✅ Foundation Complete** (Already Done):

- ✅ Created `beat_filters.py` (note: named `beat_filters.py` not `beat_effects.py`)
- ✅ Implemented basic filter generation functions
- ✅ Integrated with `video_composition.py`
- ✅ Basic frame timing implemented
- ✅ Unit tests written (16 tests)

**Remaining Work**:

- **Day 1**: Enhanced effect implementations
  - Improve zoom_pulse filter chain
  - Implement glitch effect
  - Refine color_burst implementation

- **Day 2**: Effect parameter customization
  - Add `effect_params` dict support
  - Add configuration in `config.py`
  - Test with various parameter combinations

- **Day 3**: Frame-accurate timing verification
  - Add timing verification tests
  - Ensure ±20ms accuracy
  - Optimize filter expressions

- **Days 4-5**: Testing & validation
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

**Foundation Status**:

- ✅ **Phase 3.1 Foundation**: Complete (prompt enhancement service + integration)
- ✅ **Phase 3.2 Foundation**: Complete (beat filters service + integration)

**Remaining Work**:

- **Phase 3.1 Completion**: 3 days (API optimization, enhanced templates, advanced selection)
- **Phase 3.2 Completion**: 5 days (enhanced effects, parameter customization, verification)
- **Phase 3.3**: 6 days (unchanged - structural sync)
- **Integration**: 5 days (unchanged)
- **Total Remaining: ~19 days (~4 weeks)**

**Note**: Foundation work has reduced remaining effort by ~3 days and enabled
parallel work on Phase 3.3.

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

This implementation plan provides a comprehensive roadmap for implementing the
three-phase Beat Synchronization feature. Each phase builds upon the previous to
create a cohesive, professional beat-synced video generation system.

The phased approach allows for:

- **Gradual rollout** with feature flags
- **Independent testing** of each component
- **Flexible configuration** for different use cases
- **Measurable success** through defined metrics

Total implementation time: **~4.5 weeks** with proper testing and validation.
