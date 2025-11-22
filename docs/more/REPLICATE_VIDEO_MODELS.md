# Replicate Video Generation Models

## Current Model

**Minimax Hailuo 2.3** (`minimax/hailuo-2.3`)

- **Max Duration:** 6 seconds at 1080p, up to 10 seconds at 768p
- **Resolution:** Up to 1080p (6s videos) or 768p (10s videos)
- **FPS:** 24 fps
- **Features:**
  - Text-to-video and image-to-video generation
  - Excellent prompt adherence
  - Realistic human motion and cinematic visual effects
  - Strong physics simulation
  - Expressive character animation
- **Use Cases:** Ideal for realistic human motion, cinematic effects, and character-driven videos
- **Note:** Optimized for instruction adherence and visual quality

---

## OpenAI Sora

**Status:** Not available on Replicate (as of 2025)

**Overview:**

- OpenAI's advanced text-to-video generation model
- Capable of generating high-quality videos up to 60 seconds
- Supports complex scenes with multiple characters and detailed motion
- Strong understanding of physics and spatial relationships
- Currently in limited access/testing phase
- Available only through OpenAI's API (not on Replicate)

**Key Features:**

- Long-form video generation (up to 60 seconds)
- High resolution output
- Complex scene understanding
- Realistic physics simulation
- Temporal consistency

**Availability:**

- Not on Replicate
- Limited access through OpenAI API
- Requires OpenAI API access and approval

---

## Alternative Models with Longer Duration Support

### 1. **Minimax Hailuo 02**

- **Max Duration:** Up to 10 seconds
- **Resolution:** Up to 1080p
- **FPS:** 24 fps
- **Features:**
  - Text-to-video and image-to-video
  - Enhanced physical realism
  - Stronger prompt adherence than earlier versions
- **Replicate Model:** `minimax/hailuo-02`
- **Note:** Newer version with longer duration support

### 2. **Minimax Hailuo 2.3 Fast**

- **Max Duration:** Similar to Hailuo 2.3 (6-10 seconds)
- **Resolution:** Up to 1080p
- **FPS:** 24 fps
- **Features:**
  - Lower latency version of Hailuo 2.3
  - Maintains motion quality and visual consistency
  - Faster iteration cycles
  - Optimized for image-to-video tasks
- **Replicate Model:** `minimax/hailuo-2.3-fast`
- **Best for:** When speed is more important than absolute quality

### 3. **Minimax Video-01 (Hailuo Video)**

- **Max Duration:** 6 seconds
- **Resolution:** 720p
- **FPS:** 25 fps
- **Features:**
  - First AI-native video generation model from Minimax
  - Cinematic camera movements
  - High responsiveness to text prompts
  - Fast rendering, lower resource consumption
- **Replicate Model:** `minimax/video-01`
- **Note:** Earlier model, still available but superseded by Hailuo 2.3

### 4. **Runway Gen-3 / Gen-4** (if available on Replicate)

- **Max Duration:** Up to 10 seconds
- **Estimated Cost:** ~$0.15-$0.25 per video
- **Resolution:** 720p
- **FPS:** 24 fps
- **Quality:** Professional, cinematic
- **Note:** Check if available on Replicate as `runway/gen-3` or similar

### 5. **Kling AI** (if available on Replicate)

- **Max Duration:** Up to 10 seconds
- **Estimated Cost:** ~$0.10-$0.20 per video
- **Quality:** Realistic scenes and character animations
- **Note:** Check if available on Replicate as `kling/kling-ai` or similar

### 6. **Luma Dream Machine / Luma Ray**

- **Max Duration:** 5 seconds
- **Estimated Cost:** ~$0.10 per video
- **Resolution:** 720p
- **Quality:** Cinematic, smooth camera movements
- **Replicate Model:** Check `luma/dream-machine` or `luma/ray`
- **Note:** Only 5 seconds (shorter than current model)

### 7. **Tencent Hunyuan Video**

- **Max Duration:** 5+ seconds (configurable)
- **Estimated Cost:** ~$0.08-$0.12 per video
- **Resolution:** 720p
- **Quality:** State-of-the-art, smooth motion
- **Replicate Model:** Check `tencent/hunyuan-video` or similar
- **Features:** Configurable resolution, duration, steps, guidance scale

### 8. **Zeroscope v2 XL** (Previous Model)

- **Max Duration:** 6 seconds (48 frames at 8 fps)
- **Cost:** ~$0.035 per run
- **Resolution:** Up to 1024x576
- **FPS:** 8 fps
- **Limitation:** Hard cap at 48 frames, lower FPS
- **Replicate Model:** `anotherjesse/zeroscope-v2-xl`
- **Note:** Replaced by Minimax Hailuo 2.3 for better quality and higher FPS

---

## How to Find Models on Replicate

1. **Search Replicate:**
   - Visit: <https://replicate.com/explore?query=text+to+video>
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

### For Sections > 6 seconds

**Option 1: Use Hailuo 02 (10 seconds)**

- Best for sections 7-10 seconds
- Higher quality, single generation per section
- Check pricing on Replicate

**Option 2: Generate multiple clips and concatenate**

- Use current Hailuo 2.3 (6s max)
- Generate 2-3 clips for longer sections
- Concatenate in composition engine
- More cost-effective but requires composition logic

**Option 3: Hybrid approach**

- Use Hailuo 2.3 for sections ≤ 6 seconds
- Use Hailuo 02 for sections > 6 seconds
- Implement model selection logic based on section duration

---

## Implementation Notes

### Current Code Location

- `backend/app/services/video_generation.py` - Line 18: `VIDEO_MODEL = "minimax/hailuo-2.3"`

### To Switch Models

1. Update `VIDEO_MODEL` constant
2. Adjust `input_params` based on new model's schema
3. Update `num_frames` calculation (if model supports it)
4. Test duration limits with new model
5. Update cost estimates in documentation

### Model Schema Differences

Different models may use:

- `num_frames` (current)
- `duration` (direct seconds)
- `max_frames` (limit)
- `fps` (may vary: 8, 24, 25, 30)

Always check the model's OpenAPI schema before switching.

---

## Cost Comparison

| Model | Max Duration | FPS | Cost/Run | Cost per 10s Section |
| :---- | :----------- | :-- | :------- | :------------------- |
| Minimax Hailuo 2.3 | 6s (1080p) / 10s (768p) | 24 | Check Replicate | Varies |
| Minimax Hailuo 02 | 10s | 24 | Check Replicate | Varies |
| Minimax Hailuo 2.3 Fast | 6-10s | 24 | Check Replicate | Varies |
| Minimax Video-01 | 6s | 25 | Check Replicate | Varies |
| Zeroscope v2 XL | 6s | 8 | ~$0.035 | $0.035 (truncated) |
| Luma Dream Machine | 5s | 24 | ~$0.10 | $0.20 (2 clips) |
| Runway Gen-3 | 10s | 24 | ~$0.15-$0.25 | $0.15-$0.25 (1 clip) |
| Kling AI | 10s | 24 | ~$0.10-$0.20 | $0.10-$0.20 (1 clip) |

**Note:**

- For sections > 10 seconds, you'll need to concatenate multiple clips regardless of model
- Pricing for Minimax models should be checked on Replicate as it may vary
- Sora is not available on Replicate and requires OpenAI API access

---

## Next Steps

1. **Verify model availability on Replicate:**

   ```bash
   python scripts/check_replicate_models.py --list
   ```

2. **Test Hailuo 02 for longer sections:**
   - Update `VIDEO_MODEL` in `video_generation.py` to `minimax/hailuo-02`
   - Test with a section > 6 seconds
   - Verify duration control works
   - Compare quality vs. Hailuo 2.3

3. **Update model selection logic:**
   - Add duration-based model selection (Hailuo 2.3 for ≤6s, Hailuo 02 for >6s)
   - Or implement multi-clip generation for long sections

4. **Monitor Sora availability:**
   - Check if Sora becomes available on Replicate
   - Consider OpenAI API integration if needed for longer videos (60s)

5. **Update cost tracking:**
   - Track costs per model
   - Add cost estimates to API responses
   - Monitor Replicate pricing changes
