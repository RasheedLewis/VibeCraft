# Video Playback and Clip Duration Fixes

## Date: Recent Session

## Issue 1: Video Playback Duration Handling

### Problem
When previewing individual clips (not composed video), the video player would:
- Loop back to the beginning prematurely when playing individual clips
- Not correctly stop at the end of the current clip
- Use the total timeline duration instead of the individual clip's actual duration

### Root Cause
The `MainVideoPlayer` component was using the `durationSec` prop (total timeline duration) to determine when to stop playback, rather than the actual duration of the currently loaded video file or the active clip's duration.

### Solution
Introduced `effectiveDuration` calculation that prioritizes:
1. `actualVideoDuration` - The true duration of the currently loaded video file (from `onLoadedMetadata`)
2. `activePlayerClip?.durationSec` - The planned duration of the active clip (when previewing individual clips)
3. `durationSec` prop - Total timeline duration (fallback for composed videos)

### Code Changes
**File**: `frontend/src/components/MainVideoPlayer.tsx`

- Added `actualVideoDuration` state to capture the video element's true duration
- Modified `effectiveDuration` calculation to prioritize actual video duration
- Updated `handleTimeClamp` to use `effectiveDuration` for stopping playback
- Added `useEffect` to reset `actualVideoDuration` when `videoUrl` changes

### Key Implementation Details
- `actualVideoDuration` is updated via the video element's `onLoadedMetadata` event
- `effectiveDuration` ensures the player stops at the correct boundary for individual clips
- When `usingExternalAudio` is true, we still use the timeline duration (for composed videos)

---

## Issue 2: Video Generation API Producing Clips Too Long

### Problem
- Clips were planned for 3.0 seconds (24 frames at 8fps)
- Database correctly stored `duration_sec=3.0` and `num_frames=24`
- But the Minimax Hailuo 2.3 API was generating 5-second videos instead of 3 seconds
- This caused composition issues:
  - 3 clips × 5 seconds = 15 seconds total
  - But selected audio was only 9 seconds
  - Composition would trim the video to 9 seconds, cutting off the last 6 seconds
  - Users only saw the first ~6 seconds of content instead of the full 9 seconds

### Root Cause
The Minimax Hailuo 2.3 API appears to have a minimum duration constraint or is ignoring the `num_frames` parameter in some cases, generating 5-second videos regardless of the requested frame count.

### Solution
Added automatic trimming during clip normalization:
- Modified `normalize_clip()` to accept optional `target_duration_sec` parameter
- Before normalization, check actual video duration using `ffprobe`
- If video is longer than expected (by more than 100ms), trim it using FFmpeg's `trim` filter
- Trim happens before scaling/FPS conversion to ensure accurate duration

### Code Changes

**File**: `backend/app/services/video_composition.py`
- Added `target_duration_sec` parameter to `normalize_clip()`
- Added duration checking logic using `ffprobe`
- Added trim filter: `trim=duration={target_duration_sec},setpts=PTS-STARTPTS`
- Trim filter is applied before scale/pad/fps filters

**File**: `backend/app/services/clip_generation.py`
- Updated `normalize_single_clip()` to pass `clip.duration_sec` to `normalize_clip()`
- Created `clip_duration_map` to look up expected durations

**File**: `backend/app/services/composition_execution.py`
- Updated `normalize_single_clip()` to pass expected duration from `clips` list
- Added `Optional` import

**File**: `backend/app/services/clip_generation.py` (logging)
- Added logging to verify actual vs expected duration after video generation
- Added logging to show what values are sent to the video generation API

### Key Implementation Details
- Trim filter: `trim=duration={target_duration_sec},setpts=PTS-STARTPTS`
  - `trim=duration=X` trims to exact duration
  - `setpts=PTS-STARTPTS` resets timestamps so trimmed video starts at 0
- Duration check uses 0.1 second tolerance (100ms) to avoid unnecessary trimming for minor differences
- Trimming happens during normalization, before composition, ensuring all clips are the correct length

### Future Considerations
- Investigate why Minimax Hailuo 2.3 API generates 5-second videos despite `num_frames=24`
- May need to check API documentation for minimum duration constraints
- Consider alternative video generation APIs if this behavior is consistent
- The logging added will help diagnose if this is a consistent issue or intermittent

---

## Testing Notes

### Video Playback Fix
- Test individual clip preview: should play full clip and stop at end, not loop
- Test clip navigation: forward/backward should correctly jump to clip boundaries
- Test composed video: should still work correctly with timeline duration

### Clip Duration Fix
- Generate new clips and verify they are trimmed to correct duration during normalization
- Check backend logs for "Trimming clip from X.XXs to Y.YYs" messages
- Verify composition shows full content without cutting off
- Check that `actualVideoDuration` matches expected clip duration in frontend

---

## Related Files

### Frontend
- `frontend/src/components/MainVideoPlayer.tsx` - Video player component with duration handling

### Backend
- `backend/app/services/video_composition.py` - Clip normalization and trimming
- `backend/app/services/clip_generation.py` - Clip generation and normalization calls
- `backend/app/services/composition_execution.py` - Composition pipeline with normalization
- `backend/app/services/video_generation.py` - Video generation API calls (logging added)

