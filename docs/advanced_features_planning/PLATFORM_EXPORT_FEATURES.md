# Platform Export Features for TikTok/Instagram/YouTube Shorts

## Overview

This document outlines a unified approach to generate videos that work seamlessly across TikTok, Instagram Reels, and YouTube Shorts. Instead of platform-specific exports, we'll generate videos optimized for all three platforms out-of-the-box.

---

## Platform Common Requirements

All three platforms share the same core requirements:

| Requirement | TikTok | Instagram Reels | YouTube Shorts | **Unified Standard** |
|------------|--------|------------------|----------------|---------------------|
| **Aspect Ratio** | 9:16 | 9:16 | 9:16 | ✅ **9:16** |
| **Resolution** | 1080x1920 | 1080x1920 | 1080x1920 | ✅ **1080x1920** |
| **Format** | MP4, MOV | MP4, MOV | MP4, MOV, AVI | ✅ **MP4** |
| **Duration** | Up to 10 min (typically 15-60s) | 15-90 seconds | Up to 60 seconds | ✅ **Up to 60s** |

**Key Insight:** If we generate 9:16 videos at 1080x1920 resolution, up to 60 seconds, in MP4 format, they work perfectly for all three platforms without any conversion!

---

## Current State vs. Target State

### Current State
- Generates **16:9 horizontal videos** (1920x1080)
- Requires post-processing to convert to 9:16
- Not optimized for social media platforms

### Target State
- Generate **9:16 vertical videos** (1080x1920) natively for "Short Form" videos
- Works for TikTok, Instagram Reels, and YouTube Shorts out-of-the-box
- No conversion needed - download and upload directly

---

## Unified Strategy

### Core Approach: Generate 9:16 Natively

Instead of generating 16:9 and converting, we'll generate 9:16 videos directly using Minimax's `first_frame_image` parameter. This ensures:
- ✅ No quality loss from cropping
- ✅ Better composition (content designed for vertical format)
- ✅ Works for all three platforms without conversion
- ✅ Faster workflow (no post-processing step)

### Implementation Strategy

**For "Short Form" Videos:**
1. Generate videos in **9:16 aspect ratio** natively (using `first_frame_image` with 9:16 image)
2. Ensure duration is **≤ 60 seconds** (works for all platforms)
3. Use **1080x1920 resolution** (optimal for all platforms)
4. Encode in **MP4 format** with platform-optimized settings

**For "Full Length" Videos:**
- Keep current 16:9 format (or allow user choice)
- These are typically for YouTube/Long-form content, not social media

---

## Proposed Features

### 1. Native 9:16 Generation for Short Form ⭐ HIGH PRIORITY

**Feature:** Generate "Short Form" videos in 9:16 aspect ratio natively, optimized for TikTok/Instagram/YouTube Shorts.

**How it works:**
- When user selects "Short Form" video type, generate in 9:16 by default
- Use Minimax's `first_frame_image` parameter with a 9:16 image
- Generated video is already in the correct format - no conversion needed!

**Technical Implementation:**
```python
# When video_type == "short_form" and aspect_ratio == "9:16":
# 1. Create or use 9:16 placeholder image (1080x1920)
# 2. If character image provided, resize/crop to 9:16
# 3. Use as first_frame_image in video generation
# 4. API generates 9:16 video natively

input_params = {
    "prompt": optimized_prompt,
    "duration": 6,  # or 10 for 768p
    "resolution": "1080p",
    "prompt_optimizer": True,
    "first_frame_image": nine_sixteen_image,  # 9:16 image = 9:16 output!
}
```

**Benefits:**
- ✅ No post-processing needed
- ✅ Better quality (native generation vs. cropping)
- ✅ Content composed for vertical format
- ✅ Works for all three platforms immediately

**Files to Modify:**
- `backend/app/services/video_generation.py` - Add 9:16 generation support
- `backend/app/services/video_composition.py` - Handle 9:16 videos in composition
- `backend/app/api/v1/routes_songs.py` - Add aspect ratio option

---

### 2. Duration Optimization ⭐ HIGH PRIORITY

**Feature:** Ensure Short Form videos are ≤ 60 seconds to work for all platforms.

**Implementation:**
- When composing Short Form videos, cap duration at 60 seconds
- If audio selection is longer, trim to 60 seconds (or let user select 60s range)
- Display duration clearly in UI

**User Flow:**
1. User selects "Short Form" video type
2. System automatically limits audio selection to 60 seconds max
3. Generated video is ≤ 60 seconds
4. Works for TikTok, Instagram Reels, and YouTube Shorts

**Files to Modify:**
- `backend/app/services/composition_execution.py` - Add 60s duration cap for Short Form
- Frontend - Show 60s limit in audio selection UI

---

### 3. Auto-Generated Captions/Subtitles ⭐ HIGH PRIORITY

**Feature:** Automatically generate captions/subtitles for the video using the audio transcription.

**Implementation:**
- Use existing Whisper transcription (already in the system)
- Generate SRT/VTT subtitle files
- Burn subtitles into video with social media-friendly styling
- Position captions in safe area (avoid platform UI elements)

**User Flow:**
1. User enables "Add Captions" option (checkbox in video generation)
2. System uses existing audio transcription
3. Generates styled captions optimized for vertical format
4. Burns into video automatically

**Technical Details:**
- Use FFmpeg `subtitles` filter to burn subtitles
- Style: Large, bold font, positioned in center-bottom (safe for all platforms)
- White text with black outline for visibility

**Files to Modify:**
- `backend/app/services/subtitle_generation.py` - New service (or extend existing transcription)
- `backend/app/services/video_composition.py` - Add subtitle burning
- Frontend - Add caption toggle option

---

### 4. Optimized Encoding for Social Media 🎯 MEDIUM PRIORITY

**Feature:** Encode videos with settings optimized for fast uploads and good playback on all platforms.

**Implementation:**
- Use H.264 codec (universal support)
- 1080x1920 resolution at 30fps
- Optimize bitrate for file size (balance quality vs. upload speed)
- Ensure file size stays under platform limits (especially YouTube's 128MB web limit)

**Technical Details:**
- Target bitrate: ~5-8 Mbps for 1080p (good quality, reasonable file size)
- Use 2-pass encoding for better quality at lower bitrates
- Ensure compatibility with all platforms

**Files to Modify:**
- `backend/app/services/video_composition.py` - Update encoding settings for Short Form videos

---

### 5. Hashtag Suggestions 🎯 LOW PRIORITY

**Feature:** Suggest relevant hashtags based on the song's genre, mood, and lyrics.

**Implementation:**
- Analyze song metadata (genre, mood, BPM)
- Extract keywords from lyrics (if available)
- Generate hashtag suggestions
- Display in download/export panel for easy copy-paste

**User Flow:**
1. After video generation, see suggested hashtags
2. Copy hashtags to clipboard
3. Paste into platform when uploading

**Files to Create:**
- `backend/app/services/hashtag_generator.py` - New service
- Frontend - Display hashtag suggestions in video completion panel

---

## Implementation Priority

### Phase 1: Core Features (Must Have)
1. **Native 9:16 Generation** - Generate Short Form videos in 9:16 natively
2. **Duration Optimization** - Cap at 60 seconds for all platforms
3. **Auto-Generated Captions** - Add captions using existing transcription

### Phase 2: Polish (Should Have)
4. **Optimized Encoding** - Platform-friendly encoding settings
5. **Hashtag Suggestions** - Help with discoverability

---

## Technical Implementation Notes

### Native 9:16 Generation

**Key Insight from Research:**
- Minimax Hailuo 2.3 API supports `first_frame_image` parameter
- Output video matches the aspect ratio of `first_frame_image`
- We can generate 9:16 videos natively by providing a 9:16 image!

**Implementation Steps:**

1. **Create 9:16 Placeholder Image:**
   ```python
   # Generate 1080x1920 image (9:16 aspect ratio)
   # Can be solid color, gradient, or composited with character
   nine_sixteen_image = create_9_16_placeholder(width=1080, height=1920)
   ```

2. **Handle Character Images:**
   - If character image provided, resize/crop to 9:16
   - Or composite character into 9:16 canvas
   - Use as `first_frame_image`

3. **Update Video Generation:**
   ```python
   input_params = {
       "prompt": optimized_prompt,
       "duration": 6,  # or 10 for 768p
       "resolution": "1080p",
       "prompt_optimizer": True,
       "first_frame_image": nine_sixteen_image,  # 9:16 image = 9:16 output!
   }
   ```

4. **Update Composition:**
   - Don't normalize aspect ratio if already 9:16
   - Support both 16:9 (Full Length) and 9:16 (Short Form) in composition

### Duration Handling

- API only supports 6 or 10 second clips
- For 3-second clips: Generate 6s, trim to 3s (current approach)
- For composition: Ensure total duration ≤ 60 seconds for Short Form
- Trim audio selection if user selects > 60 seconds

---

### Encoding Settings

**For Short Form (9:16) Videos:**
```bash
# Optimized encoding for social media platforms
ffmpeg -i input.mp4 \
  -c:v libx264 \
  -preset medium \
  -crf 23 \
  -b:v 6M \
  -maxrate 8M \
  -bufsize 12M \
  -r 30 \
  -c:a aac \
  -b:a 192k \
  -movflags +faststart \
  output.mp4
```

**Key Settings:**
- `libx264`: Universal codec support
- `crf 23`: Good quality/size balance
- `6M bitrate`: High quality, reasonable file size
- `30fps`: Standard for social media
- `faststart`: Enables streaming/quick preview

### Post-Processing (If Needed)

**Only needed if:**
- Video exceeds 60 seconds (trim to 60s)
- Adding captions (burn subtitles)
- Final encoding optimization

**FFmpeg Commands:**
```bash
# Trim to 60 seconds
ffmpeg -i input.mp4 -t 60 -c copy output.mp4

# Add subtitles
ffmpeg -i input.mp4 -vf "subtitles=subtitles.srt:force_style='Fontsize=24,PrimaryColour=&Hffffff,OutlineColour=&H000000,Outline=2'" output.mp4
```

---

## User Experience Flow

### Current Flow:
1. Upload song → Analyze → Select video type → Generate clips → Compose → Download video

### Enhanced Flow (Simplified):
1. Upload song → Analyze
2. Select "Short Form" video type → **Automatically generates 9:16 format**
3. Select audio range (up to 60 seconds) → Generate clips → Compose
4. **Optional:** Enable "Add Captions" checkbox
5. Download video → **Works for TikTok, Instagram, YouTube Shorts immediately!**

**Key Simplification:**
- No separate export buttons needed
- No platform selection needed
- One video works for all three platforms
- Just download and upload!

---

## Success Metrics

- **Time to Upload:** Reduce time from "video ready" to "uploaded to platform" by 50%
- **User Satisfaction:** Users can download and upload in < 1 minute (no conversion needed)
- **Compatibility:** 100% of Short Form videos work on TikTok, Instagram, and YouTube Shorts
- **Quality:** Native 9:16 generation maintains full quality (no cropping loss)

---

## Next Steps

1. **Phase 1: Native 9:16 Generation**
   - Update `video_generation.py` to use `first_frame_image` with 9:16 images
   - Create 9:16 placeholder image generator
   - Handle character images (resize/crop to 9:16)
   - Update composition to support 9:16 videos

2. **Phase 2: Duration & Encoding**
   - Add 60-second duration cap for Short Form videos
   - Optimize encoding settings for social media
   - Update UI to show 60s limit

3. **Phase 3: Captions & Polish**
   - Add auto-generated captions option
   - Add hashtag suggestions
   - Test with real users

---

## Related Files

### Backend
- `backend/app/services/video_generation.py` - **Update:** Add 9:16 generation support
- `backend/app/services/video_composition.py` - **Update:** Handle 9:16 videos, add captions
- `backend/app/services/composition_execution.py` - **Update:** Add 60s duration cap
- `backend/app/api/v1/routes_songs.py` - **Update:** Add aspect ratio option
- `backend/app/services/transcription.py` - **Use:** For caption generation

### Frontend
- `frontend/src/components/upload/VideoTypeSelector.tsx` - **Update:** Show 9:16 format info
- `frontend/src/components/song/ClipGenerationPanel.tsx` - **Update:** Add caption toggle
- `frontend/src/components/MainVideoPlayer.tsx` - **Update:** Display 9:16 videos correctly

### New Files Needed
- `backend/app/services/nine_sixteen_image_generator.py` - Generate 9:16 placeholder images
- `backend/app/services/subtitle_generation.py` - Generate and burn captions

---

## Key Decisions Made

1. **Unified Format:** One 9:16 video works for all three platforms (no separate exports)
2. **Native Generation:** Generate 9:16 natively using `first_frame_image` (no cropping)
3. **Duration:** Cap at 60 seconds (works for all platforms)
4. **Encoding:** Optimize once for all platforms (H.264, 1080p, 30fps)
5. **Simplicity:** No platform selection UI - just download and upload!

---

**Last Updated:** Based on Minimax API research and unified platform approach  
**Status:** Ready for implementation - simplified strategy

