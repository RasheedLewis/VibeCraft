# Troubleshooting Log

## Debug Overlays for UI Testing

**Note:** Debug overlays are available but commented out for character consistency UI testing:
- **UploadPage.tsx** (line ~1116): Blue debug box showing `character_consistency_enabled`, `character_reference_image_s3_key`, and `character_pose_b_s3_key` from `songDetails`
- **SelectedTemplateDisplay.tsx** (line ~77): Yellow debug box showing pose URL fetch status, loading state, and URL availability

To enable for testing, uncomment the debug overlay sections in both files. These can be modified as needed for further UI debugging.

---

## Critical Issue: Character Consistency Not Working

**Problem:** 
- (a) Most clips do not show a dancing figure/character
- (b) When a character does appear, it's not based on the provided reference image

**Historical Context:**
Prior to all refactors and adding the character consistency option, we actually did get a dancing character almost all the time. This suggests that the character consistency feature implementation may have broken or changed the prompt generation logic in a way that prevents characters from appearing.

**Status:** Needs investigation - will examine prompts in a new chat session.

**Related Files:**
- `backend/app/services/scene_planner.py` - Prompt generation
- `backend/app/services/video_generation.py` - Video generation with character images
- `backend/app/services/clip_generation.py` - Clip generation flow
