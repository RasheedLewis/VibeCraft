# Manual Testing Guide - Advanced Features Branch

This guide provides **prescriptive, step-by-step instructions** for manually testing all new
features and user flows in the `advancedFeatures` branch. Each step includes exact actions,
expected results, verification methods, and checkpoints.

**Last Updated**: Based on branch state as of testing date

---

## Table of Contents

1. [Quick Smoke Test](#quick-smoke-test) ⚡
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Primary UX Features (High Priority)](#primary-ux-features-high-priority)
   - [Test 1: Video Type Selection](#test-1-video-type-selection)
   - [Test 2: 30-Second Audio Selection](#test-2-30-second-audio-selection)
   - [Test 3: Skip Sections for Short-Form](#test-3-skip-sections-for-short-form)
4. [Character Consistency Foundation (Quick Test)](#character-consistency-foundation-quick-test)
5. [Beat Sync Foundation (Quick Test)](#beat-sync-foundation-quick-test)
6. [End-to-End User Flows](#end-to-end-user-flows)
7. [Edge Cases & Error Handling](#edge-cases--error-handling)
8. [How to Report Issues & Request Fixes](#how-to-report-issues--request-fixes)

---

## Quick Smoke Test

**Purpose**: Quickly verify that all major features work end-to-end on the happy path.

**Estimated Time**: 10-15 minutes

**Prerequisites**: Backend and frontend running (see [Prerequisites & Setup](#prerequisites--setup))

---

### Smoke Test Flow

#### Step 1: Upload and Select Video Type (2 minutes)

1. **Navigate to upload page**: Open `http://localhost:5173`
2. **Upload audio file**: Drag and drop or select `medium_audio.mp3` (30-60 seconds)
3. **Verify upload completes**: Wait for upload to finish, no errors
4. **Select "Short Form"**: Click "Short Form" option
5. **Verify selection saves**: See loading indicator, then success

**✅ Pass Criteria**:
- [ ] Upload completes without errors
- [ ] Video type selector appears
- [ ] "Short Form" selection saves successfully

---

#### Step 2: Complete Analysis (3-5 minutes)

1. **Start analysis**: Click "Start Analysis" button (or wait for auto-start)
2. **Wait for completion**: Monitor progress indicator
3. **Verify analysis completes**: No errors, analysis data available

**✅ Pass Criteria**:
- [ ] Analysis starts successfully
- [ ] Analysis completes without errors
- [ ] Backend logs show: `⏭️ [ANALYSIS] Skipping section detection (short-form video)`

---

#### Step 3: Test Audio Selection (3-5 minutes)

1. **Verify timeline appears**: Audio selection timeline should be visible
2. **Check default selection**: Should default to last 30 seconds (if track > 30s)
3. **Drag start marker**: Click and drag start marker, verify it moves smoothly
4. **Drag end marker**: Click and drag end marker, verify it moves smoothly
5. **Test 30s constraint**: Try to create > 30s selection, verify it's constrained
6. **Test audio preview**: Click Play button, verify audio plays from start to end marker
7. **Save selection**: Click "Continue with Selection" button

**✅ Pass Criteria**:
- [ ] Timeline appears with waveform
- [ ] Markers are draggable
- [ ] 30-second maximum is enforced
- [ ] Audio preview works
- [ ] Selection saves successfully

---

#### Step 4: Quick Character Upload Test (2 minutes)

1. **Verify upload section appears**: Character upload section should be visible
2. **Upload test image**: Drag and drop or select a valid image (JPEG, PNG, WEBP)
3. **Verify upload succeeds**: Image uploads without errors

**✅ Pass Criteria**:
- [ ] Character upload section appears (for short-form only)
- [ ] Image uploads successfully
- [ ] No errors in console or network tab

---

#### Step 5: Verify Song Profile Appears (1 minute)

1. **Check song profile view**: Should appear after selection is saved
2. **Verify no sections**: Sections should not appear (or be minimal) for short-form
3. **Verify selection is used**: Check that selection data is present

**✅ Pass Criteria**:
- [ ] Song profile view loads
- [ ] No section-related errors
- [ ] Selection data is present (if visible in UI)

---

### Smoke Test Summary

**All Steps Pass**: ✅ System is working on happy path

**If Any Step Fails**:
- Note which step failed
- Check Console and Network tabs for errors
- See [How to Report Issues & Request Fixes](#how-to-report-issues--request-fixes) for detailed reporting
- Proceed to full test suite below for comprehensive testing

**Quick Verification Checklist**:
- [ ] Step 1: Upload and video type selection works
- [ ] Step 2: Analysis completes and skips sections
- [ ] Step 3: Audio selection timeline works with constraints
- [ ] Step 4: Character upload works (optional)
- [ ] Step 5: Song profile appears correctly

---

**Note**: This smoke test covers the happy path only. For comprehensive testing including edge
cases, error handling, and detailed verification, proceed to the full test suite below.

---

## Prerequisites & Setup

### Step 1: Environment Setup

**Action**: Start backend server
```bash
cd backend
source venv/bin/activate  # or your virtual environment
python -m uvicorn app.main:app --reload
```

**Verification**:
- [ ] Terminal shows: `Uvicorn running on http://127.0.0.1:8000`
- [ ] No error messages in terminal
- [ ] Can access `http://localhost:8000/docs` (FastAPI docs)

**Checkpoint**: ✅ Backend running

---

**Action**: Start frontend development server
```bash
cd frontend
npm run dev
```

**Verification**:
- [ ] Terminal shows: `Local: http://localhost:5173` (or similar)
- [ ] No error messages in terminal
- [ ] Browser can access frontend URL

**Checkpoint**: ✅ Frontend running

---

**Action**: Verify database migrations
```bash
cd backend
# Check if migrations directory exists and has migration files
ls -la migrations/
```

**Verification**:
- [ ] `migrations/003_add_video_type_field.py` exists
- [ ] `migrations/002_add_audio_selection_fields.py` exists
- [ ] `migrations/004_add_character_fields.py` exists

**Checkpoint**: ✅ Migrations present

---

### Step 2: Prepare Test Audio Files

**Action**: Create test audio files directory
```bash
mkdir -p test_audio_files
```

**Required Test Files**:
1. **short_audio.mp3** (< 30 seconds)
   - Purpose: Test full track selection for short audio
   - Duration: 15-25 seconds recommended

2. **medium_audio.mp3** (30-60 seconds)
   - Purpose: Test 30-second selection from medium track
   - Duration: 45-55 seconds recommended

3. **long_audio.mp3** (> 60 seconds)
   - Purpose: Test 30-second selection from long track
   - Duration: 2-3 minutes recommended

**Verification**:
- [ ] All three test files exist
- [ ] Files are valid audio format (MP3, WAV, etc.)
- [ ] Files are accessible

**Checkpoint**: ✅ Test files ready

---

### Step 3: Open Developer Tools

**Action**: Open browser developer tools
- **Chrome/Edge**: Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)
- **Firefox**: Press `F12` or `Cmd+Option+I` (Mac) / `Ctrl+Shift+I` (Windows)

**Action**: Open Network tab
- Click "Network" tab in developer tools
- Ensure "Preserve log" is checked (if available)

**Action**: Open Console tab
- Click "Console" tab
- Clear console (right-click → "Clear console" or `Cmd+K` / `Ctrl+L`)

**Verification**:
- [ ] Network tab visible and ready
- [ ] Console tab visible and clear
- [ ] No existing errors in console

**Checkpoint**: ✅ Developer tools ready

---

## Primary UX Features (High Priority)

### Test 1: Video Type Selection

**Goal**: Verify users can select between full-length and short-form video types before analysis.

**Estimated Time**: 10-15 minutes

---

#### Checkpoint 1.1: Navigate to Upload Page

**Action**: Open frontend in browser
- Navigate to `http://localhost:5173` (or your frontend URL)

**Expected Result**:
- Page loads without errors
- Upload interface is visible
- No console errors

**Verification**:
- [ ] Page loads successfully
- [ ] Upload area/dropzone is visible
- [ ] Console shows no errors (check Console tab)

**If Issue Found**: See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Upload page accessible

---

#### Checkpoint 1.2: Upload Audio File

**Action**: Upload test audio file
- Drag and drop `medium_audio.mp3` onto upload area, OR
- Click upload area and select `medium_audio.mp3` from file picker

**Expected Result**:
- File upload begins
- Progress indicator appears (if implemented)
- Upload completes successfully
- File is processed

**Verification Steps**:
1. **Visual Check**:
   - [ ] Upload progress indicator appears (spinner, progress bar, etc.)
   - [ ] Upload completes (progress reaches 100% or indicator disappears)
   - [ ] No error messages displayed on page

2. **Network Tab Check**:
   - [ ] Find `POST /api/v1/songs/` request in Network tab
   - [ ] Request status is `200` or `201`
   - [ ] Response contains `songId` or `id` field
   - [ ] Response contains `audioUrl` field

3. **Console Check**:
   - [ ] No error messages in Console tab
   - [ ] No warnings related to upload

**If Upload Fails**:
- Check Network tab for failed request
- Check Console for error messages
- Note exact error message
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Audio file uploaded

---

#### Checkpoint 1.3: Video Type Selector Appears

**Action**: Wait for upload to complete, then observe page

**Expected Result**:
- Video type selector component appears
- Two options visible:
  - "Full Length" button/card
  - "Short Form" button/card
- Clear labels and descriptions

**Verification Steps**:
1. **Visual Check**:
   - [ ] Video type selector is visible on page
   - [ ] "Full Length" option is visible and clickable
   - [ ] "Short Form" option is visible and clickable
   - [ ] Options are clearly labeled
   - [ ] No overlapping UI elements

2. **Component Check** (if familiar with React DevTools):
   - [ ] `VideoTypeSelector` component is rendered
   - [ ] Component receives correct props

3. **Timing Check**:
   - [ ] Selector appears **after** upload completes
   - [ ] Selector appears **before** analysis starts

**If Selector Doesn't Appear**:
- Check Console for errors
- Check Network tab for failed API calls
- Verify upload actually completed
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Video type selector visible

---

#### Checkpoint 1.4: Select "Short Form"

**Action**: Click "Short Form" option

**Expected Result**:
- Selection is visually indicated (highlighted, checked, etc.)
- Loading state appears ("Setting video type..." or similar)
- API call is made to save selection
- Selection saves successfully

**Verification Steps**:
1. **Visual Check**:
   - [ ] "Short Form" option shows selected state (highlighted, checked, etc.)
   - [ ] Loading indicator appears (spinner, "Setting..." text, etc.)
   - [ ] Loading indicator disappears after save completes
   - [ ] Success state shown (if implemented)

2. **Network Tab Check**:
   - [ ] Find `PATCH /api/v1/songs/{song_id}/video-type` request
   - [ ] Request payload contains: `{"video_type": "short_form"}`
   - [ ] Request status is `200`
   - [ ] Response contains updated song data with `video_type: "short_form"`

3. **Console Check**:
   - [ ] No error messages
   - [ ] No warnings

4. **State Check** (if familiar with React DevTools):
   - [ ] Component state updates to `videoType: "short_form"`
   - [ ] `isSetting` state shows loading then false

**If Selection Fails**:
- Check Network tab for failed request
- Note exact error status code and message
- Check Console for errors
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ "Short Form" selected and saved

---

#### Checkpoint 1.5: Select "Full Length"

**Action**: Click "Full Length" option (should be able to change before analysis)

**Expected Result**:
- Selection changes to "Full Length"
- Same loading/save behavior as above
- Selection saves successfully

**Verification Steps**:
1. **Visual Check**:
   - [ ] "Full Length" option shows selected state
   - [ ] "Short Form" option shows unselected state
   - [ ] Loading indicator appears and disappears

2. **Network Tab Check**:
   - [ ] Find `PATCH /api/v1/songs/{song_id}/video-type` request
   - [ ] Request payload contains: `{"video_type": "full_length"}`
   - [ ] Request status is `200`
   - [ ] Response contains `video_type: "full_length"`

**Checkpoint**: ✅ "Full Length" selected and saved

---

#### Checkpoint 1.6: Verify Video Type Persistence

**Action**: Refresh the page (press `F5` or `Cmd+R` / `Ctrl+R`)

**Expected Result**:
- Page reloads
- Upload state is restored (if implemented)
- Video type selection is remembered and displayed

**Verification Steps**:
1. **Visual Check**:
   - [ ] Page reloads successfully
   - [ ] Video type selector shows previously selected type
   - [ ] Correct option is highlighted/selected

2. **Network Tab Check**:
   - [ ] Find `GET /api/v1/songs/{song_id}` request (if song is fetched on load)
   - [ ] Response contains `video_type: "full_length"` (or "short_form" if that was last selected)

3. **State Check**:
   - [ ] Component state reflects saved video type

**If Persistence Fails**:
- Check if song ID is stored in URL or localStorage
- Check Network tab for GET request
- Verify backend returns correct `video_type`
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Video type persists across refresh

---

#### Test 1 Summary

**All Checkpoints Passed**: ✅
- [ ] Checkpoint 1.1: Upload page accessible
- [ ] Checkpoint 1.2: Audio file uploaded
- [ ] Checkpoint 1.3: Video type selector appears
- [ ] Checkpoint 1.4: "Short Form" selected
- [ ] Checkpoint 1.5: "Full Length" selected
- [ ] Checkpoint 1.6: Video type persists

**Known Behavior**:
- Video type **must** be selected before analysis can start
- Video type **cannot** be changed after analysis completes
- Short-form videos trigger different workflows (30s selection, character upload)

---

### Test 2: 30-Second Audio Selection

**Goal**: Verify users can select up to 30 seconds from their audio track for short-form videos.

**Estimated Time**: 20-30 minutes

**Prerequisites**: Complete Test 1 (Video Type Selection) with "Short Form" selected

---

#### Checkpoint 2.1: Start Analysis

**Action**: Click "Start Analysis" button (or wait for auto-start if implemented)

**Expected Result**:
- Analysis begins
- Progress indicator appears
- Analysis completes successfully
- Beat detection runs
- Sections are skipped (for short-form)

**Verification Steps**:
1. **Visual Check**:
   - [ ] Analysis progress indicator appears
   - [ ] Progress updates (if shown)
   - [ ] Analysis completes (indicator disappears or shows "Complete")

2. **Network Tab Check**:
   - [ ] Find `POST /api/v1/songs/{song_id}/analyze` request
   - [ ] Request status is `200` or `202`
   - [ ] Find polling requests (if implemented): `GET /api/v1/songs/{song_id}/analysis`
   - [ ] Final analysis response contains analysis data

3. **Backend Logs Check**:
   - [ ] Check backend terminal for log message:
     `⏭️ [ANALYSIS] Skipping section detection (short-form video)`
   - [ ] Analysis completes without errors

**If Analysis Fails**:
- Check Network tab for failed request
- Check backend logs for errors
- Note exact error message
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Analysis completed

---

#### Checkpoint 2.2: Audio Selection Timeline Appears

**Action**: Wait for analysis to complete, then observe page

**Expected Result**:
- Audio selection interface appears
- Timeline component is visible
- Waveform visualization is displayed
- Start and end markers are visible
- Play button is visible
- Time display shows selection duration

**Verification Steps**:
1. **Visual Check**:
   - [ ] Section titled "Select Audio Segment (Up to 30s)" is visible
   - [ ] Waveform visualization is displayed (bars/graph showing audio amplitude)
   - [ ] Start marker (left handle) is visible and positioned
   - [ ] End marker (right handle) is visible and positioned
   - [ ] Selected region is highlighted (different color/brightness)
   - [ ] Play button is visible
   - [ ] Time display shows current selection (e.g., "0:15 / 0:30")

2. **Component Check** (if familiar with React DevTools):
   - [ ] `AudioSelectionTimeline` component is rendered
   - [ ] Component receives `audioUrl`, `waveform`, `durationSec`, `beatTimes` props

3. **Timing Check**:
   - [ ] Timeline appears **after** analysis completes
   - [ ] Timeline appears **only** for short-form videos (not full-length)

**If Timeline Doesn't Appear**:
- Check Console for errors
- Verify analysis actually completed
- Verify video type is "short_form"
- Check Network tab for missing data (audioUrl, waveform, etc.)
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Audio selection timeline visible

---

#### Checkpoint 2.3: Verify Default Selection

**Action**: Observe default selection without making changes

**Expected Result**:
- Selection defaults to last 30 seconds of track (if track > 30s)
- OR defaults to full track (if track < 30s)
- Selection duration is displayed
- Markers are positioned correctly

**Verification Steps**:
1. **Visual Check**:
   - [ ] Start marker is positioned (should be at `duration - 30` if track > 30s)
   - [ ] End marker is positioned (should be at `duration` if track > 30s)
   - [ ] Selected region is highlighted
   - [ ] Time display shows selection duration (should be ≤ 30 seconds)

2. **Calculation Check**:
   - Note track duration (from time display or analysis data)
   - If track > 30s: Start marker should be at `duration - 30`
   - If track < 30s: Start marker should be at `0`, end marker at `duration`
   - Selection duration = end marker position - start marker position

3. **Data Check** (if familiar with browser DevTools):
   - [ ] Component state shows correct `startSec` and `endSec` values
   - [ ] Values match visual marker positions

**If Default Selection is Wrong**:
- Note actual start/end positions
- Note expected start/end positions
- Check Console for calculation errors
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Default selection correct

---

#### Checkpoint 2.4: Drag Start Marker

**Action**: Click and drag the **start marker** (left handle) to the right

**Expected Result**:
- Marker moves smoothly as you drag
- Selection duration updates in real-time
- Marker cannot be dragged past end marker
- Selection cannot exceed 30-second maximum
- Visual feedback shows constraint

**Verification Steps**:
1. **Interaction Check**:
   - [ ] Mouse cursor changes to `ew-resize` or similar when hovering over marker
   - [ ] Marker moves smoothly as you drag (no lag or jitter)
   - [ ] Marker position updates in real-time

2. **Constraint Check**:
   - [ ] Try dragging start marker past end marker → Should stop at end marker
   - [ ] Try dragging to create > 30s selection → Should stop at 30s from end
   - [ ] Selection duration never exceeds 30 seconds

3. **Visual Feedback Check**:
   - [ ] Time display updates in real-time as you drag
   - [ ] Selected region highlight updates as you drag
   - [ ] Waveform opacity/brightness updates (selected vs unselected)

4. **State Check** (if familiar with React DevTools):
   - [ ] Component `startSec` state updates as you drag
   - [ ] `onSelectionChange` callback is called with new values

**If Dragging Doesn't Work**:
- Check Console for JavaScript errors
- Verify marker element is clickable (check z-index, pointer-events)
- Check if event handlers are attached
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Start marker dragging works

---

#### Checkpoint 2.5: Drag End Marker

**Action**: Click and drag the **end marker** (right handle) to the left and right

**Expected Result**:
- Marker moves smoothly
- Selection duration updates
- Marker cannot be dragged before start marker
- Selection cannot exceed 30-second maximum
- Marker cannot exceed track duration

**Verification Steps**:
1. **Interaction Check**:
   - [ ] Marker moves smoothly as you drag
   - [ ] Marker position updates in real-time

2. **Constraint Check**:
   - [ ] Try dragging end marker before start marker → Should stop at start marker
   - [ ] Try dragging to create > 30s selection → Should stop at 30s from start
   - [ ] Try dragging past track end → Should stop at track duration
   - [ ] Selection duration never exceeds 30 seconds

3. **Visual Feedback Check**:
   - [ ] Time display updates in real-time
   - [ ] Selected region highlight updates

**Checkpoint**: ✅ End marker dragging works

---

#### Checkpoint 2.6: Test 30-Second Maximum Constraint

**Action**: Try to create a selection longer than 30 seconds

**Steps**:
1. Position start marker at beginning of track (or any position)
2. Try to drag end marker to create > 30 second selection
3. Observe constraint behavior

**Expected Result**:
- Selection is constrained to exactly 30 seconds maximum
- End marker stops at 30s from start marker
- Visual feedback shows constraint (if implemented)
- Time display shows "30.0s" or similar

**Verification Steps**:
1. **Constraint Check**:
   - [ ] End marker stops at exactly 30s from start marker
   - [ ] Cannot drag end marker further to increase selection
   - [ ] Selection duration shows exactly 30.0 seconds (or very close, e.g., 29.9-30.0)

2. **Visual Feedback Check**:
   - [ ] If constraint is hit, visual indicator appears (warning text, color change, etc.)
   - [ ] Time display shows maximum reached

3. **Edge Case Check**:
   - [ ] Test with start marker at different positions
   - [ ] Constraint works at all positions
   - [ ] Constraint works near track boundaries

**If Constraint Doesn't Work**:
- Note actual maximum selection achieved
- Check Console for validation errors
- Check component validation logic
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ 30-second maximum enforced

---

#### Checkpoint 2.7: Test Minimum Duration Constraint

**Action**: Try to drag markers very close together

**Steps**:
1. Drag start marker and end marker as close as possible
2. Observe minimum duration constraint

**Expected Result**:
- Selection has minimum duration of 1 second
- Markers cannot overlap
- End marker stops at 1s from start marker

**Verification Steps**:
1. **Constraint Check**:
   - [ ] End marker stops at exactly 1s from start marker
   - [ ] Cannot drag markers closer together
   - [ ] Selection duration shows minimum 1.0 seconds

2. **Visual Feedback Check**:
   - [ ] If minimum is hit, visual indicator appears (if implemented)

**Checkpoint**: ✅ Minimum duration (1s) enforced

---

#### Checkpoint 2.8: Test Audio Preview

**Action**: Click the **Play button**

**Expected Result**:
- Audio playback starts from start marker position
- Playhead indicator appears and moves across timeline
- Playback stops automatically at end marker
- Can pause/resume playback

**Verification Steps**:
1. **Playback Check**:
   - [ ] Click Play button → Audio starts playing
   - [ ] Audio starts from start marker position (not beginning of track)
   - [ ] Playhead indicator (vertical line) appears on timeline
   - [ ] Playhead moves smoothly from start to end marker

2. **Stop Behavior Check**:
   - [ ] Playback stops automatically when playhead reaches end marker
   - [ ] Playhead resets to start marker position after stopping
   - [ ] Play button changes to Play icon (from Pause icon)

3. **Pause/Resume Check**:
   - [ ] Click Play button while playing → Playback pauses
   - [ ] Play button changes to Play icon
   - [ ] Click Play button while paused → Playback resumes from current position
   - [ ] Playhead continues from where it paused

4. **Audio Quality Check**:
   - [ ] Audio plays clearly (no distortion, no skipping)
   - [ ] Playhead position matches audio playback position

**If Playback Doesn't Work**:
- Check Console for audio element errors
- Check Network tab for audio file loading
- Verify `audioUrl` is valid
- Check if audio element is created and configured correctly
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Audio preview works

---

#### Checkpoint 2.9: Click Timeline to Set Playhead

**Action**: Click within the selected region on the timeline

**Expected Result**:
- Playhead jumps to clicked position
- Audio currentTime updates to clicked position
- Playhead indicator moves to clicked position

**Verification Steps**:
1. **Click Behavior Check**:
   - [ ] Click within selected region → Playhead jumps to clicked position
   - [ ] Playhead indicator moves to clicked position
   - [ ] Time display updates to show clicked position

2. **Audio Sync Check**:
   - [ ] If audio is playing, playback position updates to clicked position
   - [ ] If audio is paused, currentTime updates to clicked position

3. **Boundary Check**:
   - [ ] Click outside selected region → Behavior is correct (may not move playhead, or may move selection)
   - [ ] Click on start marker → Playhead moves to start
   - [ ] Click on end marker → Playhead moves to end

**If Click Doesn't Work**:
- Check Console for click handler errors
- Verify timeline element has click handler
- Check if click is being prevented by other elements
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Timeline click sets playhead

---

#### Checkpoint 2.10: Continue with Selection

**Action**: Once satisfied with selection, click "Continue with Selection" button

**Expected Result**:
- Selection is saved to backend
- Song profile view appears
- Selection is used for clip generation

**Verification Steps**:
1. **Visual Check**:
   - [ ] "Continue with Selection" button is visible (appears when selection is valid)
   - [ ] Button is clickable (not disabled)
   - [ ] Clicking button shows loading state (if implemented)
   - [ ] Song profile view appears after save

2. **Network Tab Check**:
   - [ ] Find `PATCH /api/v1/songs/{song_id}/selection` request
   - [ ] Request payload contains: `{"start_sec": <number>, "end_sec": <number>}`
   - [ ] Request status is `200`
   - [ ] Response contains updated song data with `selected_start_sec` and `selected_end_sec`

3. **State Check**:
   - [ ] Song profile view shows correct selection
   - [ ] Selection is remembered if page is refreshed

**If Save Fails**:
- Check Network tab for failed request
- Note exact error status code and message
- Check Console for errors
- Verify selection values are valid (start < end, duration ≤ 30s)
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Selection saved and song profile appears

---

#### Checkpoint 2.11: Verify Selection Persistence

**Action**: Refresh the page (press `F5` or `Cmd+R` / `Ctrl+R`)

**Expected Result**:
- Page reloads
- Selection is remembered and displayed
- Timeline shows previously selected range

**Verification Steps**:
1. **Visual Check**:
   - [ ] Page reloads successfully
   - [ ] Timeline shows previously selected range (if still on selection step)
   - [ ] OR song profile view shows selection was used (if past selection step)

2. **Network Tab Check**:
   - [ ] Find `GET /api/v1/songs/{song_id}` request (if song is fetched on load)
   - [ ] Response contains `selected_start_sec` and `selected_end_sec` with correct values

3. **Data Check**:
   - [ ] Selection values match what was previously selected
   - [ ] Values are within valid range (start < end, duration ≤ 30s)

**If Persistence Fails**:
- Check if song ID is stored correctly
- Check Network tab for GET request
- Verify backend returns correct `selected_start_sec` and `selected_end_sec`
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Selection persists across refresh

---

#### Test 2 Summary

**All Checkpoints Passed**: ✅
- [ ] Checkpoint 2.1: Analysis completed
- [ ] Checkpoint 2.2: Audio selection timeline visible
- [ ] Checkpoint 2.3: Default selection correct
- [ ] Checkpoint 2.4: Start marker dragging works
- [ ] Checkpoint 2.5: End marker dragging works
- [ ] Checkpoint 2.6: 30-second maximum enforced
- [ ] Checkpoint 2.7: Minimum duration (1s) enforced
- [ ] Checkpoint 2.8: Audio preview works
- [ ] Checkpoint 2.9: Timeline click sets playhead
- [ ] Checkpoint 2.10: Selection saved and song profile appears
- [ ] Checkpoint 2.11: Selection persists across refresh

**Edge Cases to Test** (see [Edge Cases](#edge-cases--error-handling) section):
- Very short track (< 30 seconds)
- Exactly 30 seconds
- Very long track (> 5 minutes)
- Rapid marker dragging
- Full-length videos (should NOT show audio selection)

---

### Test 3: Skip Sections for Short-Form

**Goal**: Verify that section inference is skipped for short-form videos, and sections UI is conditionally displayed.

**Estimated Time**: 10-15 minutes

---

#### Checkpoint 3.1: Verify Backend Skips Sections

**Action**: Complete analysis for short-form video (from Test 2)

**Expected Result**:
- Backend logs show skip message
- No section detection runs
- Analysis completes successfully

**Verification Steps**:
1. **Backend Logs Check**:
   - [ ] Check backend terminal for log message:
     ```text
     ⏭️ [ANALYSIS] Skipping section detection (short-form video) - song_id=...
     ```
   - [ ] No section detection code runs (no section-related log messages)

2. **Analysis Response Check**:
   - [ ] Check Network tab for analysis response
   - [ ] Response may have empty `sections` array or no sections data
   - [ ] Analysis completes without errors

**If Sections Are Not Skipped**:
- Check backend logs for section detection messages
- Verify `video_type` is correctly set to "short_form"
- Check `song_analysis.py` service for skip logic
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Backend skips sections for short-form

---

#### Checkpoint 3.2: Verify Frontend Sections UI

**Action**: Navigate to song profile view (after completing audio selection)

**Expected Result**:
- Sections timeline may or may not appear (depends on feature flag)
- If sections appear, they should be minimal or placeholder
- No errors related to missing sections

**Verification Steps**:
1. **Visual Check**:
   - [ ] Song profile view loads without errors
   - [ ] Sections timeline either:
     - Does NOT appear (if feature flag disabled), OR
     - Appears but shows no sections or placeholder (if feature flag enabled)
   - [ ] No error messages about missing sections

2. **Console Check**:
   - [ ] No errors related to sections
   - [ ] No warnings about missing section data

3. **Feature Flag Check** (if accessible):
   - [ ] Check Network tab for `GET /api/v1/config/features` request
   - [ ] Response shows `sections: true/false`
   - [ ] UI respects feature flag setting

**If Sections UI Shows Errors**:
- Check Console for error messages
- Verify feature flag is set correctly
- Check if sections data is expected but missing
- See [How to Report Issues](#how-to-report-issues--request-fixes) section

**Checkpoint**: ✅ Frontend sections UI handles skipped sections

---

#### Checkpoint 3.3: Compare with Full-Length

**Action**: Upload same audio file, select "Full Length", complete analysis

**Expected Result**:
- Sections are detected and displayed
- Song structure timeline shows sections
- Section cards appear in grid

**Verification Steps**:
1. **Visual Check**:
   - [ ] Sections timeline appears with sections
   - [ ] Section cards appear in grid layout
   - [ ] Sections have names, start/end times, etc.

2. **Backend Logs Check**:
   - [ ] Backend logs show section detection running
   - [ ] No skip message appears

3. **Data Check**:
   - [ ] Analysis response contains `sections` array with section data
   - [ ] Sections have valid start/end times

**Checkpoint**: ✅ Full-length videos detect sections

---

#### Test 3 Summary

**All Checkpoints Passed**: ✅
- [ ] Checkpoint 3.1: Backend skips sections for short-form
- [ ] Checkpoint 3.2: Frontend sections UI handles skipped sections
- [ ] Checkpoint 3.3: Full-length videos detect sections

**Known Behavior**:
- Section inference is **automatically skipped** for `video_type="short_form"` in backend
- Frontend sections UI is controlled by feature flag (`sectionsEnabled`)
- Short-form videos work without sections (direct clip generation)

---

## Character Consistency Foundation (Quick Test)

**Goal**: Verify that character image upload works for short-form videos (foundation only - full
workflow not yet implemented).

**Estimated Time**: 10-15 minutes

---

### Checkpoint 4.1: Character Upload Appears

**Action**: Complete analysis for short-form video, observe page

**Expected Result**:
- Character upload section appears after analysis
- Section shows:
  - "Character Consistency (Optional)" label
  - Description text
  - Upload area (drag-and-drop or file input)

**Verification Steps**:
1. **Visual Check**:
   - [ ] Character upload section is visible
   - [ ] Section appears **after** analysis completes
   - [ ] Section appears **only** for short-form videos (not full-length)
   - [ ] Upload area is visible and interactive

2. **Timing Check**:
   - [ ] Section appears before audio selection step (or after, depending on implementation)
   - [ ] Section is clearly optional (user can skip)

**Checkpoint**: ✅ Character upload section visible

---

### Checkpoint 4.2: Upload Valid Character Image

**Action**: Drag and drop or select a valid image file (JPEG, PNG, WEBP)

**Expected Result**:
- Image preview appears
- Upload progress indicator shows (if implemented)
- Upload completes successfully
- Success message or callback fires

**Verification Steps**:
1. **Visual Check**:
   - [ ] Image preview appears after selection
   - [ ] Preview shows correct image
   - [ ] Upload progress indicator appears (if implemented)
   - [ ] Upload completes (progress reaches 100% or indicator disappears)

2. **Network Tab Check**:
   - [ ] Find `POST /api/v1/songs/{song_id}/character-image` request
   - [ ] Request contains image file in FormData
   - [ ] Request status is `200` or `201`
   - [ ] Response contains `image_url` and `s3_key`

3. **Backend Check**:
   - [ ] Check backend logs for successful upload
   - [ ] Verify image is stored in S3 (if accessible)
   - [ ] Verify song record has `character_reference_image_s3_key` set
   - [ ] Verify `character_consistency_enabled` is set to `true`

**Checkpoint**: ✅ Valid image uploads successfully

---

### Checkpoint 4.3: Test Image Validation

**Action**: Try uploading invalid files

**Test Cases**:
1. **Non-image file**: Upload `.txt` or `.pdf` file
2. **Image too large**: Upload image > 10MB
3. **Invalid dimensions**: Upload image with dimensions outside valid range (if validation exists)

**Expected Result**:
- Upload is rejected
- Clear error message displayed
- User can retry with valid file

**Verification Steps**:
1. **Error Message Check**:
   - [ ] Error message is displayed for each invalid file type
   - [ ] Error message is clear and actionable
   - [ ] Error message explains what went wrong

2. **Network Tab Check**:
   - [ ] Request may be sent and return `400` status, OR
   - [ ] Request is prevented on frontend (client-side validation)

3. **State Check**:
   - [ ] Upload area is still usable after error
   - [ ] User can retry with valid file
   - [ ] Previous valid upload (if any) is not affected

**Checkpoint**: ✅ Image validation works

---

#### Test 4 Summary

**All Checkpoints Passed**: ✅
- [ ] Checkpoint 4.1: Character upload section visible
- [ ] Checkpoint 4.2: Valid image uploads successfully
- [ ] Checkpoint 4.3: Image validation works

**Known Limitations (Foundation Only)**:
- **Image interrogation** (Phase 2) not yet implemented
- **Character image generation** (Phase 3) not yet implemented
- **Full workflow** (Phase 5) not yet implemented
- Currently: Reference image is stored and can be passed to video generation, but full
  consistency workflow is pending

---

## Beat Sync Foundation (Quick Test)

**Goal**: Verify that beat sync foundation components are integrated (prompt enhancement and beat filters).

**Estimated Time**: 5-10 minutes

---

### Checkpoint 5.1: Verify Beat Detection

**Action**: Complete analysis for any video type

**Expected Result**:
- Beat detection runs during analysis
- `beat_times` array is populated
- BPM is calculated

**Verification Steps**:
1. **Analysis Response Check**:
   - [ ] Check Network tab for analysis response
   - [ ] Response contains `beat_times` array (list of numbers)
   - [ ] Response contains `bpm` value (number)
   - [ ] `beat_times` array is not empty

2. **Backend Logs Check**:
   - [ ] Backend logs show beat detection running
   - [ ] No errors related to beat detection

**Checkpoint**: ✅ Beat detection works

---

### Checkpoint 5.2: Verify Prompt Enhancement

**Action**: Generate clips for a song

**Expected Result**:
- Prompts are enhanced with rhythmic descriptors
- BPM classification is logged
- Motion descriptors are added to prompts

**Verification Steps**:
1. **Backend Logs Check**:
   - [ ] Look for log messages during clip generation
   - [ ] Logs show BPM classification (slow/medium/fast/very_fast)
   - [ ] Logs show motion descriptors being added
   - [ ] Prompts contain rhythmic motion cues

2. **Code Check** (if familiar with codebase):
   - [ ] Verify `prompt_enhancement.py` is called
   - [ ] Verify `enhance_prompt_with_rhythm()` is used

**Checkpoint**: ✅ Prompt enhancement integrated

---

### Checkpoint 5.3: Verify Beat Filters

**Action**: Compose final video

**Expected Result**:
- Beat filter expressions are generated
- Beat times are passed to composition
- Filters are applied (if enabled via config)

**Verification Steps**:
1. **Backend Logs Check**:
   - [ ] Look for log messages during composition
   - [ ] Logs show beat filter expressions being generated
   - [ ] Logs show beat times being passed to composition
   - [ ] Logs show filter application (if enabled)

2. **Code Check** (if familiar with codebase):
   - [ ] Verify `beat_filters.py` is called
   - [ ] Verify `generate_beat_filter_complex()` is used

**Checkpoint**: ✅ Beat filters integrated

---

#### Test 5 Summary

**All Checkpoints Passed**: ✅
- [ ] Checkpoint 5.1: Beat detection works
- [ ] Checkpoint 5.2: Prompt enhancement integrated
- [ ] Checkpoint 5.3: Beat filters integrated

**Known Limitations (Foundation Only)**:
- **Phase 3.1 (Prompt Engineering)**: Foundation complete, API-specific optimization pending
- **Phase 3.2 (Beat Filters)**: Foundation complete, enhanced effects pending
- **Phase 3.3 (Structural Sync)**: Not yet implemented
- **Full beat sync**: Partial implementation, full workflow pending

---

## End-to-End User Flows

### Flow 1: Short-Form Video with Character Consistency

**Complete workflow for short-form video with character image.**

**Estimated Time**: 30-45 minutes

**Steps**:
1. ✅ Upload audio file (> 30 seconds)
2. ✅ Select "Short Form" video type
3. ✅ Start and complete analysis
4. ✅ Upload character reference image (optional)
5. ✅ Select 30-second audio segment
6. ✅ Generate clips
7. ✅ Compose final video

**Success Criteria**:
- [ ] All steps complete without errors
- [ ] Video type selection works
- [ ] Analysis skips sections for short-form
- [ ] Character image uploads successfully (if attempted)
- [ ] Audio selection works (30s max)
- [ ] Clips generate successfully
- [ ] Final video composes successfully
- [ ] Character appears consistent in clips (if image uploaded)

---

### Flow 2: Full-Length Video (Traditional Flow)

**Complete workflow for full-length video (no selection, no character).**

**Estimated Time**: 20-30 minutes

**Steps**:
1. ✅ Upload audio file
2. ✅ Select "Full Length" video type
3. ✅ Start and complete analysis
4. ✅ Verify sections are detected (if feature flag enabled)
5. ✅ Generate clips
6. ✅ Compose final video

**Success Criteria**:
- [ ] Full-length flow works end-to-end
- [ ] Sections detected (if enabled)
- [ ] No audio selection step (full-length only)
- [ ] No character upload step (full-length only)
- [ ] Clips generate for full duration
- [ ] Final video composes successfully

---

## Edge Cases & Error Handling

### Edge Case 1: Very Short Audio (< 30 seconds)

**Scenario**: Upload audio file shorter than 30 seconds for short-form video.

**Test Steps**:
1. Upload `short_audio.mp3` (< 30 seconds)
2. Select "Short Form"
3. Complete analysis
4. Check audio selection interface

**Expected Behavior**:
- Audio selection should allow full track selection
- No 30-second constraint (since track < 30s)
- Can proceed with full track

**Verification**:
- [ ] Timeline shows full track selectable
- [ ] No constraint error appears
- [ ] Can proceed to clip generation

**If Issue Found**: See [How to Report Issues](#how-to-report-issues--request-fixes) section

---

### Edge Case 2: Invalid Character Image

**Scenario**: Upload invalid image file or image that fails validation.

**Test Steps**:
1. Upload audio file
2. Select "Short Form"
3. Complete analysis
4. Try uploading invalid image:
   - Non-image file (.txt, .pdf)
   - Image too large (> 10MB)
   - Image with invalid dimensions

**Expected Behavior**:
- Clear error message displayed
- Upload rejected
- Song upload not affected (character is optional)

**Verification**:
- [ ] Error message is clear and actionable
- [ ] Upload area is still usable
- [ ] Can retry with valid file

**If Issue Found**: See [How to Report Issues](#how-to-report-issues--request-fixes) section

---

### Edge Case 3: Change Video Type After Analysis

**Scenario**: Try to change video type after analysis has completed.

**Test Steps**:
1. Upload audio
2. Select "Full Length"
3. Complete analysis
4. Try to change to "Short Form"

**Expected Behavior**:
- Video type cannot be changed
- UI should prevent or show error
- Analysis results remain valid

**Verification**:
- [ ] Video type selector is disabled/hidden, OR
- [ ] Error message appears when trying to change
- [ ] Analysis results are not lost

**If Issue Found**: See [How to Report Issues](#how-to-report-issues--request-fixes) section

---

### Edge Case 4: Network Error During Selection Save

**Scenario**: Network fails while saving audio selection.

**Test Steps**:
1. Upload audio
2. Select "Short Form"
3. Complete analysis
4. Make audio selection
5. Disconnect network (or block API calls in DevTools)
6. Click "Continue with Selection"

**Expected Behavior**:
- Error handled gracefully
- Selection saved locally (if possible)
- User can retry

**Verification**:
- [ ] Error message appears
- [ ] Can retry when network restored
- [ ] Selection is not lost (if saved locally)

**If Issue Found**: See [How to Report Issues](#how-to-report-issues--request-fixes) section

---

### Edge Case 5: Missing Beat Data

**Scenario**: Analysis completes but beat_times array is empty or missing.

**Test Steps**:
1. Upload audio file with poor quality or unusual format
2. Complete analysis
3. Check if beat_times populated
4. Generate clips

**Expected Behavior**:
- Beat sync features gracefully degrade
- Video generation continues without beat sync
- No errors thrown

**Verification**:
- [ ] Clips generate successfully
- [ ] No errors related to missing beat data
- [ ] Video composes successfully

**If Issue Found**: See [How to Report Issues](#how-to-report-issues--request-fixes) section

---

## How to Report Issues & Request Fixes

### When You Find an Issue

When you encounter a problem during testing, follow these steps:

1. **Document the Issue**:
   - Note which checkpoint failed
   - Note exact steps that led to the issue
   - Note expected vs actual behavior
   - Take screenshots if helpful
   - Copy error messages from Console/Network tab

2. **Gather Context**:
   - Note browser and OS
   - Note backend/frontend versions (if known)
   - Note video type (full-length or short-form)
   - Note audio file details (duration, format)

3. **Use the AI Fix Request Template** (see below)

---

### AI Fix Request Template

When asking an AI agent (like me) to fix an issue, use this template:

```text
I found an issue during manual testing of the advancedFeatures branch.

**Checkpoint**: [e.g., "Checkpoint 2.4: Drag Start Marker"]

**Steps to Reproduce**:
1. [Exact step 1]
2. [Exact step 2]
3. [Exact step 3]

**Expected Behavior**:
[What should have happened]

**Actual Behavior**:
[What actually happened]

**Error Messages**:
[Copy error messages from Console/Network tab/backend logs]

**Environment**:
- Browser: [Chrome/Firefox/Safari] [Version]
- OS: [macOS/Windows/Linux] [Version]
- Video Type: [full_length/short_form]
- Audio File: [Duration, format]

**Screenshots/Logs**:
[Attach if available]

**Request**: Please fix this issue and improve the UX if needed.
```

---

### Example AI Fix Requests

#### Example 1: Marker Dragging Issue

```text
I found an issue during manual testing of the advancedFeatures branch.

**Checkpoint**: Checkpoint 2.4: Drag Start Marker

**Steps to Reproduce**:
1. Upload medium_audio.mp3 (45 seconds)
2. Select "Short Form"
3. Complete analysis
4. Audio selection timeline appears
5. Try to drag start marker to the right

**Expected Behavior**:
- Marker should move smoothly as I drag
- Selection duration should update in real-time
- Marker should stop at end marker if dragged too far

**Actual Behavior**:
- Marker doesn't move when I click and drag
- No visual feedback
- Console shows error: "Cannot read property 'clientX' of undefined"

**Error Messages**:
```javascript
Uncaught TypeError: Cannot read property 'clientX' of undefined
    at AudioSelectionTimeline.handleMouseMove (AudioSelectionTimeline.tsx:123)
```

**Environment**:
- Browser: Chrome 120.0
- OS: macOS 14.2
- Video Type: short_form
- Audio File: 45 seconds, MP3

**Request**: Please fix the marker dragging functionality. The mouse event handler seems to be
missing the event parameter or the event is not being passed correctly.
```

#### Example 2: Validation Issue

```text
I found an issue during manual testing of the advancedFeatures branch.

**Checkpoint**: Checkpoint 2.6: Test 30-Second Maximum Constraint

**Steps to Reproduce**:
1. Upload long_audio.mp3 (2 minutes)
2. Select "Short Form"
3. Complete analysis
4. Audio selection timeline appears
5. Position start marker at 0:00
6. Try to drag end marker to create > 30 second selection

**Expected Behavior**:
- Selection should be constrained to exactly 30 seconds maximum
- End marker should stop at 30s from start marker
- Visual feedback should show constraint

**Actual Behavior**:
- Can drag end marker to create 35-second selection
- No constraint is enforced
- Selection duration shows "35.0s"

**Error Messages**:
None in console, but validation should prevent this.

**Environment**:
- Browser: Firefox 121.0
- OS: Windows 11
- Video Type: short_form
- Audio File: 2 minutes, MP3

**Request**: Please fix the 30-second maximum constraint. The validation logic in AudioSelectionTimeline component doesn't seem to be enforcing the maximum duration correctly. Also, add visual feedback (like a warning message or color change) when the user tries to exceed the limit.
```

#### Example 3: UX Improvement Request

```text
I found a UX issue during manual testing of the advancedFeatures branch.

**Checkpoint**: Checkpoint 2.8: Test Audio Preview

**Steps to Reproduce**:
1. Upload medium_audio.mp3
2. Select "Short Form"
3. Complete analysis
4. Audio selection timeline appears
5. Click Play button

**Expected Behavior**:
- Audio should play from start marker
- Playhead should move smoothly

**Actual Behavior**:
- Audio plays correctly
- Playhead moves, but it's hard to see (very thin line, low contrast)

**Error Messages**:
None

**Environment**:
- Browser: Chrome 120.0
- OS: macOS 14.2
- Video Type: short_form

**Request**: Please improve the playhead visibility. The playhead indicator is too thin and has low contrast, making it hard to see during playback. Consider making it thicker (2-3px instead of 1px) and using a brighter color (white or accent color) with better contrast against the waveform background.
```

---

### Quick Fix Request Format

For simple issues, you can use a shorter format:

```text
**Issue**: [Brief description]
**Location**: [Component/File name]
**Fix**: [What needs to be fixed]
**Improvement**: [Optional UX improvement]
```

**Example**:
```text
**Issue**: Start marker doesn't drag smoothly
**Location**: AudioSelectionTimeline.tsx
**Fix**: Mouse event handler is missing event parameter
**Improvement**: Add visual feedback during drag (cursor change, marker highlight)
```

---

### Requesting UX Improvements

Even if something works, you can request UX improvements:

```text
**UX Improvement Request**

**Feature**: Audio Selection Timeline
**Current Behavior**: [What currently happens]
**Suggested Improvement**: [What would be better]
**Rationale**: [Why this would improve UX]

**Example**:
**Feature**: Audio Selection Timeline
**Current Behavior**: When dragging markers, there's no visual feedback showing the selection duration until you release the mouse
**Suggested Improvement**: Show selection duration in real-time as you drag (e.g., "15.3s" next to cursor or in a tooltip)
**Rationale**: Users would get immediate feedback about selection duration without having to look at the time display, making it easier to create precise selections
```

---

## Testing Checklist Summary

### High Priority (UX Features)

- [ ] Test 1: Video type selection works
- [ ] Test 2: 30-second audio selection works
- [ ] Test 2: Selection constraints enforced (30s max, 1s min)
- [ ] Test 2: Audio preview works
- [ ] Test 2: Selection persists across refresh
- [ ] Test 3: Sections skipped for short-form
- [ ] Test 3: Full-length flow works without selection

### Medium Priority (Character Consistency)

- [ ] Test 4: Character image upload works
- [ ] Test 4: Image validation works
- [ ] Test 4: Upload only appears for short-form
- [ ] Test 4: Error handling works

### Low Priority (Beat Sync Foundation)

- [ ] Test 5: Beat detection works
- [ ] Test 5: Prompt enhancement integrated (check logs)
- [ ] Test 5: Beat filters integrated (check logs)
- [ ] Test 5: Beat data flows correctly

### Edge Cases

- [ ] Edge Case 1: Very short audio (< 30s)
- [ ] Edge Case 2: Invalid character image
- [ ] Edge Case 3: Video type change after analysis
- [ ] Edge Case 4: Network errors
- [ ] Edge Case 5: Missing beat data

---

## Quick Reference

### API Endpoints

- `POST /api/v1/songs/` - Upload song
- `PATCH /api/v1/songs/{song_id}/video-type` - Set video type
- `POST /api/v1/songs/{song_id}/analyze` - Start analysis
- `PATCH /api/v1/songs/{song_id}/selection` - Save audio selection
- `POST /api/v1/songs/{song_id}/character-image` - Upload character image
- `POST /api/v1/songs/{song_id}/clips/generate` - Generate clips
- `POST /api/v1/compositions` - Compose final video

### Key Database Fields

- `video_type`: `"full_length"` or `"short_form"`
- `selected_start_sec`: Start time of audio selection (float)
- `selected_end_sec`: End time of audio selection (float)
- `character_reference_image_s3_key`: S3 key for character image
- `character_consistency_enabled`: Boolean flag

### Feature Flags

- `ENABLE_SECTIONS`: Controls section-based generation (backend)
- `sections`: Feature flag for sections UI (frontend, from API)

---

## Happy Testing! 🎬

Remember: If you find any issues, use the [AI Fix Request Template](#ai-fix-request-template) to
request fixes and improvements.
