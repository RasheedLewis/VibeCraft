# Implementation Phases — Detailed Breakdown

This document provides granular, step-by-step breakdown of each implementation phase. Each phase is designed to be independently testable and build incrementally.

**Before implementing any phase, read [`MASTER_PLAN.md`](MASTER_PLAN.md#implementation-guidelines) first for implementation guidelines, code quality standards, testing strategy, and pre-commit checklists.**

---

## Phase 0: Foundation & Setup

**Goal**: Project structure, dependencies, configuration

### Subtasks

#### 0.1 Backend Project Structure
- [ ] Create `v2/backend/app/` directory structure
- [ ] Create `v2/backend/app/__init__.py`
- [ ] Create `v2/backend/app/core/__init__.py`
- [ ] Create `v2/backend/app/api/__init__.py`
- [ ] Create `v2/backend/app/api/v1/__init__.py`
- [ ] Create `v2/backend/app/models/__init__.py`
- [ ] Create `v2/backend/app/schemas/__init__.py`
- [ ] Create `v2/backend/app/services/__init__.py`
- [ ] Create `v2/backend/app/workers/__init__.py`

#### 0.2 Backend Dependencies
- [ ] Create `v2/backend/requirements.txt` with:
  - fastapi, uvicorn
  - sqlmodel, psycopg
  - pydantic, pydantic-settings
  - python-dotenv
  - python-multipart
  - boto3 (S3)
  - replicate
  - rq (Redis Queue for background jobs)
  - redis (Redis client)
  - librosa, ffmpeg-python
  - pytest, pytest-asyncio
- [ ] Document each dependency's purpose

#### 0.3 Backend Core Files
- [ ] Create `v2/backend/app/core/config.py`:
  - Settings class with Pydantic Settings
  - Database URL, Redis URL, S3 config
  - Replicate API token
  - Environment-based config (dev/prod)
  - CORS origins configuration
- [ ] Create `v2/backend/app/core/database.py`:
  - SQLModel engine setup
  - Session dependency
  - Database initialization function
- [ ] Create `v2/backend/app/core/logging.py`:
  - Structured logging setup
  - Log levels configuration
- [ ] Create `v2/backend/app/models/job.py`:
  - Job model (SQLModel)
  - Fields: id, song_id (FK, optional), video_id (FK, optional), job_type, status, progress, error_message, created_at
  - Relationships to Song and Video
  - Note: song_id used for analysis, generation, composition jobs; video_id used for regeneration jobs

#### 0.4 Backend Main Application
- [ ] Create `v2/backend/app/main.py`:
  - FastAPI app factory
  - CORS middleware
  - Health check endpoint
  - Router registration (placeholder)
  - Startup event (init database)

#### 0.5 Frontend Project Bootstrap
- [ ] Bootstrap frontend project using Vite generator:
  - Run `npm create vite@latest frontend -- --template react-ts` in `v2/` directory
  - This creates `v2/frontend/` with React + TypeScript template
- [ ] Create additional directories in `v2/frontend/src/`:
  - `v2/frontend/src/components/` directory
  - `v2/frontend/src/pages/` directory
  - `v2/frontend/src/api/` directory
  - `v2/frontend/src/types/` directory
  - `v2/frontend/src/styles/` directory

#### 0.6 Frontend Dependencies
- [ ] Install additional dependencies in `v2/frontend/`:
  - `@tanstack/react-query` (for API calls)
  - `tailwindcss`, `postcss`, `autoprefixer`
  - Design system dependencies
- [ ] Document each dependency's purpose

#### 0.7 Frontend Configuration
- [ ] Update `v2/frontend/vite.config.ts` (created by Vite):
  - Add path aliases
  - Add proxy for API (dev)
- [ ] Update `v2/frontend/tsconfig.json` (created by Vite):
  - Add path mappings
- [ ] Create `v2/frontend/tailwind.config.ts`:
  - Tailwind configuration
  - Design system tokens

#### 0.8 Frontend Entry Points
- [ ] Update `v2/frontend/src/main.tsx` (created by Vite):
  - Add Query client setup
- [ ] Update `v2/frontend/src/App.tsx` (created by Vite):
  - Add basic router setup (placeholder)
  - Add route definitions (placeholder)

#### 0.9 Environment Configuration
- [ ] Create `v2/.env.example` with:
  - Database URL
  - Redis URL and queue name
  - S3 bucket, access key, secret key
  - Replicate API token
  - Secret key (JWT)
  - Environment (dev/prod)
  - CORS origins
- [ ] Document each environment variable
- [ ] **Environment validation** (from IMPLEMENTATION_CHALLENGES.md):
  - Add environment validation in `main.py` (check on startup, fail fast if missing)
  - Validate all required variables on application startup

#### 0.10 Deployment Infrastructure Setup
- [ ] Create `v2/Makefile`:
  - `make start` / `make dev` - Start all services locally (backend, worker, frontend, Redis)
    - Runs comprehensive pre-flight checks before starting:
      - Checks if venv exists
      - Checks and installs backend dependencies (pip install -r requirements.txt)
      - Checks and installs frontend dependencies (npm install if node_modules missing)
      - Runs frontend linting (fails if linting errors)
      - Runs backend linting (ruff check, fails if linting errors)
      - Builds frontend (fails if build errors)
      - Verifies backend imports (fails if import errors)
      - Runs frontend tests (optional, doesn't fail if no tests)
      - Runs backend tests (optional, doesn't fail if no tests)
    - Only starts services if all checks pass
  - `make install` - Install dependencies (backend + frontend)
  - `make migrate` - Run database migrations
  - `make test` - Run tests
  - `make lint` - Run linters (frontend + backend)
  - `make lint-fix` - Auto-fix linting issues
  - `make format` - Check code formatting
  - `make format-fix` - Auto-format code
  - `make lint-all` - Auto-fix linting and format all code
  - `make build` - Build frontend
  - `make stop` - Stop all dev services (backend, worker, frontend, Redis)
  - `make clean` - Clean build artifacts
- [ ] Create `v2/scripts/dev.sh`:
  - Comprehensive pre-flight check script:
    - Checks venv existence
    - Activates venv
    - Checks and installs backend dependencies
    - Checks and installs frontend dependencies
    - Runs frontend linting (exits on failure)
    - Runs backend linting (exits on failure)
    - Builds frontend (exits on failure)
    - Verifies backend imports (exits on failure)
    - Runs tests (optional, doesn't fail if no tests)
  - Starts all services only after all checks pass:
    - Backend API (uvicorn with --reload)
    - Frontend dev server (Vite)
    - RQ worker (rq worker ai_music_video)
    - Redis (via Docker if not using Railway Redis)
  - Handles cleanup on exit (SIGINT/SIGTERM)
  - Called by `make start` / `make dev`
- [ ] Create `v2/infra/docker-compose.yml` (for local development):
  - Backend service
  - Frontend service (optional, can use Vite dev server)
  - PostgreSQL service (for local database)
  - Environment variables
  - Volume mounts
  - Redis service (for job queue)
- [ ] Create `v2/infra/Dockerfile.backend`:
  - Python 3.10+ base image
  - Install dependencies
  - Copy application code
  - Expose port
  - CMD to run uvicorn
- [ ] Create `v2/scripts/health-check.sh`:
  - Check backend health
  - Check database connection
  - Check S3 access
  - Check Redis connection
- [ ] Set up Redis:
  - Local: `docker run -d -p 6379:6379 --name vibecraft-redis redis:7-alpine`
  - Or use Railway Redis addon (for production)
  - Test Redis connection: `redis-cli ping` (should return PONG)
- [ ] Create `v2/docs/DEPLOYMENT.md`:
  - Local development setup
  - Railway backend deployment (basic steps)
  - Vercel frontend deployment (basic steps)
  - Redis setup
  - AWS S3 + CloudFront setup (basic steps)
  - Environment variables reference

#### 0.11 Test Script
- [ ] Create `v2/scripts/for-development/test-phase0.sh`:
  - Check Python version (3.10+)
  - Check Node version (18+)
  - Install backend dependencies
  - Install frontend dependencies
  - Start Redis (via Docker if not using Railway Redis)
  - Start backend server (background)
  - Start RQ worker (background): `rq worker ai_music_video`
  - Start frontend dev server (background)
  - Test health check endpoint
  - Test database connection
  - Test Redis connection
  - Run health check script
  - Cleanup background processes

#### 0.12 Documentation
- [ ] Update `v2/README.md` with:
  - Setup instructions
  - Prerequisites
  - Environment setup
  - Running backend/worker/frontend/Redis
  - Testing
  - Deployment overview (link to DEPLOYMENT.md)

### Files to Create
- `v2/backend/requirements.txt`
- `v2/backend/app/main.py`
- `v2/backend/app/core/config.py`
- `v2/backend/app/core/database.py`
- `v2/backend/app/core/logging.py`
- `v2/backend/app/models/job.py`
- `v2/frontend/tailwind.config.ts` (Vite creates other frontend files)
- `v2/.env.example`
- `v2/Makefile`
- `v2/scripts/dev.sh`
- `v2/infra/docker-compose.yml`
- `v2/infra/Dockerfile.backend`
- `v2/scripts/health-check.sh`
- `v2/backend/app/workers/` (directory for worker functions)
- `v2/docs/DEPLOYMENT.md`
- `v2/scripts/for-development/test-phase0.sh`

### Files to Update
- `v2/README.md`
- `v2/frontend/package.json` (created by Vite, add additional dependencies)
- `v2/frontend/vite.config.ts` (created by Vite, add path aliases and proxy)
- `v2/frontend/tsconfig.json` (created by Vite, add path mappings)
- `v2/frontend/src/main.tsx` (created by Vite, add Query client setup)
- `v2/frontend/src/App.tsx` (created by Vite, add router setup)

### Test Criteria
- ✅ Backend server starts without errors
- ✅ Frontend dev server starts without errors
- ✅ Redis connects successfully
- ✅ RQ worker starts and connects to Redis
- ✅ Health check endpoint returns 200
- ✅ Database connection successful
- ✅ All dependencies installed
- ✅ `make start` runs all services successfully
- ✅ Health check script passes all checks

---

## Phase 1: Authentication

**Goal**: Basic user registration, login, session management

**Key Requirements:**
- Basic email/password only
- No email verification
- No password reset (for MVP)

### Subtasks

#### 1.1 User Model
- [ ] Create `v2/backend/app/models/user.py`:
  - User model (SQLModel)
  - Fields: id, email (unique), password_hash, created_at, video_count, storage_bytes
  - Password hashing utility function
  - Password verification function

#### 1.2 Auth Schemas
- [ ] Create `v2/backend/app/schemas/auth.py`:
  - RegisterRequest (email, password)
  - LoginRequest (email, password)
  - AuthResponse (token, user info)
  - UserRead (public user info)
  - Password validation (min length, etc.)

#### 1.3 Auth Service
- [ ] Create `v2/backend/app/services/auth_service.py`:
  - `register_user(email, password) -> User`
  - `authenticate_user(email, password) -> User | None`
  - `create_access_token(user_id) -> str`
  - `verify_token(token) -> user_id | None`
  - JWT token generation/verification
  - Password hashing (bcrypt)

#### 1.4 Auth API Routes
- [ ] Create `v2/backend/app/api/v1/routes_auth.py`:
  - `POST /api/auth/register` endpoint
  - `POST /api/auth/login` endpoint
  - `POST /api/auth/logout` endpoint (optional for MVP)
  - `GET /api/auth/me` endpoint (get current user)
  - Error handling (duplicate email, invalid credentials)

#### 1.5 Auth Middleware
- [ ] Create `v2/backend/app/api/deps.py`:
  - `get_current_user()` dependency
  - Extract token from Authorization header
  - Verify token and return user
  - Handle authentication errors

#### 1.6 Frontend Auth API Client
- [ ] Create `v2/frontend/src/api/auth.ts`:
  - `register(email, password)` function
  - `login(email, password)` function
  - `logout()` function
  - `getCurrentUser()` function
  - Token storage (localStorage)
  - API client with auth headers

#### 1.7 Frontend Auth Pages
- [ ] Create `v2/frontend/src/pages/LoginPage.tsx`:
  - Email/password form
  - Form validation
  - Error display
  - Redirect on success
  - Link to register page
- [ ] Create `v2/frontend/src/pages/RegisterPage.tsx`:
  - Email/password form
  - Password confirmation
  - Form validation
  - Error display
  - Redirect on success
  - Link to login page

#### 1.8 Frontend Auth Context/State
- [ ] Create `v2/frontend/src/contexts/AuthContext.tsx` (or use React Query):
  - Current user state
  - Login/logout functions
  - Auth status check
  - Protected route wrapper

#### 1.9 Update Main App
- [ ] Update `v2/backend/app/main.py`:
  - Include auth router
- [ ] Update `v2/frontend/src/App.tsx`:
  - Add auth routes
  - Add protected route wrapper
  - Redirect logic (if not logged in)

#### 1.10 Test Script
- [ ] Create `v2/scripts/for-development/test-phase1.sh`:
  - Register new user
  - Verify user in database
  - Login with credentials
  - Verify token returned
  - Get current user with token
  - Test invalid credentials
  - Test duplicate email

### Files to Create
- `v2/backend/app/models/user.py`
- `v2/backend/app/schemas/auth.py`
- `v2/backend/app/services/auth_service.py`
- `v2/backend/app/api/v1/routes_auth.py`
- `v2/backend/app/api/deps.py`
- `v2/frontend/src/pages/LoginPage.tsx`
- `v2/frontend/src/pages/RegisterPage.tsx`
- `v2/frontend/src/api/auth.ts`
- `v2/frontend/src/contexts/AuthContext.tsx` (optional)
- `v2/scripts/for-development/test-phase1.sh`

### Files to Update
- `v2/backend/app/main.py` (add auth routes)
- `v2/frontend/src/App.tsx` (add auth routes, protected routes)

### Test Criteria
- ✅ Can register new user
- ✅ Cannot register duplicate email
- ✅ Can login with valid credentials
- ✅ Cannot login with invalid credentials
- ✅ Token is valid and can be used to get current user
- ✅ Protected routes require authentication

---

## Phase 2: Audio Upload & Storage

**Goal**: Upload audio files, store in S3, basic song model

### Subtasks

#### 2.1 Song Model
- [ ] Create `v2/backend/app/models/song.py`:
  - Song model (SQLModel)
  - Fields: id, user_id (FK), title, duration_sec, audio_s3_key, created_at
  - Relationship to User

#### 2.2 Song Schemas
- [ ] Create `v2/backend/app/schemas/song.py`:
  - SongUploadResponse (song_id, status)
  - SongRead (public song info)
  - SongCreate (for internal use)

#### 2.3 Storage Service
- [ ] Create `v2/backend/app/services/storage_service.py`:
  - `upload_bytes_to_s3(bucket, key, data, content_type) -> None`
  - `download_bytes_from_s3(bucket, key) -> bytes`
  - `generate_presigned_get_url(bucket, key, expires_in) -> str`
  - `generate_presigned_put_url(bucket, key, expires_in) -> str`
  - `delete_from_s3(bucket, key) -> None`
  - S3 client initialization
  - Error handling

#### 2.4 Audio Validation
- [ ] Create `v2/backend/app/services/audio_validation.py`:
  - `validate_audio_file(file_bytes, filename) -> ValidationResult`
  - Check file format (MP3, WAV, M4A)
  - Check file size (max 50MB or similar)
  - Check duration (max 5 minutes)
  - Use ffprobe or similar to validate

#### 2.5 Song API Routes
- [ ] Create `v2/backend/app/api/v1/routes_songs.py`:
  - `POST /api/songs` endpoint:
    - Accept multipart/form-data
    - Validate file
    - Upload to S3
    - Create song record
    - Return song_id
  - `GET /api/songs/{id}` endpoint:
    - Get song details
    - Verify user owns song
  - `GET /api/songs` endpoint:
    - List user's songs
  - Error handling (invalid file, upload failure)

#### 2.6 Frontend Upload API Client
- [ ] Create `v2/frontend/src/api/songs.ts`:
  - `uploadSong(file)` function
  - `getSong(songId)` function
  - `listSongs()` function
  - Progress tracking (optional for MVP)

#### 2.7 Frontend Upload Page
- [ ] Create `v2/frontend/src/pages/UploadPage.tsx`:
  - File input (drag & drop or browse)
  - File validation (format, size)
  - Upload progress indicator
  - Success/error messages
  - Redirect to song page on success
  - Design system styling

#### 2.8 Update Main App
- [ ] Update `v2/backend/app/main.py`:
  - Include songs router
- [ ] Update `v2/frontend/src/App.tsx`:
  - Add upload route

#### 2.9 Test Script
- [ ] Create `v2/scripts/for-development/test-phase2.sh`:
  - Upload valid audio file
  - Verify file in S3
  - Verify song record in database
  - Test invalid file format
  - Test file too large
  - Test file too long
  - Get song details
  - List user's songs

### Files to Create
- `v2/backend/app/models/song.py`
- `v2/backend/app/schemas/song.py`
- `v2/backend/app/services/storage_service.py`
- `v2/backend/app/services/audio_validation.py`
- `v2/backend/app/api/v1/routes_songs.py`
- `v2/frontend/src/pages/UploadPage.tsx`
- `v2/frontend/src/api/songs.ts`
- `v2/scripts/for-development/test-phase2.sh`

### Files to Update
- `v2/backend/app/main.py` (add songs routes)
- `v2/frontend/src/App.tsx` (add upload route)

### Test Script
```bash
# scripts/for-development/test-phase2.sh
# Tests: Upload audio, verify S3 storage, verify database record
```

### Test Criteria
- ✅ Can upload valid audio file
- ✅ File is stored in S3
- ✅ Song record created in database
- ✅ Invalid files are rejected
- ✅ Can retrieve song details
- ✅ Can list user's songs

---

## Phase 3: Audio Analysis

**Goal**: Extract BPM (required), beats, genre, mood, lyrics with precise timestamps

**Key Requirements:**
- BPM is required (must be extracted)
- Lyrics extraction MUST run during analysis (before user can section song)
- If no lyrics detected, that's fine - extraction step must complete
- If lyrics are available, they must have precise timestamps for section assignment
- Word-splitting: if word spans sections, include full word in both

### Subtasks

#### 3.1 Analysis Model
- [ ] Create `v2/backend/app/models/analysis.py`:
  - Analysis model (SQLModel)
  - Fields: id, song_id (FK), bpm, beat_times (JSON), genre, mood_primary, mood_tags (JSON), mood_vector (JSON), lyrics_available, lyrics (JSON), created_at
  - Relationship to Song

#### 3.2 Analysis Schemas
- [ ] Create `v2/backend/app/schemas/analysis.py`:
  - SongAnalysis (response schema)
  - AnalysisJobResponse (job_id, status)
  - Beat, MoodVector, SectionLyrics nested schemas

#### 3.3 Beat Alignment Service
- [ ] Create `v2/backend/app/services/beat_alignment_service.py`:
  - `extract_beat_times(audio_path) -> List[float]`
  - Use librosa.beat.track() or similar
  - **Add extensive comments explaining librosa calls**
  - Return list of beat timestamps in seconds
  - Handle edge cases (no beats detected)

#### 3.4 BPM Detection Service
- [ ] Create `v2/backend/app/services/bpm_detection_service.py`:
  - `detect_bpm(audio_path) -> float`
  - Use librosa.beat.tempo() or similar
  - **Add extensive comments explaining librosa calls**
  - BPM is REQUIRED (raise error if cannot detect)
  - Return BPM value

#### 3.5 Genre/Mood Service
- [ ] Create `v2/backend/app/services/genre_mood_service.py`:
  - `analyze_genre(audio_path, bpm) -> (primary_genre, sub_genres, confidence)`
  - `analyze_mood(audio_path, bpm) -> (mood_primary, mood_tags, mood_vector)`
  - Reuse existing code from old repo
  - **Add comments explaining complex logic**
  - Return genre and mood analysis

#### 3.6 Lyric Extraction Service
- [ ] Create `v2/backend/app/services/lyric_extraction_service.py`:
  - `extract_lyrics(audio_path) -> (available: bool, lyrics: List[dict])`
  - Use Whisper via Replicate API
  - **Must run before sectioning is enabled** (even if no lyrics detected)
  - If lyrics available, they MUST have precise timestamps (start, end, text)
  - Return list of lyric segments with timestamps (empty list if none detected)
  - Handle cases where lyrics unavailable (return available=False, empty list)
  - **It's fine if no lyrics detected** - extraction step must just complete

#### 3.7 Audio Analysis Service (Orchestrator)
- [ ] Create `v2/backend/app/services/audio_analysis_service.py`:
  - `analyze_song(song_id) -> AnalysisResult`
  - Orchestrates all analysis steps:
    1. Download audio from S3
    2. Detect BPM (required)
    3. Extract beat times
    4. Analyze genre
    5. Analyze mood
    6. Extract lyrics (must run, even if none detected)
    7. Store results in database
  - **Progress tracking** (milestone-based, update database):
    - 25% after BPM/beat detection
    - 50% after genre/mood analysis
    - 70% after lyrics extraction
    - 85% after analysis complete (all data saved)
    - 100% complete
  - Error handling (if BPM cannot be detected, fail)
  - **Sectioning is only enabled after lyrics extraction step completes** (regardless of whether lyrics found)

#### 3.8 Analysis RQ Worker Function
- [ ] Create `v2/backend/app/workers/analysis_worker.py`:
  - RQ worker function for song analysis
  - Function signature: `run_analysis_job(job_id: str, song_id: str) -> dict`
  - Calls audio_analysis_service functions directly
  - Updates job status in database
  - Handles errors (RQ retry logic configured in enqueue)
  - Returns analysis results

#### 3.9 Analysis API Routes
- [ ] Update `v2/backend/app/api/v1/routes_songs.py`:
  - `POST /api/songs/{id}/analyze` endpoint:
    - Enqueue analysis job
    - Return job_id
  - `GET /api/jobs/{job_id}` endpoint:
    - Get analysis job status and progress (milestone-based: 25%, 50%, 70%, 85%, 100%)
    - Return: status, progress, error_message (if failed)
  - `GET /api/songs/{id}/analysis` endpoint:
    - Get final analysis results (after job completes)
    - Return SongAnalysis schema

#### 3.10 Update Storage Service
- [ ] Update `v2/backend/app/services/storage_service.py`:
  - Add `download_audio_to_temp(song_id) -> Path` function
  - Downloads audio to temp file for processing
  - Returns path to temp file

#### 3.11 Frontend Analysis API Client
- [ ] Update `v2/frontend/src/api/songs.ts`:
  - `analyzeSong(songId)` function
  - `getAnalysis(songId)` function
  - `getAnalysisJobStatus(jobId)` function

#### 3.12 Test Script
- [ ] Create `v2/scripts/for-development/test-phase3.sh`:
  - Upload audio file
  - Trigger analysis
  - Wait for analysis to complete
  - Verify BPM extracted (required)
  - Verify beat times extracted
  - Verify genre extracted
  - Verify mood extracted
  - Verify lyrics extraction step completed (even if no lyrics found)
  - Verify timestamps in lyrics are precise (if lyrics available)
  - Test with song that has no lyrics (should complete successfully)
  - Verify sectioning is enabled after lyrics extraction completes

### Files to Create
- `v2/backend/app/models/analysis.py`
- `v2/backend/app/schemas/analysis.py`
- `v2/backend/app/services/beat_alignment_service.py`
- `v2/backend/app/services/bpm_detection_service.py`
- `v2/backend/app/services/genre_mood_service.py`
- `v2/backend/app/services/lyric_extraction_service.py`
- `v2/backend/app/services/audio_analysis_service.py`
- `v2/backend/app/workers/analysis_worker.py`
- `v2/scripts/for-development/test-phase3.sh`

### Files to Update
- `v2/backend/app/api/v1/routes_songs.py` (add analysis endpoints)
- `v2/backend/app/services/storage_service.py` (add download function)
- `v2/frontend/src/api/songs.ts` (add analysis functions)

### Test Criteria
- ✅ BPM is extracted (required, fails if cannot detect)
- ✅ Beat times are extracted
- ✅ Genre is extracted
- ✅ Mood is extracted
- ✅ Lyrics extraction step completes (even if no lyrics detected)
- ✅ Lyrics have precise timestamps (if lyrics available)
- ✅ Sectioning is enabled only after lyrics extraction completes
- ✅ Analysis results stored in database
- ✅ Job status tracking works

---

## Phase 4: Section Management

**Goal**: User creates sections AFTER analysis, beat alignment, validation, labels

**Key Requirements:**
- Sections created AFTER analysis (so UI can snap-to-beat)
- **Sections are NOT auto-detected** - they MUST come from the user via web app/UI
- User can insert/delete/drag section markers in the UI
- Users cannot edit section start/end after creation (warn upfront)
- Users can re-label sections (1-2 words, added to prompt)
- Warn users upfront and after setting markers
- Must be 3-10 sections

### Subtasks

#### 4.1 Section Model
- [ ] Create `v2/backend/app/models/section.py`:
  - Section model (SQLModel)
  - Fields: id, song_id (FK), section_index, label, start_time, end_time, prompt_note (optional, max 100 chars), regeneration_count, created_at
  - Relationship to Song
  - Constraints: start_time < end_time, duration >= 1s, duration <= 120s

#### 4.2 Section Schemas
- [ ] Create `v2/backend/app/schemas/section.py`:
  - SectionCreate (for creating sections)
  - SectionUpdate (label only, for updating)
  - SectionRead (public section info)
  - SectionListResponse

#### 4.3 Section Management Service
- [ ] Create `v2/backend/app/services/section_management_service.py`:
  - `create_sections(song_id, sections: List[SectionCreate]) -> List[Section]`
  - `update_section_label(section_id, label) -> Section`
  - `validate_sections(sections, song_duration) -> ValidationResult`
  - `snap_to_beats(time, beat_times) -> float`
  - Validation logic:
    - 3-10 sections required
    - Each section: 1s minimum, 2min maximum
    - Total duration matches song duration
    - No overlaps
    - Sections in order

#### 4.4 Beat Snapping Logic
- [ ] Update `v2/backend/app/services/beat_alignment_service.py`:
  - `find_nearest_beat(time, beat_times) -> float`
  - `snap_time_to_beat(time, beat_times, tolerance) -> float`
  - Return nearest beat-aligned time

#### 4.5 Section API Routes
- [ ] Create `v2/backend/app/api/v1/routes_sections.py`:
  - `POST /api/songs/{id}/sections` endpoint:
    - Accept list of sections
    - Validate constraints
    - Snap to beats
    - Create sections
    - Warn if sections cannot be edited later
  - `GET /api/songs/{id}/sections` endpoint:
    - List all sections for song
  - `PATCH /api/songs/{id}/sections/{section_id}` endpoint:
    - Update label only (not start/end)
    - Validate label (1-2 words)
  - `GET /api/songs/{id}/beat-times` endpoint:
    - Return beat times for snapping UI

#### 4.6 Frontend Section API Client
- [ ] Create `v2/frontend/src/api/sections.ts`:
  - `createSections(songId, sections)` function
  - `getSections(songId)` function
  - `updateSectionLabel(songId, sectionId, label)` function
  - `getBeatTimes(songId)` function

#### 4.7 Frontend Section Timeline Component
- [ ] Create `v2/frontend/src/components/SectionTimeline.tsx`:
  - Waveform/timeline display
  - Beat markers visualization
  - Draggable section markers
  - Snap-to-beat functionality
  - Section labels input
  - Section prompt notes input (optional, 100 chars max)
  - Validation feedback
  - Warning messages (cannot edit start/end later)

#### 4.8 Frontend Section Editor Page
- [ ] Create `v2/frontend/src/pages/SectionEditorPage.tsx`:
  - Load analysis results
  - Display beat times
  - Section timeline component
  - Section list/editor
  - Validation feedback
  - Save sections button
  - Warning dialogs (upfront and after saving)
  - Design system styling

#### 4.9 Update Main App
- [ ] Update `v2/backend/app/main.py`:
  - Include sections router
- [ ] Update `v2/frontend/src/App.tsx`:
  - Add section editor route

#### 4.10 Test Script
- [ ] Create `v2/scripts/for-development/test-phase4.sh`:
  - Create valid sections (3-10 sections)
  - Verify sections created in database
  - Verify beat alignment
  - Test invalid sections (too many, too few, invalid durations)
  - Update section label
  - Test cannot update start/end
  - Test snap-to-beat functionality

### Files to Create
- `v2/backend/app/models/section.py`
- `v2/backend/app/schemas/section.py`
- `v2/backend/app/services/section_management_service.py`
- `v2/backend/app/api/v1/routes_sections.py`
- `v2/frontend/src/pages/SectionEditorPage.tsx`
- `v2/frontend/src/components/SectionTimeline.tsx`
- `v2/frontend/src/api/sections.ts`
- `v2/scripts/for-development/test-phase4.sh`

### Files to Update
- `v2/backend/app/services/beat_alignment_service.py` (add snap functions)
- `v2/backend/app/main.py` (add sections routes)
- `v2/frontend/src/App.tsx` (add section editor route)

### Test Criteria
- ✅ Can create 3-10 sections after analysis
- ✅ Sections are validated (constraints)
- ✅ Sections snap to beats
- ✅ Cannot edit section start/end after creation
- ✅ Can update section labels
- ✅ Warnings shown upfront and after saving

---

## Phase 5: Prompt Generation & Video Type Selection

**Goal**: Generate prompts, suggest video type, allow full prompt override

**Key Requirements:**
- Use existing code for prompt generation
- System generates initial prompt based on analysis (genre, mood, video type)
- User can edit/override the entire prompt (only upfront, before first generation)
- Prompt parser extracts creative direction from user input
- Section labels (1-2 words) are added to each section's prompt
- Overall song prompt uses everything; section prompts get section-specific lyrics
- Supports example prompts like:
  - "Create an ethereal music video for this ambient electronic track with floating geometric shapes"
  - "Generate a high energy punk rock video with urban graffiti aesthetics"
  - "Make a dreamy indie pop video with pastel colors and nature scenes"

### Subtasks

#### 5.1 Video Type Service
- [ ] Create `v2/backend/app/services/video_type_service.py`:
  - `suggest_video_type(analysis) -> str`
  - Rule-based suggestion (BPM, genre, mood)
  - **Human dev must review rules before commit**
  - **Prominently document rules**
  - Fixed list of ~5 video types
  - Return suggested type

#### 5.2 Prompt Generation Service
- [ ] Create `v2/backend/app/services/prompt_generation_service.py`:
  - `generate_overall_prompt(analysis, video_type, custom_prompt=None) -> str`
  - `generate_section_prompt(section, analysis, overall_prompt, section_label) -> str`
  - Use existing code from old repo
  - Combine: genre, mood, video type, custom prompt
  - Section prompts: overall + section label + section lyrics (if available) + section prompt note
  - Return prompts for each section

#### 5.3 Prompt Parser
- [ ] Create `v2/backend/app/services/prompt_parser_service.py`:
  - `parse_user_prompt(user_prompt) -> PromptComponents`
  - Extract creative direction from user input
  - Handle example prompts:
    - "Create an ethereal music video for this ambient electronic track with floating geometric shapes"
    - "Generate a high energy punk rock video with urban graffiti aesthetics"
    - "Make a dreamy indie pop video with pastel colors and nature scenes"
  - Return structured prompt components

#### 5.4 Update Analysis Schema
- [ ] Update `v2/backend/app/schemas/analysis.py`:
  - Add video_type field
  - Add custom_prompt field (optional)
  - Add overall_prompt field

#### 5.5 Prompt API Routes
- [ ] Create `v2/backend/app/api/v1/routes_prompts.py`:
  - `GET /api/songs/{id}/suggest-video-type` endpoint:
    - Return suggested video type
  - `POST /api/songs/{id}/generate-prompt` endpoint:
    - Generate overall prompt
    - Accept custom_prompt (optional)
    - Return overall prompt
  - `GET /api/songs/{id}/section-prompts` endpoint:
    - Return prompts for all sections

#### 5.6 Frontend Video Type Selector Component
- [ ] Create `v2/frontend/src/components/VideoTypeSelector.tsx`:
  - Display suggested type
  - Dropdown with fixed list (~5 types)
  - Custom input option
  - All 3 options available
  - Design system styling

#### 5.7 Frontend Prompt Editor Component
- [ ] Create `v2/frontend/src/components/PromptEditor.tsx`:
  - Display generated prompt
  - Allow full override/edit
  - Only available upfront (before first generation)
  - Text area for editing
  - Save button
  - Design system styling

#### 5.8 Frontend Prompt API Client
- [ ] Create `v2/frontend/src/api/prompts.ts`:
  - `suggestVideoType(songId)` function
  - `generatePrompt(songId, customPrompt?)` function
  - `getSectionPrompts(songId)` function
  - `updatePrompt(songId, prompt)` function

#### 5.9 Update Section Editor Page
- [ ] Update `v2/frontend/src/pages/SectionEditorPage.tsx`:
  - Add video type selector
  - Add prompt editor
  - Show generated prompts
  - Allow editing (upfront only)
  - Save prompt before proceeding

#### 5.10 Test Script
- [ ] Create `v2/scripts/for-development/test-phase5.sh`:
  - Get suggested video type
  - Verify suggestion is rule-based
  - Generate overall prompt
  - Override prompt with custom text
  - Generate section prompts
  - Verify section labels added to prompts
  - Verify section lyrics in prompts
  - Test prompt parser with example prompts

### Files to Create
- `v2/backend/app/services/video_type_service.py`
- `v2/backend/app/services/prompt_generation_service.py`
- `v2/backend/app/services/prompt_parser_service.py`
- `v2/backend/app/api/v1/routes_prompts.py`
- `v2/frontend/src/components/VideoTypeSelector.tsx`
- `v2/frontend/src/components/PromptEditor.tsx`
- `v2/frontend/src/api/prompts.ts`
- `v2/scripts/for-development/test-phase5.sh`

### Files to Update
- `v2/backend/app/schemas/analysis.py` (add video_type, custom_prompt, overall_prompt)
- `v2/frontend/src/pages/SectionEditorPage.tsx` (add video type and prompt editor)

### Test Criteria
- ✅ Video type is suggested based on analysis
- ✅ User can choose from dropdown or type custom
- ✅ Overall prompt is generated
- ✅ User can override/edit prompt (upfront only)
- ✅ Section prompts include labels and lyrics
- ✅ Prompt parser extracts creative direction

---

## Phase 6: Clip Planning

**Goal**: Plan 3-10 second clips per section (randomized, must exactly match section duration)

**Key Requirements:**
- Generate multiple clips per section (3-10 seconds each, randomized)
- Clips must exactly match section duration (sum = section duration)
- Logic to ensure exact duration matching

### Subtasks

#### 6.1 Clip Model
- [ ] Create `v2/backend/app/models/clip.py`:
  - Clip model (SQLModel)
  - Fields: id, section_id (FK), clip_index, start_time, end_time, duration_sec, prompt, video_s3_key (optional), status, regeneration_count, created_at
  - Relationship to Section
  - Constraints: duration >= 3s, duration <= 10s

#### 6.2 Clip Schemas
- [ ] Create `v2/backend/app/schemas/clip.py`:
  - ClipPlan (for planning)
  - ClipRead (public clip info)
  - ClipPlanResponse

#### 6.3 Clip Planning Service
- [ ] Create `v2/backend/app/services/clip_planning_service.py`:
  - `plan_clips_for_section(section, prompt, min_sec=3, max_sec=10) -> List[ClipPlan]`
  - Generate multiple clips per section
  - Randomize clip durations (3-10 seconds)
  - **Ensure clips exactly match section duration** (sum = section duration)
  - **Algorithm** (from IMPLEMENTATION_CHALLENGES.md):
    - If section < 3s: Single clip (allow < 3s exception)
    - If section 3-10s: Single clip
    - If section > 10s: Generate N clips (N = ceil(section_duration / 6.5) for average 6.5s)
    - Distribute duration: Use weighted random distribution, ensure last clip is 3-10s
    - Round to 0.1s precision, adjust last clip to exact sum
    - Handle edge cases: Floating-point precision, redistribution if needed
  - Return list of clip plans with start/end times

#### 6.4 Clip API Routes
- [ ] Create `v2/backend/app/api/v1/routes_clips.py`:
  - `POST /api/songs/{id}/clips/plan` endpoint:
    - Plan clips for all sections
    - Return clip plans
  - `GET /api/songs/{id}/clips` endpoint:
    - List all clips for song
  - `GET /api/songs/{id}/sections/{section_id}/clips` endpoint:
    - List clips for specific section

#### 6.5 Frontend Clip API Client
- [ ] Create `v2/frontend/src/api/clips.ts`:
  - `planClips(songId)` function
  - `getClips(songId)` function
  - `getSectionClips(songId, sectionId)` function

#### 6.6 Test Script
- [ ] Create `v2/scripts/for-development/test-phase6.sh`:
  - Plan clips for sections
  - Verify clip durations (3-10s)
  - Verify clips exactly match section duration
  - Verify multiple clips per section
  - Test with different section durations

### Files to Create
- `v2/backend/app/models/clip.py`
- `v2/backend/app/schemas/clip.py`
- `v2/backend/app/services/clip_planning_service.py`
- `v2/backend/app/api/v1/routes_clips.py`
- `v2/frontend/src/api/clips.ts`
- `v2/scripts/for-development/test-phase6.sh`

### Files to Update
- `v2/backend/app/main.py` (add clips routes)

### Test Script
```bash
# scripts/for-development/test-phase6.sh
# Tests: Plan clips for sections, verify durations (3-10s), verify exact match to section duration
```

### Test Criteria
- ✅ Multiple clips generated per section
- ✅ Clip durations are 3-10 seconds (randomized)
- ✅ Clips exactly match section duration (sum = section duration)
- ✅ Clips are properly ordered

---

## Phase 7: Video Generation

**Goal**: Generate video clips via Replicate API with error handling

**Key Requirements:**
- Parallel generation (enqueue individual clip jobs, limit concurrent RQ workers)
- RQ built-in retry: 3 attempts per clip
- If any clip persistently fails after 3 retries → fail entire video, cleanup all clips immediately
- Generic user-friendly error messages (technical details in server logs only)
- Progress tracking: Percentage-based `(completed_clips / total_clips) * 100` (maps to 0-80% of combined progress)
- Research Replicate API rate limits (document, but don't implement rate limiting logic)
- Good logging when rate limit errors occur (429 status)

### Subtasks

#### 7.1 Video Generation Service
- [ ] Create `v2/backend/app/services/video_generation_service.py`:
  - `generate_clip(clip_id, prompt, duration) -> ClipResult`
  - Call Replicate API
  - Handle Replicate job lifecycle
  - Poll for completion
  - Download generated video
  - Upload to S3
  - Update clip record
  - Error handling and retries

#### 7.2 Rate Limiting Research
- [ ] Research Replicate API rate limits (check docs, test)
  - Document rate limits in code comments or docs
  - **Do NOT implement rate limiting logic** (no queue, no throttling)
  - **Logging**: Ensure good logs when rate limit errors occur (429 status, error messages)
  - If rate limited, user sees generic error message
  - Note: Quota limits (5 GB, 15 videos) prevent excessive usage, not rate limiting

#### 7.3 Video Generation RQ Worker Function
- [ ] Create `v2/backend/app/workers/video_generation_worker.py`:
  - RQ worker function for single clip generation
  - Function signature: `run_clip_generation_job(clip_id: str) -> dict`
  - Calls video_generation_service functions directly
  - Updates clip status in database
  - **Error handling** (from IMPLEMENTATION_CHALLENGES.md):
    - RQ built-in retry: 3 attempts (configure in enqueue)
    - If clip fails after 3 retries → fail clip, return error
    - Generic error messages (log technical details, return user-friendly message)
    - S3 upload: Retry 5x with exponential backoff (normal implementation)
    - Network timeout: Normal timeout, if still fails → generic error "Network issue, please try again later"
  - Returns clip generation result

#### 7.4 Batch Generation Orchestrator
- [ ] Create `v2/backend/app/services/clip_generation_orchestrator.py`:
  - `generate_all_clips(song_id) -> JobResult`
  - Enqueue clips for generation (parallel, individual clip jobs)
  - **Database tracking**: Track clip status (generating, completed, failed) in database
  - **Progress tracking**: Update progress as `(completed_clips / total_clips) * 100` (maps to 0-80% of combined clip+composition progress)
  - **Error handling** (from IMPLEMENTATION_CHALLENGES.md):
    - If any clip persistently fails after 3 retries → fail entire video
    - Cleanup all clips immediately after failure
    - Generic error message to user
  - **Idempotency**: Implement idempotency (can retry failed clips without duplicates)
  - **Transaction boundaries** (from IMPLEMENTATION_CHALLENGES.md):
    - Use database transactions for single-operation status updates
    - Use eventual consistency for multi-service operations (database + S3)
  - Update job status

#### 7.5 Update Clip Model
- [ ] Update `v2/backend/app/models/clip.py`:
  - Add status field (planned, generating, completed, failed)
  - Add video_s3_key field
  - Add error_message field

#### 7.6 Generation API Routes
- [ ] Create `v2/backend/app/api/v1/routes_generation.py`:
  - `POST /api/songs/{id}/clips/generate` endpoint:
    - Check quota before starting (quota service will be created in Phase 12; for now, use simple database query: check `user.video_count < 15` and `user.storage_bytes < 5_000_000_000` as placeholder - this will be replaced with proper quota service in Phase 12)
    - Enqueue batch generation job
    - Return job_id
  - `GET /api/songs/{id}/generation/status` endpoint (or `GET /api/jobs/{job_id}`):
    - Get combined clip generation + composition progress
    - **Progress calculation** (from IMPLEMENTATION_CHALLENGES.md):
      - Clip generation: `(completed_clips / total_clips) * 100` → maps to 0-80%
      - Composition: Milestone-based (80%, 90%, 95%, 100%)
      - Combined: Clip generation 0-80%, composition 80-100%
    - Return: total, completed, failed, in_progress, clips, progress (0-100)

#### 7.7 Frontend Generation API Client
- [ ] Update `v2/frontend/src/api/clips.ts`:
  - `generateClips(songId)` function
  - `getClipGenerationStatus(songId)` function

#### 7.8 Test Script
- [ ] Create `v2/scripts/for-development/test-phase7.sh`:
  - Generate single clip
  - Verify clip generated and stored in S3
  - Generate multiple clips in parallel
  - Test rate limiting
  - Test retry on failure
  - Test fail entire video if clip fails after retries
  - Verify user-friendly error messages

### Files to Create
- `v2/backend/app/services/video_generation_service.py`
- `v2/backend/app/services/clip_generation_orchestrator.py`
- `v2/backend/app/workers/video_generation_worker.py`
- `v2/backend/app/api/v1/routes_generation.py`
- `v2/scripts/for-development/test-phase7.sh`
- **Note**: No rate_limiting_service.py - research Replicate limits only, no implementation

### Files to Update
- `v2/backend/app/models/clip.py` (add status, video_s3_key, error_message)
- `v2/backend/app/main.py` (add generation routes)
- `v2/frontend/src/api/clips.ts` (add generation functions)

### Test Criteria
- ✅ Single clip can be generated
- ✅ Multiple clips generated in parallel
- ✅ Clips stored in S3
- ✅ RQ retry on failure works (3 attempts)
- ✅ Entire video fails if clip fails after 3 retries
- ✅ All clips cleaned up immediately on failure
- ✅ Generic user-friendly error messages shown (technical details in logs only)
- ✅ Progress tracking works (percentage-based, 0-80%)
- ✅ Quota checked before generation

---

## Phase 8: Video Normalization

**Goal**: Normalize clips (resolution, FPS)

### Subtasks

#### 8.1 Video Normalization Service
- [ ] Create `v2/backend/app/services/video_normalization_service.py`:
  - `normalize_clip(clip_s3_key, target_resolution, target_fps) -> NormalizedClip`
  - Use FFmpeg to normalize:
    - Resolution: 1080p (1920x1080)
    - FPS: 24 (or 30)
    - Codec: H.264
  - Download from S3, process, upload back
  - Return normalized clip S3 key
  - **Add comments explaining FFmpeg commands**

#### 8.2 Batch Normalization
- [ ] Update `v2/backend/app/services/video_normalization_service.py`:
  - `normalize_all_clips(clip_ids) -> List[NormalizedClip]`
  - Normalize all clips for a song
  - Update clip records with normalized S3 keys
  - Error handling

#### 8.3 Update Video Generation Service
- [ ] Update `v2/backend/app/services/video_generation_service.py`:
  - Call normalization after clip generation
  - Store normalized clip S3 key

#### 8.4 Test Script
- [ ] Create `v2/scripts/for-development/test-phase8.sh`:
  - Normalize single clip
  - Verify resolution is 1080p
  - Verify FPS is 24 (or 30)
  - Normalize multiple clips
  - Verify all clips have consistent resolution/FPS

### Files to Create
- `v2/backend/app/services/video_normalization_service.py`
- `v2/scripts/for-development/test-phase8.sh`

### Files to Update
- `v2/backend/app/services/video_generation_service.py` (call normalization)
- `v2/backend/app/models/clip.py` (add normalized_s3_key field)

### Test Script
```bash
# scripts/for-development/test-phase8.sh
# Tests: Normalize clips, verify resolution/FPS consistency
```

### Test Criteria
- ✅ Clips are normalized to 1080p
- ✅ Clips have consistent FPS (24 or 30)
- ✅ All clips for a song have same resolution/FPS

---

## Phase 9: Video Composition

**Goal**: Stitch clips, mux audio, create final video

**Key Requirements:**
- Handle duration mismatches
- **Clips are already normalized from Phase 8** (1080p @ 24fps) - verify before stitching
- Mux audio with video
- Upload final video to S3
- RQ built-in retry: 2 attempts
- If fails after 2 retries → fail video, cleanup immediately
- Progress tracking: Milestone-based (80%, 90%, 95%, 100%) - part of combined clip+composition progress
- Generic user-friendly error messages
- **Memory**: 4GB+ RAM required for composition (document in deployment)

### Subtasks

#### 9.1 Video Model
- [ ] Create `v2/backend/app/models/video.py`:
  - Video model (SQLModel)
  - Fields: id, song_id (FK), user_id (FK), video_type, video_s3_key, shareable_url, duration_sec, file_size_bytes, is_finalized, created_at, finalized_at
  - Relationships to Song and User

#### 9.2 Video Schemas
- [ ] Create `v2/backend/app/schemas/video.py`:
  - ComposeVideoRequest (clip_ids)
  - ComposeVideoResponse (job_id)
  - VideoRead (public video info)

#### 9.3 Video Composition Service
- [ ] Create `v2/backend/app/services/video_composition_service.py`:
  - `compose_video(song_id, clip_ids, audio_s3_key) -> VideoResult`
  - Use FFmpeg to:
    1. Download all clips from S3
    2. **Verify clips are already normalized** (from Phase 8: 1080p @ 24fps)
    3. Concatenate clips in order
    4. Mux with original audio
    5. Handle duration mismatches
    6. Ensure final output is 1080p @ 24fps (clips should already be normalized, but verify)
    7. Upload final video to S3
  - **Add comments explaining FFmpeg commands**
  - Handle audio/video sync issues
  - Return final video S3 key

#### 9.4 Composition RQ Worker Function
- [ ] Create `v2/backend/app/workers/composition_worker.py`:
  - RQ worker function for video composition
  - Function signature: `run_composition_job(job_id: str, song_id: str) -> dict`
  - Calls video_composition_service functions directly
  - Updates job status in database
  - Creates Video record
  - **Progress tracking** (milestone-based, update database):
    - 80% stitching
    - 90% uploading
    - 95% verification
    - 100% complete
  - **Error handling** (from IMPLEMENTATION_CHALLENGES.md):
    - RQ built-in retry: 2 attempts (configure in enqueue)
    - If fails after 2 retries → fail video, cleanup immediately
    - Generic error message to user
    - No manual retry (failures are final)
  - Returns composition result

#### 9.5 Composition API Routes
- [ ] Create `v2/backend/app/api/v1/routes_composition.py`:
  - `POST /api/songs/{id}/compose` endpoint:
    - Accept clip_ids
    - Enqueue composition job
    - Return job_id
  - `GET /api/songs/{id}/compose/{job_id}/status` endpoint (or use combined `GET /api/songs/{id}/generation/status`):
    - Get composition job status
    - **Progress**: Milestone-based (80%, 90%, 95%, 100%) - part of combined clip+composition progress
    - Return: job_id, status, progress (80-100%), composed_video_id (if completed), error (if failed)
  - `GET /api/songs/{id}/compose/{job_id}/result` endpoint:
    - Get final video URL (presigned)

#### 9.6 Frontend Composition API Client
- [ ] Create `v2/frontend/src/api/composition.ts`:
  - `composeVideo(songId, clipIds)` function
  - `getCompositionStatus(songId, jobId)` function
  - `getComposedVideo(songId, jobId)` function

#### 9.7 Test Script
- [ ] Create `v2/scripts/for-development/test-phase9.sh`:
  - Compose video from clips
  - Verify clips are in correct order
  - Verify audio is synced
  - Verify output is 1080p @ 24fps
  - Test with duration mismatches
  - Verify final video plays correctly

### Files to Create
- `v2/backend/app/models/video.py`
- `v2/backend/app/schemas/video.py`
- `v2/backend/app/services/video_composition_service.py`
- `v2/backend/app/workers/composition_worker.py`
- `v2/backend/app/api/v1/routes_composition.py`
- `v2/frontend/src/api/composition.ts`
- `v2/scripts/for-development/test-phase9.sh`

### Files to Update
- `v2/backend/app/main.py` (add composition routes)

### Test Script
```bash
# scripts/for-development/test-phase9.sh
# Tests: Compose video from clips, verify audio sync, verify output quality
```

### Test Criteria
- ✅ Clips are stitched in correct order
- ✅ Audio is synced with video
- ✅ Output is 1080p @ 24fps
- ✅ Duration mismatches are handled
- ✅ Final video plays correctly

---

## Phase 10: Regeneration

**Goal**: Regenerate sections/clips (once each)

**Key Requirements:**
- **Regeneration tracking** (from IMPLEMENTATION_CHALLENGES.md):
  - Track regeneration in database (regeneration_count field)
  - Allow regeneration if previous attempt failed
  - Section regeneration resets clip regeneration counts
  - Show regeneration status in UI (remaining attempts)
  - Limits: Once per section, once per clip (tracked separately)
- **Progress tracking**: Percentage-based `(completed / total) * 100` for regeneration
- Generic user-friendly error messages

### Subtasks

#### 10.1 Regeneration Service
- [ ] Create `v2/backend/app/services/regeneration_service.py`:
  - `check_regeneration_allowed(video_id, section_id, clip_id, type) -> bool`
  - `regenerate_section(video_id, section_id) -> job_id`
  - `regenerate_clip(video_id, clip_id) -> job_id`
  - **Regeneration tracking** (from IMPLEMENTATION_CHALLENGES.md):
    - Check regeneration counts (max 1 per section, max 1 per clip)
    - Allow regeneration if previous attempt failed
    - Section regeneration resets clip regeneration counts for that section
  - Enqueue regeneration job
  - Update regeneration_count in database

#### 10.2 Update Models
- [ ] Update `v2/backend/app/models/section.py`:
  - Add regeneration_count field (default 0)
- [ ] Update `v2/backend/app/models/clip.py`:
  - Add regeneration_count field (default 0)

#### 10.3 Regeneration API Routes
- [ ] Create `v2/backend/app/api/v1/routes_regeneration.py`:
  - `POST /api/videos/{id}/regenerate/section/{section_id}` endpoint:
    - Check regeneration allowed (once per section, allow if previous attempt failed)
    - Reset clip regeneration counts for this section
    - Enqueue regeneration job
    - Return job_id
  - `POST /api/videos/{id}/regenerate/clip/{clip_id}` endpoint:
    - Check regeneration allowed (once per clip, allow if previous attempt failed)
    - Enqueue regeneration job
    - Return job_id
  - `GET /api/videos/{id}/regeneration/status` endpoint (or `GET /api/jobs/{job_id}`):
    - Get regeneration progress
    - Progress: Percentage-based `(completed / total) * 100`
    - Return: job_id, status, progress (0-100), result (if completed), error (if failed)

#### 10.4 Frontend Regeneration Dialog Component
- [ ] Create `v2/frontend/src/components/RegenerateDialog.tsx`:
  - Dialog/modal component
  - Options: "Entire section" or "Just this clip"
  - Show remaining regeneration count
  - Confirm button
  - Design system styling

#### 10.5 Frontend Regeneration API Client
- [ ] Create `v2/frontend/src/api/regeneration.ts`:
  - `regenerateSection(videoId, sectionId)` function
  - `regenerateClip(videoId, clipId)` function
  - `getRegenerationStatus(videoId)` function

#### 10.6 Update Video Player
- [ ] Update `v2/frontend/src/components/VideoPlayer.tsx` (created in Phase 14):
  - Add "Regenerate" button (when paused)
  - Open regeneration dialog
  - Show regeneration status

#### 10.7 Test Script
- [ ] Create `v2/scripts/for-development/test-phase10.sh`:
  - Regenerate section (first time - should work)
  - Regenerate section (second time - should fail)
  - Regenerate clip (first time - should work)
  - Regenerate clip (second time - should fail)
  - Verify regeneration_count incremented
  - Verify limits enforced

### Files to Create
- `v2/backend/app/services/regeneration_service.py`
- `v2/backend/app/api/v1/routes_regeneration.py`
- `v2/frontend/src/components/RegenerateDialog.tsx`
- `v2/frontend/src/api/regeneration.ts`
- `v2/scripts/for-development/test-phase10.sh`

### Files to Update
- `v2/backend/app/models/section.py` (add regeneration_count)
- `v2/backend/app/models/clip.py` (add regeneration_count)
- `v2/backend/app/main.py` (add regeneration routes)
- `v2/frontend/src/components/VideoPlayer.tsx` (add regenerate button)

### Test Script
```bash
# scripts/for-development/test-phase10.sh
# Tests: Regenerate section (once), regenerate clip (once), verify limits enforced
```

### Test Criteria
- ✅ Can regenerate section once
- ✅ Cannot regenerate section twice
- ✅ Can regenerate clip once
- ✅ Cannot regenerate clip twice
- ✅ Regeneration counts tracked correctly

---

## Phase 11: Finalization & Cleanup

**Goal**: Finalize videos, cleanup intermediates, warn users

**Key Requirements:**
- Warn users upfront and after clicking "Finalize" that it can't be undone
- Users cannot un-finalize (permanent)
- Cleanup intermediates after finalization

### Subtasks

#### 11.1 Finalization Service
- [ ] Create `v2/backend/app/services/finalization_service.py`:
  - `finalize_video(video_id, user_id) -> FinalizationResult`
  - Check video is not already finalized
  - Mark video as finalized
  - **Cleanup approach** (from IMPLEMENTATION_CHALLENGES.md):
    - Cleanup only happens when video generation is done (either succeeded or failed)
    - User cannot regenerate while cleanup is running (cleanup only happens when done)
    - Delete all clip files from S3 (log and continue if delete fails)
    - Delete temp files (log and continue if delete fails)
    - Keep only final video
    - **Don't worry if S3 deletes fail** - log and continue
    - **Orphaned files are acceptable** - no cleanup job needed
  - **Transaction boundaries** (from IMPLEMENTATION_CHALLENGES.md):
    - Use database locks for critical sections (finalization)
    - Don't use transactions for long-running operations
  - Update video record (is_finalized=True, finalized_at=now)

#### 11.2 Storage Cleanup
- [ ] Update `v2/backend/app/services/storage_service.py`:
  - `cleanup_intermediates(video_id) -> CleanupResult`
  - List all clips for video
  - Delete clip files from S3 (log and continue if delete fails)
  - Delete temp files (log and continue if delete fails)
  - Log cleanup actions
  - **Note**: Orphaned files are acceptable, no need for atomic deletes

#### 11.3 Update Video Model
- [ ] Update `v2/backend/app/models/video.py`:
  - Add is_finalized field (default False)
  - Add finalized_at field (optional)

#### 11.4 Finalization API Routes
- [ ] Create `v2/backend/app/api/v1/routes_finalization.py`:
  - `POST /api/videos/{id}/finalize` endpoint:
    - Check video exists and user owns it
    - Check video is not finalized
    - Finalize video
    - Cleanup intermediates
    - Return success
  - `GET /api/videos/{id}/finalization-status` endpoint:
    - Check if video is finalized

#### 11.5 Frontend Finalize Button Component
- [ ] Create `v2/frontend/src/components/FinalizeButton.tsx`:
  - Button component
  - Warning dialog (upfront and after clicking)
  - Confirm finalization
  - Disable if already finalized
  - Design system styling

#### 11.6 Frontend Finalization API Client
- [ ] Create `v2/frontend/src/api/finalization.ts`:
  - `finalizeVideo(videoId)` function
  - `getFinalizationStatus(videoId)` function

#### 11.7 Update Video Player
- [ ] Update `v2/frontend/src/components/VideoPlayer.tsx`:
  - Show finalize button (if not finalized)
  - Hide regenerate button if finalized
  - Show warning dialogs

#### 11.8 Test Script
- [ ] Create `v2/scripts/for-development/test-phase11.sh`:
  - Finalize video
  - Verify video marked as finalized
  - Verify intermediates deleted from S3
  - Verify cannot un-finalize
  - Verify cannot regenerate after finalization
  - Test warnings shown

### Files to Create
- `v2/backend/app/services/finalization_service.py`
- `v2/backend/app/api/v1/routes_finalization.py`
- `v2/frontend/src/components/FinalizeButton.tsx`
- `v2/frontend/src/api/finalization.ts`
- `v2/scripts/for-development/test-phase11.sh`

### Files to Update
- `v2/backend/app/models/video.py` (add is_finalized, finalized_at)
- `v2/backend/app/services/storage_service.py` (add cleanup function)
- `v2/backend/app/main.py` (add finalization routes)
- `v2/frontend/src/components/VideoPlayer.tsx` (add finalize button)

### Test Criteria
- ✅ Video can be finalized
- ✅ Intermediates are deleted (or logged if delete fails - orphaned files acceptable)
- ✅ Video cannot be un-finalized
- ✅ Cannot regenerate after finalization
- ✅ User cannot regenerate while cleanup is running (cleanup only happens when done)
- ✅ Warnings shown upfront and after

---

## Phase 12: Rate Limiting & Storage Management

**Goal**: Enforce quotas, track usage, show user-friendly error messages

**Key Requirements:**
- **Quota enforcement timing** (from IMPLEMENTATION_CHALLENGES.md):
  - Check quota: Before starting generation (Phase 7)
  - Quota freed: Immediately on video deletion
  - Mid-generation: Finish current video, block new generations
  - Use database transaction for quota check/update (prevent race conditions)
- 15 videos max, 5 GB storage max per user
- Return generic user-friendly error when limits hit: "You've reached your limit (15 videos). Delete existing videos to create more."
- No upgrade option (keep simple)

### Subtasks

#### 12.1 Update User Model
- [ ] Update `v2/backend/app/models/user.py`:
  - Add video_count field (default 0)
  - Add storage_bytes field (default 0)

#### 12.2 Quota Service
- [ ] Create `v2/backend/app/services/quota_service.py`:
  - `check_user_quota(user_id) -> QuotaStatus`
  - `get_user_quota_status(user_id) -> QuotaStatus`
  - Calculate storage usage (sum of video file sizes)
  - Count videos per user
  - **Use database transaction for quota check/update** (prevent race conditions)
  - Return 429 status with generic user-friendly message: "You've reached your limit (15 videos). Delete existing videos to create more."

#### 12.3 Storage Management Service
- [ ] Create `v2/backend/app/services/storage_management_service.py`:
  - `update_user_storage(user_id, file_size_bytes) -> None`
  - `update_user_video_count(user_id, delta) -> None`
  - `get_user_quota_status(user_id) -> QuotaStatus`
  - Track storage usage
  - Track video count

#### 12.4 Rate Limit Middleware
- [ ] Create `v2/backend/app/middleware/rate_limit_middleware.py`:
  - Check quotas before upload
  - Check quotas before composition
  - Return 429 status with user-friendly message
  - Message: "You've reached your limit. Delete existing videos to create more."

#### 12.5 Update Upload Route
- [ ] Update `v2/backend/app/api/v1/routes_songs.py`:
  - Check video quota before upload
  - Check storage quota before upload
  - Return error if quota exceeded

#### 12.6 Update Composition Route
- [ ] Update `v2/backend/app/api/v1/routes_composition.py`:
  - Check video quota before composition
  - Check storage quota before composition
  - Update user quotas after successful composition
  - Limits apply AFTER video creation completes

#### 12.7 Frontend Quota Display
- [ ] Create `v2/frontend/src/components/QuotaDisplay.tsx`:
  - Show quota usage (videos: X/15, storage: X GB/5 GB)
  - Display in user profile or header
  - Design system styling

#### 12.8 Test Script
- [ ] Create `v2/scripts/for-development/test-phase12.sh`:
  - Create 15 videos (should work)
  - Try to create 16th video (should fail with message)
  - Upload files totaling 5 GB (should work)
  - Try to upload more (should fail with message)
  - Delete video (quota should update)
  - Verify limits apply AFTER video creation

### Files to Create
- `v2/backend/app/services/quota_service.py`
- `v2/backend/app/services/storage_management_service.py`
- `v2/backend/app/middleware/rate_limit_middleware.py`
- `v2/frontend/src/components/QuotaDisplay.tsx`
- `v2/scripts/for-development/test-phase12.sh`

### Files to Update
- `v2/backend/app/models/user.py` (add video_count, storage_bytes)
- `v2/backend/app/api/v1/routes_songs.py` (check quotas)
- `v2/backend/app/api/v1/routes_composition.py` (check quotas, update quotas)

### Test Criteria
- ✅ 15 video limit enforced
- ✅ 5 GB storage limit enforced
- ✅ Limits apply AFTER video creation completes
- ✅ User-friendly error messages shown
- ✅ Quota updates when videos deleted

---

## Phase 13: Video Library & Sharing

**Goal**: List videos, shareable URLs, delete

### Subtasks

#### 13.1 Library API Routes
- [ ] Create `v2/backend/app/api/v1/routes_library.py`:
  - `GET /api/videos` endpoint:
    - List user's videos
    - Return: id, title, shareable_url, created_at, is_finalized
  - `DELETE /api/videos/{id}` endpoint:
    - Delete video
    - Delete from S3
    - Update user quotas
    - Return success

#### 13.2 Shareable URL Generation
- [ ] Update `v2/backend/app/services/storage_service.py`:
  - `generate_shareable_url(video_id) -> str`
  - Generate presigned URL (long expiration)
  - Or use public URL if bucket is public
  - Store in video record

#### 13.3 Frontend Library API Client
- [ ] Create `v2/frontend/src/api/library.ts`:
  - `listVideos()` function
  - `deleteVideo(videoId)` function
  - `getShareableUrl(videoId)` function

#### 13.4 Frontend Video Card Component
- [ ] Create `v2/frontend/src/components/VideoCard.tsx`:
  - Display video info
  - Show shareable URL (copyable)
  - Delete button
  - Design system styling

#### 13.5 Frontend Video Library Page
- [ ] Create `v2/frontend/src/pages/VideoLibraryPage.tsx`:
  - List all user's videos
  - Video cards with status and progress (for in-progress videos)
  - Show in-progress videos with progress indicator
  - Empty state
  - Design system styling
  - **Auto-resume**: When user clicks on in-progress video, automatically start polling for progress

#### 13.6 Update Main App
- [ ] Update `v2/frontend/src/App.tsx`:
  - Add library route

#### 13.7 Test Script
- [ ] Create `v2/scripts/for-development/test-phase13.sh`:
  - List videos
  - Generate shareable URL
  - Verify URL is accessible
  - Delete video
  - Verify video deleted from S3
  - Verify quota updated

### Files to Create
- `v2/backend/app/api/v1/routes_library.py`
- `v2/frontend/src/pages/VideoLibraryPage.tsx`
- `v2/frontend/src/components/VideoCard.tsx`
- `v2/frontend/src/api/library.ts`
- `v2/scripts/for-development/test-phase13.sh`

### Files to Update
- `v2/backend/app/services/storage_service.py` (add shareable URL function)
- `v2/backend/app/main.py` (add library routes)
- `v2/frontend/src/App.tsx` (add library route)

### Test Script
```bash
# scripts/for-development/test-phase13.sh
# Tests: List videos, generate shareable URL, delete video, verify quota updated
```

### Test Criteria
- ✅ Can list user's videos
- ✅ Shareable URL is generated
- ✅ Shareable URL is accessible
- ✅ Can delete video
- ✅ Quota updated after deletion

---

## Phase 14: Frontend - Video Player & Lyrics

**Goal**: Video player, lyrics display, regeneration UI

### Subtasks

#### 14.1 Video Player Component
- [ ] Create `v2/frontend/src/components/VideoPlayer.tsx`:
  - HTML5 video element
  - Play/pause controls
  - Progress bar
  - Fullscreen support
  - Design system styling
  - Handle video loading states

#### 14.2 Lyrics Display Component
- [ ] Create `v2/frontend/src/components/LyricsDisplay.tsx`:
  - Display lyrics for current section
  - Show lyrics below video
  - **Stretch goal**: Highlight lyrics based on playback time
  - Design system styling

#### 14.3 Video Page
- [ ] Create `v2/frontend/src/pages/VideoPage.tsx`:
  - Video player component
  - Lyrics display component
  - Regenerate button (if not finalized)
  - Finalize button (if not finalized)
  - Shareable URL display
  - Design system styling

#### 14.4 Lyrics Assignment Service (Backend)
- [ ] Create `v2/backend/app/services/lyric_assignment_service.py`:
  - `assign_lyrics_to_sections(lyrics, sections) -> List[SectionLyrics]`
  - Assign lyrics to sections based on timestamps
  - Handle word-splitting (include full word in both sections)
  - Return lyrics for each section (empty list if no lyrics available)
  - Handle case where no lyrics were detected (return empty lists for all sections)

#### 14.5 Update Section API
- [ ] Update `v2/backend/app/api/v1/routes_sections.py`:
  - `GET /api/songs/{id}/sections/{section_id}/lyrics` endpoint:
    - Return lyrics for section (empty list if no lyrics available)

#### 14.6 Frontend Lyrics API Client
- [ ] Update `v2/frontend/src/api/sections.ts`:
  - `getSectionLyrics(songId, sectionId)` function

#### 14.7 Test Script
- [ ] Create `v2/scripts/for-development/test-phase14.sh`:
  - Play video
  - Display lyrics
  - Test pause/regenerate flow
  - Test lyrics assignment
  - Test word-splitting across sections

### Files to Create
- `v2/frontend/src/components/VideoPlayer.tsx`
- `v2/frontend/src/components/LyricsDisplay.tsx`
- `v2/frontend/src/pages/VideoPage.tsx`
- `v2/backend/app/services/lyric_assignment_service.py`
- `v2/scripts/for-development/test-phase14.sh`

### Files to Update
- `v2/backend/app/api/v1/routes_sections.py` (add lyrics endpoint)
- `v2/frontend/src/api/sections.ts` (add lyrics function)
- `v2/frontend/src/App.tsx` (add video route)

### Test Criteria
- ✅ Video plays correctly
- ✅ Lyrics display for current section (or empty if no lyrics)
- ✅ Pause/regenerate flow works
- ✅ Lyrics assigned correctly to sections (or empty lists if no lyrics)
- ✅ Word-splitting works (full word in both sections, if lyrics available)

---

## Phase 15: Progress Overlay & UI Polish

**Goal**: Progress indicators, error handling, UI polish

**Key Requirements:**
- **Progress tracking** (from IMPLEMENTATION_CHALLENGES.md):
  - Three separate progress endpoints:
    1. Analysis: `GET /api/jobs/{job_id}` - Milestone-based (25%, 50%, 70%, 85%, 100%)
    2. Clip generation + composition: `GET /api/songs/{id}/generation/status` - Combined (0-100%)
       - Clip generation: 0-80% (percentage-based)
       - Composition: 80-100% (milestone-based: 80%, 90%, 95%, 100%)
    3. Regeneration: `GET /api/videos/{id}/regeneration/status` - Percentage-based
  - Frontend polls every 3 seconds
  - Progress persists in database (user can resume polling when returning)
  - Show one thing at a time (no multi-phase progress)
- **Error messages**: Generic, user-friendly (technical details in logs only)
- **User workflow**: Jobs continue running if user leaves, progress shown when they return

### Subtasks

#### 15.1 Progress Overlay Component
- [ ] Create `v2/frontend/src/components/ProgressOverlay.tsx`:
  - Show progress for different phases:
    - Phase 1: Analysis progress (milestone-based: 25%, 50%, 70%, 85%, 100%)
    - Phase 2: Generation progress (combined clip+composition: 0-100%)
    - Phase 3: Regeneration progress (percentage-based: 0-100%)
  - Poll appropriate endpoint every 3 seconds
  - Show progress stages:
    - Analysis: "Analyzing song...", "Detecting beats...", etc.
    - Generation: "Generating clips...", "Composing video...", etc.
  - Progress bar
  - Error display (generic user-friendly messages)
  - Loading states
  - Auto-resume polling when user returns to in-progress video

#### 15.2 Error Display Component
- [ ] Create `v2/frontend/src/components/ErrorDisplay.tsx`:
  - Display user-friendly error messages
  - Show songId for errors
  - Retry button (if applicable)
  - Design system styling

#### 15.3 Update Section Editor Page
- [ ] Update `v2/frontend/src/pages/SectionEditorPage.tsx`:
  - Add progress overlay (Phase 1: Analysis)
  - Poll `GET /api/jobs/{job_id}` every 3 seconds
  - Show analysis progress (milestone-based: 25%, 50%, 70%, 85%, 100%)
  - Show analysis results
  - Show prompt editor
  - Handle errors (generic user-friendly messages)
  - Auto-resume polling if user returns to page

#### 15.4 Update Video Page
- [ ] Update `v2/frontend/src/pages/VideoPage.tsx`:
  - Add progress overlay (Phase 2: Generation)
  - Poll `GET /api/songs/{id}/generation/status` every 3 seconds
  - Show combined clip+composition progress (0-100%)
  - Handle errors (generic user-friendly messages)
  - Auto-resume polling if user returns to page

#### 15.5 Error Handling (Backend)
- [ ] Update all API routes:
  - Return user-friendly error messages
  - Log technical details to server
  - Include songId in error responses

#### 15.6 Test Script
- [ ] Create `v2/scripts/for-development/test-phase15.sh`:
  - Test progress overlay displays
  - Test error handling
  - Test UI responsiveness
  - Test error messages are user-friendly

### Files to Create
- `v2/frontend/src/components/ProgressOverlay.tsx`
- `v2/frontend/src/components/ErrorDisplay.tsx`
- `v2/scripts/for-development/test-phase15.sh`

### Files to Update
- `v2/frontend/src/pages/SectionEditorPage.tsx` (add progress overlay)
- `v2/frontend/src/pages/VideoPage.tsx` (add progress overlay)
- All API routes (user-friendly errors)

### Test Script
```bash
# scripts/for-development/test-phase15.sh
# Tests: Show progress, handle errors, UI responsiveness
```

### Test Criteria
- ✅ Progress overlay shows correctly for all three phases (analysis, generation, regeneration)
- ✅ Polling works every 3 seconds
- ✅ Progress persists when user returns (auto-resume polling)
- ✅ Generic user-friendly error messages shown (technical details in logs only)
- ✅ UI is responsive

---

## Phase 16: End-to-End Testing & Sample Videos

**Goal**: Full pipeline test, generate sample videos for MVP demo, documentation

### Subtasks

#### 16.1 E2E Test Script
- [ ] Create `v2/scripts/for-development/test-e2e.sh`:
  - Full pipeline test:
    1. Register user
    2. Upload audio
    3. Analyze song
    4. Create sections
    5. Generate prompts
    6. Plan clips
    7. Generate clips
    8. Compose video
    9. Finalize video
  - Test all error cases
  - Verify all requirements met

#### 16.2 Sample Video Generation Script
- [ ] Create `v2/scripts/for-development/generate-sample-videos.sh`:
  - Generate 3 sample videos:
    1. Upbeat/energetic song
    2. Slow/emotional song
    3. Complex transitions
  - Use sample audio files
  - Document results

#### 16.3 API Documentation
- [ ] Update `v2/docs/ARCHITECTURE.md`:
  - Complete API documentation section
  - All endpoints with full details
  - Request/response examples
  - Error codes
  - Progress tracking details

#### 16.4 Deployment Documentation
- [ ] Create `v2/docs/DEPLOYMENT.md`:
  - Deployment guide
  - Environment setup
  - Infrastructure requirements
  - Step-by-step deployment

#### 16.5 Sample Videos Documentation
- [ ] Create `v2/docs/SAMPLE_VIDEOS.md`:
  - Document sample videos
  - URLs/links
  - Description for evaluator

#### 16.6 Update README
- [ ] Update `v2/README.md`:
  - Complete setup guide
  - Usage instructions
  - API documentation link

#### 16.7 Code Documentation
- [ ] Review all service files:
  - Ensure docstrings complete
  - Ensure comments added (especially librosa)
  - Ensure type hints everywhere

#### 16.8 Test Script
- [ ] Create `v2/scripts/for-development/test-phase16.sh`:
  - Run E2E tests
  - Generate sample videos
  - Verify documentation complete

### Files to Create
- `v2/scripts/for-development/test-e2e.sh`
- `v2/scripts/for-development/generate-sample-videos.sh`
- `v2/docs/ARCHITECTURE.md` (update API documentation section)
- `v2/docs/DEPLOYMENT.md`
- `v2/docs/SAMPLE_VIDEOS.md`
- `v2/scripts/for-development/test-phase16.sh`

### Files to Update
- `v2/README.md` (complete setup guide)
- All service files (ensure docstrings complete)

### Test Script
```bash
# scripts/for-development/test-e2e.sh
# Tests: Full pipeline from upload to final video, all error cases

# scripts/for-development/generate-sample-videos.sh
# Generates: 3 sample videos meeting evaluator recommendations
```

### Test Criteria
- ✅ Full pipeline works end-to-end
- ✅ All error cases handled
- ✅ Sample videos generated
- ✅ Documentation complete
- ✅ All MVP requirements met

---

## Phase 17: Production Deployment Configuration

**Goal**: Configure production-specific settings and optimize deployment

**Note**: Basic deployment infrastructure (Makefile, docker-compose, health checks, Redis setup) was completed in Phase 0. This phase focuses on production-specific optimizations and configurations.

### Subtasks

#### 17.1 Production Configuration
- [ ] Update `v2/backend/app/core/config.py`:
  - Production-specific settings
  - Security hardening
  - Performance optimizations
  - Error handling improvements
  - **Memory**: Document 4GB+ RAM requirement for Railway backend (from IMPLEMENTATION_CHALLENGES.md)

#### 17.2 Production Environment Variables
- [ ] Update `v2/.env.example`:
  - Production environment variables
  - Document all required vars for production
  - Add production-specific configuration options

#### 17.3 Railway Deployment Configuration
- [ ] Create `v2/railway.json` (if needed):
  - Build configuration
  - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Health check endpoint: `/health`
- [ ] Update `v2/docs/DEPLOYMENT.md`:
  - Railway-specific deployment steps:
    - How to create Railway project
    - How to add PostgreSQL addon
    - How to connect Git repository
    - How to set environment variables
    - How to configure build/start commands
    - How to view logs and monitor
  - Database migration steps on Railway (from IMPLEMENTATION_CHALLENGES.md):
    - Use Alembic for migrations (SQLModel compatible)
    - Create migration per phase
    - Keep reversible migrations
    - Separate data migrations from schema migrations
    - Option 1: Run migrations via Railway CLI
    - Option 2: Run migrations on startup (if configured)
    - Option 3: Run migrations manually via Railway shell
  - RQ Worker deployment on Railway:
    - How to create separate Railway service for worker
    - How to set worker command: `rq worker ai_music_video`
    - How to share environment variables with backend API
    - How to monitor worker logs in Railway

#### 17.4 Vercel Deployment Configuration
- [ ] Create `v2/frontend/vercel.json`:
  - Build configuration
  - Environment variables
  - Rewrite rules (if needed)
- [ ] Update `v2/docs/DEPLOYMENT.md`:
  - Vercel-specific deployment steps
  - Environment variable setup on Vercel
  - Build configuration

#### 17.5 AWS S3 + CloudFront Production Setup
- [ ] Update `v2/docs/DEPLOYMENT.md`:
  - Production S3 bucket configuration
  - CloudFront distribution setup
  - CORS configuration for production
  - IAM user setup for production
  - Security best practices

#### 17.6 RQ Worker Production Setup
- [ ] Update `v2/docs/DEPLOYMENT.md`:
  - RQ Worker production deployment:
    - How to create separate Railway service for worker
    - How to configure worker command: `rq worker ai_music_video`
    - How to share environment variables (DATABASE_URL, REDIS_URL, etc.)
    - How to scale workers (multiple instances for parallel processing)
    - How to monitor worker logs in Railway
    - How to restart workers on code changes
  - Redis setup:
    - How to add Railway Redis addon
    - How to configure REDIS_URL environment variable
    - How to verify Redis connection
  - Monitoring setup:
    - How to view worker logs in Railway
    - How to monitor job queue length (via Redis CLI or dashboard)
    - How to set up alerts for failed jobs
    - How to monitor worker memory usage

#### 17.7 Production Test Script
- [ ] Create `v2/scripts/for-development/test-phase17.sh`:
  - Test production configuration
  - Verify all production environment variables
  - Test production build process
  - Verify deployment readiness

### Files to Create
- `v2/railway.json` (if needed)
- `v2/frontend/vercel.json`
- `v2/scripts/for-development/test-phase17.sh`

### Files to Update
- `v2/backend/app/core/config.py` (production config)
- `v2/.env.example` (production env vars)
- `v2/docs/DEPLOYMENT.md` (production deployment guide)

### Test Script
```bash
# scripts/for-development/test-phase17.sh
# Tests: Production configuration, build process, deployment readiness
```

### Test Criteria
- ✅ Production configuration loads correctly
- ✅ Production build succeeds
- ✅ All production environment variables documented
- ✅ Deployment documentation complete

---

## Phase 18: Production Deployment & Monitoring

**Goal**: Deploy to production, set up monitoring, verify everything works

### Subtasks

#### 18.1 Production Deployment
- [ ] Set up production database (Railway PostgreSQL addon)
  - Create PostgreSQL addon in Railway
  - Note connection string for environment variables
- [ ] Configure S3 bucket (production)
  - Create S3 bucket with appropriate region
  - Configure bucket policies and CORS
  - Set up IAM user with read/write permissions
- [ ] Set up CloudFront distribution
  - Create CloudFront distribution pointing to S3 bucket
  - Configure CORS and caching policies
  - Note CloudFront domain for environment variables
- [ ] Set up Redis for production
  - Add Railway Redis addon to project
  - Note Redis URL for environment variables
- [ ] Set up environment variables on Railway (Backend API service)
  - DATABASE_URL (from PostgreSQL addon)
  - REDIS_URL (from Redis addon)
  - RQ_WORKER_QUEUE=ai_music_video
  - S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
  - REPLICATE_API_TOKEN
  - SECRET_KEY (JWT signing)
  - CORS_ORIGINS (Vercel frontend URL)
  - ENVIRONMENT=production
- [ ] Set up environment variables on Vercel
  - VITE_API_URL (Railway backend URL)
  - Any other frontend-specific variables
- [ ] Build and deploy backend API to Railway
  - Connect Railway to Git repository
  - Configure build command (if needed)
  - Configure start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - Deploy and verify health check endpoint
- [ ] Deploy RQ worker to Railway (separate service)
  - Create new Railway service in same project
  - Use same Git repository
  - Configure start command: `rq worker ai_music_video`
  - Share environment variables with backend API service
  - Deploy and verify worker connects to Redis
- [ ] Build and deploy frontend to Vercel
  - Connect Vercel to Git repository
  - Configure build command: `npm run build`
  - Configure output directory: `dist`
  - Deploy and verify frontend is accessible
- [ ] Run database migrations
  - Option 1: Via Railway CLI: `railway run alembic upgrade head`
  - Option 2: Via Railway shell: Connect to shell and run migrations
  - Option 3: On startup: Configure migrations to run automatically (if desired)
  - Verify all tables created
  - Verify migrations table exists and is up to date
- [ ] Configure domain and SSL (optional)
  - Set up custom domain on Railway (if needed)
  - Set up custom domain on Vercel (if needed)
  - SSL certificates are automatic on Railway/Vercel

#### 18.2 Monitoring Setup
- [ ] **Defer monitoring & observability until post-MVP** (from IMPLEMENTATION_CHALLENGES.md)
- [ ] Basic logging setup:
  - Railway logs (automatic, view in Railway dashboard)
  - Vercel logs (automatic, view in Vercel dashboard)
  - Railway worker logs (view worker execution logs)
  - Structured logging for debugging
- [ ] Create `v2/scripts/monitor.sh` (basic):
  - Check Railway backend health
  - Check Vercel frontend status
  - Check RQ worker status and job queue
  - Check database connection
  - Check S3 access

#### 18.3 Monitoring Documentation
- [ ] Update `v2/docs/DEPLOYMENT.md`:
  - How to view logs (Railway, Vercel, worker logs)
  - How to debug production issues (basic)
  - **Note**: Full monitoring & observability deferred to post-MVP

#### 18.4 Production Testing
- [ ] Test full pipeline in production
- [ ] Verify all MVP requirements met
- [ ] Generate sample videos in production
- [ ] Test with evaluator prompts

#### 18.5 Deployment Checklist
- [ ] All environment variables configured (Railway backend, Railway worker, Vercel)
- [ ] Database migrations run
- [ ] S3 bucket configured with proper permissions
- [ ] CloudFront distribution configured
- [ ] Backend API accessible on Railway
- [ ] Frontend accessible on Vercel
- [ ] RQ worker deployed and running on Railway
- [ ] SSL configured (automatic on Railway/Vercel)
- [ ] Domain DNS configured (if using custom domain)
- [ ] Monitoring/logging set up
- [ ] Health checks passing
- [ ] MVP checkpoint: All 7 requirements met
- [ ] Sample videos: 3 videos generated
- [ ] Demo ready: Evaluator can test

#### 18.6 Test Script
- [ ] Create `v2/scripts/for-development/test-phase18.sh`:
  - Production health checks
  - Full pipeline in production
  - Monitoring verification

### Files to Create
- `v2/infra/monitoring/docker-compose.monitoring.yml` (optional)
- `v2/scripts/monitor.sh`
- `v2/docs/MONITORING.md`
- `v2/scripts/for-development/test-phase18.sh`

### Files to Update
- `v2/docs/DEPLOYMENT.md` (add production deployment steps)

### Test Script
```bash
# scripts/for-development/test-phase18.sh
# Tests: Production health checks, full pipeline in production, monitoring
```

### Test Criteria
- ✅ Production deployment successful
- ✅ All services running
- ✅ Full pipeline works in production
- ✅ Monitoring set up
- ✅ MVP checkpoint met
- ✅ Sample videos generated
- ✅ Demo ready

