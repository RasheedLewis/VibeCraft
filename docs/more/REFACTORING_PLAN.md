# Refactoring Plan - Careful Incremental Approach

## Philosophy

We're taking a **careful, incremental approach** to refactoring. After each commit, we will run a complete E2E flow to verify the changes are safe.

## Safety Criteria

A commit is considered **safe** if:
- ✅ A song track uploads successfully
- ✅ Clip generation completes successfully
- ✅ Video composition completes successfully
- ✅ All operations complete in reasonable time
- ✅ No excessive polling or log spam
- ✅ No errors in console or logs

If any of these criteria fail, the commit is **not safe** and should be reverted or fixed before proceeding.

## Approach

We will refactor in **logical groups/chunks** based on what was attempted in the `refactoring` branch. The goal is to break down the large commits from that branch into smaller, more manageable commits that can be verified independently.

## Starting Point

We'll begin by breaking up the **first big commit** from the `refactoring` branch into several smaller commits. This allows us to:
1. Test each logical change independently
2. Identify issues early
3. Maintain a working codebase at each step
4. Build confidence incrementally

## Process

1. **Identify logical grouping** - Review the abandoned refactoring branch commits
2. **Extract a small, cohesive change** - One logical improvement per commit
3. **Make the change** - Implement the refactoring
4. **Run E2E test** - Verify the change doesn't break functionality
5. **Commit if safe** - Only commit if all safety criteria pass
6. **Repeat** - Move to the next logical grouping

## Candidate Commits - Breaking Up Commit 068da39

Based on analysis of commit `068da39` ("Codebase Cleanup and Simplification"), here are the logical groupings for incremental commits. **Note: All section-related refactoring is skipped** - we're keeping section logic in for now.

### Commit 1: Code Cleanup and Deletions

**Chunks within this commit:**

**Chunk 1.1: Remove Trigger.dev Integration**
- Delete `backend/triggers/` directory (composeVideo.ts, example.ts, songAnalysis.ts)
- Delete `trigger.config.ts`
- Update `.gitignore` to remove `.trigger/` directory

**Chunk 1.2: Script Cleanup and Consolidation**
- Delete unused scripts: `check_analysis_jobs.py`, `compose_local.py`, `deploy.sh`, `generate_test_clips.py`, `get_clips_duration.py`, `get_final_video_urls.py`, `get_recent_songs.py`, `loop_audio.py`, `preload_test_clips.py`, `trim_audio.py`
- Create `scripts/db_query.py` (consolidated utility)
- Update `scripts/check_replicate_models.py`
- Update `scripts/dev.sh`

**Chunk 1.3: Remove WIP/Experimental Code**
- Delete `wip/clip_planner.py`
- Delete `wip/test_clip_planner.py`

**Chunk 1.4: Remove Sample/Test Media Files**
- Delete `samples/compTest/clip1.mp4`, `clip2.mp4`, `clip3.mp4`, `clip4.mp4`, `testAudio.mp3`

**Chunk 1.5: Root-Level Package Management Cleanup**
- Delete `package.json` (root level)
- Delete `package-lock.json` (root level)

**Rationale:** All standalone deletions and cleanup with no dependencies on other code. Safest commit to start with.

---

### Commit 2: Configuration and Infrastructure Updates

**Chunks within this commit:**

**Chunk 2.1: Database Configuration Changes**
- Delete `backend/app.db` (SQLite database)
- Update `backend/app/core/config.py` (PostgreSQL by default)

**Chunk 2.2: Environment Configuration Reorganization**
- Move `docs/backend.env.example` → `backend/.env.example`
- Delete `docs/frontend.env.example`

**Chunk 2.3: Git Configuration Updates**
- Add `.stash/` directory (for preserved section types)
- Update `.gitignore` (add `.stash/`, `.cursor/`, remove `.trigger/`)

**Chunk 2.4: Frontend Configuration Updates**
- Update `frontend/src/lib/apiClient.ts`
- Update `frontend/src/vite-env.d.ts`
- Update `frontend/vite.config.ts`

**Chunk 2.5: Backend Model Updates**
- Update `backend/app/models/user.py` (add fields)

**Rationale:** Configuration and infrastructure changes. Requires E2E test to verify database connection, frontend functionality, and API still work.

---

### Commit 3: Documentation and Utilities

**Chunks within this commit:**

**Chunk 3.1: Documentation Reorganization (Moves)**
- Move `docs/adam/BEAT_FRAME_ALIGNMENT.md` → `docs/more/BEAT_ALIGNMENT.md` (with updates)
- Move `docs/DESIGN_SYSTEM.md` → `docs/more/DESIGN_SYSTEM.md`
- Move `docs/PRD.md` → `docs/more/ORIGINAL_PRD.md`

**Chunk 3.2: Documentation Reorganization (Deletions)**
- Delete outdated docs: `README.md`, `MVP_ROADMAP.md`, `ROADMAP.md`, `USER_GUIDE.md`, `VIDEO_PLAYER.md`, `VIDEO_POLLING_FE.md`
- Delete `docs/adam/` directory contents (all outdated planning docs)
- Delete `docs/adam/memory.md`

**Chunk 3.3: Documentation Reorganization (New Docs)**
- Create `docs/more/ADAMS_SCRATCHPAD.md`
- Create `docs/more/CODE_ANALYSIS_REPORT.md`
- Create `docs/more/MUSICAL_ANALYSIS_MODULE.md`
- Create `docs/more/REPLICATE_VIDEO_MODELS.md`
- Create `docs/more/SAMPLE_AUDIO_GUIDE.md`
- Update `docs/ARCH.md`
- Update `docs/DEV_GUIDE.md`

**Chunk 3.4: Restore Video API Testing Scripts**
- Create `video-api-testing/` directory with:
  - `README.md`
  - `requirements.txt`
  - `test_batch.py`
  - `test_interactive.py`
  - `test_seed_variations.py`
  - `test_video.py`

**Rationale:** Documentation and utility additions. No code impact on main application.

---

## Execution Order

The 3 commits are ordered to minimize risk:
1. **Commit 1:** Code cleanup and deletions (safest, no dependencies)
2. **Commit 2:** Configuration and infrastructure (requires E2E verification)
3. **Commit 3:** Documentation and utilities (no code impact)

Each commit should be tested with E2E flow before proceeding to the next.

## Reference

See `docs/more/abandoned_refactoring_branch.md` for details on what was attempted in the previous refactoring branch.

