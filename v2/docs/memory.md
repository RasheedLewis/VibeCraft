# Memory

Working on phase: 3
Read MASTER_PLAN, ARCHITECTURE, and then only the part of IMPLEMENTATION_PHASES corresponding to the phase for you to develop
DO NOT modify anything outside of v2/ — ALL of our work will be done in v2/
Put created docs in v2/docs/more/
After completing your assigned work, you will (a) tell me how to run the test script you created, which is always the last sub-phase, and (b) look for opportunities to refactor, and (c) analyze whether there's mission-critical logic we need unit tests for

## Phase 2: Complete ✅
- Backend and frontend implementation complete
- Test script: `bash v2/scripts/for-development/test-phase2.sh`

---

## Phase 3: 3-Agent Split Strategy

**Goal**: Extract BPM (required), beats, genre, mood, lyrics with precise timestamps

**Key Requirements:**
- BPM is required (must be extracted)
- Lyrics extraction MUST run during analysis (before user can section song)
- If no lyrics detected, that's fine - extraction step must complete
- If lyrics are available, they must have precise timestamps for section assignment
- Word-splitting: if word spans sections, include full word in both

### **Agent 1: Analysis Services Agent**
**Focus**: Core analysis services, models, schemas, storage helper
- Subtasks: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.10
- Files to create:
  - `v2/backend/app/models/analysis.py` (Analysis model with song relationship)
  - `v2/backend/app/schemas/analysis.py` (SongAnalysis, AnalysisJobResponse, nested schemas)
  - `v2/backend/app/services/beat_alignment_service.py` (extract_beat_times using librosa)
  - `v2/backend/app/services/bpm_detection_service.py` (detect_bpm using librosa, REQUIRED)
  - `v2/backend/app/services/genre_mood_service.py` (analyze_genre, analyze_mood)
  - `v2/backend/app/services/lyric_extraction_service.py` (extract_lyrics using Whisper/Replicate)
  - `v2/backend/app/services/audio_analysis_service.py` (orchestrator with progress tracking)
- Files to update:
  - `v2/backend/app/services/storage_service.py` (add download_audio_to_temp function)
  - `v2/backend/app/models/__init__.py` (export Analysis model)
- **Key Requirements**:
  - BPM detection is REQUIRED (raise error if cannot detect)
  - Lyrics extraction must run (even if none detected) - sectioning enabled only after this completes
  - Progress tracking: 25% (BPM/beats), 50% (genre/mood), 70% (lyrics), 85% (saved), 100% (complete)
  - Add extensive comments explaining librosa calls and complex logic
- **Dependencies**: Phase 2 must be complete (Song model, S3 storage)
- **Note**: Requires librosa, ffmpeg, Replicate API token for lyrics extraction

### **Agent 2: Worker & API Agent**
**Focus**: RQ worker, API routes, test script
- Subtasks: 3.8, 3.9, 3.12
- Files to create:
  - `v2/backend/app/workers/analysis_worker.py` (RQ worker function: run_analysis_job)
  - `v2/scripts/for-development/test-phase3.sh` (comprehensive test script)
- Files to update:
  - `v2/backend/app/api/v1/routes_songs.py` (add analysis endpoints):
    - `POST /api/songs/{id}/analyze` (enqueue job, return job_id)
    - `GET /api/jobs/{job_id}` (get job status and progress)
    - `GET /api/songs/{id}/analysis` (get final analysis results)
- **Key Requirements**:
  - Worker updates job status in database
  - API returns milestone-based progress (25%, 50%, 70%, 85%, 100%)
  - Test script verifies all analysis components (BPM required, lyrics extraction completes, timestamps precise)
- **Dependencies**: Agent 1 must be complete (all analysis services)
- **Note**: Requires Redis/RQ worker running for background jobs

### **Agent 3: Frontend Analysis Agent**
**Focus**: Frontend API client for analysis
- Subtasks: 3.11
- Files to update:
  - `v2/frontend/src/api/songs.ts` (add analysis functions):
    - `analyzeSong(songId)` - trigger analysis
    - `getAnalysis(songId)` - get analysis results
    - `getAnalysisJobStatus(jobId)` - poll job status
- **Dependencies**: Agent 2 must be complete (API endpoints ready)
- **Note**: Frontend will poll job status to show progress (milestone-based)
