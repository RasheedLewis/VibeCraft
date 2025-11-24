# Beat-Sync Visual Effects Guide

This guide covers beat-synchronized visual effects that enhance video rhythm perception through FFmpeg post-processing.

## Overview

Beat-sync effects are visual enhancements that trigger on musical beats to create stronger perception of rhythm synchronization. Effects are applied during video composition using FFmpeg filters.

**Key Implementation Details:**

- Effects trigger within tolerance window around each beat (default: ±20ms, configurable)
- Effects are applied to **every 4th beat** (not every beat) to avoid over-saturation
- Effects **rotate** through different types: flash → color_burst → zoom_pulse → brightness_pulse → glitch → repeat
- Each effect is applied **3 times in a row** before rotating to the next
- Effects are frame-accurate and applied before audio muxing in the composition pipeline
- Test mode available via `BEAT_EFFECT_TEST_MODE=true` for exaggerated effects (3x intensity, 3x tolerance)

**Effect Rotation Pattern:**

- Beats 0, 4, 8: Flash effect
- Beats 12, 16, 20: Color burst effect
- Beats 24, 28, 32: Zoom pulse effect
- Beats 36, 40, 44: Brightness pulse effect
- Beats 48, 52, 56: Glitch effect
- Then repeats...

---

## Effects Reference

| Effect | What It Does | Duration | Normal Mode | Test Mode |
| ------ | ------------ | -------- | ----------- | --------- |
| **Flash** | Brightness spike | 50ms | +30 RGB values | +90 RGB values, 150ms |
| **Color Burst** | Saturation increase | 100ms | 1.5x saturation, +0.1 brightness | 2.0x saturation, +0.2 brightness, 300ms |
| **Zoom Pulse** | Scale increase | 200ms | 1.05x zoom (5%) | 1.15x zoom (15%), 600ms |
| **Brightness Pulse** | Brightness increase | 100ms | +0.15 brightness | +0.3 brightness, 300ms |
| **Glitch** | RGB channel shift | 100ms | 3-pixel shift | 8-pixel shift, 300ms |

### 1. Flash Effect (Default)

**Description:** Brightness pulse/flash on beats - subtle brightness increase when beats occur.

**Implementation:**
- **Filter Type:** `flash`
- **FFmpeg Filter:** `geq` (generic equation) - adds intensity to R, G, B channels
- **Effect:** RGB values increased by 30 (normal) or 90 (test mode)
- **Duration:** 50ms flash window (normal) or 150ms (test mode)
- **Visual:** Brief white/bright flashes that occur exactly on every 4th beat

**Files:**
- `backend/app/services/video_composition.py`
- `backend/app/services/beat_filters.py`
- `backend/app/services/beat_filter_applicator.py`

### 2. Color Burst Effect

**Description:** Color saturation and brightness increase on beats.

**Implementation:**
- **Filter Type:** `color_burst`
- **FFmpeg Filter:** `eq` (equalizer) - adjusts saturation and brightness
- **Effect:** Saturation increased to 1.5x, brightness increased by 0.1 (normal) or 2.0x saturation, +0.2 brightness (test mode)
- **Duration:** 100ms window (normal) or 300ms (test mode)
- **Visual:** Colors become more vibrant/saturated on beats

**Files:**
- `backend/app/services/beat_filters.py`

### 3. Zoom Pulse Effect

**Description:** Subtle zoom pulse on beats - slight scale increase synchronized to rhythm.

**Implementation:**
- **Filter Type:** `zoom_pulse`
- **FFmpeg Filter:** `scale` - scales video dimensions
- **Effect:** 5% zoom increase (normal) or 15% (test mode)
- **Duration:** 200ms window (normal) or 600ms (test mode)
- **Visual:** Video slightly zooms in on each beat

**Files:**
- `backend/app/services/beat_filters.py`

### 4. Brightness Pulse Effect

**Description:** Brightness increase on beats (alternative to flash).

**Implementation:**
- **Filter Type:** `brightness_pulse`
- **FFmpeg Filter:** `eq` - adjusts brightness only
- **Effect:** Brightness increased by 0.15 (normal) or 0.3 (test mode)
- **Duration:** 100ms window (normal) or 300ms (test mode)
- **Visual:** Video gets brighter on beats (more subtle than flash)

**Files:**
- `backend/app/services/beat_filters.py`

### 5. Glitch Effect

**Description:** Digital glitch effect on beats - RGB channel shift creating a chromatic aberration effect.

**Implementation:**
- **Filter Type:** `glitch`
- **FFmpeg Filter:** `geq` - shifts red channel right, blue channel left
- **Effect:** 3-pixel shift (normal) or 8-pixel shift (test mode)
- **Duration:** 100ms window (normal) or 300ms (test mode)
- **Visual:** Color separation on beats (red/blue fringes), digital "glitch" appearance

**Files:**
- `backend/app/services/beat_filters.py`
- `backend/app/services/beat_filter_applicator.py`

---

## AI vs FFmpeg Distinction

### What the AI Model Generates (minimax/hailuo-2.3)

The AI model generates the **core video content**:

- **Character appearance** - The figure/character itself
- **Dancing/motion** - How the character moves (dancing, bouncing, etc.)
- **Visual style** - Abstract style, color palette, aesthetic
- **Camera motion** - Zoom, pan, static camera
- **Scene composition** - Overall visual design

**Characteristics:**
- These are **continuous** - the character is always present, always moving
- Motion is **organic** - follows the character's natural movement
- Style is **consistent** throughout the clip
- Generated **before** composition

**Example:** A character dancing throughout a 5-second clip - this is all AI-generated.

### What FFmpeg Adds (Beat-Sync Effects)

FFmpeg applies **post-processing effects** that trigger at precise beat moments:

**Characteristics:**
- **Timing:** Precise, frame-accurate, triggered exactly on beats
- **Duration:** Very brief (50-200ms per beat)
- **Nature:** Post-processing layer on top of the video
- **Synchronization:** **Always** synchronized to beat timestamps (frame-accurate)

### How to Distinguish

| Aspect | AI-Generated | FFmpeg Effects |
| ------ | ------------ | -------------- |
| **Timing** | Continuous, smooth, organic | Precise, frame-accurate, triggered exactly on beats |
| **Duration** | Lasts throughout the clip | Very brief (50-200ms per beat) |
| **Nature** | Part of the video content itself | Post-processing layer on top |
| **Synchronization** | May or may not align with beats | Always synchronized to beat timestamps |

**Key Test:**
- If an effect happens **exactly on every 4th beat** with precise timing → FFmpeg
- If motion/style is **continuous and smooth** → AI model

### Common Confusion Points

**"The character is dancing on beats - is that FFmpeg?"**
- **No!** That's the AI model responding to your prompt. FFmpeg doesn't control character motion.

**"The colors change on beats - is that FFmpeg?"**
- **Maybe!**
  - If colors change **smoothly** throughout → AI-generated
  - If colors have **sudden intensity spikes** exactly on beats → FFmpeg color burst

**"The video zooms on beats - is that FFmpeg?"**
- **Maybe!**
  - If zoom is **smooth and continuous** → AI-generated camera motion
  - If zoom is **brief pulses** exactly on beats → FFmpeg zoom pulse

---

## Testing & Verification

### Quick Verification

1. **Check Logs:**
   - Look for beat filter application messages in `logs/worker.log`
   - Verify beat count matches song duration
   - Check for: `"Applying {filter_type} beat filters for {N} beats"`
   - Check for: `"Applying effects to {N} beats (every 4th beat, from {N} total beats)"`

2. **Visual Inspection:**
   - Watch final composed video
   - Look for effects synchronized to beats (every 4th beat)
   - Use short-form videos (30 seconds) for easier observation

3. **Test Mode:**
   - Set environment variable: `BEAT_EFFECT_TEST_MODE=true`
   - Effects are 3x more intense, 3x longer duration
   - Much easier to see what FFmpeg adds
   - Logs show: `[TEST MODE] Exaggerating {filter_type} effect`

### Comparison Video Method

**Best way to see FFmpeg effects:**

1. Set environment variable: `export SAVE_NO_EFFECTS_VIDEO=true`
2. Generate a video (with effects enabled)
3. Check `comparison_videos/` directory for:
   - `no_effects_<video_name>.mp4` - Video before FFmpeg effects (pure AI-generated)
   - Compare with the final composed video (with FFmpeg effects)
4. The difference between these two videos shows exactly what FFmpeg adds

### Frame-by-Frame Analysis

1. Use video player with frame-by-frame controls
2. Find a beat timestamp (from logs)
3. Step through frames around that beat
4. Look for sudden changes (flash, zoom, color burst)
5. These are **FFmpeg effects** (AI motion is smooth)

### Log Messages to Look For

```text
[VIDEO-COMPOSE] Applying {filter_type} beat filters for {N} beats
[VIDEO-COMPOSE] Applying effects to {N} beats (every 4th beat, from {N} total beats)
[TEST MODE] Exaggerating {filter_type} effect, tolerance={N}ms
[VIDEO-COMPOSE] Beat filters applied successfully
```

---

## Configuration

### Environment Variables

**Test Mode:**
- `BEAT_EFFECT_TEST_MODE=true` - Enables exaggerated effects (3x intensity, 3x tolerance)

**Comparison Videos:**
- `SAVE_NO_EFFECTS_VIDEO=true` - Saves pre-effects version for comparison

### Effect Parameters

Effects can be customized via `BeatEffectConfig` in `backend/app/core/config.py`:

**Flash Effect:**
- `flash_intensity` (default: 30) - RGB increase amount
- `flash_color` (default: "white")

**Glitch Effect:**
- `glitch_intensity` (default: 0.3) - Channel shift intensity (0.0-1.0)

**Zoom Pulse:**
- `zoom_pulse_amount` (default: 1.05) - Zoom multiplier

**Color Burst:**
- `color_burst_saturation` (default: 1.5) - Saturation multiplier
- `color_burst_brightness` (default: 0.1) - Brightness increase

**Tolerance:**
- `tolerance_ms` (default: 20) - Tolerance window in milliseconds

### Setting Effect Type

Currently, effect type is set in `composition_execution.py`:
- Default: `filter_type = "flash"`
- Can be changed to: `"color_burst"`, `"zoom_pulse"`, `"brightness_pulse"`, `"glitch"`

**Note:** Even when a single effect type is set, effects rotate through all types on every 4th beat.

---

## Troubleshooting

### Effects Not Visible

1. **Check beat times are available:**
   - Verify song analysis completed successfully
   - Check `beat_times` array is populated
   - Look for "Found {N} beat times" in logs

2. **Check effect is being applied:**
   - Look for "Applying {filter_type} beat filters" in logs
   - Verify no errors in filter application
   - Check FFmpeg command includes beat filters

3. **Use test mode:**
   - Set `BEAT_EFFECT_TEST_MODE=true` to make effects more visible
   - Effects are 3x more intense and 3x longer duration
   - Use short videos for easier observation

4. **Remember:** Effects only appear on every 4th beat, not every beat

### Effects Only on First 50 Beats

**FIXED:** This limitation has been removed. Effects now apply to all beats.

If you still see this issue:
- Check `video_composition.py` - should NOT have `[:50]` limit
- Verify chunking logic is working for videos with many beats

### Effects Not Frame-Accurate

1. **Check tolerance settings:**
   - Default tolerance is 20ms (±20ms window)
   - Can be adjusted in `beat_filters.py` or via config
   - Test mode multiplies tolerance by 3x

2. **Verify frame rate:**
   - Default is 24 FPS
   - Ensure frame rate matches video frame rate

### Effects Not Rotating

- Effects should rotate: flash → color_burst → zoom_pulse → brightness_pulse → glitch → repeat
- Each effect appears 3 times in a row (on beats 0,4,8 then 12,16,20, etc.)
- Check logs for: `"Applying effects to {N} beats (every 4th beat)"`

---

## Quick Reference

### Effect Comparison

| Effect | What It Does | Duration | How to Spot |
| ------ | ------------ | -------- | ----------- |
| **Flash** | Brightness spike | 50ms | Brief white flash on every 4th beat |
| **Color Burst** | Saturation increase | 100ms | Colors become more vibrant on beats |
| **Zoom Pulse** | Scale increase | 200ms | Video zooms in slightly on beats |
| **Brightness Pulse** | Brightness increase | 100ms | Video gets brighter on beats |
| **Glitch** | RGB channel shift | 100ms | Red/blue fringes on beats |

### Key Points

- **AI Model Generates:** Character, dancing, motion, style, colors (continuous, organic)
- **FFmpeg Adds:** Brief effects that trigger exactly on every 4th beat (frame-accurate, post-processing)
- **Best Way to See FFmpeg Effects:**
  - Use `SAVE_NO_EFFECTS_VIDEO=true` to automatically save both versions for comparison
  - Use `BEAT_EFFECT_TEST_MODE=true` for exaggerated effects (makes effects 3x more visible)
  - Compare video with/without effects side-by-side
  - Watch frame-by-frame around beat timestamps

### Testing Checklist

- [ ] Flash effect visible on every 4th beat
- [ ] Color burst effect visible on beats (if in rotation)
- [ ] Zoom pulse effect visible on beats (if in rotation)
- [ ] Glitch effect visible on beats (if in rotation)
- [ ] Effects apply to ALL beats (not just first 50)
- [ ] Effects rotate through all 5 types
- [ ] Effects are frame-accurate (±20ms tolerance)
- [ ] Logs show correct beat count
- [ ] Logs show "Beat filters applied successfully"
- [ ] Test mode makes effects more visible

---

**Last Updated:** Based on current implementation
**Related Files:**
- `backend/app/services/video_composition.py`
- `backend/app/services/beat_filters.py`
- `backend/app/services/beat_filter_applicator.py`
- `backend/app/core/config.py` (BeatEffectConfig)

