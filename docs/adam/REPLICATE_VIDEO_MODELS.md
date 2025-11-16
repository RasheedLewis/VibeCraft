# Replicate Video Generation Models - Duration Support

## Current Model

**Zeroscope v2 XL** (`anotherjesse/zeroscope-v2-xl`)
- **Max Duration:** 6 seconds (48 frames at 8 fps)
- **Cost:** ~$0.035 per run
- **Resolution:** Up to 1024x576
- **FPS:** 8 fps
- **Limitation:** Hard cap at 48 frames

---

## Alternative Models with Longer Duration Support

### 1. **Runway Gen-3 / Gen-4** (if available on Replicate)
- **Max Duration:** Up to 10 seconds
- **Estimated Cost:** ~$0.15-$0.25 per video
- **Resolution:** 720p
- **FPS:** 24 fps
- **Quality:** Professional, cinematic
- **Note:** Check if available on Replicate as `runway/gen-3` or similar

### 2. **Kling AI** (if available on Replicate)
- **Max Duration:** Up to 10 seconds
- **Estimated Cost:** ~$0.10-$0.20 per video
- **Quality:** Realistic scenes and character animations
- **Note:** Check if available on Replicate as `kling/kling-ai` or similar

### 3. **Luma Dream Machine / Luma Ray**
- **Max Duration:** 5 seconds
- **Estimated Cost:** ~$0.10 per video
- **Resolution:** 720p
- **Quality:** Cinematic, smooth camera movements
- **Replicate Model:** Check `luma/dream-machine` or `luma/ray`
- **Note:** Only 5 seconds (slightly better than Zeroscope's 6s cap, but not much)

### 4. **Tencent Hunyuan Video**
- **Max Duration:** 5+ seconds (configurable)
- **Estimated Cost:** ~$0.08-$0.12 per video
- **Resolution:** 720p
- **Quality:** State-of-the-art, smooth motion
- **Replicate Model:** Check `tencent/hunyuan-video` or similar
- **Features:** Configurable resolution, duration, steps, guidance scale

### 5. **Haiper 2.0** (if available on Replicate)
- **Max Duration:** 4 or 6 seconds
- **Resolution:** 720p (4K version coming)
- **Note:** Check if available on Replicate

### 6. **Hailuo Video-01** (if available on Replicate)
- **Max Duration:** 6 seconds
- **Estimated Cost:** ~$0.05-$0.10 per video
- **Quality:** Excellent, versatile
- **Note:** Check if available on Replicate

### 7. **CogVideoX-5B** (if available on Replicate)
- **Max Duration:** 6 seconds (49 frames at 8fps)
- **Estimated Cost:** ~$0.05 per video
- **Quality:** High quality, good balance
- **Note:** Check if available on Replicate

---

## How to Find Models on Replicate

1. **Search Replicate:**
   - Visit: https://replicate.com/explore?query=text+to+video
   - Filter by "Video Generation" category
   - Check model descriptions for duration limits

2. **Check Model Schema:**
   ```python
   import replicate
   client = replicate.Client(api_token=YOUR_TOKEN)
   model = client.models.get("owner/model-name")
   version = model.latest_version
   # Check version.openapi_schema for input parameters
   # Look for: num_frames, duration, max_frames, etc.
   ```

3. **Test Duration Limits:**
   - Try increasing `num_frames` parameter
   - Check if model accepts `duration` parameter directly
   - Review model documentation on Replicate

---

## Recommended Approach

### For Sections > 6 seconds:

**Option 1: Use a 10-second model (Runway/Kling)**
- Best for sections 7-10 seconds
- Higher cost but better quality
- Single generation per section

**Option 2: Generate multiple clips and concatenate**
- Use current Zeroscope (6s max)
- Generate 2-3 clips for longer sections
- Concatenate in PR-13 (Composition Engine)
- More cost-effective but requires composition logic

**Option 3: Hybrid approach**
- Use Zeroscope for sections ≤ 6 seconds
- Use longer-duration model for sections > 6 seconds
- Implement model selection logic based on section duration

---

## Implementation Notes

### Current Code Location:
- `backend/app/services/video_generation.py` - Line 20: `VIDEO_MODEL = "anotherjesse/zeroscope-v2-xl"`

### To Switch Models:
1. Update `VIDEO_MODEL` constant
2. Adjust `input_params` based on new model's schema
3. Update `num_frames` calculation (if model supports it)
4. Test duration limits with new model
5. Update cost estimates in documentation

### Model Schema Differences:
Different models may use:
- `num_frames` (current)
- `duration` (direct seconds)
- `max_frames` (limit)
- `fps` (may vary: 8, 24, 30)

Always check the model's OpenAPI schema before switching.

---

## Cost Comparison

| Model | Max Duration | Cost/Run | Cost per 10s Section |
|-------|--------------|----------|---------------------|
| Zeroscope v2 XL | 6s | $0.035 | $0.035 (truncated) |
| Luma Dream Machine | 5s | $0.10 | $0.20 (2 clips) |
| Hunyuan Video | 5+ s | $0.08-$0.12 | $0.16-$0.24 (2 clips) |
| Runway Gen-3 | 10s | $0.15-$0.25 | $0.15-$0.25 (1 clip) |
| Kling AI | 10s | $0.10-$0.20 | $0.10-$0.20 (1 clip) |

**Note:** For sections > 10 seconds, you'll need to concatenate multiple clips regardless of model.

---

## Next Steps

1. **Verify model availability on Replicate:**
   ```bash
   python scripts/check_replicate_models.py --list
   ```

2. **Test a longer-duration model:**
   - Pick a model from above
   - Update `VIDEO_MODEL` in `video_generation.py`
   - Test with a section > 6 seconds
   - Verify duration control works

3. **Update model selection logic:**
   - Add duration-based model selection
   - Or implement multi-clip generation for long sections

4. **Update cost tracking:**
   - Track costs per model
   - Add cost estimates to API responses

