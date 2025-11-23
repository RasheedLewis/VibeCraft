# Prompt Analysis Report

## Investigation Results

### 1. Repetitive Dance Phrases - Where They Come From

**Location:** `backend/app/services/prompt_enhancement.py`

**The Problematic Phrase:**

```text
"energetic, driving, dynamic, upbeat energetic dancing, rapid rhythmic dance motion, 
quick dance steps synchronized to tempo, dynamic dancing synchronized to 129 BPM tempo, 
rhythmic motion matching the beat with clear repetitive pattern"
```

**How It's Built:**

1. **Tempo Descriptor** (line 51, 131):
   - For fast BPM (129 BPM): `"energetic, driving, dynamic, upbeat"`
   - From `TEMPO_DESCRIPTORS["fast"]`

2. **Motion Descriptor** (line 18, 127):
   - For "dancing" motion type at fast tempo: `"energetic dancing, rapid rhythmic dance motion, quick dance steps synchronized to tempo, dynamic dancing"`
   - From `MOTION_TYPES["dancing"]["fast"]`

3. **Final Rhythmic Phrase** (lines 135-137):

   ```python
   rhythmic_phrase = (
       f"{tempo_descriptor} {motion_descriptor} synchronized to {bpm_int} BPM tempo, "
       f"rhythmic motion matching the beat with clear repetitive pattern"
   )
   ```

**Result:** The phrase combines:

- Tempo descriptor: "energetic, driving, dynamic, upbeat"
- Motion descriptor: "energetic dancing, rapid rhythmic dance motion, quick dance steps synchronized to tempo, dynamic dancing"
- BPM sync: "synchronized to 129 BPM tempo"
- Repetitive pattern: "rhythmic motion matching the beat with clear repetitive pattern"

**Issues:**

- "energetic" appears twice (in tempo descriptor AND motion descriptor)
- "dynamic" appears twice (in tempo descriptor AND motion descriptor)
- "dancing" appears multiple times
- "synchronized to tempo" appears twice
- "repetitive pattern" may be overkill (we already have "rhythmic motion matching the beat")

**Recommendation:**

- Simplify the motion descriptors to avoid duplication
- Remove "repetitive pattern" or make it optional
- Consider combining tempo and motion descriptors more intelligently

---

### 2. Image Interrogation (Image-to-Text) - Current Status

**Location:** `backend/app/services/image_interrogation.py`

**Function:** `interrogate_reference_image()`

**Current Usage:**

- **ONLY called in:** `backend/app/services/character_consistency.py` → `generate_character_image_job()`
- **NOT used during regular video generation** - only when generating a consistent character image from a reference
- **Purpose:** Converts reference images into detailed character descriptions for character image generation

**How It Works:**

1. **Primary Method:** OpenAI GPT-4 Vision (if `OPENAI_API_KEY` is configured)
   - Uses structured prompt to analyze character image
   - Returns JSON with: `prompt`, `character_description`, `style_notes`
   - More detailed and structured output

2. **Fallback Method:** Replicate's `methexis-inc/img2prompt` (if OpenAI not available)
   - Uses Replicate API token (same as video generation)
   - Less structured output (just a prompt string)
   - Automatically falls back if OpenAI fails

**Configuration:**

**OpenAI API Key (Preferred):**

- Environment variable: `OPENAI_API_KEY`
- Location in code: `backend/app/core/config.py` line 56
- Required for: GPT-4 Vision model access
- Cost: ~$0.01 per image interrogation (estimated)

**Replicate API Token (Fallback):**

- Environment variable: `REPLICATE_API_TOKEN`
- Already configured for video generation
- Used for: `methexis-inc/img2prompt` model
- Cost: Included in Replicate usage

**Current Status:**

- Image interrogation is **implemented and working**
- It's **only used for character image generation**, not for regular video generation
- If `OPENAI_API_KEY` is not set, it falls back to Replicate automatically
- The interrogation result is stored in `song.character_interrogation_prompt` (JSON)

**To Enable OpenAI Vision:**

1. Get OpenAI API key from <https://platform.openai.com/api-keys>
2. Add to `.env` file: `OPENAI_API_KEY=sk-...`
3. Restart backend/worker
4. Image interrogation will automatically use OpenAI (better quality) instead of Replicate fallback

**Note:** Image interrogation is NOT used during regular video generation. The reference image is passed directly to the video generation model (`first_frame_image` parameter), and the model uses it visually without text description.

**How the Interrogation Response is Used:**

The interrogation result (dict with `prompt`, `character_description`, `style_notes`) is used to build a prompt for **character image generation** (not video generation):

**Location:** `backend/app/services/character_image_generation.py` (lines 56-61)

**Prompt Building Process:**

1. **Base prompt:** Uses `interrogation_result["prompt"]` (the detailed prompt from interrogation)
2. **Add description:** Appends `interrogation_result["character_description"]`
3. **Add style notes:** If available, appends `interrogation_result["style_notes"]`
4. **Add consistency keywords:** Appends ". High quality, detailed, consistent character design, clear features, professional illustration"

**Final Enhanced Prompt:**

```python
enhanced_prompt = f"{interrogation_prompt}. {character_description}"
if style_notes:
    enhanced_prompt += f" Style: {style_notes}"
enhanced_prompt += ". High quality, detailed, consistent character design, clear features, professional illustration"
```

**This enhanced prompt is then used with:**

- **Model:** Stable Diffusion XL (`stability-ai/sdxl`)
- **Purpose:** Generate a "consistent" character image from the reference
- **Result:** Stored in `song.character_generated_image_s3_key` and used as priority 1 for video generation

**Logging:**

- The full API response from image interrogation is now logged with `[IMAGE-INTERROGATION]` prefix
- Shows the complete `prompt`, `character_description`, and `style_notes` returned by the API
- Helps debug what the image-to-text model is extracting from reference images

---

## Summary

### Repetitive Phrases

- **Source:** `prompt_enhancement.py` combines tempo descriptors + motion descriptors + BPM sync + repetitive pattern
- **Issue:** Too much duplication ("energetic", "dynamic", "dancing", "synchronized" all appear multiple times)
- **Fix Needed:** Simplify motion descriptors, remove redundant phrases

### Image Interrogation

- **Status:** ✅ Implemented and working
- **Usage:** Only for character image generation, not regular video generation
- **Configuration:**
  - `OPENAI_API_KEY` (preferred) - not required, has fallback
  - `REPLICATE_API_TOKEN` (fallback) - already configured
- **Action:** If you want better character descriptions, add `OPENAI_API_KEY` to `.env`
