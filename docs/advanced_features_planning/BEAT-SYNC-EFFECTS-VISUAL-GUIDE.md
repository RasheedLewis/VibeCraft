# Beat-Sync Effects: Visual Guide - Distinguishing AI vs FFmpeg

## Overview

This guide helps you distinguish between:
- **(a) What the video generation AI model creates** (character, dancing, motion, visual style)
- **(b) What FFmpeg post-processing adds** (beat-sync visual effects)

**Key Implementation Details:**

- Effects trigger within ±20ms tolerance window around each beat
- Effects are applied to **every 4th beat** (not every beat) to avoid over-saturation
- Effects **rotate** through different types: flash → color_burst → zoom_pulse → brightness_pulse → glitch → repeat
- Each effect is applied **3 times in a row** before rotating to the next
- Effects are frame-accurate (within ±20ms of beat timestamps)
- Effects are applied before audio muxing in the composition pipeline

**Effect Rotation Pattern:**
- Beats 0, 4, 8: Flash effect
- Beats 12, 16, 20: Color burst effect
- Beats 24, 28, 32: Zoom pulse effect
- Beats 36, 40, 44: Brightness pulse effect
- Beats 48, 52, 56: Glitch effect
- Then repeats...

---

## What the AI Model Generates (minimax/hailuo-2.3)

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

---

## What FFmpeg Adds (Beat-Sync Effects)

FFmpeg applies **post-processing effects** that trigger at precise beat moments:

### 1. Flash Effect
**What it does:** Increases RGB values (brightness) at beat moments

**FFmpeg filter:** `geq` (generic equation) - adds intensity to R, G, B channels
- **Normal mode:** +30 RGB values for 50ms around each beat
- **Test mode:** +90 RGB values for 150ms around each beat

**What to look for:**
- Brief white/bright flashes that occur **exactly on every 4th beat**
- Very short duration (50-150ms)
- Happens **on top of** the AI-generated video
- Frame-accurate timing (within ±20ms of beat timestamp)
- **Note:** Effects rotate, so flash appears every ~12 beats (3 flashes, then other effects)

**Visual example:**
- Video is playing normally
- **Flash!** (brief brightness spike on 4th beat)
- Video continues normally
- **Flash!** (8th beat)
- **Flash!** (12th beat)
- Then switches to color burst effect

**Search terms for examples:**
- "ffmpeg flash effect video"
- "beat-sync flash effect"
- "video brightness pulse on beat"
- "ffmpeg geq filter flash"

**URLs/Resources:**
- FFmpeg `geq` filter docs: https://ffmpeg.org/ffmpeg-filters.html#geq
- Video examples: Search YouTube for "beat-sync flash effect" or "audio-reactive flash"

---

### 2. Color Burst Effect
**What it does:** Increases color saturation and brightness at beat moments

**FFmpeg filter:** `eq` (equalizer) - adjusts saturation and brightness
- **Normal mode:** 1.5x saturation, +0.1 brightness for 100ms
- **Test mode:** 2.0x saturation, +0.2 brightness for 300ms

**What to look for:**
- Colors become **more vibrant/saturated** on beats
- Brief color intensity spike
- Happens **on top of** existing colors (doesn't change the color palette itself)

**Visual example:**
- Video has purple/blue color palette (from AI)
- **Beat hits** → colors become more intense/vibrant
- Colors return to normal
- **Next beat** → intensity spike again

**Search terms:**
- "ffmpeg saturation boost"
- "color burst effect video"
- "beat-sync color intensity"
- "ffmpeg eq filter saturation"

**URLs/Resources:**
- FFmpeg `eq` filter: https://ffmpeg.org/ffmpeg-filters.html#eq

---

### 3. Zoom Pulse Effect
**What it does:** Slightly zooms in at beat moments

**FFmpeg filter:** `scale` - scales video dimensions
- **Normal mode:** 1.05x zoom (5% larger) for 200ms
- **Test mode:** 1.15x zoom (15% larger) for 600ms

**What to look for:**
- Video **slightly zooms in** on each beat
- Very subtle (5% is barely noticeable)
- Happens **on top of** any AI-generated camera motion

**Visual example:**
- Video is playing (maybe AI already has some zoom)
- **Beat hits** → video zooms in slightly more
- Zooms back out
- **Next beat** → zoom pulse again

**Search terms:**
- "ffmpeg zoom pulse effect"
- "beat-sync zoom"
- "video scale filter pulse"
- "audio-reactive zoom"

**URLs/Resources:**
- FFmpeg `scale` filter: https://ffmpeg.org/ffmpeg-filters.html#scale

---

### 4. Brightness Pulse Effect
**What it does:** Increases overall brightness at beat moments

**FFmpeg filter:** `eq` - adjusts brightness only
- **Normal mode:** +0.15 brightness for 100ms
- **Test mode:** +0.3 brightness for 300ms

**What to look for:**
- Video gets **brighter** on beats
- Similar to flash but uses brightness filter (not RGB manipulation)
- More subtle than flash effect

**Search terms:**
- "ffmpeg brightness pulse"
- "beat-sync brightness"
- "video brightness filter"

---

### 5. Glitch Effect
**What it does:** Shifts RGB channels horizontally (chromatic aberration)

**FFmpeg filter:** `geq` - shifts red channel right, blue channel left
- **Normal mode:** 3-pixel shift for 100ms
- **Test mode:** 8-pixel shift for 300ms

**What to look for:**
- **Color separation** on beats (red/blue fringes)
- Digital "glitch" appearance
- RGB channels misaligned briefly

**Visual example:**
- Video playing normally
- **Beat hits** → red/blue color fringes appear (like chromatic aberration)
- Returns to normal
- **Next beat** → glitch again

**Search terms:**
- "ffmpeg glitch effect"
- "chromatic aberration effect"
- "RGB channel shift video"
- "beat-sync glitch"
- "digital glitch effect"

**URLs/Resources:**
- Example: Search YouTube for "chromatic aberration effect" or "RGB glitch effect"

---

## How to Distinguish: Key Differences

### Timing
- **AI-generated motion:** Continuous, smooth, organic
- **FFmpeg effects:** Precise, frame-accurate, triggered exactly on beats

### Duration
- **AI-generated motion:** Lasts throughout the clip
- **FFmpeg effects:** Very brief (50-200ms per beat)

### Nature
- **AI-generated:** Part of the video content itself (character, style, motion)
- **FFmpeg effects:** Post-processing layer on top of the video

### Synchronization
- **AI-generated:** May or may not align with beats (depends on prompt/model)
- **FFmpeg effects:** **Always** synchronized to beat timestamps (frame-accurate)

---

## Testing Strategy

### Step 1: Generate a Video and Save Both Versions
1. Set environment variable: `SAVE_NO_EFFECTS_VIDEO=true`
2. Generate a video (with effects enabled)
3. The system will automatically save:
   - **Pre-effects version**: `comparison_videos/no_effects_<video_name>.mp4` (pure AI-generated, no FFmpeg effects)
   - **Final version**: The normal composed video (with FFmpeg effects)
4. Compare the two videos side-by-side
5. **Differences = FFmpeg effects**

### Step 2: Generate a Video Without Effects (Alternative)
1. Temporarily disable beat filters in code (`BEAT_EFFECTS_ENABLED=false`)
2. Generate a video
3. Watch it - this shows **pure AI-generated content**

### Step 3: Generate Same Video With Effects
1. Enable beat filters (`BEAT_EFFECTS_ENABLED=true`)
2. Generate the same video (same song, same clips)
3. Watch it - compare to Step 2
4. **Differences = FFmpeg effects**

### Step 3: Use Test Mode
1. Set `BEAT_EFFECT_TEST_MODE=true`
2. Effects are 3x more intense, 3x longer duration
3. Much easier to see what FFmpeg adds

### Step 4: Frame-by-Frame Analysis
1. Use video player with frame-by-frame controls
2. Find a beat timestamp (from logs)
3. Step through frames around that beat
4. Look for sudden changes (flash, zoom, color burst)
5. These are **FFmpeg effects** (AI motion is smooth)

---

## Common Confusion Points

### "The character is dancing on beats - is that FFmpeg?"
**No!** That's the AI model responding to your prompt. FFmpeg doesn't control character motion.

### "The colors change on beats - is that FFmpeg?"
**Maybe!** 
- If colors change **smoothly** throughout → AI-generated
- If colors have **sudden intensity spikes** exactly on beats → FFmpeg color burst

### "The video zooms on beats - is that FFmpeg?"
**Maybe!**
- If zoom is **smooth and continuous** → AI-generated camera motion
- If zoom is **brief pulses** exactly on beats → FFmpeg zoom pulse

---

## Visual Comparison Examples

### AI-Generated (No FFmpeg):
```
Frame 1: Character dancing, purple colors
Frame 2: Character dancing, purple colors (smooth transition)
Frame 3: Character dancing, purple colors
... (smooth throughout)
```

### With FFmpeg Flash Effect:
```
Frame 1: Character dancing, purple colors
Frame 2: Character dancing, purple colors (smooth)
Frame 3: Character dancing, purple colors (smooth)
Frame 4: **BEAT HITS** → Character dancing, purple colors + BRIGHT FLASH
Frame 5: Character dancing, purple colors (flash fading)
Frame 6: Character dancing, purple colors (back to normal)
... (smooth until next beat)
```

---

## Search Terms for Examples

### General Beat-Sync Effects:
- "beat-sync visual effects"
- "audio-reactive video effects"
- "music visualization effects"
- "ffmpeg beat synchronization"

### Specific Effects:
- "ffmpeg flash effect tutorial"
- "video brightness pulse on beat"
- "chromatic aberration effect"
- "beat-sync zoom pulse"
- "color burst video effect"

### YouTube/Video Examples:
- Search: "beat-sync flash effect" → Find music videos with flash effects
- Search: "chromatic aberration" → See RGB channel shift examples
- Search: "audio-reactive zoom" → See zoom pulse examples

### Technical Resources:
- FFmpeg filter documentation: https://ffmpeg.org/ffmpeg-filters.html
- FFmpeg `geq` filter: https://ffmpeg.org/ffmpeg-filters.html#geq
- FFmpeg `eq` filter: https://ffmpeg.org/ffmpeg-filters.html#eq
- FFmpeg `scale` filter: https://ffmpeg.org/ffmpeg-filters.html#scale

---

## Quick Reference: What to Look For

| Effect | What It Does | Duration | How to Spot |
|--------|--------------|----------|-------------|
| **Flash** | Brightness spike | 50ms | Brief white flash on beats |
| **Color Burst** | Saturation increase | 100ms | Colors become more vibrant on beats |
| **Zoom Pulse** | Scale increase | 200ms | Video zooms in slightly on beats |
| **Brightness Pulse** | Brightness increase | 100ms | Video gets brighter on beats |
| **Glitch** | RGB channel shift | 100ms | Red/blue fringes on beats |

---

## Summary

**AI Model Generates:**
- Character, dancing, motion, style, colors (continuous, organic)

**FFmpeg Adds:**
- Brief effects that trigger exactly on beats (frame-accurate, post-processing)

**Key Test:**
- If an effect happens **exactly on every beat** with precise timing → FFmpeg
- If motion/style is **continuous and smooth** → AI model

**Best Way to See FFmpeg Effects:**
- Use `SAVE_NO_EFFECTS_VIDEO=true` to automatically save both versions for comparison
- Use `BEAT_EFFECT_TEST_MODE=true` for exaggerated effects (makes effects 3x more visible)
- Compare video with/without effects side-by-side
- Watch frame-by-frame around beat timestamps

**How to Use the Comparison Feature:**
1. Set environment variable: `export SAVE_NO_EFFECTS_VIDEO=true`
2. Generate a video (with effects enabled)
3. Check `comparison_videos/` directory for:
   - `no_effects_<video_name>.mp4` - Video before FFmpeg effects (pure AI-generated)
   - Compare with the final composed video (with FFmpeg effects)
4. The difference between these two videos shows exactly what FFmpeg adds

