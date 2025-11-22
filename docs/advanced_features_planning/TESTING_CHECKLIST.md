# Testing Checklist - All Features Built Today

This checklist helps you systematically test all features implemented in this branch.

## ✅ Pre-Testing Setup

- [ ] Backend is running (`cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload`)
- [ ] Frontend is running (`cd frontend && npm run dev`)
- [ ] Browser open at `http://localhost:5173`
- [ ] Have a test audio file ready (30-60 seconds, with clear beats - electronic/hip-hop work best)

---

## 🔐 Feature 1: Authentication System

**Location:** Frontend `/login` page, Backend `/api/v1/auth/*`

### Test Registration
- [ ] Navigate to app (should redirect to `/login` if not authenticated)
- [ ] Click "Register" or toggle to registration mode
- [ ] Enter email: `test@example.com`
- [ ] Enter password: `testpassword123`
- [ ] Optionally enter display name: `Test User`
- [ ] Click "Register"
- [ ] **Expected:** Redirects to `/projects` page, user is logged in

### Test Login
- [ ] Click "Logout" button (if visible)
- [ ] Should redirect to `/login`
- [ ] Enter same email and password
- [ ] Click "Login"
- [ ] **Expected:** Redirects to `/projects` page

### Test Protected Routes
- [ ] While logged out, try to access `/` or `/projects` directly
- [ ] **Expected:** Redirects to `/login`

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

---

## 📁 Feature 2: Project Listing (Max 5)

**Location:** Frontend `/projects` page, Backend `/api/v1/songs/` (GET)

### Test Empty State
- [ ] After login, view `/projects` page
- [ ] **Expected:** Shows "No projects yet. Create your first one!" message
- [ ] **Expected:** "Create New" button visible

### Test Project Creation & Listing
- [ ] Create 1 project (upload a song, complete flow)
- [ ] Go to `/projects` page
- [ ] **Expected:** Project appears in list with title, filename, duration
- [ ] Create 2 more projects (total 3)
- [ ] **Expected:** All 3 projects visible

### Test 5-Project Limit
- [ ] Create 2 more projects (total 5)
- [ ] **Expected:** All 5 projects visible
- [ ] Try to create 6th project
- [ ] **Expected:** Error message: "sorry create a new account, limit of 5 reached"
- [ ] **Expected:** Warning banner on projects page: "You've reached the maximum of 5 projects"

### Test Project Navigation
- [ ] Click on a project card
- [ ] **Expected:** Navigates to upload page with `?songId=...` in URL
- [ ] **Expected:** Project state loads correctly

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

---

## 💾 Feature 3: State Persistence

**Location:** Frontend `UploadPage.tsx`, localStorage key: `vibecraft_current_song_id`

### Test Page Refresh
- [ ] Upload a song and complete some steps (e.g., select video type, start analysis)
- [ ] Note the `songId` in URL (e.g., `?songId=abc-123`)
- [ ] Refresh the page (F5 or Cmd+R)
- [ ] **Expected:** Same song loads, same stage, URL still has `songId` parameter
- [ ] **Expected:** Can continue where you left off

### Test localStorage
- [ ] Open browser DevTools → Application → Local Storage
- [ ] Look for `vibecraft_current_song_id`
- [ ] **Expected:** Contains the current song ID
- [ ] Navigate to different project
- [ ] **Expected:** `vibecraft_current_song_id` updates

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

---

## 📏 Feature 4: File Size Validation

**Location:** Backend `/api/v1/songs/upload`, `MAX_AUDIO_FILE_SIZE_MB = 100`

### Test Normal File
- [ ] Upload a normal-sized audio file (< 100MB)
- [ ] **Expected:** Upload succeeds

### Test Large File
- [ ] Try to upload a file > 100MB (or create a dummy large file)
- [ ] **Expected:** Error message: "Audio file size (X.XMB) exceeds maximum (100MB)"
- [ ] **Expected:** Upload is rejected

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

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

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

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

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

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

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

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

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

---

## ⚡ Feature 9: Increased Concurrency

**Location:** Backend `routes_songs.py`, `DEFAULT_MAX_CONCURRENCY = 4`

### Test Parallel Generation
- [ ] Generate clips for a song (should generate 6-8 clips)
- [ ] Observe clip generation progress
- [ ] **Expected:** Multiple clips generate simultaneously
- [ ] **Expected:** Up to 4 clips can be processing at once
- [ ] **Expected:** Overall generation time is reduced compared to 2 concurrent

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

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
- [ ] Set environment variable: `export BEAT_EFFECT_TEST_MODE=true`
- [ ] Restart backend
- [ ] Generate a new video
- [ ] **Expected:** Effects are more visible/exaggerated
- [ ] **Expected:** Logs show: `[TEST MODE] Exaggerating flash effect`

### Test Effect Types
- [ ] Flash Effect: Brief white/bright flashes on beats
- [ ] Color Burst: Sudden increase in color saturation on beats
- [ ] Zoom Pulse: Subtle zoom-in effect on beats
- [ ] Brightness Pulse: Overall brightness increase on beats
- [ ] Glitch Effect: Digital glitch with RGB channel shift on beats

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

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

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

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

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

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

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

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

**Status:** ⬜ Not Started | 🟡 In Progress | ✅ Passed | ❌ Failed

---

## 📊 Test Summary

After completing all tests, fill in this summary:

**Total Features Tested:** ___ / 13

**Passed:** ___
**Failed:** ___
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
- Check backend logs for "Using reference image: <url>"
- Verify character was selected before generating clips
- Use high-quality character image

---

**Last Updated:** Based on Saturday Plan implementation
**Related Docs:**
- `Gentle_Testing_Guide.md` - Detailed testing procedures
- `Saturday-Plan.md` - Implementation plan
- `BEAT-SYNC-IMPLEMENTATION-PLAN.md` - Beat-sync effects details

