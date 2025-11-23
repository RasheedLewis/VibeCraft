# Testing Features 8-11 Simultaneously

This guide helps you test all four features in a single video generation flow:
- **Feature 8**: Character Consistency
- **Feature 9**: Beat-Sync Visual Effects
- **Feature 10**: Cost Tracking  
- **Feature 11**: Rate Limiting

---

## **In-Chat** Step-by-step testing guide

### Step 1: Stop any running services

If services are running, stop them first:

```bash
make stop
```

Wait a few seconds, then verify they're stopped.

---

### Step 2: Decide on test mode

For Feature 9 (Beat-Sync Effects), you can enable test mode to make effects more visible.

- Option A: Normal mode (default) — effects are subtle
- Option B: Test mode — effects are exaggerated (3x intensity)

If you want test mode, set the environment variable before starting:

```bash
BEAT_EFFECT_TEST_MODE=true make start
```

If you want normal mode, just run:

```bash
make start
```

Note: Prompts are automatically logged to `video-api-testing/prompts.log` — no setup needed.

---

### Step 3: Start all services

Run one of these:

```bash
# Normal mode
make start

# OR Test mode (exaggerated effects)
BEAT_EFFECT_TEST_MODE=true make start
```

What happens:
- Backend starts on http://localhost:8000
- Worker starts (processes video generation)
- Frontend starts on http://localhost:5173
- Logs are written to `logs/` directory

Wait until you see: "All services started!"

---

### Step 4: Open the app

1. Open your browser
2. Go to: http://localhost:5173
3. You should see the login page (or be redirected there)

---

### Step 5: Login/Register

1. If you have an account: enter email and password, click "Login"
2. If not: click "Register", enter email/password, click "Register"
3. You should be redirected to the upload page

---

### Step 6: Upload a test song

1. Have a test audio file ready (30-60 seconds, with clear beats — electronic/hip-hop works well)
2. On the upload page, drag and drop your file or click to browse
3. Wait for upload to complete
4. You should see the song appear with a waveform

---

### Step 7: Start analysis

1. Select video type: "Short Form" or "Full Length"
2. Click "Start Analysis" or similar button
3. Wait 3-5 minutes for analysis to complete
4. You should see sections appear on the timeline

---

### Step 8: Select audio range (if Short Form)

1. If you selected "Short Form", select a 15-30 second range on the timeline
2. Click to confirm the selection

---

### Step 9: Choose a character (Feature 8: Character Consistency)

1. You'll see character selection options
2. Option A: Choose a template character (you'll see both poses)
3. Option B: Upload a custom character image
4. Select your choice

This tests Feature 8 — the character should appear consistently across all clips.

---

### Step 10: Generate clips (this tests multiple features)

1. Click "Generate Clips" or similar
2. Wait 5-10 minutes (clips generate in parallel — up to 4 at once)
3. Watch the progress — multiple clips should generate simultaneously

While waiting, you can check logs:

Open a new terminal and run:
```bash
# Watch worker logs for cost tracking
tail -f logs/worker.log | grep -E "COST|cost"

# Watch for character consistency logs
tail -f logs/worker.log | grep -E "character|CHARACTER|reference.*image"

# Watch for prompt logs
tail -f logs/worker.log | grep -E "PROMPT|prompt"
```

What to look for:
- `[COST-TRACKING] Stored cost $X.XXXX for song ...` (Feature 10: Cost Tracking)
- `[VIDEO-GEN] Using reference image: <url>` (Feature 8: Character Consistency)
- `[VIDEO-GEN] FULL PROMPT (optimized): ...` (Feature 5: Prompt Logging)

---

### Step 11: Check prompt logging (automatic)

Prompts are automatically logged. Check the file:

```bash
cat video-api-testing/prompts.log
```

You should see JSON lines like:
```json
{"prompt": "...", "songId": "...", "clipId": "...", "optimized": true}
```

Each clip generation adds one line automatically — no extra setup needed.

---

### Step 12: Compose video (this tests Feature 9: Beat-Sync Effects)

1. After all clips are generated, click "Compose Video" or similar
2. Wait 3-5 minutes for composition
3. While waiting, watch worker logs:

```bash
tail -f logs/worker.log | grep -E "beat|BEAT|flash|effect|TEST MODE"
```

What to look for:
- `[VIDEO-COMPOSE] Applying flash beat filters for {N} beats`
- `[VIDEO-COMPOSE] Beat filters applied successfully`
- If test mode: `[TEST MODE] Exaggerating flash effect`

---

### Step 13: Watch the final video

1. After composition completes, the video should appear
2. Click play and watch carefully
3. Look for:
   - Visual effects on beats (flashes, color bursts, etc.)
   - Effects throughout the entire video (not just the beginning)
   - Effects synchronized with the music rhythm

If you used test mode, effects should be more obvious (3x brighter, longer duration).

---

### Step 14: Verify Feature 8: Character Consistency

1. Watch the generated clips (before composition)
2. Check:
   - Same character appears in all clips
   - Character matches your reference image (template or custom)
   - Character performs actions from prompts (not just static)

---

### Step 15: Verify Feature 10: Cost Tracking

Check the database or API response for cost:

```bash
# Check worker logs for final cost
grep "COST-TRACKING.*Final cost" logs/worker.log
```

You should see something like:
```
[COST-TRACKING] Final cost for song {song_id}: $0.3000
```

Expected costs:
- ~$0.05 per clip (minimax/hailuo-2.3)
- +$0.03 if character consistency enabled (one-time)
- Example: 6 clips = ~$0.30, with character = ~$0.33

---

### Step 16: Test Feature 11: Rate Limiting (optional)

This is harder to test manually, but you can try:

1. Open browser console (F12)
2. Run this (replace YOUR_TOKEN with your actual token):
```javascript
for(let i=0; i<70; i++) {
  fetch('http://localhost:8000/api/v1/songs/', {
    headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
  })
}
```

3. After 60+ requests in a minute, you might see 429 (Too Many Requests) errors

Or test health check exemption:
```bash
for i in {1..100}; do curl http://localhost:8000/healthz; done
```

All should return 200 (health checks aren't rate limited).

---

## 📊 Testing Findings

### Prompt Logging (Feature 5)
**Status:** ✅ Working

- **Total prompts logged:** 102 entries in `video-api-testing/prompts.log`
- **Unique songs:** 2 songs have prompts logged
- **Format:** JSON lines with `prompt`, `songId`, `clipId`, and `optimized` fields
- **BPM-aware descriptors:** Prompts include tempo-aware text like "synchronized to 129 BPM tempo", "rhythmic motion matching the beat"
- **Example prompt:** "Abstract visual style, neutral color palette with #9370DB, #BA55D3, and #DDA0DD, danceable mood, Electronic aesthetic, medium with medium pacing, fast_zoom camera motion (fast speed), energetic, driving, dynamic, upbeat energetic dancing, rapid rhythmic dance motion, quick dance steps synchronized to tempo, dynamic dancing synchronized to 129 BPM tempo, rhythmic motion matching the beat with clear repetitive pattern. Camera: static."

**Note:** Some test prompts with `songId: null` appear in the log (likely from earlier testing).

### Cost Tracking (Feature 10)
**Status:** ⚠️ Needs Verification

- **Expected behavior:** Cost tracking logs should appear with `[COST-TRACKING]` prefix in worker logs
- **Current status:** No cost tracking logs found in recent worker logs
- **Possible reasons:**
  - Cost tracking is only logged at composition completion (not during clip generation)
  - Clips may still be generating (cost tracking happens per clip)
  - Logs may be in a different worker log file

**Action needed:** Check logs after composition completes, or verify cost tracking is being called during clip generation.

### Clip Generation Concurrency
**Status:** ✅ Working

- **Workers:** 4 RQ workers running (worker.log.1 through worker.log.4)
- **Observed:** Multiple clips generating in parallel
- **Example:** Clip jobs completing at different times (19:42:37, 19:42:48, 19:44:43) showing parallel processing

---

## Quick verification checklist

After completing all steps, verify:

- [ ] **Feature 8 (Character Consistency)**: Same character in all clips, matches reference image
- [ ] **Feature 9 (Beat-Sync Effects)**: Effects visible on beats throughout video
- [ ] **Feature 10 (Cost Tracking)**: Cost logged in worker logs and stored in database
- [ ] **Feature 11 (Rate Limiting)**: Middleware active (may need automation to test fully)
- [ ] **Prompt Logging**: `video-api-testing/prompts.log` has entries

---

## Troubleshooting

If something doesn't work:

1. Check services are running: `ps aux | grep -E "(uvicorn|rq worker|vite)"`
2. Check logs: `tail -f logs/worker.log` or `tail -f logs/backend.log`
3. Restart services: `make stop` then `make start` (or with test mode)

---

## Summary

- Prompts are logged automatically — no setup needed
- Test mode: use `BEAT_EFFECT_TEST_MODE=true make start` for exaggerated effects
- All features work together — one video generation tests all four features
- Logs are your friend — check `logs/worker.log` to see what's happening

Ready to start? Run `make start` (or with test mode) and follow the steps above.

```shellscript
make stop
```

```shellscript
BEAT_EFFECT_TEST_MODE=true make start
```

```shellscript
make start
```

```shellscript
# Normal mode
make start

# OR Test mode (exaggerated effects)
BEAT_EFFECT_TEST_MODE=true make start
```

```shellscript
# Watch worker logs for cost tracking
tail -f logs/worker.log | grep -E "COST|cost"

# Watch for character consistency logs
tail -f logs/worker.log | grep -E "character|CHARACTER|reference.*image"

# Watch for prompt logs
tail -f logs/worker.log | grep -E "PROMPT|prompt"
```

```shellscript
cat video-api-testing/prompts.log
```

```json
{"prompt": "...", "songId": "...", "clipId": "...", "optimized": true}
```

```shellscript
tail -f logs/worker.log | grep -E "beat|BEAT|flash|effect|TEST MODE"
```

```shellscript
# Check worker logs for final cost
grep "COST-TRACKING.*Final cost" logs/worker.log
```

```plaintext
[COST-TRACKING] Final cost for song {song_id}: $0.3000
```

```javascript
for(let i=0; i<70; i++) {
  fetch('http://localhost:8000/api/v1/songs/', {
    headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
  })
}
```

```shellscript
for i in {1..100}; do curl http://localhost:8000/healthz; done
```

---

## 📋 Step-by-Step Test

### Step 1: Generate a Complete Video

1. **Upload a song** with clear beats (30-60 seconds, electronic/hip-hop)
2. **Complete analysis** (wait 3-5 minutes)
3. **Select video type** (Short Form or Full Length)
4. **Select audio range** (if Short Form)
5. **Choose character** (optional - affects cost tracking)
6. **Generate clips** (wait 5-10 minutes)
7. **Compose video** (wait 3-5 minutes)

### Step 2: Test Feature 8 - Character Consistency

**During clip generation, check worker logs for:**

```bash
# Monitor all worker logs (multiple workers)
tail -f logs/worker.log.* 2>/dev/null | grep -E "character|CHARACTER|reference.*image|Using reference" || tail -f logs/worker.log | grep -E "character|CHARACTER|reference.*image|Using reference"
```

**Look for:**
- `[VIDEO-GEN] Using reference image: <url>`
- `[CLIP-GEN] character_consistency_enabled=True`
- `[CLIP-GEN] character_image_url={'set' if character_image_url else 'none'}`

**After clips are generated:**

1. **Watch the generated clips**
2. **Observe character consistency:**
   - Same character should appear in all clips
   - Character should match your reference image (template or custom)
   - Character should perform actions from prompts (not just static)
   - Both image AND text prompt are used together

**Test Template Character:**
- Select a template character (see both poses displayed)
- Generate clips
- Verify character matches template image

**Test Custom Image Upload:**
- Upload a custom character image
- Generate clips
- Verify character matches your uploaded image

### Step 3: Test Feature 9 - Beat-Sync Visual Effects

**While video is composing, check worker logs for:**

```bash
# Monitor all worker logs (multiple workers)
tail -f logs/worker.log.* 2>/dev/null | grep -E "beat|BEAT|flash|effect" || tail -f logs/worker.log | grep -E "beat|BEAT|flash|effect"
```

**Look for:**
- `[VIDEO-COMPOSE] Applying flash beat filters for {N} beats`
- `[VIDEO-COMPOSE] Beat filters applied successfully`
- `Found {N} beat times for beat alignment and filters`

**After video completes:**

1. **Watch the final composed video**
2. **Observe visual effects:**
   - Effects should trigger at precise beat moments
   - Effects should be visible throughout entire video (not just first 50 beats)
   - Effects should align with music rhythm

**Test with Exaggerated Effects (Optional):**

1. Set environment variable: `export BEAT_EFFECT_TEST_MODE=true`
2. Restart backend
3. Generate a new video
4. Effects should be more visible/exaggerated
5. Logs should show: `[TEST MODE] Exaggerating flash effect`

### Step 4: Test Feature 10 - Cost Tracking

**During clip generation, check worker logs for:**

```bash
# Monitor all worker logs (multiple workers)
tail -f logs/worker.log.* 2>/dev/null | grep -E "COST|cost" || tail -f logs/worker.log | grep -E "COST|cost"
```

**Look for:**
- `[COST] Estimated cost for 1 clips using minimax/hailuo-2.3: $X.XXXX`
- `[COST-TRACKING] Stored cost $X.XXXX for song {song_id} (total: $X.XXXX)`
- `[COST-TRACKING] Final cost for song {song_id}: $X.XXXX`

**After video completes:**

1. **Check database or API response:**
   ```bash
   # Query the song via API or database
   # Look for `total_generation_cost_usd` field
   ```

2. **Verify cost accumulation:**
   - Cost should be calculated per clip generation
   - Total cost should accumulate for the song
   - If character consistency is enabled, should include character costs

**Expected Costs:**
- Base: ~$0.05 per clip (minimax/hailuo-2.3)
- Character consistency: +$0.03 per song (one-time)
- Example: 6 clips = ~$0.30, with character = ~$0.33

### Step 5: Test Feature 11 - Rate Limiting

**Test during normal usage:**

1. **Make rapid API requests:**
   - Refresh projects page many times quickly
   - Or use browser console:
   ```javascript
   for(let i=0; i<70; i++) {
     fetch('http://localhost:8000/api/v1/songs/', {
       headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
     })
   }
   ```

2. **Check for rate limit:**
   - After many requests (60+ in a minute), you might see 429 (Too Many Requests)
   - Limits are generous: 60/min, 1000/hour, 10000/day
   - Normal usage should not hit limits

**Test Health Check Exemption:**

1. Make many requests to `/healthz`:
   ```bash
   for i in {1..100}; do curl http://localhost:8000/healthz; done
   ```
2. **Expected:** All requests return 200 (health checks are not rate limited)

---

## ✅ Verification Checklist

### Feature 8: Character Consistency
- [ ] Same character appears in all clips
- [ ] Character matches reference image (template or custom)
- [ ] Character performs actions from prompts (not just static)
- [ ] Both image AND text prompt are used together
- [ ] Logs show reference image usage

### Feature 9: Beat-Sync Visual Effects
- [ ] Effects trigger on beats (not randomly)
- [ ] Effects work for entire video duration (not just first 50 beats)
- [ ] Effects are synchronized with music rhythm
- [ ] Logs show beat filter application messages
- [ ] Test mode makes effects more visible (if tested)

### Feature 10: Cost Tracking
- [ ] Cost is calculated for each clip generation
- [ ] Total cost is accumulated for the song
- [ ] Cost is stored in database (`total_generation_cost_usd`)
- [ ] Logs show cost tracking messages
- [ ] Character consistency adds to cost (if enabled)

### Feature 11: Rate Limiting
- [ ] Rate limiting works (may not be easily testable without automation)
- [ ] Health check endpoints are not rate limited
- [ ] Limits are generous (60/min, 1000/hour, 10000/day) for normal use
- [ ] 429 error returned when limits exceeded

---

## 🐛 Troubleshooting

### Character doesn't match reference
- **Check:** Did you select a character before generating clips?
- **Check:** Backend logs show "Using reference image: <url>"?
- **Try:** Use a clear, high-quality character image
- **Check:** Both image AND text prompt are used together (not replacement)

### Beat effects not visible
- **Check:** Are you watching the final composed video? (Effects are in composition, not individual clips)
- **Try:** Enable test mode: `BEAT_EFFECT_TEST_MODE=true make start` (or restart backend with env var)
- **Check:** Audio has clear beats? (Electronic/hip-hop work best)

### Cost not showing
- **Check:** Worker logs for cost tracking messages
- **Check:** Database for `total_generation_cost_usd` field
- **Note:** Cost is stored but not displayed in UI yet (backend only)

### Rate limiting not working
- **Check:** Middleware is enabled in `app/main.py`
- **Check:** Health checks are exempt (should always return 200)
- **Note:** Limits are generous, may not hit them during normal testing

---

## 📊 Expected Results Summary

After completing the test, you should have:

1. **Consistent character** - Same character appears across all clips, matching reference image
2. **Video with beat-sync effects** - Visual effects synchronized to beats
3. **Cost tracked** - Total cost stored in database (e.g., $0.30 for 6 clips)
4. **Rate limiting active** - Middleware protecting API endpoints

All four features should work simultaneously without conflicts!

