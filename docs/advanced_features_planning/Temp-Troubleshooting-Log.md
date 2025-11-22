# Troubleshooting Log

## Debug Overlays for UI Testing

**Note:** Debug overlays are available but commented out for character consistency UI testing:
- **UploadPage.tsx** (line ~1116): Blue debug box showing `character_consistency_enabled`, `character_reference_image_s3_key`, and `character_pose_b_s3_key` from `songDetails`
- **SelectedTemplateDisplay.tsx** (line ~77): Yellow debug box showing pose URL fetch status, loading state, and URL availability

To enable for testing, uncomment the debug overlay sections in both files. These can be modified as needed for further UI debugging.

---

## Critical Issue: Character Consistency Not Working

**Problem:** 
- (a) Most clips do not show a dancing figure/character
- (b) When a character does appear, it's not based on the provided reference image

**Historical Context:**
Prior to all refactors and adding the character consistency option, we actually did get a dancing character almost all the time. This suggests that the character consistency feature implementation may have broken or changed the prompt generation logic in a way that prevents characters from appearing.

**Status:** Needs investigation - will examine prompts in a new chat session.

**Related Files:**
- `backend/app/services/scene_planner.py` - Prompt generation
- `backend/app/services/video_generation.py` - Video generation with character images
- `backend/app/services/clip_generation.py` - Clip generation flow

**See also:** [Prompt Building Flow](./Prompt-Building-Flow.md) for detailed documentation on how prompts are constructed.

---

## Image Parameter Verification

### Code Flow Analysis

**Image Retrieval (`clip_generation.py`):**
1. `_get_character_image_urls()` checks `song.character_consistency_enabled` (line 457)
2. If enabled, generates presigned S3 URLs for character images
3. Returns `(character_image_urls, character_image_url)` tuple

**Image Passing (`clip_generation.py` → `video_generation.py`):**
1. Images passed to `generate_section_video()` as:
   - `reference_image_url` (single, fallback)
   - `reference_image_urls` (list, prioritized)

**Image-to-Video Path (`video_generation.py`):**

**Path 1: Single Image (lines 232-242)**
- If single image exists, calls `_generate_image_to_video()`
- In `_generate_image_to_video()` (line 69): `input_params["image"] = reference_image_url`
- ✅ **Image IS added to input_params**

**Path 2: Multiple Images or Fallback (lines 272-296)**
- If multiple images or fallback path: `input_params["image"] = image_urls[0]` (line 295)
- ✅ **Image IS added to input_params**

**API Call (line 317-320):**
```python
prediction = client.predictions.create(
    version=version,
    input=input_params,  # Contains "image" key if images provided
)
```

### Potential Issues Found

1. **Parameter Name Verification Needed:**
   - Code uses `"image"` (singular) parameter
   - Need to verify if Minimax Hailuo 2.3 expects `"image"`, `"images"`, `"reference_image"`, or another name
   - Documentation/testing needed to confirm correct parameter name

2. **Exception Handling Bug (lines 243-246):**
   - If `_generate_image_to_video()` throws exception, `is_image_to_video` is set to `False`
   - Code continues and may add image to `input_params` at line 295
   - But `generation_type` will be "text-to-video" even though image is in params
   - This could cause confusion in logging but shouldn't prevent image from being sent

3. **URL Validation:**
   - Presigned URLs might expire or be invalid
   - URLs might be empty strings that pass validation but fail at API
   - Need to verify URLs are actually accessible before passing to API

4. **Model Support:**
   - Code assumes `minimax/hailuo-2.3` supports image input
   - May need to verify model version actually supports image-to-video
   - Different model versions may have different parameter names

### Verification Steps Needed

1. **Check actual API calls in logs:**
   - Look for `[VIDEO-GEN] Calling Replicate API` log entries
   - Verify `has_image={'image' in input_params or 'images' in input_params}` shows `True`
   - Check if `input_params` actually contains image URL when logged

2. **Verify parameter name:**
   - Check Replicate API documentation for `minimax/hailuo-2.3`
   - Test with actual API call to confirm parameter name
   - May need to check model version schema: `client.models.get("minimax/hailuo-2.3").latest_version.get_openapi_schema()`

3. **Check URL accessibility:**
   - Verify presigned URLs are valid and accessible
   - Check if URLs expire before API call
   - Verify S3 bucket permissions allow Replicate to access images

4. **Add debug logging:**
   - Log the actual `input_params` dict before API call (redact sensitive data)
   - Log whether image URL is in the params
   - Log the full API response/error messages
