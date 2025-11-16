# **🎯 VibeCraft MVP Roadmap — Focused on Core Requirements**

This is a **lean, focused MVP roadmap** that prioritizes three core requirements:

1. **Audio visual sync** (video matches audio timing/beats)
2. **Multi clip composition** (3-5 clips stitched together)
3. **Consistent visual style** across clips

**Note:** We are temporarily abandoning section-based workflows for MVP. The MVP will generate multiple clips for the entire song and stitch them together.

---

## **✅ Completed Foundation (PRs 1-9)**

The following PRs are **already complete** and provide the foundation for MVP:

- **PR-01:** Project Initialization & Repo Setup ✅
- **PR-02:** Audio Upload Service ✅
- **PR-03:** Audio Preprocessing Pipeline ✅
- **PR-04:** Music Analysis Engine (BPM, Beats, Sections) ✅
- **PR-05:** Genre & Mood Classification ✅
- **PR-06:** Lyric Extraction & Section Alignment ✅
- **PR-07:** Song Profile UI ✅
- **PR-08:** Section Scene Planner (Template + Prompt Builder) ✅
- **PR-09:** Section Video Generation Pipeline ✅

**What we have:**

- Audio upload and preprocessing
- BPM detection and beat grid
- Genre/mood classification
- Scene planning and prompt generation
- Single video clip generation via Replicate API
- Basic UI for song profile

**What we're simplifying for MVP:**

- No section-based generation (generate clips for entire song)
- No section approval workflow
- No section-level UI controls

---

## **MVP-01 — Multi-Clip Generation for Full Song (Time-Based Boundaries)** ✅ **Done (Rasheed)**

**Goal:** Generate 3-5 video clips for an entire song using simple time-based boundaries.

1. Define clip planning service that snaps boundaries to beat grid and frame intervals
2. Persist planned clips (start/end/beats/duration) with status tracking + metadata columns
3. Expose planning APIs (`POST /api/songs/:id/clips/plan` + `GET /api/songs/:id/clips`) to generate/head list plans
4. Enqueue per-clip generation jobs (controlled concurrency) that hit Replicate
5. Support variable clip lengths (3–15s) converted to `num_frames` for 8 fps models
6. Track per-clip job status and aggregate progress (`completed/total`)
7. Expose endpoint for multi-clip generation job + status (reuse job poller)
8. Frontend: multi-clip generation UI
   - 8a. Poll `/api/songs/:id/clips/status` alongside job poller and manage polling lifecycle
   - 8b. Render progress panel (“Generating clip X of N…”) with active clip metadata + cancel/compose actions
   - 8c. Display clip list rows with status badges, duration/frames/beats, and per-status actions (preview/regenerate/retry)
   - 8d. Surface completed clip visuals (thumbnail strip or mosaic) and empty/error states
9. Record 8 fps and frame counts in metadata for downstream composition

**Note:** Clips will be 3-6 seconds each, totaling the song duration. Uses simple time-based boundaries (no beat alignment yet). Generated clips are at 8 FPS (from Replicate API), which will be upscaled to 30+ FPS during composition. Beat alignment will be added in MVP-02.

**Testing:** Generate video for a 30-second song. Verify 3-5 clips are generated, each clip's duration is between 3-6s, total duration equals song duration, individual clip success/failure is tracked, and FPS metadata is stored. Check frontend shows progress for multi-clip generation.

---

## **MVP-02 — Beat Alignment Calculation & Planning** ✅ **Done (Adam)**

**Goal:** Calculate beat-aligned clip boundaries (independent of clip generation).

1. Implement beat-to-frame alignment algorithm (see `docs/BEAT_FRAME_ALIGNMENT.md`)
2. Build helper function to calculate optimal clip boundaries from beat grid
3. Account for video generation API FPS (8 FPS) when calculating beat-to-frame alignment:
   - Beat interval: `60 / BPM` seconds
   - Frame interval: `1 / 8 = 0.125` seconds
   - Use nearest frame to each beat for alignment
4. Adjust clip durations to match nearest beats (within 3-6s constraints)
5. Create API endpoint: `GET /api/songs/:id/beat-aligned-boundaries` that returns calculated boundaries
6. Store beat alignment metadata (which beats each boundary aligns with)
7. Add validation to ensure boundaries don't drift from beat grid

**Note:** This PR focuses on **calculation and planning only** - it doesn't require clips to exist. Can work in parallel with MVP-01. The calculated boundaries can be used by MVP-01 for generation, or applied retroactively to existing clips.

**Testing:** Calculate beat-aligned boundaries for a song with known BPM (e.g., 110 BPM). Verify boundaries align with beat times (within acceptable tolerance, accounting for 8 FPS frame intervals). Test with different BPMs and song lengths.

---

## **MVP-03 — Video Composition & Stitching (Backend)** ✅ **Done (Adam)**

**Goal:** Stitch 3-5 clips together into a single video (works with any clips, beat-aligned or not).

1. Implement video concatenation using FFmpeg
2. Accept clips in any order (will be sorted by start_time)
3. Insert transitions at clip boundaries:
   - Hard cuts (basic implementation first)
   - Optional: Beat-synced cuts (if beat metadata available from MVP-11)
   - Optional: Light flares or zoom effects (if time permits)
4. Normalize all clips to same resolution (1080p) and FPS (30+)
   - Upscale from source 8 FPS to 30+ FPS using frame interpolation
5. Apply color grading LUT for consistency (basic pass)
6. Mux original song audio with video timeline
7. Ensure no audio drift (audio and video stay in sync)
8. Export final MP4/WebM
9. Upload final output to cloud storage
10. Create API endpoint for composition: `POST /api/songs/:id/compose`

**Note:** This can work with clips from MVP-01 (time-based) or MVP-02 (beat-aligned). Beat-synced transitions are optional enhancement. This comes before style consistency (MVP-04) to validate the stitching pipeline works end-to-end.

**Testing:** Stitch 3-5 clips together (can use time-based clips from MVP-01). Verify clips are in correct order, output is 1080p/30fps, audio is synced with video, and final video plays correctly. Test with beat-aligned clips when MVP-02 is complete.

---

## **MVP-04 — Prompt Experimentation + Consistent Visual Style** 🔬 **Adam → then together**

**Goal:** Maintain visual coherence across all clips in a song through systematic prompt engineering and experimentation.

1. **Run extensive tests and collect results:**
   - Generate multiple test videos with different prompt variations
   - Document outcomes for each variation (visual quality, style consistency, coherence)
   - Create a test catalog/database of prompt → video results

2. **Experiment with different templates:**
   - Test existing scene planner templates with various songs/genres
   - Create new template variations for different moods and genres
   - Compare template effectiveness across different musical styles
   - Document which templates work best for which genres/moods

3. **Test different Replicate models:**
   - Compare `anotherjesse/zeroscope-v2-xl` with alternative models
   - Evaluate model-specific features (seed support, style tokens, context persistence)
   - Document model capabilities and limitations
   - Test model switching strategies (same model vs. model-specific prompts)

4. **Catalog prompt → video mapping:**
   - Build a database/catalog of successful prompt patterns
   - Map prompt components to visual outcomes (color, mood, aesthetic, motion)
   - Document prompt engineering patterns that produce consistent results
   - Create a prompt library organized by genre, mood, and visual style

5. **Targeted prompt tweaks and iteration:**
   - Test incremental prompt modifications (single word/phrase changes)
   - Measure impact of specific prompt components (adjectives, style descriptors, motion verbs)
   - Document which tweaks produce desired visual changes
   - Create a prompt tuning workflow for fine-tuning visual style

6. **Advanced prompt engineering techniques:**
   - Research and experiment with prompt engineering techniques for style consistency
   - Test seed inheritance and shared style tokens across clips
   - Experiment with style reference images or embeddings (if supported by model)
   - Test prompt chaining and context persistence across multiple video generation calls
   - Investigate if Replicate API supports style transfer or reference-based generation

7. **Style consistency implementation:**
   - Generate a "style seed" for the entire song that all clips inherit
   - Develop prompt templates that maintain visual coherence (color palette, mood, aesthetic)
   - Implement style consistency parameters in scene planner and video generation services
   - Test style consistency across multiple clips for the same song

8. **Documentation and guidelines:**
   - Document successful techniques and create style consistency guidelines
   - Create a style consistency playbook with best practices
   - Document limitations, trade-offs, and edge cases discovered
   - Add style consistency validation/testing utilities

**Note:** This PR comes after MVP-03 (stitching) so we can validate the full pipeline works first, then improve style quality. Adam will lead the initial experimentation phase, then both developers will collaborate on implementation. Expect significant iteration and testing. The experimental phase should produce a comprehensive catalog of what works and what doesn't.

**Testing:** Generate multiple clips for a song with style consistency enabled. Verify visual style consistency (colors, mood, aesthetic) across all clips. Stitch clips together and verify cohesive look in final video. Test across different genres and song lengths. Document any limitations or trade-offs discovered.

---

## **MVP-05 — Web UI Editor for Clip Boundaries** 👤 **Assigned: Rasheed**

**Goal:** Allow users to manually adjust clip boundaries with a visual editor.

1. Build timeline UI component with draggable playhead
2. Display audio waveform and beat markers on timeline
3. Implement draggable clip boundary markers
4. Add snap-to-beat functionality (boundaries snap to nearest beat)
5. Show visual feedback when boundary is snapped to beat
6. Allow users to add/remove clip boundaries
7. Validate boundaries (must be within song duration, maintain 3-6s clip constraints)
8. Save user-defined boundaries to backend
9. Use custom boundaries for clip generation instead of auto-planned boundaries
10. Add "Reset to Auto" button to revert to automatic planning

**Note:** This is optional for MVP - auto-planned boundaries (MVP-02) can be used if UI editor is not ready.

**Testing:** Open editor for a song. Drag clip boundaries on timeline, verify they snap to beats. Add/remove boundaries, verify validation works. Save boundaries and verify they're used for clip generation.

---

## **MVP-06 — Full Song Video Generation API**

**Goal:** Single API endpoint that orchestrates the entire MVP pipeline.

1. Endpoint: `POST /api/songs/:id/generate-video`
2. Create job entry in database
3. Orchestrate the pipeline:
   - Get song analysis (BPM, beats, genre, mood)
   - Plan 3-5 clips with beat-aligned boundaries (or use user-defined from MVP-05)
   - Generate clips in parallel with consistent style (MVP-04)
   - Stitch clips together with beat-synced transitions (MVP-03)
   - Mux audio and export final video
4. Add job status polling endpoint: `GET /api/jobs/:jobId`
5. Add progress UI showing stages:
   - "Planning clips..."
   - "Generating clip 1 of 4..."
   - "Generating clip 2 of 4..."
   - "Stitching clips..."
   - "Finalizing..."
   - "Complete"

**Testing:** Call full video generation endpoint, poll status endpoint. Verify job progresses through all stages, final video is generated, and frontend progress UI updates accordingly.

---

## **MVP-07 — Deployment**

**Goal:** Deploy MVP to production environment.

1. Set up production infrastructure (hosting, database, storage)
2. Configure environment variables and secrets management
3. Deploy backend API (FastAPI) to production server
4. Deploy frontend (React/Vite) to CDN or static hosting
5. Set up production database (PostgreSQL)
6. Configure S3 bucket for production storage
7. Set up RQ workers for background job processing
8. Configure FFmpeg in production environment
9. Set up monitoring and logging
10. Configure domain and SSL certificates
11. Test production deployment end-to-end
12. Document deployment process and runbooks

**Testing:** Verify all services work in production environment. Test full pipeline (upload, analysis, generation, composition) in production. Monitor for errors and performance issues.

---

## **MVP-08 — MVP Polish & Testing**

**Goal:** Ensure MVP works end-to-end and is ready for demo.

1. Test full pipeline with various song lengths (30s, 60s, 90s)
2. Verify audio-visual sync across different BPMs (80-140 BPM)
3. Test style consistency across different genres
4. Fix any audio drift issues
5. Improve error handling and retry logic
6. Add basic loading states and error messages in UI
7. Test edge cases (very short songs, very long songs, songs with variable tempo)
8. Document known limitations

**Testing:** Perform end-to-end tests with multiple songs. Verify all three core requirements are met:

- ✅ Audio visual sync (transitions at beats)
- ✅ Multi clip composition (3-5 clips stitched)
- ✅ Consistent visual style (cohesive look across clips)

---

## **MVP Success Criteria**

By the end of MVP-08, the system must:

1. ✅ **Audio Visual Sync:** Video transitions align with audio beats (within acceptable tolerance)
2. ✅ **Multi Clip Composition:** Successfully stitch 3-5 clips together into a single video
3. ✅ **Consistent Visual Style:** All clips in a song share a cohesive visual aesthetic

**Demo Ready:** User can upload a song, click "Generate Video", and receive a complete music video with beat-synced visuals.

---

## **What's Deferred (Post-MVP)**

These features will be implemented after MVP is complete:

- Section-based generation and approval workflow
- Individual section video preview and regeneration
- Full song scene planning with section mapping
- Clip approval and selection UI
- Cost optimization and caching
- Sample videos and showcase gallery
- Advanced transitions and effects

---

## **Estimated Timeline**

- **MVP-01:** ✅ 2-3 days (multi-clip generation) - **Done (Rasheed)**
- **MVP-02:** ✅ 1-2 days (beat alignment) - **Done (Adam)**
- **MVP-03:** ✅ 2-3 days (composition & stitching - backend) - **Done (Adam)**
- **MVP-04:** 5-7 days (prompt experimentation + style consistency - experimental, Adam leads then collaboration)
- **MVP-05:** 2-3 days (web UI editor for clip boundaries - optional) - **Assigned: Rasheed**
- **MVP-06:** 1-2 days (API orchestration)
- **MVP-07:** 2-3 days (deployment)
- **MVP-08:** 1-2 days (polish & testing)

**Total MVP:** ~15-23 days remaining (MVP-01, 02, 03 complete)

---

## **Key Technical Decisions for MVP**

1. **Simplified Architecture:** Generate clips for entire song, not per-section
2. **Beat Alignment:** Use beat grid to align clip boundaries and transitions
3. **Style Consistency:** Research and implement prompt engineering + seed inheritance
4. **Composition:** Use FFmpeg for stitching, focus on beat-synced hard cuts
5. **Testing:** Focus on 30-90 second songs for MVP (easier to test and iterate)

---

## **Dependencies & Integration Points**

### **Dependency Graph**

```text
Foundation (PRs 1-9) ✅
    │
    ├─→ PR-04 (Beat Grid) ──────┐
    ├─→ PR-08 (Scene Planner)   │
    └─→ PR-09 (Video Generation)│
            │                    │
            │                    │
    ┌───────┴────────┐          │
    │                │          │
    ▼                ▼          ▼
┌──────────┐   ┌──────────┐  ┌──────────┐
│ MVP-01   │   │ MVP-02   │  │ MVP-03   │
│ Multi-   │   │ Beat     │  │ Composi- │
│ Clip Gen │   │ Align    │  │ tion &   │
│ (Time-   │   │ (Calc)   │  │ Stitch   │
│ Based)   │   │          │  │          │
│ ✅ Done  │   │ ✅ Done  │  │ ✅ Done  │
│ (Rasheed)│   │ (Adam)   │  │ (Adam)   │
└──────────┘   └──────────┘  └──────────┘
    │                │              │
    │                │              │
    └────────┬───────┴──────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │   MVP-04                     │ 🔬 Adam → together
    │ Prompt Experimentation +     │
    │ Consistent Visual Style      │
    └──────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
    ▼                 ▼
┌─────────┐    ┌──────────────┐
│ MVP-05  │    │   MVP-06     │
│ UI Edit │    │ Full API     │
│(Optional)│   │ Orchestration│
│Rasheed  │    │              │
└─────────┘    └──────────────┘
                      │
                      ▼
               ┌──────────────┐
               │   MVP-07     │
               │  Deployment  │
               └──────────────┘
                      │
                      ▼
               ┌──────────────┐
               │   MVP-08     │
               │ Polish & Test│
               └──────────────┘
```

### **Detailed Dependencies**

- **MVP-01** depends on:
  - PR-09 (video generation)
  - Existing `plan_clips_for_section()` helper
  - **No dependency on MVP-02** - uses simple time-based boundaries

- **MVP-02** depends on:
  - PR-04 (beat grid from analysis)
  - **No dependency on MVP-01** - calculates boundaries independently
  - Can work in parallel with MVP-01

- **MVP-03** depends on:
  - MVP-01 (needs clips to stitch, but can use time-based clips)
  - **No dependency on MVP-02** - works with any clips, beat-aligned or not
  - Can work with MVP-01 clips while MVP-02 is in progress

- **MVP-04** depends on:
  - PR-08 (scene planner)
  - MVP-01 (multi-clip generation) ✅
  - MVP-03 (stitching pipeline validated) ✅
  - 🔬 **Adam leads experimentation, then collaborative implementation**

- **MVP-05** depends on:
  - MVP-02 (beat alignment for snap-to-beat) ✅
  - MVP-03 (stitching works - validates boundaries) ✅
  - **Assigned: Rasheed**
  - **Optional:** Can be deferred if time is limited

- **MVP-06** depends on:
  - MVP-01 (multi-clip generation)
  - MVP-02 (beat alignment - optional, can use time-based if not ready)
  - MVP-03 (composition & stitching)
  - MVP-04 (style consistency)
  - MVP-05 (optional - UI editor)

- **MVP-07** depends on:
  - MVP-06 (complete pipeline)

- **MVP-08** depends on:
  - MVP-07 (production deployment)

### **Critical Path**

The critical path (minimum required sequence) is:

```text
PR-09 → MVP-01 ✅ → MVP-03 ✅ → MVP-04 → MVP-06 → MVP-07 → MVP-08
```

**MVP-02 (Beat Alignment)** ✅ can be done in parallel with MVP-01 and MVP-03, then integrated later.

**MVP-05 (UI Editor)** is optional and can be done in parallel with MVP-04 or deferred.

### **Parallel Work Opportunities**

- **MVP-01, MVP-02, and MVP-03 can all work in parallel:** ✅ **All complete**
  - **MVP-01:** ✅ Generate clips with time-based boundaries (independent) - **Done (Rasheed)**
  - **MVP-02:** ✅ Calculate beat-aligned boundaries (independent, just needs beat grid) - **Done (Adam)**
  - **MVP-03:** ✅ Stitch clips together (needs MVP-01 clips, but doesn't need MVP-02) - **Done (Adam)**

- **Integration points:**
  - MVP-01 can optionally use MVP-02's calculated boundaries (if ready)
  - MVP-03 can optionally use beat metadata from MVP-02 for better transitions (if ready)
  - Both work independently if the other isn't ready

- **MVP-04** (Style Consistency) can start after MVP-03 is validated:
  - MVP-03 (stitching) can be built and tested with basic clips
  - MVP-04 (style consistency) can improve clips while MVP-03 is being refined

- **MVP-05** (UI Editor) can be built in parallel with MVP-04:
  - UI Editor is frontend-only (depends on MVP-02 for beat data)
  - Can be developed while MVP-04 (style consistency) is being researched

---

## **Risk Mitigation**

1. **Style Consistency:** If prompt engineering doesn't work well, document limitations and use best-effort approach
2. **Beat Alignment:** If beat detection is inaccurate, fall back to time-based boundaries
3. **Audio Drift:** Use FFmpeg's audio sync features and test thoroughly
4. **Replicate API Limits:** Have fallback plans for rate limits and timeouts
