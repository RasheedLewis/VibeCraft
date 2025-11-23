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

## MVP-02 — Beat Alignment Calculation & Planning

**Purpose:** Calculate beat-aligned clip boundaries so transitions happen on beats. Uses song's `beat_times` from analysis to determine where clips should start/end, then calculates exact `num_frames = duration_sec * fps` for video generation.

**Unit tests:** `pytest backend/tests/unit/test_beat_alignment.py -v`

**API test:**

1. **Prerequisites:** Song must be analyzed first:
   ```bash
   # Get song ID and check if analyzed:
   curl http://localhost:8000/api/v1/songs/ | jq '.[0].id'
   docker exec ai-music-video-postgres psql -U postgres -d ai_music_video \
     -c "SELECT song_id, bpm FROM song_analyses WHERE song_id = '{song_id}';"
   
   # If not analyzed, trigger analysis:
   curl -X POST http://localhost:8000/api/v1/songs/{song_id}/analyze | jq
   # Poll status: curl http://localhost:8000/api/v1/jobs/{job_id} | jq
   # Troubleshooting: Ensure RQ worker is running (ps aux | grep "rq worker")
   ```

2. **Get beat-aligned boundaries:**
   ```bash
   # Default (24 FPS) or custom FPS (8 FPS for current model, 30 FPS for better alignment):
   curl "http://localhost:8000/api/v1/songs/{song_id}/beat-aligned-boundaries?fps=8.0" | jq
   ```

3. **Verify response:** Check `boundaries[]` array includes `startTime`, `endTime`, `durationSec` (3-6s), beat/frame indices, alignment errors, and validation metrics (`maxAlignmentError`, `validationStatus`).

4. **Test scenarios:** Different BPMs (80, 110, 140), FPS values (8/24/30), and song lengths (<10s, >60s).

## MVP-03 — Video Composition & Stitching

**Purpose:** Stitch multiple video clips into a single music video with audio sync, normalization (1080p/24fps), and basic transitions.

**Unit tests:** `pytest backend/tests/unit/test_video_composition.py -v`

**Testing workflow:**

1. **Local testing script (rapid iteration):**
   ```bash
   python scripts/compose_local.py \
     --clips ~/Desktop/clip1.mp4 ~/Desktop/clip2.mp4 ~/Desktop/clip3.mp4 \
     --audio ~/Desktop/song.mp3 \
     --output ~/Desktop/composed.mp4
   # Optional: --fps 24 --resolution 1920 1080 --skip-validation --keep-temp --verbose
   ```
   Tests: FFmpeg normalization, concatenation, audio muxing, duration handling, verification.
   See `docs/adam/VideoCompTesting.md` for details.

2. **Production pipeline (S3 and full workflow):**
   Once satisfied with local script, test full pipeline to verify S3 upload/download and other differences:
   ```bash
   # Get song ID and SectionVideo IDs:
   curl http://localhost:8000/api/v1/songs/ | jq '.[0].id'
   curl http://localhost:8000/api/v1/songs/{song_id}/sections | jq '.[] | .sectionVideo.id'
   
   # Enqueue composition job:
   curl -X POST http://localhost:8000/api/v1/songs/{song_id}/compose \
     -H "Content-Type: application/json" \
     -d '{"clip_ids": ["{id1}", "{id2}", "{id3}"], "clip_metadata": [...]}' | jq
   
   # Poll status: curl http://localhost:8000/api/v1/songs/{song_id}/compose/{job_id}/status | jq
   ```
   Tests: S3 operations, RQ workers, database tracking, full orchestration.
   Key differences: S3 storage, RQ workers, DB records, song.duration_sec from DB, 5-min cap.
   See `docs/adam/COMPOSITION_SCRIPT_COMPARISON.md` for details.

3. **Verify output:** Video plays correctly, audio synced, 1080p/24fps, clips in order, last clip extended if needed.

**Inspecting normalization:** Use `--keep-temp` flag to keep intermediate normalized files for inspection. See `docs/adam/VideoCompTesting.md` for details on what normalization does (scaling, letterboxing, FPS conversion) and how to inspect the results.

**Testing with many clips:** Before MVP-03 is complete, test with 40 clips to verify memory usage, performance, and duration handling. See `docs/adam/VideoCompTesting.md` for details.
