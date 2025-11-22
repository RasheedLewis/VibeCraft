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

**Purpose**: Quickly verify all major features work end-to-end, including Character Consistency (Phases 2-7) and Beat Sync (Phases 3.1-3.3).

**Time**: 20-25 minutes | **Prerequisites**: Backend and frontend running

### Steps

1. **Upload & Select Video Type** (2 min)
   - Upload `medium_audio.mp3` (30-60s)
   - Select "Short Form"
   - **Verify**: Upload completes, selector appears, selection saves

2. **Complete Analysis** (3-5 min)
   - Click "Start Analysis"
   - **Verify**: Analysis completes, backend logs show:
     - Section skip message for short-form
     - Beat detection completed (`beat_times` array populated)
     - BPM calculated and stored

3. **Test Audio Selection** (3-5 min)
   - Verify timeline appears with waveform
   - Drag start/end markers, verify 30s max constraint
   - Test audio preview (Play button)
   - Click "Continue with Selection"
   - **Verify**: Timeline works, constraints enforced, preview works, selection saves

4. **Character Consistency Setup** (3-5 min)
   - Click "Choose Template" button OR upload custom character image
   - **Verify**: Template modal opens OR custom upload succeeds
   - Select template character OR upload JPEG/PNG/WEBP
   - **Verify**: Character image stored, `character_consistency_enabled` set to true
   - **Verify**: Backend logs show character image generation job enqueued (Phase 5)
   - **Verify**: CharacterPreview component displays uploaded image (Phase 6)

5. **Generate Clips with Character Consistency & Beat Sync** (5-7 min)
   - Click "Generate Clips"
   - **Verify**: Backend logs show:
     - **Character Consistency (Phase 2)**: Image interrogation service called (OpenAI or Replicate fallback)
     - **Character Consistency (Phase 3)**: Character image generation job running (Replicate SDXL)
     - **Character Consistency (Phase 4)**: Image-to-video generation with consistent character image
     - **Beat Sync (Phase 3.1)**: Prompt optimization for API, motion type selection, BPM extraction
   - **Verify**: Clips generate successfully with character consistency
   - **Verify**: Generated character image stored in S3 (Phase 5)

6. **Compose Video with Beat Sync** (3-5 min)
   - Click "Compose Video"
   - **Verify**: Backend logs show:
     - **Beat Sync (Phase 3.3)**: Beat-aligned boundary calculation
     - **Beat Sync (Phase 3.2)**: Beat filter generation (flash, color_burst, zoom_pulse, glitch)
     - **Beat Sync (Phase 3.3)**: Clip trimming/extending to beat boundaries
     - **Beat Sync (Phase 3.3)**: Transition verification
   - **Verify**: Final video composed successfully
   - **Verify**: Visual beat effects visible in video (flash, color burst, etc.)
   - **Verify**: Clip transitions occur on beats (rhythmically correct)
   - **Verify**: Character consistency maintained across clips

7. **Verify Song Profile** (1 min)
   - Check song profile view appears
   - **Verify**: Profile loads, CharacterPreview component shows character image
   - **Verify**: No section errors, character consistency status visible

**All Steps Pass**: System working on happy path with full Character Consistency (Phases 2-7) and Beat Sync (Phases 3.1-3.3) integration

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

## Character Consistency (Phases 1-7) ✅ COMPLETE

**Goal**: Verify complete Character Consistency workflow from image upload through consistent character image generation and video clip generation.

**Time**: 30-40 min | **Prerequisites**: Backend with OpenAI API key or Replicate API token configured

### Phase 1: Foundation (Database & Storage) ✅ COMPLETE

**4.1 Upload Section Appears**

- Complete analysis for short-form video
- Verify: Character upload section visible (short-form only), appears after analysis
- Verify: "Choose Template" button visible next to upload area
- Verify: CharacterPreview component appears after image upload (Phase 6)

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
- **Verify**: Preview appears, `POST /api/v1/songs/{id}/character-image` returns 200, image saved to S3
- **Verify**: CharacterPreview component displays uploaded image (Phase 6)
- **Verify**: Can switch between template and custom upload

**4.5 Test Validation**

- Try uploading invalid files (.txt, > 10MB, invalid dimensions)
- **Verify**: Clear error messages, upload rejected, can retry

### Phase 2: Image Interrogation Service ✅ COMPLETE

**4.6 Image Interrogation Workflow**

- Upload custom character image (not template)
- **Verify**: Backend logs show character image generation job enqueued
- **Verify**: Backend logs show `interrogate_reference_image()` called
- **Verify**: If OpenAI API key configured, logs show OpenAI GPT-4 Vision call
- **Verify**: If OpenAI unavailable, logs show Replicate `img2prompt` fallback
- **Verify**: Interrogation result stored in `character_interrogation_prompt` field (JSON)
- **Verify**: Prompt contains: `prompt`, `character_description`, `style_notes`

**4.7 Interrogation Error Handling**

- Test with invalid image URL or corrupted image
- **Verify**: Error logged, job fails gracefully, `character_consistency_enabled` set to false
- **Verify**: User can retry with new image

### Phase 3: Character Image Generation Service ✅ COMPLETE

**4.8 Consistent Character Image Generation**

- After image interrogation completes
- **Verify**: Backend logs show `generate_consistent_character_image()` called
- **Verify**: Replicate SDXL model called with interrogated prompt and reference image
- **Verify**: Job polls for completion (logs show polling attempts)
- **Verify**: Generated image URL returned when job succeeds
- **Verify**: Generated image downloaded and uploaded to S3:
  - `songs/{song_id}/character_generated.jpg`
- **Verify**: `character_generated_image_s3_key` field populated in database

**4.9 Generation Error Handling**

- Test with invalid Replicate API token or model failure
- **Verify**: Error logged, job fails gracefully, `character_consistency_enabled` set to false
- **Verify**: User can retry generation

### Phase 4: Video Generation Service Updates ✅ COMPLETE

**4.10 Image-to-Video Generation**

- Generate clips with character image uploaded
- **Verify**: Backend logs show `_generate_image_to_video()` called
- **Verify**: Replicate Hailuo 2.3 model called with generated character image
- **Verify**: Image-to-video generation succeeds for all 6 clips
- **Verify**: Clips maintain character consistency across all clips

**4.11 Enhanced Fallback Logic**

- Test with missing or invalid character image
- **Verify**: Backend logs show fallback to text-to-video generation
- **Verify**: Clips still generate successfully (graceful degradation)
- **Verify**: No errors thrown, workflow continues

**4.12 Multiple Reference Images Support**

- Use template character (both poses)
- **Verify**: Backend logs show `reference_image_urls` array with 2 URLs
- **Verify**: Video generation attempts multiple images
- **Verify**: Falls back to single image if model doesn't support multiple

### Phase 5: Orchestration Workflow ✅ COMPLETE

**4.13 Full Workflow Integration**

- Upload character image → Generate clips
- **Verify**: Backend logs show complete workflow:
  1. Download reference image from S3
  2. Interrogate image (Phase 2)
  3. Generate consistent character image (Phase 3)
  4. Upload generated image to S3
  5. Update song record with generated image key
  6. Use generated image for video generation (Phase 4)
- **Verify**: Background job (`generate_character_image_job`) executes successfully
- **Verify**: Job status tracked in RQ queue

**4.14 Storage Helpers**

- Check S3 bucket after character image generation
- **Verify**: Both reference and generated images stored correctly:
  - `songs/{song_id}/character_reference.jpg` (user upload)
  - `songs/{song_id}/character_generated.jpg` (generated consistent image)
- **Verify**: Presigned URLs generated correctly for image access

### Phase 6: Frontend Integration ✅ COMPLETE

**4.15 CharacterPreview Component**

- After character image uploaded
- **Verify**: CharacterPreview component displays image
- **Verify**: Loading state shown while fetching image
- **Verify**: Error state shown if image fails to load
- **Verify**: Component handles missing image gracefully

**4.16 Character Image Upload UI**

- Upload custom character image
- **Verify**: Drag-and-drop works in CharacterImageUpload component
- **Verify**: File validation (format, size, dimensions) works
- **Verify**: Preview updates after successful upload
- **Verify**: Error messages displayed for invalid uploads

### Phase 7: Testing & Documentation ✅ COMPLETE

**4.17 Test Scripts**

- Run test scripts in `scripts/checkpoints-advanced-features/`:
  - `test-character-interrogation-1.sh` (Phase 2)
  - `test-character-generation-2.sh` (Phase 3)
  - `test-character-workflow-3.sh` (Phase 5)
  - `test-character-complete-4.sh` (Phase 4 + full workflow)
- **Verify**: All test scripts pass
- **Verify**: Scripts reference correct phases from implementation doc

**Character Consistency Summary**: All phases (1-7) complete and working

**Known**: Full workflow implemented - image interrogation → character generation → image-to-video → consistent clips across all 6 clips.

---

## Beat Sync Foundation

**Goal**: Verify all Beat Sync phases (3.1, 3.2, 3.3) are working correctly.

**Time**: 20-30 min

### Phase 3.1: Prompt Engineering ✅ COMPLETE

**5.1 Beat Detection & BPM Calculation**

- Complete analysis
- Verify: `beat_times` array populated in database, `bpm` calculated and stored
- Verify: Backend logs show beat detection completion

**5.2 API-Specific Prompt Optimization**

- Generate clips for short-form video
- Verify: Backend logs show prompt optimization for Minimax Hailuo 2.3:
  - Prompts include BPM information
  - Motion descriptors added (bouncing, pulsing, rotating, etc.)
  - API-specific formatting applied
- Check logs for: `optimize_prompt_for_api` calls

**5.3 Motion Type Selection**

- Generate clips with different genres/moods
- Verify: Backend logs show motion type selection based on:
  - Scene context (chorus, verse, bridge)
  - Mood (energetic, calm, melancholic)
  - Genre (electronic, dance, rock, etc.)
  - BPM (slow, medium, fast, very fast)
- Verify: Appropriate motion types selected (bouncing, pulsing, rotating, stepping, looping)

**5.4 BPM Extraction from Prompts**

- Generate clips with prompts containing BPM references
- Verify: BPM extracted correctly from prompts like "128 BPM", "120BPM"
- Verify: Extracted BPM used for prompt optimization

### Phase 3.2: Audio-Reactive FFmpeg Filters ✅ COMPLETE

**5.5 Frame-Accurate Beat Time Conversion**

- Compose final video
- Verify: Backend logs show `convert_beat_times_to_frames()` called
- Verify: Beat times converted to frame indices with correct FPS

**5.6 Beat Filter Generation**

- Compose final video
- Verify: Backend logs show beat filter expressions generated:
  - `generate_beat_filter_expression()` called with beat_times
  - Filter type selected (flash, color_burst, zoom_pulse, brightness_pulse, glitch)
- Verify: Beat times passed to `concatenate_clips()` function

**5.7 Glitch Effect Filter**

- Compose final video with glitch effect enabled
- Verify: Backend logs show glitch filter generation
- Verify: RGB channel shift filter applied (check FFmpeg filter string)
- Verify: Visual glitch effect appears on beats in final video

**5.8 Effect Parameter Customization**

- Check `backend/app/core/config.py` for `BeatEffectConfig`
- Verify: Environment variables available for effect customization:
  - `BEAT_EFFECT_TYPE` (flash, color_burst, zoom_pulse, glitch, brightness_pulse)
  - `BEAT_FLASH_INTENSITY`, `BEAT_FLASH_COLOR`
  - `BEAT_GLITCH_INTENSITY`
  - `BEAT_ZOOM_PULSE_AMOUNT`
  - `BEAT_COLOR_BURST_SATURATION`, `BEAT_COLOR_BURST_BRIGHTNESS`
- Verify: Default values used if not set

**5.9 Visual Beat Effects in Final Video**

- Compose final video
- Verify: Visual effects trigger on beats (flash, color burst, zoom pulse, etc.)
- Verify: Effects are frame-accurate (within ±20ms of beat timestamps)
- Verify: Effects visible in final composed video

### Phase 3.3: Structural Sync ✅ COMPLETE

**5.10 Beat-Aligned Boundary Calculation**

- Generate clips and compose final video
- Verify: Backend logs show `calculate_beat_aligned_clip_boundaries()` called
- Verify: Boundaries calculated with:
  - Minimum/maximum duration constraints (3-6 seconds)
  - Beat alignment for start/end times
  - Frame-accurate alignment

**5.11 User Selection Support (30-Second Clips)**

- Upload audio, select "Short Form", make 30-second selection
- Generate clips and compose
- Verify: Backend logs show user selection start/end times used
- Verify: `calculate_beat_aligned_clip_boundaries()` called with:
  - `user_selection_start` and `user_selection_end` parameters
  - Boundaries calculated within selection range
- Verify: Clips aligned to beats within selected segment

**5.12 Clip Trimming to Beat Boundaries**

- Compose final video
- Verify: Backend logs show `trim_clip_to_beat_boundary()` called when needed
- Verify: Clips trimmed to align with beat-aligned start/end times
- Verify: FFmpeg trim filter applied correctly

**5.13 Clip Extension to Beat Boundaries**

- Compose final video with clips shorter than beat boundaries
- Verify: Backend logs show `extend_clip_to_beat_boundary()` called
- Verify: Clips extended using frame freeze (tpad) and fadeout
- Verify: Extended clips align with beat boundaries

**5.14 Transition Verification**

- Compose final video
- Verify: Backend logs show `verify_beat_aligned_transitions()` called
- Verify: All transitions verified to be within ±50ms of beat boundaries
- Verify: Transition errors logged if any exceed tolerance

**5.15 Beat-Aligned Clip Transitions**

- Compose final video
- Verify: All clip transitions occur on beat boundaries
- Verify: Transitions are smooth and rhythmically correct
- Verify: No jarring cuts between beats
- Verify: Final video has strong beat synchronization perception

**Beat Sync Summary**: All checkpoints pass

**Known**: All three phases (3.1, 3.2, 3.3) are complete and integrated.

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
- Verify: If beat_times is empty, beat filters skip but composition still works

### 6. Beat Sync with Very Fast/Slow Tempo

- Upload audio with very fast BPM (> 160) or very slow BPM (< 60)
- Complete analysis and generate clips
- Verify: Appropriate motion types selected (pulsing for fast, looping for slow)
- Verify: Beat filters work correctly with extreme tempos
- Verify: Beat-aligned boundaries calculated correctly

### 7. Beat Sync with Sparse Beats

- Upload audio with irregular or sparse beat detection
- Complete analysis and generate clips
- Verify: Beat-aligned boundaries handle sparse beats gracefully
- Verify: Clips still transition on available beats
- Verify: No errors from missing beat data

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
