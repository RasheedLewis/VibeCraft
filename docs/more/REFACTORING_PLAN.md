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

## Backend Refactoring Plan - Commit b83bd9c

Based on commit `b83bd9c` ("Backend Codebase Improvements and Refactorings"), here are the logical groupings for incremental commits:

### Backend Commit 1: Extract Core Infrastructure

**Chunks:**
- **Chunk 1.1:** Extract Queue Management (`backend/app/core/queue.py`)
  - Centralize RQ queue initialization with `@lru_cache`
  - Remove duplicate `_get_queue()` functions from services
  - Consistent timeout handling

- **Chunk 1.2:** Extract Constants (`backend/app/core/constants.py`)
  - Centralize all application constants (timeouts, limits, config)
  - Remove magic numbers and strings from routes and services

**Rationale:** Foundation infrastructure changes. Low risk, improves maintainability.

---

### Backend Commit 2: Error Handling and Exceptions

**Chunks:**
- **Chunk 2.1:** Create Custom Exception Hierarchy (`backend/app/exceptions.py`)
  - Create `VibeCraftError` base class
  - Specific exceptions: `SongNotFoundError`, `ClipNotFoundError`, `AnalysisError`, `ClipGenerationError`, `CompositionError`, etc.

- **Chunk 2.2:** Update Error Handling Throughout Codebase
  - Replace generic `ValueError`/`RuntimeError` with custom exceptions
  - Update API routes to handle specific exception types
  - Better error messages for API consumers

**Rationale:** Improves error handling consistency. Requires E2E test to verify error responses.

---

### Backend Commit 3: Modernize FastAPI and Datetime

**Chunks:**
- **Chunk 3.1:** Modernize FastAPI Lifespan Events (`backend/app/main.py`)
  - Replace deprecated `@app.on_event()` with `lifespan` context manager
  - Fixes 92 deprecation warnings

- **Chunk 3.2:** Modernize Datetime Usage (all models)
  - Replace `datetime.utcnow()` with `datetime.now(UTC)` in all models
  - Fixes 34 deprecation warnings
  - Files: `analysis.py`, `clip.py`, `composition.py`, `song.py`, `user.py`

**Rationale:** Modernization changes. Low risk, removes deprecation warnings.

---

### Backend Commit 4: Repository Pattern and Base Job Service

**Chunks:**
- **Chunk 4.1:** Create Repository Pattern (`backend/app/repositories/`)
  - Create `song_repository.py` and `clip_repository.py`
  - Centralized data access with consistent error handling

- **Chunk 4.2:** Create Base Job Management Class (`backend/app/services/base_job.py`)
  - Abstract `BaseJobService` with generic type parameter
  - Common methods: `update_progress()`, `complete_job()`, `fail_job()`

**Rationale:** Architectural improvements. Requires careful migration and E2E testing.

---

### Backend Commit 5: Remove Dead Code and Update Tests

**Chunks:**
- **Chunk 5.1:** Remove Dead Code
  - Delete `backend/app/services/mock_analysis.py` (726 lines)
  - Update `backend/app/services/__init__.py` and `scene_planner.py`

- **Chunk 5.2:** Consolidate Job Status Endpoint (`backend/app/api/v1/routes_jobs.py`)
  - Unified `/jobs/{job_id}` to handle all job types

- **Chunk 5.3:** Update Tests
  - Fix queue patching in tests (use `core.queue.get_queue`)
  - Update exception expectations
  - Update scene_planner tests

**Rationale:** Cleanup and consolidation. Requires E2E test to verify job status endpoint works.

---

## Frontend Refactoring Plan - Commit 7478443

Based on commit `7478443` ("Frontend Major Refactoring of UploadPage"), here are the logical groupings for incremental commits:

### Frontend Commit 1: Extract Constants and Utilities

**Chunks:**
- **Chunk 1.1:** Extract Constants (`frontend/src/constants/upload.ts`)
  - `ACCEPTED_MIME_TYPES`, `MAX_DURATION_SECONDS`, `SECTION_TYPE_LABELS`, `SECTION_COLORS`, `WAVEFORM_BASE_PATTERN`, `WAVEFORM_BARS`

- **Chunk 1.2:** Extract Utility Functions
  - `frontend/src/utils/formatting.ts` - formatBytes, formatSeconds, formatBpm, etc.
  - `frontend/src/utils/validation.ts` - isSongAnalysis, isClipGenerationSummary, extractErrorMessage
  - `frontend/src/utils/sections.ts` - getSectionTitle, buildSectionsWithDisplayNames, mapMoodToMoodKind
  - `frontend/src/utils/waveform.ts` - parseWaveformJson
  - `frontend/src/utils/audio.ts` - computeDuration
  - `frontend/src/utils/status.ts` - normalizeJobStatus, normalizeClipStatus

**Rationale:** Pure extraction, no logic changes. Low risk.

---

### Frontend Commit 2: Extract Polling Hooks

**Chunks:**
- **Chunk 2.1:** Create Generic Polling Hook (`frontend/src/hooks/useJobPolling.ts`)
  - Generic polling hook for job status with configurable callbacks

- **Chunk 2.2:** Create Specific Polling Hooks
  - `frontend/src/hooks/useAnalysisPolling.ts` - Analysis job polling wrapper
  - `frontend/src/hooks/useClipPolling.ts` - Clip generation polling wrapper
  - `frontend/src/hooks/useCompositionPolling.ts` - Composition job polling wrapper

- **Chunk 2.3:** Update TypeScript Types (`frontend/src/types/song.ts`)
  - Make `JobStatusResponse` generic to support type-safe polling hooks
  - Fix Axios response handling in polling hooks

**Rationale:** Extracts polling logic. Requires E2E test to verify polling still works correctly.

---

### Frontend Commit 3: Extract Upload Components

**Chunks:**
- **Chunk 3.1:** Create Upload Components (`frontend/src/components/upload/`)
  - `UploadCard.tsx` - File upload UI
  - `BackgroundOrbs.tsx` - Animated background
  - `RequirementPill.tsx` - Requirement badge
  - `SummaryStat.tsx` - Stat display
  - `AnalysisProgress.tsx` - Progress indicator
  - `Icons.tsx` - Icon components

- **Chunk 3.2:** Refactor UploadPage to Use New Components
  - Replace inline components with extracted ones
  - Update imports and usage

**Rationale:** Component extraction. Requires E2E test to verify upload flow works.

---

### Frontend Commit 4: Extract Song Components

**Chunks:**
- **Chunk 4.1:** Create Song Components (`frontend/src/components/song/`)
  - `SongTimeline.tsx` - Timeline visualization
  - `WaveformDisplay.tsx` - Waveform visualization
  - `MoodVectorMeter.tsx` - Mood visualization
  - `ClipStatusBadge.tsx` - Clip status badge
  - `AnalysisSectionRow.tsx` - Analysis section row
  - `WaveformPlaceholder.tsx` - Placeholder component
  - `AnalysisSummary.tsx` - Analysis summary display
  - `ClipGenerationPanel.tsx` - Clip generation management

- **Chunk 4.2:** Refactor UploadPage to Use New Components
  - Replace inline components with extracted ones
  - Update imports and usage

**Rationale:** Component extraction. Requires E2E test to verify song display and clip generation work.

---

### Frontend Commit 5: Final Cleanup and Linting

**Chunks:**
- **Chunk 5.1:** Linting and Formatting Fixes
  - Remove unused imports and variables
  - Fix `setState` in `useEffect` warnings (wrapped in `setTimeout`)
  - Fix all Prettier formatting issues
  - Remove unused props

**Rationale:** Final cleanup. Low risk, improves code quality.

---

## Execution Order

**Backend Refactoring:**
1. Backend Commit 1: Core Infrastructure (safest)
2. Backend Commit 3: Modernize FastAPI/Datetime (low risk)
3. Backend Commit 2: Error Handling (requires E2E)
4. Backend Commit 4: Repository Pattern (requires careful testing)
5. Backend Commit 5: Cleanup and Tests (requires E2E)

**Frontend Refactoring:**
1. Frontend Commit 1: Constants and Utilities (safest)
2. Frontend Commit 2: Polling Hooks (requires E2E)
3. Frontend Commit 3: Upload Components (requires E2E)
4. Frontend Commit 4: Song Components (requires E2E)
5. Frontend Commit 5: Final Cleanup (low risk)

Each commit should be tested with E2E flow before proceeding to the next.

## Finishing Refactoring Plan - Commit 51cedcf

Based on commit `51cedcf` ("WIP - Frontend Refactoring, Polling Fixes, and Analysis Logging"), here are the logical groupings for incremental commits to finish the refactoring:

### Finishing Commit 1: Fix Polling Performance Issues

**Chunks:**
- **Chunk 1.1:** Fix Polling Hook Callbacks (`frontend/src/hooks/useAnalysisPolling.ts`, `frontend/src/hooks/useClipPolling.ts`)
  - Memoize all callbacks with `useCallback` to prevent recreation on every render
  - Fix `useClipPolling` to only poll clip summary when no active job exists
  - Ensure stable dependency arrays for all hooks
  - **Problem:** Excessive polling (200+ requests/minute) causing log spam and performance issues
  - **Root Causes:**
    - Callbacks recreated on every render triggering `useEffect` restarts
    - Double polling in `useClipPolling` (job polling + summary polling running simultaneously)
  - **Result:** Polling should run at intended 3-5 second intervals

**Rationale:** Critical performance fix. Requires E2E test to verify polling frequency is correct and no functionality is broken.

---

### Finishing Commit 2: Backend Error Handling for Stale Jobs

**Chunks:**
- **Chunk 2.1:** Improve Clip Generation Error Handling (`backend/app/services/clip_generation.py`)
  - Handle missing clips gracefully instead of raising exceptions
  - Change from raising `ClipNotFoundError` to logging warnings and returning "skipped" status
  - Prevents worker crashes from stale RQ jobs
  - **Problem:** `ClipNotFoundError` exceptions spamming logs from stale RQ jobs

**Rationale:** Improves robustness. Requires E2E test to verify stale jobs don't crash workers.

---

### Finishing Commit 3: Add Analysis Pipeline Logging

**Chunks:**
- **Chunk 3.1:** Add Timing Logs to Song Analysis (`backend/app/services/song_analysis.py`)
  - Add step-by-step timing logs:
    - S3 download time
    - Librosa audio load time
    - Beat tracking time
    - Section detection time
    - Mood/genre computation time
    - Lyric extraction time
    - Database save time

- **Chunk 3.2:** Add Whisper API Timing (`backend/app/services/lyric_extraction.py`)
  - Add specific Whisper API call timing

**Rationale:** Performance monitoring. Low risk, adds observability. Helps identify bottlenecks.

---

### Finishing Commit 4: Test Performance Analysis

**Chunks:**
- **Chunk 4.1:** Fix Test Markings (`backend/tests/unit/test_genre_mood_analysis.py`)
  - Uncomment `test_tension_normalization` (was incorrectly marked as slow)

- **Chunk 4.2:** Generate Test Performance Report
  - Create `TEST_PERFORMANCE_REPORT.md` with actual test timings
  - Document findings: 156 tests in 1.90s, only 1 test >1s (`test_tension_normalization` at 1.11s)

**Rationale:** Test cleanup and documentation. Low risk, improves test suite understanding.

---

## Execution Order for Finishing Refactoring

1. **Finishing Commit 1:** Fix Polling Performance (critical, requires E2E)
2. **Finishing Commit 2:** Backend Error Handling (important, requires E2E)
3. **Finishing Commit 3:** Analysis Pipeline Logging (low risk, observability)
4. **Finishing Commit 4:** Test Performance Analysis (low risk, documentation)

Each commit should be tested with E2E flow before proceeding to the next.

---

## Reference

See `docs/more/abandoned_refactoring_branch.md` for details on what was attempted in the previous refactoring branch.

