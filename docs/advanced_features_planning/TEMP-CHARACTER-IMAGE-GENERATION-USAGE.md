# Character Image Generation - Actual Usage

## Summary

**YES, we ARE doing character image generation, but only in specific cases:**

### When Character Image Generation Runs

1. **Custom Character Image Upload** (`POST /{song_id}/character-image`)
   - User uploads their own character image
   - **Triggers:** `generate_character_image_job` is enqueued (line 730-734 in `routes_songs.py`)
   - **Uses Image Interrogation:** ✅ YES - calls `interrogate_reference_image()` (line 64 in `character_consistency.py`)
   - **Process:**
     1. Interrogates the uploaded image (image-to-text)
     2. Generates a "consistent" character image using the interrogation result
     3. Stores in `song.character_generated_image_s3_key`
     4. This generated image is used for video generation (priority 1)

2. **Template Character Application** (`POST /template-characters/{character_id}/apply`)
   - User selects a template character
   - **Does NOT trigger:** Character image generation job
   - **Does NOT use:** Image interrogation
   - **Process:**
     1. Just copies template images to song's S3 location
     2. Stores in `song.character_reference_image_s3_key` and `song.character_pose_b_s3_key`
     3. These template images are used directly for video generation

### Image Priority During Video Generation

When generating clips, `_get_character_image_urls()` uses this priority (from `clip_generation.py` line 473-539):

1. **Priority 1:** `character_generated_image_s3_key` (if exists)
   - Only exists if character image generation job completed successfully
   - This is the "consistent" character image generated from interrogation

2. **Priority 2:** `character_reference_image_s3_key` (fallback)
   - The original uploaded image OR template character pose-a
   - Used if generation didn't happen or failed

3. **Priority 3:** `character_pose_b_s3_key` (additional)
   - Template character pose-b (if available)
   - Added to list but not used as primary

### When Image Interrogation is Actually Used

**Image interrogation (`interrogate_reference_image`) is ONLY called when:**

- A user uploads a **custom character image** (not template)
- The `generate_character_image_job` runs successfully
- It's used to create a detailed prompt for generating a "consistent" character image

**Image interrogation is NOT used when:**

- Using template characters (they're used directly)
- Generating video clips (reference images are passed directly to video model)
- The character image generation job fails or isn't enqueued

### Current Status

- **Character image generation:** ✅ Implemented and working
- **Image interrogation:** ✅ Implemented and working (only for custom uploads)
- **Template characters:** ✅ Work without image generation/interrogation
- **Fallback behavior:** ✅ If generation fails, uses reference image directly

### To Verify It's Working

Check logs for:

- `"Enqueued character image generation job for song {song_id}"` - when upload happens
- `"Interrogating reference image for song {song_id}"` - when interrogation runs
- `"Using character generated image for clip generation"` - when generated image is used
- `"Using character reference image (pose-a) for clip generation"` - when fallback is used

### Configuration

- **OpenAI API Key:** Optional but recommended for better interrogation quality
  - Set `OPENAI_API_KEY` in `.env`
  - Falls back to Replicate if not set
- **Replicate API Token:** Required (already configured)
  - Used for both video generation and image generation
  - Also used as fallback for image interrogation
