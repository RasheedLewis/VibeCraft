# Troubleshooting Log

## Debug Overlays for UI Testing

**Note:** Debug overlays are available but commented out for character consistency UI testing:
- **UploadPage.tsx** (line ~1116): Blue debug box showing `character_consistency_enabled`, `character_reference_image_s3_key`, and `character_pose_b_s3_key` from `songDetails`
- **SelectedTemplateDisplay.tsx** (line ~77): Yellow debug box showing pose URL fetch status, loading state, and URL availability

To enable for testing, uncomment the debug overlay sections in both files. These can be modified as needed for further UI debugging.

---

## Current Testing Status - Gentle Testing Guide

**Testing Guide Summary:**
The gentle testing guide outlines 7 steps for testing the video app:
1. **Upload Audio** (2 min) - Upload file, wait for completion
2. **Choose Video Type** (1 min) - Select "Short Form" or "Full Length"
3. **Start Analysis** (3-5 min) - Analysis runs automatically (full-length) or after audio selection (short-form)
4. **Select 30 Seconds of Audio** (3 min) - Drag markers to select segment (short-form only, happens BEFORE analysis)
5. **Choose a Character** (3-5 min) - Upload character image or select template
6. **Generate Video Clips** (5-10 min) - Generate 6 video clips
7. **Compose Final Video** (3-5 min) - Compose final video from clips

**Current Step: Step 3 - Analysis in Progress** ✅
- ✅ Step 1: Audio uploaded successfully
- ✅ Step 2: Video type selected (30-second/Short Form)
- ✅ Step 4 (done early): 30-second audio segment selected and confirmed
- 🔄 Step 3: Analysis started and currently running (3-5 minutes)
- ⏭️ Next: Step 5 - Choose a Character (after analysis completes)

**Note:** For short-form videos, the flow has been updated so audio selection (Step 4) happens BEFORE analysis (Step 3), allowing analysis to work on the pre-selected segment.

## Sequence Flow: Current vs Desired

### Current Sequence (Before Fix)

**For Full-Length Videos:**
1. Upload audio file
2. Select video type ("Full Length")
3. Analysis starts automatically
4. Analysis completes (3-5 minutes)
5. Character selection (optional)
6. Generate clips

**For Short-Form Videos (30-Second):**
1. Upload audio file
2. Select video type ("30-Second Video")
3. Analysis starts automatically ❌ (should wait for audio selection)
4. Analysis completes (3-5 minutes)
5. Audio selection UI appears (requires `analysisData.beatTimes` from analysis)
6. User selects 30 seconds
7. Character selection
8. Generate clips

**Problem:** Audio selection UI requires analysis to complete first (needs `beatTimes`), but user should select audio BEFORE analysis runs so analysis can work on the selected segment.

### Desired Sequence (After Fix)

**For Full-Length Videos:**
1. Upload audio file
2. Select video type ("Full Length")
3. Analysis starts automatically
4. Analysis completes (3-5 minutes)
5. Character selection (optional)
6. Generate clips

**For Short-Form Videos (30-Second):**
1. Upload audio file
2. Select video type ("30-Second Video")
3. Audio selection UI appears immediately (uses `metadata.durationSeconds` from upload)
4. User selects 30 seconds
5. Analysis starts automatically after selection is saved
6. Analysis completes (3-5 minutes)
7. Character selection
8. Generate clips

**Key Changes:**
- Audio selection happens BEFORE analysis (not after)
- Audio selection UI uses duration from file upload metadata (no analysis required)
- Analysis only starts after user has selected their 30-second segment
- `beatTimes` are optional in `AudioSelectionTimeline` (can work without them)

### Implementation Status

✅ **Completed:**
- Modified `useVideoTypeSelection` to NOT auto-start analysis for `short_form` videos
- Added audio selection UI that appears before analysis (uses `metadata.durationSeconds`)
- Made `beatTimes` optional in `AudioSelectionTimeline` component
- Added "Confirm & Start Analysis" button inside AudioSelectionTimeline component
- Analysis now triggers after user confirms their selection
- Fixed button disappearing issue by removing premature reset logic
- Moved button inside timeline component for better UX
- Made button smaller (md size) for better visual balance
- Fixed all TypeScript and lint errors
- ✅ **All issues resolved and tested successfully**

## Previous Testing Status (All Issues Resolved ✅)

**All Known Issues Fixed:**
  1. ✅ Modal visibility state management fixed
  2. ✅ Modal appears only after upload (not immediately)
  3. ✅ Analysis starts automatically after video type selection (full-length) or after audio selection confirmation (short-form)
  4. ✅ Modal stays visible for 1 second after selection
  5. ✅ Job polling starts properly without 404 errors
  6. ✅ Debug code removed
  7. ✅ Redundant UI elements removed
  8. ✅ Audio selection UI appears before analysis for short-form videos
  9. ✅ Button moved inside timeline component
  10. ✅ Button no longer disappears immediately
  11. ✅ Template character images render correctly

**Status:** All issues from previous testing sessions have been resolved. The flow is now working as designed.

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

## Testing Progress

**Completed Steps:**
- ✅ Upload audio file
- ✅ ✅ Modal overlay appears and blocks interaction
- ✅ Select "30-Second Video" or "Full-Length Video"
- ✅ Modal stays visible for ~1 second
- ✅ Audio selection UI appears (for short-form)
- ✅ User can select 30-second segment
- ✅ "Confirm & Start Analysis" button works correctly
- ✅ Analysis starts after confirmation
- ✅ No 404 errors in console
- ✅ `videoType` is correctly set and persisted

**Current:** Analysis in progress (Step 3 of testing guide)

**Next:** After analysis completes, proceed to character selection (Step 5)

