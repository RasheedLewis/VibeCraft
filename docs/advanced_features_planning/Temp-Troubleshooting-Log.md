# Troubleshooting Log

## Current Testing Status

**Ready for Testing:**
- Video type selection modal overlay flow has been fixed and is ready for testing
- All known issues have been addressed:
  1. ✅ Modal visibility state management fixed
  2. ✅ Modal appears only after upload (not immediately)
  3. ✅ Analysis starts automatically after video type selection
  4. ✅ Modal stays visible for 1 second after selection
  5. ✅ Job polling starts properly without 404 errors
  6. ✅ Debug code removed
  7. ✅ Redundant UI elements removed

**Next: Test the complete flow:**
  1. Upload audio file
  2. Verify modal overlay appears and blocks interaction
  3. Select "30-Second Video" or "Full-Length Video"
  4. Verify modal stays visible for ~1 second
  5. Verify analysis starts automatically (check for job polling)
  6. Verify no 404 errors in console
  7. Verify `videoType` is correctly set and persisted
  8. Verify analysis completes and UI progresses to next step

## Fixes Applied So Far

### 1. 409 Conflict Error on Video Type Selection
**Problem:** User got 409 error immediately after clicking "30-Second Video" option.

**Root Cause:** Analysis already existed for the song, and backend prevents changing video type after analysis completes.

**Fixes:**
- Updated `UploadPage.tsx` to conditionally render `VideoTypeSelector` only when:
  - `!analysisPolling.data` (no analysis exists)
  - `analysisState === 'idle'` (analysis not running)
- Enhanced error handling in `useVideoTypeSelection.ts` to provide user-friendly 409 error messages
- Added backend unit tests for `ensure_no_analysis` function in `test_api_utils.py`

### 2. Analysis Starting Automatically Without Video Type Selection
**Problem:** Analysis was starting immediately after file upload, before user could select video type.

**Root Cause:** `analysisPolling.startAnalysis()` was being called directly in `handleFileUpload` in `UploadPage.tsx`.

**Fix:**
- Removed automatic `analysisPolling.startAnalysis()` call from `handleFileUpload`
- Analysis now only starts after video type is selected via `useVideoTypeSelection` hook

### 3. Frontend Blank Page After Analysis Completed
**Problem:** Frontend showed blank page after analysis completed, with debug showing `videoType=null` even though analysis existed.

**Root Cause:** `videoType` state wasn't being properly synced from `songDetails.video_type` after analysis completed.

**Fixes:**
- Modified `UploadPage.tsx` to always call `fetchSongDetails` after analysis completes
- Updated `useVideoTypeSelection.ts` to consistently sync `videoType` from `songDetails.video_type` when available
- Changed `useEffect` dependency array from `[songDetails?.video_type]` to `[songDetails]` to prevent React hook warnings

### 4. 404 Error When Selecting Video Type
**Problem:** User got 404 error immediately after selecting video type.

**Root Cause:** `onAnalysisTriggered` callback was calling `fetchAnalysis()` immediately after starting analysis, but analysis result wasn't ready yet (returns 404).

**Fixes:**
- Modified `useVideoTypeSelection.ts` to capture `jobId` from analyze endpoint response
- Updated `useAnalysisPolling.ts` to expose `setJobId` method for external jobId setting
- Changed `onAnalysisTriggered` callback to accept `jobId` parameter and set it in polling hook
- This allows job polling to start automatically without trying to fetch analysis immediately

### 5. Video Type Selector Not Prominent Enough
**Problem:** User couldn't easily see the "Choose Your Video Format" section - it appeared too low on the page.

**Fix:**
- Converted `VideoTypeSelector` to a modal overlay that:
  - Blocks entire screen with dark backdrop (`bg-black/80 backdrop-blur-sm`)
  - Centers selector in modal card
  - Uses high z-index (`z-50`) to appear above all content
  - Is un-exitable (no close button) - user must select video type to proceed

### 6. Modal Disappearing Too Quickly
**Problem:** Modal overlay disappeared immediately after video type selection, making it hard to see the selection was registered.

**Fix:**
- Added `videoTypeModalVisible` state to control modal visibility
- Added `useEffect` that keeps modal visible for 1 second after `videoType` is set
- Modal only hides after the 1-second delay

### 7. React Hook Lint Warning - Synchronous setState in Effect
**Problem:** ESLint error: "Calling setState synchronously within an effect can trigger cascading renders"

**Location:** `UploadPage.tsx` line 105 - `setVideoTypeModalVisible(true)` called directly in `useEffect`

**Fix Applied:**
- Wrapped `setVideoTypeModalVisible(true)` in `setTimeout(..., 0)` to defer the state update
- This avoids synchronous setState in effect, satisfying the linter

**⚠️ Potential Issue:** Wrapping setState in setTimeout(0) is a workaround that may have timing implications. The effect now has:
```typescript
if (!videoType) {
  const timer = setTimeout(() => {
    setVideoTypeModalVisible(true)
  }, 0)
  return () => clearTimeout(timer)
}
```

**Note:** This might cause the modal to appear slightly delayed, or there may be edge cases where the visibility state doesn't sync properly with `videoType` changes. Consider if this is the right approach or if we should derive `videoTypeModalVisible` from `videoType` directly instead of managing it as separate state.

### 8. Modal Visibility State Management Issues
**Problem:** 
- `videoTypeModalVisible` was initialized to `true`, causing modal to show immediately even when no file was uploaded
- Modal visibility logic was convoluted and didn't properly handle all edge cases
- Debug div was left in production code
- Redundant "Start Analysis" button section existed (analysis should start automatically)

**Fixes:**
- Changed `videoTypeModalVisible` initial state from `true` to `false`
- Improved `useEffect` logic to properly show/hide modal based on:
  - `stage === 'uploaded'` (file has been uploaded)
  - `!videoType` (no video type selected yet)
  - `!analysisPolling.data` (no analysis exists)
  - `analysisState === 'idle'` (analysis not running)
- Modal now shows when file is uploaded and no video type is set
- Modal hides with 1-second delay after video type is selected
- Removed debug div from production code
- Removed redundant "Start Analysis" button section (analysis starts automatically via `useVideoTypeSelection` hook)
- Added `videoTypeModalVisible` reset to `resetState` function for clean state management

## Files Modified

- `frontend/src/pages/UploadPage.tsx` - Modal overlay, conditional rendering, state management
- `frontend/src/hooks/useVideoTypeSelection.ts` - Error handling, jobId passing
- `frontend/src/hooks/useAnalysisPolling.ts` - Added `setJobId` method
- `frontend/src/components/VideoTypeSelector.tsx` - (No changes, but used in modal)
- `backend/app/api/v1/utils.py` - `ensure_no_analysis` function (409 logic)
- `backend/tests/unit/test_api_utils.py` - Unit tests for 409 logic
- `backend/tests/test_video_type_api.py` - Integration tests for video type API

## Next Steps for Testing

1. Upload audio file
2. Verify modal overlay appears and blocks interaction
3. Select "30-Second Video" or "Full-Length Video"
4. Verify modal stays visible for ~1 second
5. Verify analysis starts automatically (check for job polling)
6. Verify no 404 errors in console
7. Verify `videoType` is correctly set and persisted
8. Verify analysis completes and UI progresses to next step

