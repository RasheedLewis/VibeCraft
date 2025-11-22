# Manual Testing Guide - Advanced Features Branch

Prescriptive step-by-step testing instructions for all new features in the `advancedFeatures`
branch. Each step includes exact actions, expected results, verification methods, and checkpoints.

---

## Table of Contents

1. [Quick Smoke Test](#quick-smoke-test) ⚡
2. [Prerequisites & Setup](#prerequisites--setup)
3. [Primary UX Features](#primary-ux-features)
4. [Character Consistency Foundation](#character-consistency-foundation)
5. [Beat Sync Foundation](#beat-sync-foundation)
6. [End-to-End Flows](#end-to-end-flows)
7. [Edge Cases](#edge-cases)
8. [How to Report Issues](#how-to-report-issues)

---

## Quick Smoke Test

**Purpose**: Quickly verify all major features work end-to-end.

**Time**: 10-15 minutes | **Prerequisites**: Backend and frontend running

### Steps

1. **Upload & Select Video Type** (2 min)
   - Upload `medium_audio.mp3` (30-60s)
   - Select "Short Form"
   - **Verify**: Upload completes, selector appears, selection saves

2. **Complete Analysis** (3-5 min)
   - Click "Start Analysis"
   - **Verify**: Analysis completes, backend logs show section skip message

3. **Test Audio Selection** (3-5 min)
   - Verify timeline appears with waveform
   - Drag start/end markers, verify 30s max constraint
   - Test audio preview (Play button)
   - Click "Continue with Selection"
   - **Verify**: Timeline works, constraints enforced, preview works, selection saves

4. **Quick Character Selection** (2 min)
   - Click "Choose Template" button
   - Select a template character from modal
   - **Verify**: Modal opens, templates load, selection applies successfully
   - **Alternative**: Upload custom image (JPEG/PNG/WEBP)
   - **Verify**: Upload succeeds, no errors

5. **Verify Song Profile** (1 min)
   - Check song profile view appears
   - **Verify**: Profile loads, no section errors

**All Steps Pass**: System working on happy path

**If Any Step Fails**: Note which step, check Console/Network tabs, see [How to Report Issues](#how-to-report-issues)

---

## Prerequisites & Setup

### Environment Setup

**Backend**:

```bash
cd backend && source venv/bin/activate
python -m uvicorn app.main:app --reload
```

**Verify**: `Uvicorn running on http://127.0.0.1:8000`, can access `/docs`

**Frontend**:

```bash
cd frontend && npm run dev
```

**Verify**: Frontend accessible, no errors

**Migrations**: Verify `migrations/002_*.py`, `003_*.py`, `004_*.py` exist

### Test Files

Prepare:

- `short_audio.mp3` (< 30s) - Test full selection
- `medium_audio.mp3` (30-60s) - Test 30s selection
- `long_audio.mp3` (> 60s) - Test selection from long track

### Developer Tools

Open browser DevTools (F12), enable Network and Console tabs, clear console.

---

## Primary UX Features

### Test 1: Video Type Selection

**Goal**: Verify video type selection before analysis.

**Time**: 10-15 min

#### Checkpoints

**1.1 Navigate & Upload**

- Open `http://localhost:5173`
- Upload `medium_audio.mp3`
- Verify: Page loads, upload completes, `POST /api/v1/songs/` returns 200/201

**1.2 Video Type Selector Appears**

- Wait for upload completion
- Verify: Selector visible with "Full Length" and "Short Form" options

**1.3 Select "Short Form"**

- Click "Short Form"
- Verify: Selected state shown, loading indicator,
  `PATCH /api/v1/songs/{id}/video-type` returns 200

**1.4 Select "Full Length"**

- Click "Full Length"
- Verify: Selection changes, saves successfully

**1.5 Verify Persistence**

- Refresh page (F5)
- Verify: Selection remembered, `GET /api/v1/songs/{id}` returns correct
  `video_type`

**Test 1 Summary**: All checkpoints pass

**Known**: Video type must be selected before analysis, cannot change after analysis.

---

### Test 2: 30-Second Audio Selection

**Goal**: Verify 30-second audio selection for short-form videos.

**Time**: 20-30 min | **Prerequisites**: Test 1 with "Short Form" selected

#### Checkpoints

**2.1 Start Analysis**

- Click "Start Analysis"
- Verify: Analysis completes, backend logs show skip message:
  `⏭️ [ANALYSIS] Skipping section detection (short-form video)`

**2.2 Timeline Appears**

- Wait for analysis completion
- Verify: Timeline visible with waveform, start/end markers, play button, time
  display

**2.3 Default Selection**

- Observe default selection
- Verify: Defaults to last 30s (if track > 30s) or full track (if < 30s)

**2.4 Drag Markers**

- Drag start marker right, drag end marker left/right
- Verify: Markers move smoothly, duration updates, constraints enforced:
  - Cannot exceed 30s max
  - Cannot go below 1s min
  - Cannot drag past boundaries

**2.5 Test Constraints**

- Try creating > 30s selection
- Try dragging markers very close
- Verify: 30s max enforced, 1s min enforced

**2.6 Audio Preview**

- Click Play button
- Verify: Audio plays from start marker, playhead moves, stops at end
  marker, can pause/resume

**2.7 Timeline Click**

- Click within selected region
- Verify: Playhead jumps to clicked position

**2.8 Save Selection**

- Click "Continue with Selection"
- Verify: `PATCH /api/v1/songs/{id}/selection` returns 200, song profile
  appears

**2.9 Verify Persistence**

- Refresh page
- Verify: Selection remembered, `GET /api/v1/songs/{id}` returns
  `selected_start_sec`/`selected_end_sec`

**Test 2 Summary**: All checkpoints pass

---

### Test 3: Skip Sections for Short-Form

**Goal**: Verify section inference is skipped for short-form videos.

**Time**: 10-15 min

#### Checkpoints

**3.1 Backend Skips Sections**

- Complete analysis for short-form video
- Verify: Backend logs show skip message, no section detection runs

**3.2 Frontend Sections UI**

- Navigate to song profile view
- Verify: Sections timeline either hidden or shows placeholder (depends on
  feature flag), no errors

**3.3 Compare with Full-Length**

- Upload same audio, select "Full Length", complete analysis
- Verify: Sections detected and displayed for full-length

**Test 3 Summary**: All checkpoints pass

**Known**: Section inference automatically skipped for `video_type="short_form"`.

---

## Character Consistency Foundation

**Goal**: Verify character image upload and template character selection work.

**Time**: 15-20 min

### Checkpoints

**4.1 Upload Section Appears**

- Complete analysis for short-form video
- Verify: Character upload section visible (short-form only), appears after
  analysis
- Verify: "Choose Template" button visible next to upload area

**4.2 Template Character Selection**

- Click "Choose Template" button
- **Verify**: Modal opens, displays 4 characters in grid (4 columns)
- **Verify**: Each character shows 2 poses stacked vertically
- **Verify**: Character names and descriptions visible
- **Verify**: `GET /api/v1/template-characters` returns 200 with templates array
- Select a character (click on character column)
- **Verify**: Modal shows loading state during application
- **Verify**: `POST /api/v1/songs/{id}/character-image/template` returns 200
- **Verify**: Modal closes after successful selection
- **Verify**: Character consistency enabled in database
- **Verify**: Both poses (pose-a and pose-b) stored in S3:
  - `songs/{song_id}/character_reference.jpg` (pose-a)
  - `songs/{song_id}/character_pose_b.jpg` (pose-b)

**4.3 Template Character Error Handling**

- Try selecting template when song doesn't exist (404)
- Try selecting template for full_length video (400 error)
- Try selecting invalid character ID (404 error)
- **Verify**: Clear error messages displayed in modal

**4.4 Upload Custom Image**

- Upload valid image (JPEG/PNG/WEBP)
- **Verify**: Preview appears, `POST /api/v1/songs/{id}/character-image` returns
  200, image saved to S3
- **Verify**: Can switch between template and custom upload

**4.5 Test Validation**

- Try uploading invalid files (.txt, > 10MB, invalid dimensions)
- **Verify**: Clear error messages, upload rejected, can retry

**4.6 Both Poses Used in Video Generation**

- Complete clip generation with template character selected
- **Verify**: Backend logs show both poses passed to video generation
- **Verify**: `reference_image_urls` array contains 2 URLs (pose-a and pose-b)
- **Verify**: Video generation attempts multiple images, falls back to single if
  model doesn't support
- **Verify**: Clips generated successfully with character consistency

**Character Consistency Summary**: All checkpoints pass

**Known**: Foundation only - full workflow (interrogation, generation) pending.

---

## Beat Sync Foundation

**Goal**: Verify beat sync foundation components are integrated.

**Time**: 5-10 min

### Checkpoints

**5.1 Beat Detection**

- Complete analysis
- Verify: `beat_times` array populated, `bpm` calculated

**5.2 Prompt Enhancement**

- Generate clips
- Verify: Backend logs show BPM classification, motion descriptors added to
  prompts

**5.3 Beat Filters**

- Compose final video
- Verify: Backend logs show beat filter expressions generated, beat times
  passed to composition

**Beat Sync Summary**: All checkpoints pass

**Known**: Foundation only - full beat sync (structural sync) pending.

---

## End-to-End Flows

### Flow 1: Short-Form with Template Character

**Steps**: Upload → Select "Short Form" → Analysis → Select template character
→ Select 30s → Generate clips → Compose

**Success**: All steps complete, template character applied (both poses stored),
clips use character consistency, clips use selected range.

**Alternative**: Upload custom character image instead of template.

### Flow 2: Full-Length (Traditional)

**Steps**: Upload → Select "Full Length" → Analysis → Generate clips → Compose

**Success**: Full-length flow works, sections detected (if enabled), no selection/character steps.

---

## Edge Cases

### 1. Very Short Audio (< 30s)

- Upload < 30s audio, select "Short Form", complete analysis
- Verify: Full track selectable, no 30s constraint error

### 2. Invalid Character Image

- Try uploading .txt, > 10MB, invalid dimensions
- Verify: Clear error, upload rejected, can retry

### 3. Change Video Type After Analysis

- Upload, select "Full Length", complete analysis, try changing to "Short Form"
- Verify: Change prevented or error shown

### 4. Network Error During Selection Save

- Make selection, disconnect network, click "Continue"
- Verify: Error handled gracefully, can retry when network restored

### 5. Missing Beat Data

- Upload poor quality audio, complete analysis, generate clips
- Verify: Clips generate successfully, beat sync gracefully degrades

---

## How to Report Issues

### When You Find an Issue

1. **Document**: Note checkpoint, exact steps, expected vs actual,
   screenshots/logs
2. **Gather Context**: Browser/OS, video type, audio file details
3. **Use AI Fix Request Template** (below)

### AI Fix Request Template

```text
I found an issue during manual testing of the advancedFeatures branch.

**Checkpoint**: [e.g., "Checkpoint 2.4: Drag Start Marker"]

**Steps to Reproduce**:
1. [Exact step 1]
2. [Exact step 2]
3. [Exact step 3]

**Expected Behavior**: [What should have happened]
**Actual Behavior**: [What actually happened]
**Error Messages**: [Copy from Console/Network/backend logs]

**Environment**:
- Browser: [Chrome/Firefox/Safari] [Version]
- OS: [macOS/Windows/Linux] [Version]
- Video Type: [full_length/short_form]
- Audio File: [Duration, format]

**Request**: Please fix this issue and improve the UX if needed.
```

### Quick Fix Format

```text
**Issue**: [Brief description]
**Location**: [Component/File name]
**Fix**: [What needs to be fixed]
**Improvement**: [Optional UX improvement]
```

### UX Improvement Request

```text
**Feature**: [Feature name]
**Current Behavior**: [What currently happens]
**Suggested Improvement**: [What would be better]
**Rationale**: [Why this would improve UX]
```

---

## Quick Reference

### API Endpoints

- `POST /api/v1/songs/` - Upload song
- `PATCH /api/v1/songs/{song_id}/video-type` - Set video type
- `POST /api/v1/songs/{song_id}/analyze` - Start analysis
- `PATCH /api/v1/songs/{song_id}/selection` - Save audio selection
- `GET /api/v1/template-characters` - List available template characters
- `POST /api/v1/songs/{song_id}/character-image/template` - Apply template character
- `POST /api/v1/songs/{song_id}/character-image` - Upload custom character image
- `POST /api/v1/songs/{song_id}/clips/generate` - Generate clips
- `POST /api/v1/compositions` - Compose final video

### Key Database Fields

- `video_type`: `"full_length"` or `"short_form"`
- `selected_start_sec`, `selected_end_sec`: Audio selection times
- `character_reference_image_s3_key`: Character pose-a image S3 key
- `character_pose_b_s3_key`: Character pose-b image S3 key (template characters)
- `character_consistency_enabled`: Boolean flag

### Feature Flags

- `ENABLE_SECTIONS`: Controls section-based generation (backend)
- `sections`: Feature flag for sections UI (frontend, from API)

---

## Happy Testing! 🎬

Use the [AI Fix Request Template](#ai-fix-request-template) to request fixes and improvements.
