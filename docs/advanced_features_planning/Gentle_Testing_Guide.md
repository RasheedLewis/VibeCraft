# Gentle Testing Guide - All New Features

A comprehensive guide to test all the new features and improvements added in this branch.

---

## What You Need First

1. **Backend running**: Open terminal, go to `backend` folder, run:

   ```bash
   source venv/bin/activate
   python -m uvicorn app.main:app --reload
   ```

   Wait until you see "Uvicorn running on <http://127.0.0.1:8000>"

2. **Frontend running**: Open another terminal, go to `frontend` folder, run:

   ```bash
   npm run dev
   ```

   Wait until you see the frontend URL (usually <http://localhost:5173>)

3. **Test audio file**: Have an audio file ready (30-60 seconds is good, with clear beats)

4. **Browser**: Open <http://localhost:5173> in your browser

---

## 🎨 Feature 1: Beat-Sync Visual Effects (15-20 minutes)

**What was added:** Five types of visual effects that sync to musical beats: flash,
color_burst, zoom_pulse, brightness_pulse, and glitch.

### Testing Beat-Sync Effects

**Prerequisites:**

- Complete a full video generation (upload → analyze → generate clips → compose)
- Use an audio file with clear, strong beats (electronic, hip-hop, or pop work well)

**Steps:**

1. **Generate a complete video** (follow full E2E flow below)
2. **Watch the final composed video**
3. **Observe visual effects on beats:**
   - Effects should trigger at precise beat moments
   - Effects should be visible throughout the entire video (not just first 50 beats)
   - Effects should align with the music rhythm

### Testing Individual Effect Types

**To test specific effects, you can enable test mode:**

1. **Set test mode environment variable:**

   ```bash
   export BEAT_EFFECT_TEST_MODE=true
   ```

   (This exaggerates effects for easier observation)

2. **Restart backend** with test mode enabled

3. **Generate a video** and observe the exaggerated effects

**Effect Types to Observe:**

#### 1. Flash Effect (Default)

- **What to look for:** Brief white/bright flashes on each beat
- **How to verify:** Watch video frame-by-frame, flashes should occur at beat moments
- **Test mode:** Flashes are 3x brighter and last 150ms (vs normal 50ms)

#### 2. Color Burst

- **What to look for:** Sudden increase in color saturation and brightness on beats
- **How to verify:** Colors should "pop" more intensely at beat moments
- **Test mode:** Saturation and brightness are 1.5-2x stronger

#### 3. Zoom Pulse

- **What to look for:** Subtle zoom-in effect on beats
- **How to verify:** Video should slightly zoom in at beat moments
- **Test mode:** Zoom is 1.15x (vs normal 1.05x)

#### 4. Brightness Pulse

- **What to look for:** Overall brightness increase on beats
- **How to verify:** Video should get brighter at beat moments
- **Test mode:** Brightness increase is 2x stronger

#### 5. Glitch Effect

- **What to look for:** Digital glitch effect with RGB channel shift on beats
- **How to verify:** Red/blue channel separation visible at beat moments
- **Test mode:** Glitch intensity is 2x stronger

**Verification Checklist:**

- [ ] Effects trigger on beats (not randomly)
- [ ] Effects work for entire video duration (not just first 50 beats)
- [ ] Effects are synchronized with music rhythm
- [ ] Test mode makes effects more visible for verification

---

## 🎭 Feature 2: Character Consistency Improvements (10 minutes)

**What was added:** Verified and improved that both reference image AND text prompt
are used together (not replacement).

### Testing Character Consistency

**Steps:**

1. **Upload a song** and complete analysis
2. **Select "Short Form"** video type
3. **Choose a character:**
   - Option A: Select a template character (see both poses displayed)
   - Option B: Upload a custom character image
4. **Generate clips** (wait 5-10 minutes)
5. **Observe character consistency:**
   - Same character should appear in all clips
   - Character should match your reference image
   - Character should perform actions described in prompts

**What to verify:**

- [ ] Character looks consistent across all clips
- [ ] Character matches reference image (template or custom)
- [ ] Character performs actions from prompts (not just static image)
- [ ] Both image and prompt are used together (character + motion)

**Check logs:** Look for these log messages in backend:

- `[VIDEO-GEN] Using reference image: <url>`
- `[VIDEO-GEN] FULL PROMPT (optimized): <prompt>`
- `[VIDEO-GEN] FULL PROMPT (original): <prompt>`

---

## 📝 Feature 3: Prompt Visibility & Logging (5 minutes)

**What was added:** Full prompts are now logged for rapid iteration and debugging.

### Testing Prompt Logging

**Steps:**

1. **Generate clips** for a song
2. **Check backend worker logs** (terminal where worker is running)
3. **Look for prompt logs:**
   - `[VIDEO-GEN] FULL PROMPT (optimized): ...`
   - `[VIDEO-GEN] FULL PROMPT (original): ...`
   - `[PROMPT-ENHANCE] FULL ENHANCED PROMPT: ...`

**Frontend Prompt Visibility:**

1. **After clips are generated**, hover over a completed clip card
2. **Click the info button** (ⓘ) that appears
3. **View prompt modal:**
   - Shows full generated prompt
   - Shows model used
   - Pretty JSON formatting

**What to verify:**

- [ ] Prompts are logged in worker logs
- [ ] Prompts are visible in UI via info button
- [ ] Both optimized and original prompts are logged
- [ ] Enhanced prompts include BPM-aware descriptors

---

## 🎵 Feature 4: BPM-Aware Prompting (5 minutes)

**What was added:** Enhanced prompts with tempo descriptors (slow/flowing,
energetic/driving) based on BPM.

### Testing BPM-Aware Prompts

**Steps:**

1. **Upload songs with different BPMs:**
   - Slow song (60-80 BPM)
   - Medium song (100-120 BPM)
   - Fast song (140+ BPM)
2. **Generate clips** for each
3. **Check prompt logs** for tempo descriptors:
   - Slow songs: "slow, flowing" motion
   - Medium songs: "steady, moderate" motion
   - Fast songs: "energetic, driving" motion

**What to verify:**

- [ ] Prompts include tempo-appropriate descriptors
- [ ] Slow songs get "slow, flowing" descriptors
- [ ] Fast songs get "energetic, driving" descriptors
- [ ] Rhythmic phrases mention BPM explicitly

---

## 💃 Feature 5: Improved Dancing Prompts (5 minutes)

**What was added:** Motion type selection prioritizes "dancing" for dance-related genres/moods.

### Testing Dancing Prompts

**Steps:**

1. **Upload a dance/hip-hop/pop song** (genres that should trigger dancing)
2. **Generate clips**
3. **Check prompt logs** for "dancing" motion type
4. **Observe generated clips:**
   - Should show more dancing motion
   - Character should be more active/dynamic

**What to verify:**

- [ ] Dance-related genres trigger "dancing" motion type
- [ ] Prompts include dancing descriptors
- [ ] Generated videos show more dancing motion

---

## 💾 Feature 6: State Persistence (2 minutes)

**What was added:** Page refresh maintains current project state using localStorage.

### Testing State Persistence

**Steps:**

1. **Upload a song** and complete some steps (e.g., select video type, start analysis)
2. **Note the song ID** in the URL (e.g., `?songId=...`)
3. **Refresh the page** (F5 or Cmd+R)
4. **Verify state persists:**
   - Should still show the same song
   - Should still be on the same stage
   - URL should still have songId parameter

**What to verify:**

- [ ] Page refresh doesn't lose progress
- [ ] Song state is restored from localStorage
- [ ] Can continue where you left off

---

## 🔐 Feature 7: Authentication System (5 minutes)

**What was added:** JWT-based authentication with user registration, login, and protected routes.

### Testing Authentication

**Steps:**

1. **Go to the app** - Should redirect to `/login` if not authenticated
2. **Register a new account:**
   - Enter email (e.g., `test@example.com`)
   - Enter password
   - Optionally enter display name
   - Click "Register"
   - Should redirect to `/projects` page
3. **Logout:**
   - Click "Logout" button
   - Should redirect back to `/login`
4. **Login:**
   - Enter the same email and password
   - Click "Login"
   - Should redirect to `/projects` page

**What to verify:**

- [ ] Registration creates account and logs in automatically
- [ ] Login works with correct credentials
- [ ] Logout clears session and redirects to login
- [ ] Protected routes redirect to login if not authenticated

---

## 📁 Feature 8: Project Listing (5 minutes)

**What was added:** Projects page listing user's songs (max 5 most recent).

### Testing Project Listing

**Steps:**

1. **View projects page:**
   - After login, you should see `/projects` page
   - If you have no projects, you'll see "No projects yet" message
2. **Create multiple projects:**
   - Upload 2-3 songs
   - Complete the flow for each (or just upload)
3. **Check projects page:**
   - Should show your songs (max 5 most recent)
   - Each project shows title, filename, duration
   - If video is composed, shows "✓ Video composed"
4. **Test project limit:**
   - Create 6+ projects
   - Projects page should show only 5 most recent
   - Warning message appears about 5-project limit

**What to verify:**

- [ ] Projects page lists your songs (max 5)
- [ ] Each project shows correct metadata
- [ ] Clicking a project opens it
- [ ] "Create New" navigates to upload page
- [ ] 5-project limit is enforced

---

## 💰 Feature 9: Cost Tracking (2 minutes)

**What was added:** Per-video cost estimation and storage in database.

### Testing Cost Tracking

**Steps:**

1. **Generate a complete video** (upload → analyze → generate clips → compose)
2. **Check database** (or API response) for `total_generation_cost_usd` field
3. **Verify cost is stored:**
   - Cost should be calculated per clip
   - Total cost should be accumulated for the song
   - Cost should be stored in database

**What to verify:**

- [ ] Cost is calculated for each clip generation
- [ ] Total cost is stored in song record
- [ ] Cost includes character consistency premium (if applicable)

**Note:** Cost is stored but not displayed in UI yet (backend only).

---

## ⚡ Feature 11: Increased Concurrency (5 minutes)

**What was added:** Increased clip generation concurrency from 2 to 4.

### Testing Concurrency

**Steps:**

1. **Generate clips** for a song (should generate 6-8 clips)
2. **Observe clip generation:**
   - Multiple clips should generate simultaneously
   - Up to 4 clips can be generating at once
   - Clips should complete faster than before

**What to verify:**

- [ ] Multiple clips generate in parallel
- [ ] Up to 4 clips can be processing simultaneously
- [ ] Overall generation time is reduced

---

## 🚦 Feature 12: Rate Limiting (Optional - 2 minutes)

**What was added:** Rate limiting middleware with per-user and per-IP limits.

### Testing Rate Limiting

**Steps:**

1. **Make many rapid API requests:**
   - Refresh projects page many times quickly
   - Or use browser console to make many fetch requests
2. **Check for rate limit:**
   - After many requests, you might see a 429 (Too Many Requests) error
   - This is expected behavior

**What to verify:**

- [ ] Rate limiting works (may not be easily testable without automation)
- [ ] Health check endpoints (`/healthz`) are not rate limited
- [ ] Limits are generous (60/min, 1000/hour, 10000/day) for normal use

**Note:** Rate limiting has generous limits, so you may not hit them during normal testing.

---

## 🔧 Feature 13: Rapid Iteration Testing Script (10 minutes)

**What was added:** Interactive script for rapid prompt experimentation.

### Testing Rapid Iteration Script

**Steps:**

1. **Navigate to video-api-testing directory:**

   ```bash
   cd video-api-testing
   ```

2. **Run the interactive script:**

   ```bash
   python test_rapid_iteration.py
   ```

3. **Use interactive commands:**
   - Press ENTER to generate a video
   - Type `prompt <text>` to change prompt
   - Type `model <name>` to change model
   - Type `show` to see current settings
   - Type `quit` to exit

4. **Check logs:**
   - Full prompts are logged to `rapid_iteration.log`
   - Each generation logs the prompt used

**What to verify:**

- [ ] Script runs interactively
- [ ] Can change prompts and models on the fly
- [ ] Prompts are logged to file
- [ ] Can generate multiple videos quickly for iteration

---

## 📊 Full End-to-End Regression Test (30-40 minutes)

**Test the complete flow to ensure nothing broke:**

1. **Login/Register** (if not already logged in)
2. **Upload audio file**
3. **Select video type** (Short Form or Full Length)
4. **Start analysis** (wait 3-5 minutes)
5. **Select audio range** (if Short Form)
6. **Choose character** (template or custom image)
7. **Generate clips** (wait 5-10 minutes)
   - Check prompt visibility in UI (info button on clips)
   - Verify multiple clips generate in parallel
8. **Compose video** (wait 3-5 minutes)
   - Watch final video
   - Verify beat-sync effects throughout
   - Verify character consistency
9. **Check projects page:**
   - Project should appear in list
   - Can click to reopen it
10. **Refresh page:**
    - State should persist
    - Can continue where you left off

**What to verify:**

- [ ] All steps work as before
- [ ] New features don't break existing functionality
- [ ] Video generation completes successfully
- [ ] All new features work in context of full flow

---

## 🎯 Quick Test Checklist

After testing, you should be able to say:

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

## 🐛 Troubleshooting

### Problem: Beat effects not visible

- **Check:** Are you watching the final composed video? (Effects are in composition, not individual clips)
- **Try:** Enable test mode: `export BEAT_EFFECT_TEST_MODE=true` and restart backend
- **Check:** Audio has clear beats? (Electronic/hip-hop work best)

### Problem: Character doesn't match reference

- **Check:** Did you select a character before generating clips?
- **Check:** Backend logs show "Using reference image: <url>"?
- **Try:** Use a clear, high-quality character image

### Problem: Prompts not visible in UI

- **Check:** Clips must be completed (not just queued)
- **Try:** Hover over completed clip card, click info button (ⓘ)
- **Check:** Browser console for errors

### Problem: Can't see projects

- **Check:** Are you logged in?
- **Try:** Create a new project first, then check projects page
- **Check:** Browser console for API errors

---

## 📚 Reference

For more detailed information:

- **Beat-Sync Effects:** See `BEAT-SYNC-IMPLEMENTATION-PLAN.md`
- **Full E2E Flow:** See `Old_Gentle_Testing_Guide.md`
- **Architecture:** See `ARCH.md`

---

## That's It

This guide covers all the new features added in this branch. Follow the steps in
order, and you'll test everything. Keep it simple, take your time, and check each
step before moving to the next.

Good luck! 🎬
