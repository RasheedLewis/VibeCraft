# E2E Testing Checklist

Quick reference for testing the full video generation flow with all features.

> **See also:** [TEST_CHECKLIST_FEATURES_8_11.md](./TEST_CHECKLIST_FEATURES_8_11.md) - Comprehensive testing guide for Features 8-11 (Character Consistency, Beat-Sync Visual Effects, Cost Tracking, Rate Limiting)

This checklist is designed for E2E testing of those features in a single video generation flow.

## Pre-Test Setup

1. **Start services with test mode and comparison video saving**:

   ```bash
   make start-dev
   ```

   This automatically enables:
   - `BEAT_EFFECT_TEST_MODE=true` (exaggerated effects for easier visibility)
   - `SAVE_NO_EFFECTS_VIDEO=true` (saves comparison video without effects)

   **Alternative:** For normal mode without test mode:

   ```bash
   make start
   ```

## Test Flow

1. **Upload song** (30-60 seconds, clear beats)
2. **Start analysis** (wait 3-5 minutes)
3. **Select video type** (Short Form or Full Length)
4. **Select audio range** (if Short Form)
5. **Choose character** (optional - affects cost tracking)
6. **Select visual style template** (abstract/environment/character/minimal - defaults to 'abstract')
7. **Generate clips** (wait 5-10 minutes)
8. **Compose video** (wait 3-5 minutes)

## What to Check

### 1. Cost Tracking ✅

**During clip generation, watch logs:**

```bash
tail -f logs/worker.log | grep -E "COST|cost"
```

**Look for:**

- `[COST] Estimated cost for 1 clips using minimax/hailuo-2.3: $X.XXXX`
- `[COST-TRACKING] Stored cost $X.XXXX for song {song_id} (total: $X.XXXX)`

**After completion, check database:**

- Query song via API or database
- Verify `total_generation_cost_usd` field is populated
- Expected: ~$0.05 per clip + $0.03 if character consistency enabled

### 2. Dancing Prompt Changes ✅

**Check prompt logs:**

```bash
cat video-api-testing/prompts.log | tail -5
```

**Look for:**

- New dancing instruction: `"the figure is dancing dynamically, varying the limbs that they move, and at some point turning around"`
- This should appear in ALL prompts

**Visual evaluation:**

- Watch generated clips
- Compare to previous videos (if available)
- Figures should be dancing more dynamically
- Should see varied limb movement
- Should see figure turning around at some point

### 3. Visual Effects on Beats ✅

**During composition, watch logs:**

```bash
tail -f logs/worker.log | grep -E "beat|BEAT|flash|effect|Applying.*beat"
```

**Look for:**

- `Applying flash beat filters for {N} beats` (or other effect types)
- `Applying color_burst beat filters for {N} beats`
- `Applying zoom_pulse beat filters for {N} beats`
- `Applying brightness_pulse beat filters for {N} beats`
- `Applying glitch beat filters for {N} beats`
- Effects should rotate: flash (3x) → color_burst (3x) → zoom_pulse (3x) → brightness_pulse (3x) → glitch (3x) → repeat
- Effects applied to every 4th beat (not every beat)

**After composition, compare videos:**

1. **Find comparison video:**

   ```bash
   ls -lh comparison_videos/
   ```

   - Should see: `no_effects_{video_name}.mp4`

2. **Compare the two videos:**
   - **Without effects** (`comparison_videos/no_effects_*.mp4`): Raw AI-generated video after concatenation/trimming/looping
   - **With effects** (final composed video): Same video + FFmpeg beat-sync effects

3. **What to look for:**
   - **Flash effect** (every 4th beat, 3 times in a row): Brief white/bright flashes
   - **Color burst** (next 3 every-4th beats): Sudden color saturation/intensity spikes
   - **Zoom pulse** (next 3 every-4th beats): Subtle zoom in/out
   - **Brightness pulse** (next 3 every-4th beats): Brightness increase/decrease
   - **Glitch effect** (next 3 every-4th beats): Digital glitch artifacts
   - Effects should align with music beats (not random)
   - Effects should be visible throughout entire video (not just beginning)

4. **If effects are hard to see:**
   - Use `make start-dev` instead of `make start` (enables test mode automatically)
   - Effects will be 3x more intense
   - Logs will show: `[TEST MODE] Exaggerating {effect_type} effect`

## Quick Verification Commands

```bash
# Check cost tracking
grep "COST-TRACKING.*Stored cost" logs/worker.log | tail -5

# Check dancing prompt
grep "dancing dynamically" video-api-testing/prompts.log | head -3

# Check beat effects
grep "Applying.*beat filters" logs/worker.log | tail -10

# List comparison videos
ls -lh comparison_videos/ 2>/dev/null || echo "No comparison videos found (set SAVE_NO_EFFECTS_VIDEO=true)"
```

## Expected Results

✅ **Cost Tracking:**

- Cost logged per clip generation
- Total cost accumulated in database
- Character consistency adds $0.03 if enabled

✅ **Dancing Prompts:**

- All prompts include new dancing instruction
- Figures dance more dynamically
- Varied limb movement visible
- Figure turns around at some point

✅ **Visual Effects:**

- Effects visible on every 4th beat
- Effects rotate through 5 types (flash → color_burst → zoom_pulse → brightness_pulse → glitch)
- Each effect type applied 3 times before switching
- Effects synchronized with music beats
- Comparison video shows clear difference (with vs without effects)

## Troubleshooting

**No cost tracking logs:**

- Check worker logs for errors
- Verify song was retrieved successfully
- Check database for `total_generation_cost_usd` field

**No dancing improvement:**

- Check prompts.log for new instruction
- May need to simplify other motion descriptors (see Saturday-Plan.md findings)

**Effects not visible:**

- Check `comparison_videos/` directory exists and has files
- Compare side-by-side: `no_effects_*.mp4` vs final video
- Use `make start-dev` for more visible effects (test mode)
- Check logs for beat filter application messages
