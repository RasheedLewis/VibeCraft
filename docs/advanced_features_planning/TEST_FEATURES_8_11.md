# Testing Features 8-11 Simultaneously

This guide helps you test all four features in a single video generation flow:
- **Feature 8**: Character Consistency
- **Feature 9**: Beat-Sync Visual Effects
- **Feature 10**: Cost Tracking  
- **Feature 11**: Rate Limiting

---

## 🎯 Combined Testing Flow

### Prerequisites

1. **Backend running**: `cd backend && source ../.venv/bin/activate && python -m uvicorn app.main:app --reload`
2. **Worker running**: `cd backend && rq worker ai_music_video`
3. **Frontend running**: `cd frontend && npm run dev`
4. **Test audio**: Use a song with clear, strong beats (electronic/hip-hop work best)

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
tail -f logs/worker.log | grep -E "character|CHARACTER|reference.*image|Using reference"
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
tail -f logs/worker.log | grep -E "beat|BEAT|flash|effect"
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
tail -f logs/worker.log | grep -E "COST|cost"
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

