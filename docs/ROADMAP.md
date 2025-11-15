# **🚀 AI Music Video Generation Roadmap — With Numbered Subtasks**

Absolutely — here is the **fully numbered PR roadmap**, where **every subtask has its own unique number** for tracking in GitHub Projects, Jira, Linear, etc.

I kept all ordering logical and sequential.

---

## **PR-01 — Project Initialization & Repo Setup** ✅ DONE

1. Initialize monorepo or backend+frontend repos
2. Set up package managers (pnpm / pip / poetry / npm)
3. Add environment templates (`.env.example`)
4. Configure TypeScript backend (or Python FastAPI)
5. Create React/Vite frontend scaffold
6. Set up linting (ESLint, Prettier)
7. Add CI pipeline for linting & typecheck
8. Validate clean build for backend + frontend

**Testing:** Run `make build` and `make lint-all` - both should pass with no errors.

---

## **PR-02 — Audio Upload Service**

1. Create `/api/songs` POST endpoint
2. Implement audio file validation (type, duration)
3. Implement multipart file handling
4. Upload audio file to object storage (S3/Supabase)
5. Generate and store metadata (filename, size, MIME type)
6. Return `songId` and `audioUrl`
7. Build Upload UI screen
8. Show upload success + waveform placeholder UI

**Testing:** Upload an audio file via UI or `curl -X POST /api/songs -F "file=@song.mp3"`. Verify file is stored and `songId`/`audioUrl` are returned. Check upload UI shows success state.

---

## **PR-03 — Audio Preprocessing Pipeline**

1. Implement mono downmix (stereo → mono)
2. Implement resampling to 44.1kHz
3. Extract waveform JSON via librosa
4. Store processed audio file
5. Link processed file to database record
6. Add preprocessing stage to backend analysis job

**Testing:** Upload a stereo audio file, verify processed file is mono/44.1kHz and waveform JSON is generated. Check DB record links to processed file.

---

## **PR-04 — Music Analysis Engine (BPM, Beats, Sections)**

1. Implement BPM detection module
2. Implement beat onset detection
3. Build beat grid time array
4. Implement novelty curve calculation
5. Detect structural boundaries
6. Group repeated segments to identify chorus/verse
7. Implement `/api/songs/:id/analyze` orchestration endpoint
8. Store `SongAnalysis` results in DB
9. Add frontend loading steps for analysis progress

**Testing:** Call `POST /api/songs/:id/analyze` on uploaded song. Verify response includes BPM, beat times, and sections array (intro/verse/chorus). Check frontend shows analysis progress steps.

---

## **PR-05 — Genre & Mood Classification** ✅ DONE

1. Compute mood features: energy, valence, tension
2. Build genre classifier (CLAP / embedding model)
3. Map classification outputs to standardized genres
4. Compute `moodTags` and `moodVector`
5. Integrate genre/mood outputs into analysis object
6. Add genre/mood display UI badges

**Testing:** Run `pytest backend/tests/unit/test_genre_mood_analysis.py -v` (unit tests) and `python backend/tests/test_genre_mood.py` (integration test) with sample audio. Verify analysis response includes `primaryGenre`, `moodTags`, and `moodVector` fields.

---

## **PR-06 — Lyric Extraction & Section Alignment** ✅ DONE

1. Implement Whisper ASR via Replicate API (MVP: Whisper-only approach)
2. Segment ASR output into timed lines
3. Align lyrics to section timestamps *(can use mock sections until PR-04 complete)*
4. Add `sectionLyrics[]` to analysis
5. Display lyric previews inside section cards

**Future enhancements (not in MVP):**
- Track recognition API (Shazam/ACRCloud) → fetch lyrics from lyrics API for known tracks
- Lyrics API integration (Musixmatch/Genius) for higher-quality pre-formatted lyrics
- Vocal stem extraction (Demucs/Spleeter) → run Whisper on isolated vocals for better accuracy

**Testing:** Run analysis on song with vocals. Verify `sectionLyrics[]` array is populated with timed text aligned to sections. Check lyric previews appear in section cards.

---

## **PR-07 — Song Profile UI**

1. Build timeline segmented into intro/verse/chorus/etc
2. Create SectionCard component
3. Render mood tags inside section card
4. Render lyric snippet inside section card
5. Add Generate/Regenerate buttons
6. Add waveform visual under header
7. Display genre + mood summary

**Testing:** Navigate to song profile page. Verify timeline shows all sections, each SectionCard displays mood tags and lyrics from PR-05/PR-06 data. Check genre/mood summary appears at top.

---

## **PR-08 — Section Scene Planner (Template + Prompt Builder)** ✅ DONE

1. Implement template definitions (Abstract first)
2. Map mood to intensity + color palette
3. Map genre to camera motion presets
4. Map section type to shot patterns
5. Build function `buildSceneSpec(sectionId)`
6. Implement prompt builder combining all features
7. Add internal endpoint `/build-scene` for debugging

**Testing:** Call `POST /build-scene` with a sectionId. Verify response includes scene spec with prompt, color palette, camera motion, and shot pattern derived from section's mood/genre/type.

---

## **PR-09 — Section Video Generation Pipeline**

1. Connect backend to Replicate API
2. Build `generateSectionVideo(sceneSpec)` function
3. Implement AI job polling utility
4. Persist `SectionVideo` record on completion
5. Save seed, prompts, duration, resolution metadata
6. Build frontend loading spinner for generation
7. Build video preview player UI
8. Build "Regenerate Section Video" button

**Testing:** Click "Generate" on a section card. Verify loading spinner appears, backend polls Replicate job, video is generated and saved. Check video preview player displays generated clip and "Regenerate" button works.

---

## **PR-10 — Section Clip Management**

1. Allow "approve" clip for a section
2. Add ability to store selected clipId in section mapping
3. Show approved clip badge in UI
4. Add "Use in Full Video" button
5. Prevent overwrite when clip is approved (unless explicitly regenerated)
6. Allow viewing all generated clips per section

**Testing:** Approve a generated clip, verify badge appears and clipId is stored. Regenerate should require confirmation. Check "Use in Full Video" button is enabled and all clips are viewable.

---

## **PR-11 — Full Song Scene Planner**

1. Build `buildFullScenePlan(songId)`
2. Evaluate each section for approved clip
3. Insert approved clips into plan
4. Queue generation for missing clips
5. Validate timing across entire track
6. Store scene array in DB for final render

**Testing:** Call `POST /api/songs/:id/build-full-plan` on song with mix of approved/unapproved sections. Verify plan includes approved clips and queues generation for missing ones. Check timing validation passes.

---

## **PR-12 — Full-Length Video Generation**

1. Implement parallel execution for all section generation tasks
2. Track clip generation jobs and pipe into completion aggregator
3. Force global style consistency (seed inheritance, shared style tokens)
4. Normalize all clips to same aspect ratio
5. Save raw section clips for composition stage

**Testing:** Trigger full video generation. Verify all section clips generate in parallel, job tracking shows progress, generated clips share consistent style tokens, and all clips have matching aspect ratio.

---

## **PR-13 — Video Composition Engine**

1. Concatenate video clips in correct timeline order
2. Insert beat-matched transitions (cut, zoom, flare)
3. Normalize resolution to 1080p
4. Normalize FPS to 30+
5. Apply color grading LUT
6. Mux original song audio with video timeline
7. Export MP4/WebM
8. Upload final output to cloud storage

**Testing:** Run composition on full song with all clips. Verify clips are in correct order, transitions align with beats, output is 1080p/30fps, audio is synced, and final video is uploaded to storage.

---

## **PR-14 — Full Video Generation API**

1. Endpoint: `POST /api/songs/:id/generate-full-video`
2. Create job entry
3. Trigger:
   - Scene planning
   - Section generation
   - Composition engine
4. Add job status polling endpoint
5. Add progress UI ("Generating", "Compositing", "Finalizing")

**Testing:** Call full video generation endpoint, poll status endpoint. Verify job progresses through "Generating" → "Compositing" → "Finalizing" stages. Check frontend progress UI updates accordingly.

---

## **PR-15 — Deployment (MVP Release)**

1. Deploy backend API
2. Deploy frontend app
3. Configure environment variables (Replicate keys, S3, etc.)
4. Add HTTPS/SSL configuration
5. Add logging + request tracing
6. Add basic rate limiting
7. Test upload → analysis → generation end-to-end in production

**Testing:** Perform full end-to-end test in production: upload song → analyze → generate sections → compose full video. Verify HTTPS works, logs are captured, and rate limiting prevents abuse.

---

## **PR-16 — Sample Videos & Showcase**

1. Generate high-energy music video example
2. Generate slow emotional music video example
3. Generate complex transition-heavy example
4. Create demo gallery page in frontend
5. Add sample outputs to README
6. Ensure all samples meet 1080p + beat-sync requirements

**Testing:** Navigate to demo gallery page. Verify all three sample videos display, play correctly, and meet 1080p/beat-sync quality standards. Check README includes sample links.

---

## **PR-17 — Cost Optimization & Caching**

1. Add caching for analysis results
2. Cache scene prompts to avoid reconstruction
3. Cache embeddings for genre/mood
4. Avoid duplicate generation of approved section videos
5. Add per-video cost tracking utilities
6. Reduce calls to expensive models via shared seeds/style tokens

**Testing:** Re-analyze same song twice, verify second call uses cached results. Check cost tracking shows reduced API calls. Verify approved clips are not regenerated unless explicitly requested.

---

## **PR-18 — Final Polish & Bugfixes**

1. Improve frontend loading indicators
2. Add error toast notifications
3. Improve retry logic for AI inference failures
4. Fix lyric misalignment edge cases
5. Smooth out transition timing
6. Apply final performance tuning (async optimizations, concurrency)
7. Final UX review and cleanup

**Testing:** Test error scenarios (API failures, network issues) - verify toast notifications appear and retry logic works. Check loading indicators are smooth and transitions are beat-synced. Perform full UX walkthrough.

---

## **Done — Complete Numbered Roadmap**

If you'd like next:

## **⬜ Generate MERMAID diagrams for PR flow**

## **⬜ Turn each PR & subtask into GitHub Issues (ready to paste)**

## **⬜ Create project folder structure**

## **⬜ Add estimated time per PR (48h MVP version)**

Tell me which you want.
