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

1. **❌ CRITICAL: Wrong Parameter Name (CONFIRMED):**
   - Code uses `"image"` (singular) parameter
   - **Actual API parameter name is `"first_frame_image"`** (verified via `check_replicate_models.py`)
   - This explains why character images are not being used - they're being passed with the wrong parameter name
   - **Fix needed:** Change `input_params["image"]` to `input_params["first_frame_image"]` in:
     - `video_generation.py::_generate_image_to_video()` (line 69)
     - `video_generation.py::generate_section_video()` (line 295)

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

2. **✅ Verify parameter name: COMPLETED**
   - Verified via `scripts/check_replicate_models.py` and direct API schema inspection
   - **Confirmed:** Parameter name is `"first_frame_image"` (not `"image"`)
   - All input parameters for `minimax/hailuo-2.3`:
     - `prompt` (required, string)
     - `duration` (unknown)
     - `resolution` (unknown)
     - `prompt_optimizer` (boolean)
     - `first_frame_image` (string) - "First frame image for video generation. The output video will have the same aspect ratio as this image."

3. **Check URL accessibility:**
   - Verify presigned URLs are valid and accessible
   - Check if URLs expire before API call
   - Verify S3 bucket permissions allow Replicate to access images

4. **Add debug logging:**
   - Log the actual `input_params` dict before API call (redact sensitive data)
   - Log whether image URL is in the params
   - Log the full API response/error messages

---

## Beat Synchronization: Expected Effects and Verification

### What You Should See in the Final Composed Video

According to the implementation plan, the following beat-sync features should be active:

1. **Beat-Aligned Clip Transitions (Phase 3.3):**
   - Clip boundaries should align to beats within ±50ms
   - Transitions between clips should occur on or very close to beat timestamps
   - **Visual Effect:** Cuts between clips should feel rhythmically correct, not random

2. **Beat-Synced Visual Effects (Phase 3.2):**
   - **Flash Effect:** Brightness pulses/flashes on beats (currently the only implemented effect)
   - **Effect Duration:** 50ms flash window (±50ms tolerance around each beat)
   - **Visual Effect:** Subtle brightness increase (RGB +30) when beats occur
   - **Note:** Only first 50 beats are processed (line 445 in `video_composition.py`)

### Current Implementation Status

**Beat Alignment (Clip Boundaries):**
- ✅ **Implemented:** `composition_execution.py` lines 198-273
- ✅ **Feature Flag:** `beat_aligned = True` (hardcoded, line 199)
- ✅ **Process:**
  1. Retrieves `beat_times` from song analysis (line 194)
  2. Calculates beat-aligned boundaries using `calculate_beat_aligned_clip_boundaries()` (line 210)
  3. Trims or extends clips to match beat boundaries (lines 219-269)
  4. Logs: `"Calculating beat-aligned clip boundaries"` and `"Completed beat-aligned clip adjustment"`

**Beat Filters (Visual Effects):**
- ✅ **Implemented:** `video_composition.py` lines 416-482
- ⚠️ **Only Flash Effect:** Currently only `filter_type="flash"` is implemented (line 336, 432)
- ⚠️ **Limited to 50 Beats:** Only processes first 50 beats (line 445: `beat_times[:50]`)
- ✅ **Process:**
  1. Beat times passed to `concatenate_clips()` (line 335)
  2. If `beat_times` exist, applies flash filter (line 417)
  3. Uses FFmpeg `geq` filter to increase RGB by 30 on beats (lines 457-462)
  4. 50ms tolerance window around each beat (line 439)
  5. Logs: `"Applying flash beat filters for {len(beat_times)} beats"` and `"Beat filters applied successfully"`

### How to Verify Beat Sync is Working

**1. Check Logs During Composition:**

Look for these log messages in the worker logs:
```
Found {N} beat times for beat alignment and filters
Calculating beat-aligned clip boundaries
Calculated {N} beat-aligned boundaries
Completed beat-aligned clip adjustment
Applying flash beat filters for {N} beats
Beat filters applied successfully
```

**2. Verify Beat Alignment:**

- **Expected:** Clip transitions should align to beats
- **Check:** Look at clip boundary timestamps vs beat times
- **Code Location:** `composition_execution.py` lines 210-217 logs boundary count
- **Verification:** Compare `boundary.start_time` and `boundary.end_time` to nearest beat times (should be within ±50ms)

**3. Verify Beat Filters:**

- **Expected:** Subtle brightness flashes on beats
- **Visual Check:** Watch final video - should see brief brightness increases synchronized to music beats
- **Code Location:** `video_composition.py` line 420 logs filter application
- **Potential Issue:** If filter application fails, logs: `"Failed to apply beat filters, continuing without filters"` (line 481)
- **Note:** Effect is subtle (RGB +30) and may be hard to notice depending on video content

### Potential Issues

1. **Beat Filters May Not Be Visible:**
   - Effect is subtle (RGB +30 increase)
   - Only applies to first 50 beats (for 30-second videos, this should cover most/all beats)
   - If video is already very bright, effect may not be noticeable
   - **Fix:** Could increase intensity or add more visible effects (color_burst, zoom_pulse)

2. **Beat Alignment May Not Be Perfect:**
   - Clips are trimmed/extended, but if original clips are far from beat boundaries, adjustment may be noticeable
   - **Check:** Look for log messages about trimming/extending clips

3. **Beat Times May Be Missing:**
   - If `analysis.beat_times` is empty or None, no beat sync will occur
   - **Check:** Log message `"Found {N} beat times"` should show non-zero count

4. **Filter Application May Fail Silently:**
   - If FFmpeg filter fails, it logs a warning but continues without filters (line 481)
   - **Check:** Look for `"Failed to apply beat filters"` warnings in logs

### Code Locations

- **Beat Alignment: `backend/app/services/composition_execution.py` lines 191-273**
- **Beat Filters: `backend/app/services/video_composition.py` lines 416-482**
- **Beat Alignment Logic: `backend/app/services/beat_alignment.py`**
- **Beat Filter Generation: `backend/app/services/beat_filters.py`**

### Testing Recommendations

1. **Check composition logs** for beat sync messages
2. **Compare clip boundaries** to beat times (should align within ±50ms)
3. **Watch final video** for brightness flashes on beats (may be subtle)
4. **Verify beat_times** are present in song analysis (should be non-empty array)
5. **Check for filter errors** in logs (should not see "Failed to apply beat filters")

---

## Clip Generation Concurrency Issue

### Problem

Only 1 clip appears to be generating even though `DEFAULT_MAX_CONCURRENCY = 2` should allow 2 clips to run in parallel.

### Current Behavior

**Expected:** With `max_parallel=2`, 2 clips should run concurrently:
- Clip 0 (index 0): No dependency, runs immediately
- Clip 1 (index 1): No dependency, runs immediately
- Clip 2 (index 2): Depends on Clip 0, waits for Clip 0 to finish
- Clip 3 (index 3): Depends on Clip 1, waits for Clip 1 to finish

**Actual:** Only 1 clip appears to be generating at a time.

### Root Cause Analysis

**RQ Dependency System:**
- Jobs with dependencies are stored in RQ's "deferred" registry
- When a dependency finishes, RQ should automatically move the dependent job to the main queue
- However, there can be delays in RQ's dependency resolution

**Current Status Check:**
- Clip #1 (index 0): RQ job finished, but database may show "processing" (status mismatch)
- Clip #2 (index 1): Currently started/processing
- Clip #3 (index 2): Queued in main queue, dependency (Clip #1) is finished, but not starting

**Issue:** Clip #3's dependency is finished, but RQ hasn't moved it to "started" status yet. This suggests:
1. RQ dependency resolution may have a delay
2. Worker may need to poll for ready jobs
3. There may be a bug in RQ's dependency handling

### How to Verify

**Check RQ Job States:**
```python
from app.core.queue import get_queue
from rq.job import Job
from rq.registry import DeferredJobRegistry, StartedJobRegistry

queue = get_queue()
deferred = DeferredJobRegistry(queue=queue)
started = StartedJobRegistry(queue=queue)

print(f"Main queue: {len(queue)} jobs")
print(f"Deferred: {len(list(deferred.get_job_ids()))} jobs")
print(f"Started: {len(list(started.get_job_ids()))} jobs")
```

**Check Clip Statuses:**
- Look for clips with `status="queued"` but their dependency jobs are finished
- These should automatically move to "started" when the worker picks them up

### Potential Solutions

1. **Worker Polling:** RQ workers should automatically check for ready jobs when dependencies complete, but there may be a delay
2. **Manual Dependency Resolution:** Could manually move jobs from deferred to main queue when dependencies finish
3. **Reduce Dependency Chain:** Could use a different concurrency model that doesn't rely on RQ dependencies
4. **Check Worker Configuration:** Ensure worker is configured to process multiple jobs (though RQ typically handles this automatically)

### Code Locations

- **Concurrency Control:** `backend/app/services/clip_generation.py` line 94: `depends_on = jobs[idx - max_parallel] if idx >= max_parallel else None`
- **Default Concurrency:** `backend/app/core/constants.py` line 6: `DEFAULT_MAX_CONCURRENCY = 2`
- **Job Enqueueing:** `backend/app/services/clip_generation.py` lines 104-111

### Notes

- RQ's deferred job registry can accumulate jobs from previous runs (found 83 deferred jobs from old runs)
- Jobs with finished dependencies should automatically move to main queue, but there may be timing issues
- The worker should pick up ready jobs automatically, but there can be delays in dependency resolution
