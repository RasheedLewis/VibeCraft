# Testing Checklist - All Features Built Today

This checklist helps you systematically test all features implemented in this branch.

## ✅ Pre-Testing Setup

**What You Need First:**

1. **Backend running**: Open terminal, go to `backend` folder, run:

   ```bash
   source venv/bin/activate
   python -m uvicorn app.main:app --reload
   ```

   Wait until you see "Uvicorn running on <http://127.0.0.1:8000>"

2. **Worker running**: In another terminal, go to `backend` folder, run:

   ```bash
   source venv/bin/activate
   rq worker ai_music_video
   ```

3. **Frontend running**: Open another terminal, go to `frontend` folder, run:

   ```bash
   npm run dev
   ```

   Wait until you see the frontend URL (usually <http://localhost:5173>)

4. **Test audio file**: Have an audio file ready (30-60 seconds is good, with clear beats - electronic/hip-hop work best)

5. **Browser**: Open <http://localhost:5173> in your browser

**Or use `make start` to start all services at once.**

---

## 🔐 Feature 1: Authentication System

**Location:** Frontend `/login` page, Backend `/api/v1/auth/*`

### Test Registration

- [ ] Navigate to app (should redirect to `/login` if not authenticated)
- [ ] Click "Register" or toggle to registration mode
- [ ] Enter email: `test@example.com`
- [ ] Enter password: `password`
- [ ] Optionally enter display name: `Test User`
- [ ] Click "Register"
- [ ] **Expected:** Automatically logs in and redirects to upload page (`/`), user is logged in

### Test Login

- [ ] Click "Logout" button (in projects modal)
- [ ] Should redirect to `/login`
- [ ] Enter email: `test@example.com` and password: `password`
- [ ] Click "Login"
- [ ] **Expected:** Redirects to upload page (`/`)

### Test Protected Routes

- [ ] While logged out, try to access `/` or `/projects` directly
- [ ] **Expected:** Redirects to `/login`

**Status:** ✅ Passed

---

## 📁 Feature 2: Project Listing (Max 5)

**Location:** Frontend projects modal (click 😊 button), Backend `/api/v1/songs/` (GET)

### Test Empty State

- [ ] After login, click the 😊 profile button (top-right)
- [ ] **Expected:** Projects modal opens
- [ ] **Expected:** Shows "No projects yet. Create your first one!" message
- [ ] **Expected:** "Create New" button visible (only one, at top)

### Test Project Creation & Listing

- [ ] Create 1 project (upload a song, complete flow)
- [ ] Click 😊 profile button to open projects modal
- [ ] **Expected:** Project appears in list with title, filename, duration
- [ ] Create 2 more projects (total 3)
- [ ] **Expected:** All 3 projects visible in modal

### Test 5-Project Limit

- [ ] Create 2 more projects (total 5)
- [ ] **Expected:** All 5 projects visible
- [ ] Try to create 6th project
- [ ] **Expected:** Error message: "sorry create a new account, limit of 5 reached"
- [ ] **Expected:** Warning banner on projects page: "You've reached the maximum of 5 projects"

### Test Project Navigation

- [ ] Click on a project card in the modal
- [ ] **Expected:** Modal closes
- [ ] **Expected:** Navigates to upload page with `?songId=...` in URL
- [ ] **Expected:** Project state loads correctly

**Status:** ✅ Passed

---

## 💾 Feature 3: State Persistence

**Location:** Frontend `UploadPage.tsx`, URL parameter `?songId=...`

**Note:** Original intention was not to require songId to persist in URL/localStorage, but now that we have a project list modal, we can recover state by selecting projects from the list. The project list serves as the primary way to resume work on existing projects.

### Test Page Refresh

- [ ] Upload a song and complete some steps (e.g., select video type, start analysis)
- [ ] Note the `songId` in URL (e.g., `?songId=abc-123`)
- [ ] Refresh the page (F5 or Cmd+R)
- [ ] **Expected:** Same song loads, same stage, URL still has `songId` parameter
- [ ] **Expected:** Can continue where you left off

### Test Project List Recovery

- [ ] Upload a song and complete some steps
- [ ] Close the browser tab or navigate away
- [ ] Open the app again and click the profile button
- [ ] **Expected:** Project appears in the projects modal
- [ ] Click on the project
- [ ] **Expected:** Project state loads correctly from the project list

**Status:** ✅ Passed

---

## 📏 Feature 4: File Size Validation

**Location:** Backend `/api/v1/songs/upload`, `MAX_AUDIO_FILE_SIZE_MB = 100`

### Test Normal File

- [x] Upload a normal-sized audio file (< 100MB)
- [x] **Expected:** Upload succeeds

### Test Large File

- [x] Try to upload a file > 100MB (or create a dummy large file)
- [x] **Expected:** Error message: "Audio file size (X.XMB) exceeds maximum (100MB)"
- [x] **Expected:** Upload is rejected

**Status:** ✅ Passed

---

## 📝 Feature 5: Prompt Visibility & Logging

**Location:** Backend worker logs, Frontend clip info button

### Test Backend Logging

- [ ] Generate clips for a song
- [ ] Check backend worker logs (terminal where worker is running)
- [ ] Look for log messages:
  - `[VIDEO-GEN] FULL PROMPT (optimized): ...`
  - `[VIDEO-GEN] FULL PROMPT (original): ...`
  - `[PROMPT-ENHANCE] FULL ENHANCED PROMPT: ...`
- [ ] **Expected:** Full prompts are logged (not truncated)

### Test Frontend UI

- [ ] After clips are generated, hover over a completed clip card
- [ ] **Expected:** Info button (ⓘ) appears
- [ ] Click the info button
- [ ] **Expected:** Modal opens showing:
  - Full generated prompt
  - Model used
  - Pretty JSON formatting

### Test Prompt Logging to File

- [ ] Generate clips for a song
- [ ] Check `video-api-testing/prompts.log` file
- [ ] **Expected:** Each clip generation logs a JSON line with:
  - `prompt`: Full optimized prompt
  - `songId`: Song UUID
  - `clipId`: Clip UUID
  - `optimized`: true

**Status:** ✅ Passed

---

## 🎵 Feature 6: BPM-Aware Prompting

**Location:** Backend `prompt_enhancement.py`

### Test Slow Song (60-80 BPM)

- [ ] Upload a slow song (60-80 BPM)
- [ ] Generate clips
- [ ] Check prompt logs
- [ ] **Expected:** Prompts include "slow, flowing" motion descriptors
- [ ] **Expected:** Rhythmic phrases mention BPM

### Test Medium Song (100-120 BPM)

- [ ] Upload a medium tempo song
- [ ] Generate clips
- [ ] Check prompt logs
- [ ] **Expected:** Prompts include "steady, moderate" motion descriptors

### Test Fast Song (140+ BPM)

- [ ] Upload a fast song (140+ BPM)
- [ ] Generate clips
- [ ] Check prompt logs
- [ ] **Expected:** Prompts include "energetic, driving" motion descriptors

**Status:** ✅ Passed

---

## 💃 Feature 7: Improved Dancing Prompts

**Location:** Backend `prompt_enhancement.py`, `scene_planner.py`

### Test Dance Genre

- [ ] Upload a dance/hip-hop/pop song
- [ ] Generate clips
- [ ] Check prompt logs
- [ ] **Expected:** Motion type is "dancing"
- [ ] **Expected:** Prompts include dancing descriptors
- [ ] Watch generated clips
- [ ] **Expected:** Character shows more dancing motion (more active/dynamic)

**Status:** ✅ Passed

---

## 🎭 Feature 8: Character Consistency

**Location:** Backend `character_consistency.py`, `video_generation.py`

### Test Template Character

- [ ] Upload a song and complete analysis
- [ ] Select "Short Form" video type
- [ ] Choose a template character (see both poses displayed)
- [ ] Generate clips
- [ ] **Expected:** Same character appears in all clips
- [ ] **Expected:** Character matches template image
- [ ] **Expected:** Character performs actions from prompts (not just static)

### Test Custom Image Upload

- [ ] Upload a custom character image
- [ ] Generate clips
- [ ] **Expected:** Character matches your uploaded image
- [ ] **Expected:** Character appears consistently across clips
- [ ] Check backend logs for: `[VIDEO-GEN] Using reference image: <url>`
- [ ] **Expected:** Both image AND text prompt are used together

**Status:** ✅ Passed

---

## ⚡ Feature 9: Increased Concurrency

**Location:** Backend `routes_songs.py`, `DEFAULT_MAX_CONCURRENCY = 4`

### Test Parallel Generation

- [ ] Generate clips for a song (should generate 6-8 clips)
- [ ] Observe clip generation progress
- [ ] **Expected:** Multiple clips generate simultaneously
- [ ] **Expected:** Up to 4 clips can be processing at once
- [ ] **Expected:** Overall generation time is reduced compared to 2 concurrent

**Status:** ✅ Passed

---

## 🎨 Feature 10: Beat-Sync Visual Effects

**Location:** Backend `video_composition.py`, `beat_filter_applicator.py`

### Test Normal Mode

- [ ] Complete a full video generation (upload → analyze → generate clips → compose)
- [ ] Use an audio file with clear, strong beats (electronic/hip-hop)
- [ ] Watch the final composed video
- [ ] **Expected:** Visual effects trigger at precise beat moments
- [ ] **Expected:** Effects are visible throughout entire video (not just first 50 beats)
- [ ] **Expected:** Effects align with music rhythm

### Test with Test Mode (Exaggerated Effects)

- [ ] Set environment variable: `BEAT_EFFECT_TEST_MODE=true make start` (or `export BEAT_EFFECT_TEST_MODE=true` then restart backend/worker)
- [ ] Generate a new video
- [ ] **Expected:** Effects are more visible/exaggerated (3x intensity, 3x tolerance duration)
- [ ] **Expected:** Logs show: `[TEST MODE] Exaggerating flash effect`
- [ ] **Note:** Test mode makes effects easier to observe for verification

### Test Effect Types

**1. Flash Effect (Default)**

- **What to look for:** Brief white/bright flashes on each beat
- **How to verify:** Watch video frame-by-frame, flashes should occur at beat moments
- **Test mode:** Flashes are 3x brighter and last 150ms (vs normal 50ms)

**2. Color Burst**

- **What to look for:** Sudden increase in color saturation and brightness on beats
- **How to verify:** Colors should "pop" more intensely at beat moments
- **Test mode:** Saturation and brightness are 1.5-2x stronger

**3. Zoom Pulse**

- **What to look for:** Subtle zoom-in effect on beats
- **How to verify:** Video should slightly zoom in at beat moments
- **Test mode:** Zoom is 1.15x (vs normal 1.05x)

**4. Brightness Pulse**

- **What to look for:** Overall brightness increase on beats
- **How to verify:** Video should get brighter at beat moments
- **Test mode:** Brightness increase is 2x stronger

**5. Glitch Effect**

- **What to look for:** Digital glitch effect with RGB channel shift on beats
- **How to verify:** Red/blue channel separation visible at beat moments
- **Test mode:** Glitch intensity is 2x stronger

**Status:** ✅ Passed

---

## 💰 Feature 11: Cost Tracking

**Location:** Backend `cost_tracking.py`, `Song.total_generation_cost_usd`

### Test Cost Calculation

- [ ] Generate a complete video (upload → analyze → generate clips → compose)
- [ ] Check database or API response for `total_generation_cost_usd` field
- [ ] **Expected:** Cost is calculated per clip generation
- [ ] **Expected:** Total cost is accumulated for the song
- [ ] **Expected:** Cost is stored in database
- [ ] Check backend logs for: `[COST-TRACKING] Stored cost $X.XXXX for song ...`

**Note:** Cost is stored but not displayed in UI yet (backend only).

**Status:** ⚠️ Needs Investigation

- **Issue:** Cost tracking logs not appearing during successful composition
- **Bug Found:** `song.id` was used instead of `song_id` in `clip_generation.py` line 289, causing NameError when song retrieval failed
- **Fix Applied:** Changed to use `song_id` directly and added error handling
- **Action Needed:** Re-test after fix to verify cost tracking logs appear

---

## 🚦 Feature 12: Rate Limiting

**Location:** Backend `rate_limiting.py`, middleware

### Test Rate Limits

- [ ] Make many rapid API requests (refresh projects page many times quickly)
- [ ] Or use browser console to make many fetch requests:

  ```javascript
  for(let i=0; i<70; i++) {
    fetch('http://localhost:8000/api/v1/songs/', {
      headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
    })
  }
  ```

- [ ] **Expected:** After many requests, might see 429 (Too Many Requests) error
- [ ] **Expected:** Limits are generous (60/min, 1000/hour, 10000/day) for normal use

### Test Health Check Exemption

- [ ] Make many requests to `/api/v1/health/healthz`
- [ ] **Expected:** Health check should NOT be rate limited (always returns 200)

**Status:** ✅ Passed

---

## 🔧 Feature 13: Rapid Iteration Testing Script

**Location:** `video-api-testing/test_rapid_iteration.py`

### Test Script

- [ ] Navigate to `video-api-testing` directory
- [ ] Run: `python test_rapid_iteration.py`
- [ ] **Expected:** Interactive script starts
- [ ] Press ENTER to generate a video
- [ ] **Expected:** 4-second video generates
- [ ] Type `prompt <text>` to change prompt
- [ ] **Expected:** Prompt updates
- [ ] Type `model <name>` to change model
- [ ] **Expected:** Model updates
- [ ] Type `show` to see current settings
- [ ] **Expected:** Settings displayed
- [ ] Check `rapid_iteration.log` file
- [ ] **Expected:** Full prompts are logged for each iteration

**Status:** ✅ Passed

---

## 🎬 Full End-to-End Regression Test

**Test the complete flow to ensure nothing broke:**

1. [ ] **Login/Register** (if not already logged in)
2. [ ] **Upload audio file**
3. [ ] **Select video type** (Short Form or Full Length)
4. [ ] **Start analysis** (wait 3-5 minutes)
5. [ ] **Select audio range** (if Short Form)
6. [ ] **Choose character** (template or custom image)
7. [ ] **Generate clips** (wait 5-10 minutes)
   - [ ] Check prompt visibility in UI (info button on clips)
   - [ ] Verify multiple clips generate in parallel (up to 4)
8. [ ] **Compose video** (wait 3-5 minutes)
   - [ ] Watch final video
   - [ ] Verify beat-sync effects throughout
   - [ ] Verify character consistency
9. [ ] **Check projects page:**
   - [ ] Project should appear in list
   - [ ] Can click to reopen it
10. [ ] **Refresh page:**
    - [ ] State should persist
    - [ ] Can continue where you left off

**Status:** ✅ Passed

---

## 📊 Test Summary

After completing all tests, fill in this summary:

**Total Features Tested:** ___ / 13

**Passed:** ___
**Failed:**___
**Warnings:** ___

**Critical Issues Found:**
1.
2.
3.

**Notes:**
-

-
-

---

## 🐛 Troubleshooting

### Backend not responding

- Check backend is running: `ps aux | grep uvicorn`
- Check logs for errors
- Try restarting backend

### Frontend not loading

- Check frontend is running: `ps aux | grep vite`
- Check browser console for errors
- Try clearing browser cache

### Effects not visible

- Enable test mode: `export BEAT_EFFECT_TEST_MODE=true` and restart backend
- Use audio with clear beats (electronic/hip-hop)
- Watch the final composed video (not individual clips)

### Character doesn't match

- **Check:** Did you select a character before generating clips?
- **Check:** Backend logs show "Using reference image: <url>"?
- **Try:** Use a clear, high-quality character image
- **Check:** Both image AND text prompt are used together (not replacement)

### Prompts not visible in UI

- **Check:** Clips must be completed (not just queued)
- **Try:** Hover over completed clip card, click info button (ⓘ)
- **Check:** Browser console for errors

### Can't see projects

- **Check:** Are you logged in?
- **Try:** Create a new project first, then check projects page
- **Check:** Browser console for API errors

---

## 🎯 Quick Test Summary

After testing, you should be able to verify:

**Beat-Sync Effects:**

- [ ] Flash effects visible on beats throughout video
- [ ] Effects work for entire duration (not just first 50 beats)
- [ ] Test mode makes effects more visible

**Character Consistency:**

- [ ] Character matches reference image
- [ ] Character appears consistently across clips
- [ ] Both image and prompt are used together

**Prompt Visibility:**

- [ ] Prompts logged in worker logs
- [ ] Prompts visible in UI via info button
- [ ] Prompts logged to `video-api-testing/prompts.log`
- [ ] BPM-aware descriptors in prompts

**Authentication:**

- [ ] Can register and login
- [ ] Protected routes require authentication
- [ ] Projects page shows user's songs (max 5)

**State & UX:**

- [ ] Page refresh maintains state
- [ ] Can navigate between projects
- [ ] File size validation works

**Performance:**

- [ ] Multiple clips generate in parallel (up to 4)
- [ ] Overall generation time improved

---

**Last Updated:** Based on Saturday Plan implementation
**Related Docs:**

- `TEST_FEATURES_8_11.md` - Combined testing guide for features 8-11
- `Saturday-Plan.md` - Implementation plan
- `BEAT-SYNC-IMPLEMENTATION-PLAN.md` - Beat-sync effects details
