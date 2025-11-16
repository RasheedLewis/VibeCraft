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

**Note:** This endpoint calculates beat-aligned clip boundaries from the song's beat analysis. It does **not** take clips as input - it uses the song's `beat_times` from analysis to calculate where clip boundaries should be placed. These calculated boundaries can then be used later for clip generation.

**Purpose:** Calculate where clip boundaries should be so that **transitions between clips happen on beats**. Video generation APIs let you specify `num_frames` (which with `fps` gives exact timing), so this helper:
1. Finds beat-aligned boundaries (where clips should start/end)
2. Calculates exact `num_frames` for each clip: `num_frames = duration_sec * fps`
3. When you generate clips with those exact frame counts, transitions automatically happen on beats

See `docs/adam/BEAT_ALIGNMENT_USAGE.md` for detailed workflow examples.

**Unit tests:** `pytest backend/tests/unit/test_beat_alignment.py -v` (fast, no audio files needed)

**API test:**

1. **Prerequisites:** The song must have been analyzed first (to get `beat_times`):
   ```bash
   # Get a song ID (or use an existing one)
   curl http://localhost:8000/api/v1/songs/ | jq '.[0].id' # eg "8136f2bd-6b20-44b6-92c5-45029b9f6ac6"
   
   # Check if song has been analyzed (find existing SongAnalysisRecord):
   docker exec ai-music-video-postgres psql -U postgres -d ai_music_video -c "SELECT song_id, bpm, duration_sec, created_at FROM song_analyses WHERE song_id = '{song_id}';"
   <!-- docker exec ai-music-video-postgres psql -U postgres -d ai_music_video -c "SELECT song_id, bpm, duration_sec, created_at FROM song_analyses WHERE song_id = '8136f2bd-6b20-44b6-92c5-45029b9f6ac6';" -->
   
   # Or list all analyzed songs:
   docker exec ai-music-video-postgres psql -U postgres -d ai_music_video -c "SELECT song_id, bpm, duration_sec, created_at FROM song_analyses ORDER BY created_at DESC LIMIT 10;"
   
   # If song hasn't been analyzed yet, trigger analysis:
   curl -X POST http://localhost:8000/api/v1/songs/{song_id}/analyze | jq
   # curl -X POST http://localhost:8000/api/v1/songs/8136f2bd-6b20-44b6-92c5-45029b9f6ac6/analyze | jq
   # Response: {"jobId": "analysis-...", "status": "queued"}
   
   # Check job status (replace {job_id} with the jobId from above, e.g., "analysis-535371a3-24b3-4f3e-b0f2-0ea62d7301cc"):
   curl http://localhost:8000/api/v1/jobs/{job_id} | jq
   # Example: curl http://localhost:8000/api/v1/jobs/analysis-535371a3-24b3-4f3e-b0f2-0ea62d7301cc | jq
   
   # Job status response includes:
   # - status: "queued", "processing", "completed", or "failed"
   # - progress: 0-100 (percentage complete)
   # - analysisId: UUID of analysis record (when completed)
   # - error: Error message (if failed)
   # - result: Full SongAnalysis object (when completed, includes beat_times)
   
   # Poll until status is "completed" or "failed":
   # Example: watch -n 2 'curl -s http://localhost:8000/api/v1/jobs/{job_id} | jq .status'
   # Or check manually every few seconds until analysis completes
   
   # Troubleshooting: If job stays "queued", check if RQ worker is running:
   # 1. Check if Redis is running:
   docker ps | grep ai-music-video-redis
   # Or: redis-cli ping  # Should return "PONG"
   
   # 2. Check if RQ worker process is running:
   ps aux | grep "rq worker ai_music_video"
   
   # 3. If worker is not running, start it (in a separate terminal):
   # cd backend && source ../.venv/bin/activate && rq worker ai_music_video
   # Or use: make dev  # (starts all services including worker)
   
   # 4. Check queue status (if rq-dashboard is installed):
   # rq-dashboard  # Opens dashboard at http://localhost:9181
   
   # 5. If job stays "queued" but worker is running, try:
   # - Restart the worker (it may have lost connection to Redis)
   # - Check worker terminal output for errors
   # - Verify Redis connection: docker exec ai-music-video-redis redis-cli ping
   # - Check if job is in Redis: docker exec ai-music-video-redis redis-cli LLEN "rq:queue:ai_music_video"
   #   (Should show > 0 if jobs are queued)
   
   # Progress milestones:
   # - 25%: Beat detection complete
   # - 50%: Section detection complete
   # - 70%: Mood/genre analysis complete (currently working on lyric extraction)
   # - 85%: Lyric extraction complete
   # - 100%: Analysis complete
   # If stuck at 70%, lyric extraction may be slow or failing (check worker logs)
   
   # 6. If Python crashes when triggering analysis (macOS fork safety issue):
   # - The dev script (make dev) now automatically sets OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
   # - If running worker manually, set: export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
   # - This disables Objective-C runtime fork safety checks that crash in RQ worker processes
   ```

2. **Get beat-aligned boundaries:**
   ```bash
   # Default FPS (24.0)
   curl http://localhost:8000/api/v1/songs/{song_id}/beat-aligned-boundaries | jq
   
   # Custom FPS (e.g., 8 FPS for current video generation API)  <-  our current model
   curl "http://localhost:8000/api/v1/songs/{song_id}/beat-aligned-boundaries?fps=8.0" | jq
   # curl "http://localhost:8000/api/v1/songs/8136f2bd-6b20-44b6-92c5-45029b9f6ac6/beat-aligned-boundaries?fps=8.0" | jq
   
   # Higher FPS for better alignment (e.g., 30 FPS)
   curl "http://localhost:8000/api/v1/songs/{song_id}/beat-aligned-boundaries?fps=30.0" | jq
   ```

3. **Verify response:**
   - Response includes `boundaries[]` array with clip boundaries
   - Each boundary has `startTime`, `endTime`, `durationSec` (should be 3-6 seconds)
   - Each boundary includes beat alignment metadata: `startBeatIndex`, `endBeatIndex`, `startFrameIndex`, `endFrameIndex`
   - Alignment errors: `startAlignmentError`, `endAlignmentError` (in seconds)
   - Validation metrics: `maxAlignmentError`, `avgAlignmentError`, `validationStatus` ("valid" or "warning")
   - Response includes `clipCount`, `songDuration`, `bpm`, `fps`, `totalBeats`

4. **Example response structure:**
   ```json
   {
     "boundaries": [
       {
         "startTime": 0.0,
         "endTime": 4.364,
         "startBeatIndex": 0,
         "endBeatIndex": 8,
         "startFrameIndex": 0,
         "endFrameIndex": 35,
         "startAlignmentError": 0.0,
         "endAlignmentError": 0.011,
         "durationSec": 4.364,
         "beatsInClip": [0, 1, 2, 3, 4, 5, 6, 7, 8]
       },
       ...
     ],
     "clipCount": 3,
     "songDuration": 30.0,
     "bpm": 110.0,
     "fps": 24.0,
     "totalBeats": 55,
     "maxAlignmentError": 0.045,
     "avgAlignmentError": 0.029,
     "validationStatus": "valid"
   }
   ```

5. **Test different scenarios:**
   - **Different BPMs:** Test with songs at different BPMs (80, 110, 140) to verify alignment quality
   - **Different FPS:** Compare alignment errors at 8 FPS vs 24 FPS vs 30 FPS (higher FPS should have lower errors)
   - **Short songs:** Test with songs < 10 seconds (should still produce valid boundaries)
   - **Long songs:** Test with songs > 60 seconds (should produce multiple clips)
