# Minimax Hailuo 2.3 Aspect Ratio Research

## Date: Current Session

## Key Finding: API Parameter Mismatch! ⚠️

The current code uses parameters that **do not exist** in the actual Minimax Hailuo 2.3 API on Replicate, BUT we ARE already using `first_frame_image` for character consistency!

### Current Code (PARTIALLY CORRECT):
```python
# In video_generation.py, lines 306-332
input_params = {
    "prompt": optimized_prompt,
    "num_frames": max(1, min(frame_count, 120)),  # ❌ NOT SUPPORTED
    "width": 576,  # ❌ NOT SUPPORTED
    "height": 320,  # ❌ NOT SUPPORTED
    "fps": effective_fps,  # ❌ NOT SUPPORTED
}

# BUT we DO add first_frame_image when character images are provided:
if image_urls:
    input_params["first_frame_image"] = image_urls[0]  # ✅ THIS IS CORRECT!
```

**Key Points:**
- ✅ We ARE using `first_frame_image` for character consistency (line 324 in `video_generation.py`)
- ❌ But we're also passing invalid parameters (`num_frames`, `width`, `height`, `fps`)
- ❌ We're not using the correct API parameters (`duration`, `resolution`, `prompt_optimizer`)
- ⚠️ Character images might not be 9:16, so we're not getting 9:16 output even when using `first_frame_image`

### Actual API Parameters (CORRECT):
```python
input_params = {
    "prompt": "Text prompt for generation",
    "duration": 6,  # or 10 (seconds) - 10s only for 768p
    "resolution": "768p",  # or "1080p" - 1080p only supports 6s duration
    "prompt_optimizer": True,  # boolean
    "first_frame_image": "url_or_base64",  # Optional - output follows image aspect ratio
}
```

---

## Actual API Schema (from Replicate)

**Model:** `minimax/hailuo-2.3`  
**Latest Version:** `23a02633b5a44780345a59d4d43f8bd510efa239c56f08f29639ff24fa6615e1`  
**Created:** 2025-11-07

### Input Parameters:

1. **`prompt`** (string)
   - Text prompt for generation

2. **`duration`** (number)
   - Duration of the video in seconds
   - **Default:** 6
   - **Options:** 6 or 10 seconds
   - **Note:** 10 seconds is only available for 768p resolution

3. **`resolution`** (string)
   - Pick between 768p or 1080p resolution
   - **Default:** "768p"
   - **Options:** "768p" or "1080p"
   - **Note:** 1080p supports only 6-second duration

4. **`prompt_optimizer`** (boolean)
   - Use prompt optimizer
   - **Default:** True

5. **`first_frame_image`** (string)
   - First frame image for video generation
   - **Key Feature:** The output video will have the same aspect ratio as this image
   - **Format:** URL or Base64-encoded image
   - **Requirements:**
     - Format: JPG, JPEG, PNG, or WebP
     - Size: Less than 20MB
     - Dimensions: Shortest side greater than 300 pixels
     - Aspect ratio: Between 2:5 and 5:2 (supports 9:16!)

---

## Solution for 9:16 Vertical Videos

### Method 1: Use `first_frame_image` with 9:16 Image ⭐ RECOMMENDED

**How it works:**
- Provide a `first_frame_image` with 9:16 aspect ratio
- The generated video will automatically match that aspect ratio
- No post-processing cropping needed!

**Implementation:**
```python
# Generate or use a 9:16 placeholder image
# For example: 1080x1920 pixels (9:16 aspect ratio)
first_frame_9_16 = create_9_16_placeholder_image()  # or use existing character image

input_params = {
    "prompt": optimized_prompt,
    "duration": 6,  # or 10 for 768p
    "resolution": "1080p",  # or "768p"
    "prompt_optimizer": True,
    "first_frame_image": first_frame_9_16,  # 9:16 image = 9:16 output!
}
```

**Benefits:**
- ✅ Native 9:16 generation (no cropping needed)
- ✅ Better quality (no information loss from cropping)
- ✅ Works with character consistency (already using first_frame_image)
- ✅ Supports both text-to-video and image-to-video workflows

**Considerations:**
- If using character consistency, the character image might not be 9:16
- Solution: Resize/crop character image to 9:16 before using as first_frame_image
- Or: Generate a 9:16 placeholder and composite character into it

---

### Method 2: Post-Process 16:9 to 9:16 (Current Approach)

**How it works:**
- Generate video in default 16:9 (or whatever the API gives)
- Crop/transform to 9:16 using FFmpeg

**Implementation:**
```python
# Generate video (will be 16:9 by default)
input_params = {
    "prompt": optimized_prompt,
    "duration": 6,
    "resolution": "1080p",
    "prompt_optimizer": True,
}

# Then crop to 9:16 using FFmpeg
ffmpeg -i input_16_9.mp4 -vf "crop=1080:1920:(iw-1080)/2:(ih-1920)/2" output_9_16.mp4
```

**Drawbacks:**
- ❌ Loses information (crops sides of 16:9 video)
- ❌ May crop out important content (character, action)
- ❌ Requires post-processing step
- ❌ Lower quality (cropped vs. native generation)

---

## Aspect Ratio Support

### Text-to-Video (No first_frame_image):
- **Default:** 16:9 aspect ratio
- **Resolution options:**
  - 768p: 1366x768 (16:9) or can be 10 seconds
  - 1080p: 1920x1080 (16:9) or 6 seconds max

### Image-to-Video (With first_frame_image):
- **Output:** Matches the aspect ratio of `first_frame_image`
- **Supported aspect ratios:** Between 2:5 and 5:2
  - ✅ 9:16 (vertical) = 0.5625 (within 2:5 = 0.4 to 5:2 = 2.5)
  - ✅ 16:9 (horizontal) = 1.777 (within range)
  - ✅ 1:1 (square) = 1.0 (within range)
  - ✅ 4:3 (traditional) = 1.333 (within range)

**Key Insight:** We can generate 9:16 videos natively by providing a 9:16 `first_frame_image`!

---

## Current Code Issues

### Problem 1: Using Non-Existent Parameters (BUT we DO use first_frame_image!)

**File:** `backend/app/services/video_generation.py`

**Current code (lines 306-332):**
```python
input_params = {
    "prompt": optimized_prompt,
    "num_frames": max(1, min(frame_count, 120)),  # ❌ Doesn't exist in API
    "width": 576,  # ❌ Doesn't exist in API
    "height": 320,  # ❌ Doesn't exist in API
    "fps": effective_fps,  # ❌ Doesn't exist in API
}

# BUT we DO add first_frame_image when character images are provided:
if image_urls:
    input_params["first_frame_image"] = image_urls[0]  # ✅ THIS IS CORRECT!
```

**Key Points:**
- ✅ **We ARE using `first_frame_image`** for character consistency (line 324)
- ✅ **We ARE using `first_frame_image`** in `_generate_image_to_video` (line 89)
- ❌ But we're also passing invalid parameters (`num_frames`, `width`, `height`, `fps`)
- ❌ We're not using the correct API parameters (`duration`, `resolution`, `prompt_optimizer`)
- ⚠️ **Character images are likely square (1024x1024) or user-uploaded (unknown ratio)**, so even when using `first_frame_image`, we're not getting 9:16 output

**Why this might still work:**
- Replicate API might be ignoring unknown parameters
- Or the API is accepting them but not using them (defaulting to duration/resolution)
- This could explain why videos are coming out at unexpected durations (5 seconds instead of 3 seconds)
- The `first_frame_image` parameter IS working, but the output aspect ratio matches the image (not 9:16)

### Problem 2: Duration Mismatch

**Issue:** Videos are generated at 5 seconds instead of requested 3 seconds

**Root Cause:** 
- Code requests `num_frames=24` for 3 seconds at 8fps
- But API doesn't support `num_frames` parameter
- API uses `duration` parameter (6 or 10 seconds only)
- API is probably defaulting to 6 seconds, then getting trimmed to 5 seconds somehow

**Solution:** Use `duration` parameter correctly:
```python
# For 3-second clips, we can't do it directly (API only supports 6 or 10s)
# Options:
# 1. Generate 6s video, trim to 3s (current approach)
# 2. Generate 6s video, use only first 3s (wasteful but works)
# 3. Accept 6s clips and plan composition accordingly
```

---

## Recommended Implementation Plan

### Phase 1: Fix API Parameters (CRITICAL)

1. **Update `video_generation.py` to use correct parameters:**
   ```python
   input_params = {
       "prompt": optimized_prompt,
       "duration": 6,  # Use actual API parameter
       "resolution": "1080p",  # or "768p"
       "prompt_optimizer": True,
   }
   ```

2. **Remove invalid parameters:**
   - Remove `num_frames`, `width`, `height`, `fps`
   - These don't exist in the API

3. **Handle duration:**
   - API only supports 6 or 10 seconds
   - For shorter clips, generate 6s and trim to desired length
   - Update clip planning to account for 6s minimum

### Phase 2: Add 9:16 Support

1. **Create 9:16 placeholder image generator:**
   - Generate a 9:16 image (1080x1920) for vertical videos
   - Can be solid color, gradient, or composited with character

2. **Add aspect ratio option to video generation:**
   - Add `aspect_ratio` parameter to `generate_section_video()`
   - When `aspect_ratio="9:16"`, use `first_frame_image` with 9:16 image
   - When `aspect_ratio="16:9"`, don't use `first_frame_image` (or use 16:9 image)

3. **Update composition to handle both aspect ratios:**
   - Support both 16:9 and 9:16 videos in composition
   - Don't normalize aspect ratio if already correct

### Phase 3: Character Consistency with 9:16

1. **Resize character images to 9:16:**
   - When aspect_ratio="9:16" and character_image provided
   - Resize/crop character image to 9:16
   - Use as `first_frame_image`

2. **Or composite character into 9:16 canvas:**
   - Create 9:16 background
   - Place character image in center
   - Use composite as `first_frame_image`

---

## Testing Plan

1. **Test current API behavior:**
   - Verify that current code works despite wrong parameters
   - Check if API ignores unknown parameters
   - Document actual output resolution/duration

2. **Test 9:16 generation:**
   - Create 9:16 placeholder image
   - Generate video with `first_frame_image` set to 9:16 image
   - Verify output is 9:16 aspect ratio

3. **Test character consistency with 9:16:**
   - Resize character image to 9:16
   - Generate video with character + 9:16 aspect ratio
   - Verify character appears correctly in vertical format

---

## Code Changes Needed

### File: `backend/app/services/video_generation.py`

**Current issues:**
- Lines 306-312: Using non-existent parameters
- Need to switch to `duration` and `resolution` parameters
- Need to handle aspect ratio via `first_frame_image`

**Changes:**
1. Replace `num_frames`, `width`, `height`, `fps` with `duration`, `resolution`
2. Add aspect ratio support via `first_frame_image`
3. Update duration handling (6s minimum, trim if needed)

### File: `backend/app/services/video_composition.py`

**May need updates:**
- Handle different aspect ratios in normalization
- Don't force 16:9 if video is already 9:16

---

## Questions to Resolve

1. **Why does current code work if parameters don't exist?**
   - Is Replicate ignoring unknown parameters?
   - Or is there a different API version being used?

2. **What's the actual output resolution?**
   - Current code requests 576x320
   - But API uses `resolution` parameter (768p or 1080p)
   - What resolution are we actually getting?

3. **How to handle variable clip durations?**
   - API only supports 6 or 10 seconds
   - But we need 3-second clips
   - Should we generate 6s and trim, or change clip planning?

4. **Character image aspect ratio:**
   - Character images might be square or other ratios
   - How to handle when user wants 9:16 output?
   - Resize? Crop? Composite?

---

## Next Steps

1. ✅ **Research complete** - Found API parameter mismatch
2. ⏳ **Fix API parameters** - Update code to use correct parameters
3. ⏳ **Test 9:16 generation** - Verify we can generate vertical videos
4. ⏳ **Update composition** - Support both aspect ratios
5. ⏳ **Add UI option** - Let users choose 16:9 or 9:16

---

## References

- Replicate Model: https://replicate.com/minimax/hailuo-2.3
- API Schema: Retrieved via `check_replicate_models.py` script
- Web Research: Minimax aspect ratio capabilities

---

**Last Updated:** Current session  
**Status:** Research complete - Ready for implementation

