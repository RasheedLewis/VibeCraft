# Quick Testing Guide

## PR-05 — Genre & Mood Classification

**Unit tests:** `pytest backend/tests/unit/test_genre_mood_analysis.py -v` (fast, no audio files)

**Integration test:** `source .venv/bin/activate && python backend/tests/test_genre_mood.py` with sample audio. Verify analysis response includes `primaryGenre`, `moodTags`, and `moodVector` fields.

**Frontend:** Start dev server and verify `GenreBadge` and `MoodBadge` components render correctly with no console errors at `http://localhost:5173`.

## PR-06 — Lyric Extraction & Section Alignment

**Unit tests:** `pytest backend/tests/unit/test_lyric_extraction.py -v` (fast, no audio files or API calls)

**Integration test:** `source .venv/bin/activate && python backend/tests/test_lyrics.py` with sample audio (requires Replicate API token). Verify `sectionLyrics[]` array is populated with timed text aligned to sections. Check lyric previews appear in section cards.

## PR-08 — Section Scene Planner (Template + Prompt Builder)

**Unit tests:** `pytest backend/tests/unit/test_scene_planner.py -v` (fast, no audio files needed)

**API test:** `curl -X POST http://localhost:8000/api/v1/scenes/build-scene -H "Content-Type: application/json" -d '{"sectionId": "section-4"}'`. Verify response includes scene spec with prompt, color palette, camera motion, and shot pattern derived from section's mood/genre/type.

## PR-09 — Section Video Generation Pipeline

**Unit tests:** `pytest backend/tests/unit/test_video_generation.py -v` (fast, mocks Replicate API)

**Manual E2E test:**

- Unfortunately not possible yet as 'Generate video' is not available, no SectionCard is implemented yet.

**API test:**

1. Start generation: `curl -X POST http://localhost:8000/api/v1/sections/section-4/generate -H "Content-Type: application/json" -d '{"sectionId": "section-4", "template": "abstract"}'`
   - Returns 202 Accepted immediately with `{"sectionVideoId": "...", "status": "processing", "message": "Video generation started"}`
   - Note: `sectionVideoId` is the database record ID (one video per section, not multiple calls)
2. Poll for completion: `curl http://localhost:8000/api/v1/sections/section-4/video`
   - Returns 200 with status "processing" while generating, "completed" when done
   - Response includes `prompt` field showing the full prompt sent to video generation API
   - **Expected wait time:** 1-3 minutes (Zeroscope v2 XL typically takes 1-3 min, max timeout is 15 min)
   - Check backend logs for progress: `"Video generation in progress (attempt X/180, ~Ys elapsed)..."`
   - When status is "completed", response includes `videoUrl` field (e.g., `"https://replicate.delivery/pbxt/..."`)
3. View the video: Open the `videoUrl` in your browser, or download with `curl -O <videoUrl>`
   - **View the prompt sent to video API:** `docker exec ai-music-video-postgres psql -U postgres -d ai_music_video -c "SELECT prompt, status, error_message, replicate_job_id, created_at FROM section_videos WHERE section_id = 'section-4' ORDER BY created_at DESC LIMIT 1;"`
   - **If there's an error**, check `status, error_message, replicate_job_id` in the command above and see `https://replicate.com/p/{replicate_job_id}` for more details
