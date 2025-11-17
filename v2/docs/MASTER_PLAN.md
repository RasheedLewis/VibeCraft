# VibeCraft v2 — Master Plan

**Note**: This is the single source of truth for VibeCraft v2. All requirements, architecture, and implementation phases are documented here.

---

## Table of Contents

1. [MVP Checkpoint Requirements](#mvp-checkpoint-requirements)
2. [Requirements & Scope](#requirements--scope)
3. [Architecture & Tech Stack](#architecture--tech-stack)
4. [Implementation Guidelines](#implementation-guidelines)
5. [Implementation Phases](#implementation-phases)
6. [Deployment](#deployment)

**Related Documents:**
- [`ARCHITECTURE.md`](ARCHITECTURE.md) - Detailed architecture, tech stack, APIs, data models, user flows
- [`IMPLEMENTATION_PHASES.md`](IMPLEMENTATION_PHASES.md) - Granular breakdown of all 18 implementation phases
- [`POST_PHASE_NOTES.md`](POST_PHASE_NOTES.md) - Testing strategy, integration tests, unit tests, and phase-specific test scripts

---

## MVP Checkpoint Requirements

**Must Have (All Required):**
1. ✅ Working video generation for at least ONE category (music video)
2. ✅ Basic prompt to video flow (text input to video output)
3. ✅ Audio visual sync (video matches audio timing/beats)
4. ✅ Multi clip composition (at least 3 to 5 clips stitched together)
5. ✅ Consistent visual style across clips
6. ✅ Deployed pipeline (API or web interface)
7. ✅ Sample outputs (at least 2 generated videos demonstrating capability)

**At Minimum (All Required):**
1. ✅ Prompt Parser: Interprets user input and extracts creative direction
2. ✅ Content Planner: Breaks video into scenes/segments with timing
3. ✅ Generation Engine: Calls AI models (video, image, audio) for each segment
4. ✅ Composition Layer: Stitches clips with transitions and audio sync
5. ✅ Output Handler: Renders final video in standard format (MP4, WebM)

**Evaluator Recommendations (For Demo):**
- ✅ One video synced to an upbeat/energetic song
- ✅ One video synced to a slow/emotional song
- ✅ One video demonstrating complex visual transitions

**Note**: Users can override/edit the video prompt entirely (already supported via prompt editing in UI).

---

## Requirements & Scope

### Core Requirements

**Front-End**
- Must use DESIGN_SYSTEM
- Render final video with play button and shareable URL
- Show song representation with markers to divide into 3-10 sections (1s-2min each, max 5min song)
- Allow user to label each section and add optional section prompt notes (100 chars max)
- Show suggestion for common pop structure
- Progress overlay (analysis results + prompt approval, then generation progress)
- Music video type selection (system suggests, user chooses)
- User can override/edit entire prompt
- Lyrics display under video (stretch: real-time highlighting)
- Regeneration UI (pause → regenerate → choose section/clip)
- Finalize button
- Video library (list, shareable URL, delete)

**Back-End**
- Song analysis (BPM required, beats, genre, mood, lyrics with timestamps)
- User-generated sections (not auto-generated)
- Beat alignment (snap markers to beat grid)
- Lyrics assignment to sections (precise timestamps, word-splitting across sections)
- Clip generation (3-10 seconds per clip, multiple clips per section)
- Video normalization and composition (stitch, mux audio, handle mismatches)
- Parallel generation with rate limiting and auto-retry
- Error handling (fail entire video if any part fails)
- Authentication (email/password, simple)
- Rate limiting (15 videos max, 5 GB storage max per user)
- Regeneration (once per section, once per clip)
- Finalization (triggers cleanup, no further edits)
- Storage cleanup (discard intermediates after finalization)

**Architecture Principles**
- Modular, internal-API-like design
- Lean, understandable code (especially librosa)
- Reuse existing code where appropriate
- Comprehensive testing at each phase
- One-command test scripts for all functionality

---

## In Scope vs. Out of Scope

### ✅ In Scope (MVP)

**Core Functionality**
- User authentication (email/password)
- Audio upload (MP3, WAV, M4A, max 5 minutes)
- Song analysis (BPM, beats, genre, mood, lyrics with timestamps)
- User-defined sections (3-10 sections, 1s-2min each, beat-aligned)
- Section labels and optional prompt notes (100 chars max)
- Music video type selection (system suggests, user chooses)
- Clip generation (3-10 seconds per clip, multiple clips per section)
- Video composition (stitch clips, mux audio, 1080p output)
- Regeneration (once per section, once per clip)
- Finalization (triggers cleanup, no further edits)
- Video library (list, shareable URL, delete)
- Rate limiting (15 videos max, 5 GB storage max per user)
- Lyrics display under video (with stretch goal: real-time highlighting)

**Technical**
- Modular, internal-API-like service architecture
- Lean, understandable code (especially librosa)
- Reuse existing code where appropriate
- Comprehensive testing at each phase
- One-command test scripts for all functionality

### ❌ Out of Scope (Post-MVP)

- Section-based approval workflow (user creates sections directly)
- Multiple video templates/styles (single type selection)
- Character consistency training
- Manual video editing UI
- Multi-camera or 3D production
- Advanced transitions/effects (basic hard cuts only)
- Cost optimization/caching (basic implementation)
- Sample video gallery
- User collaboration/sharing features
- Mobile app
- Real-time collaboration
- Advanced analytics

---

## Risks and Possible Mitigations

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **librosa complexity** | High | High | Add extensive comments, break into smaller functions, document each step |
| **Replicate API rate limits** | Medium | Medium | Implement queue with concurrency limits, exponential backoff retries |
| **Video/audio sync drift** | High | Medium | Use FFmpeg's audio sync features, test thoroughly, handle mismatches gracefully |
| **Beat detection inaccuracy** | Medium | Medium | Fall back to time-based boundaries, allow manual adjustment |
| **Storage quota management** | Medium | Low | Track usage accurately, implement cleanup, warn users before limits |
| **Parallel clip generation failures** | High | Medium | Retry logic, fail-fast on critical errors, clear error messages |

### Product Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **User confusion with sections** | Medium | Medium | Clear UI, helpful suggestions, validation feedback |
| **Regeneration limits unclear** | Low | Medium | Show limits clearly in UI, explain why limits exist |
| **Finalization irreversible** | Medium | Low | Clear warnings, confirmation dialog, explain what happens |
| **Quota limits too restrictive** | Medium | Low | Monitor usage, adjust if needed, clear messaging |

### Process Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Scope creep** | High | Medium | Strict adherence to in-scope items, defer out-of-scope to post-MVP |
| **Code complexity grows** | High | Medium | Regular refactoring, modular architecture, code reviews |
| **Testing gaps** | High | Medium | Test scripts at every phase, comprehensive test coverage |

---

## System Requirements

### Functional Requirements

1. **User Management**
   - Email/password authentication
   - User session management
   - Rate limiting per user

2. **Audio Processing**
   - Accept MP3, WAV, M4A formats
   - Max 5 minutes duration
   - Extract BPM, beat times, genre, mood, lyrics

3. **Section Management**
   - User creates 3-10 sections
   - Sections: 1 second minimum, 2 minutes maximum
   - Beat-aligned snapping
   - Labels and optional prompt notes

4. **Video Generation**
   - Generate 3-6 second clips per section
   - Multiple clips per section (random durations)
   - Parallel generation with rate limiting
   - Retry on failures

5. **Video Composition**
   - Normalize clips (resolution, FPS)
   - Stitch clips together
   - Mux with original audio
   - Handle duration mismatches

6. **Regeneration**
   - Once per section
   - Once per clip
   - Track regeneration counts

7. **Finalization**
   - User-triggered
   - Cleanup intermediates
   - No further edits

### Non-Functional Requirements

- **Performance**: Video generation completes within reasonable time (10-15 min for 3-5 min song)
- **Reliability**: 90%+ success rate for video generation
- **Scalability**: Support multiple concurrent users
- **Security**: Secure authentication, rate limiting, input validation
- **Usability**: Clear UI, helpful error messages, progress feedback
- **Maintainability**: Modular code, comprehensive tests, clear documentation

---

## Architecture & Tech Stack

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for detailed architecture, tech stack, APIs, data models, user flows, and deployment architecture.

**Summary:**
- **Backend**: FastAPI (Python 3.10+), PostgreSQL, RQ workers (background jobs), Redis, AWS S3
- **Frontend**: React + TypeScript, Vite, Tailwind CSS
- **Infrastructure**: Railway (backend + workers), Vercel (frontend), AWS S3 + CloudFront (storage/CDN)
- **External APIs**: Replicate API (video generation, Whisper), AWS S3, CloudFront

---

## Implementation Guidelines

This section contains the guidelines, standards, and checklists that apply to ALL phases. Before implementing any phase, read this section first, then read the specific phase breakdown in [`IMPLEMENTATION_PHASES.md`](IMPLEMENTATION_PHASES.md).

### Key Principles

- **Testable**: Each phase must be independently testable
- **Incremental**: Build one service/component at a time
- **Documented**: Clear interfaces, docstrings, comments (especially librosa)
- **Verified**: Run test script, confirm all tests pass before moving on
- **Confirmed**: AI agent must confirm understanding with developer at each step
- **Pre-Commit Checks**: **CRITICAL** - Before committing any phase:
  - `make lint` must pass with 0 errors (frontend + backend)
  - `make build` must pass with 0 errors (frontend + backend)
  - `make test` must pass with 0 failures (frontend + backend)
  - **NEVER commit if any check fails**
- **Commit Strategy**: Commit entire phase at once, only after all pre-commit checks pass

### AI Agent Guidelines

At each phase:
1. **Confirm Understanding**: Ask developer to confirm understanding of phase goals
2. **Check v1 Implementation**: Review how the feature was implemented in v1 (root of project) to inform v2 implementation:
   - Examine existing code in root `backend/` and `frontend/` directories
   - Understand the approach, patterns, and solutions used
   - Note any lessons learned or issues encountered
   - **v2 can use a different approach** - v1 is for reference, not a requirement to match exactly
   - Adapt and improve based on v1 experience while keeping v2 lean and modular
   - **Note**: It's possible the work wasn't implemented in v1 - that's fine, proceed with v2 implementation from scratch
3. **List Files**: Show exact files to create/update
4. **Show Interfaces**: Display service interfaces before implementation
5. **Test First**: Create test script before implementation
6. **Incremental**: Implement one service/component at a time
7. **Document**: Add docstrings, comments (especially librosa)
8. **Verify**: Run test script, confirm all tests pass
9. **Refactor**: Clean up, remove dead code, simplify
10. **Update Memory for Next Phase**: **BEFORE finishing current phase**, update `v2/docs/memory.md` with a 2-or-3-Agent Split Strategy for the *next* phase:
    - Analyze the next phase's subtasks from `IMPLEMENTATION_PHASES.md`
    - Create a split strategy (2 or 3 agents) with clear role assignments
    - Use descriptive names (e.g., "Backend Agent", "Frontend Agent", "Infrastructure Agent")
    - List subtasks, files to create/update, and dependencies for each agent
    - Note coordination requirements (parallel work, handoff points, etc.)
    - This helps agents coordinate when working on the next phase
11. **Pre-Commit Verification**: **CRITICAL** - Before committing a phase:
    - Run `make lint` - Must pass with 0 errors
    - Run `make build` - Must pass with 0 errors
    - Run `make test` - Must pass with 0 failures
    - Verify both frontend AND backend pass all checks
    - **DO NOT commit if any lint/build/test fails**
12. **Commit Strategy**: Commit entire phase at once, only after all checks pass

### Code Quality Standards

- **Type Hints**: All functions must have type hints
- **Docstrings**: All public functions must have docstrings
- **Comments**: Complex logic (especially librosa) must have inline comments
- **Error Handling**: All external calls must have error handling
- **Logging**: Use structured logging for debugging
- **Testing**: Each service must have unit tests

### Testing Strategy

- **Unit Tests**: Test each service independently
  - Mock external APIs (Replicate, S3, Redis/RQ)
  - Mock network failures, API errors
- **Integration Tests**: Minimal integration tests
  - Use test database, LocalStack for S3, local Redis, RQ worker
  - Start Redis locally, run worker, enqueue test jobs
- **E2E Tests**: Test full user flows
  - Use test Replicate account, test S3 bucket
- **Test Scripts**: One-command scripts in `scripts/for-development/`
  - Include setup/teardown, use fixtures
- **Local Development**: Use `make start` to run all services locally

### Pre-Commit Checklist (MANDATORY)

**Before committing ANY phase, verify ALL of the following:**

- [ ] `make lint` passes with **0 errors** (frontend + backend)
- [ ] `make build` passes with **0 errors** (frontend + backend)
- [ ] `make test` passes with **0 failures** (frontend + backend)
- [ ] All linter warnings resolved (or explicitly documented as acceptable)
- [ ] All build warnings resolved (or explicitly documented as acceptable)
- [ ] All tests pass (no skipped tests unless explicitly documented)
- [ ] Phase test script (`test-phaseX.sh`) passes successfully
- [ ] **DO NOT commit if any check fails - fix issues first**

### Code Quality Checklist

- [ ] Type hints on all functions
- [ ] Docstrings on all public functions
- [ ] Comments on complex logic (especially librosa)
- [ ] Error handling on all external calls
- [ ] Logging for debugging
- [ ] Tests for each service
- [ ] User-friendly error messages

### Testing Checklist

- [ ] Unit tests for each service
- [ ] Integration tests for service interactions
- [ ] E2E tests for full flows
- [ ] Test script runs successfully
- [ ] All edge cases tested
- [ ] Error cases tested

---

## Implementation Phases

See [`IMPLEMENTATION_PHASES.md`](IMPLEMENTATION_PHASES.md) for detailed, granular breakdown of all 18 phases with step-by-step subtasks, file lists, test scripts, and key requirements.

**Note**: Before implementing any phase, read the [Implementation Guidelines](#implementation-guidelines) section above first, then read the specific phase breakdown in `IMPLEMENTATION_PHASES.md`.

---

## Deployment

### Selected Infrastructure

**Backend API**: Railway
- FastAPI application
- PostgreSQL database (Railway PostgreSQL addon)
- Redis (Railway Redis addon)
- Environment variables and secrets management
- Manual deploy from Git (via Railway CLI or dashboard)

**Background Workers**: Railway (Separate Service)
- RQ worker process (same codebase as backend)
- Processes jobs from Redis queue
- Can scale independently (multiple worker instances)
- Same environment variables as backend API
- Deploy as separate Railway service with command: `rq worker ai_music_video`

**Frontend**: Vercel
- React + Vite static build
- Environment variables for API URL
- Manual deploy from Git (via Vercel CLI or dashboard)
- Edge network for fast global delivery

**Video Storage & CDN**: AWS S3 + CloudFront
- S3 bucket for video file storage
- CloudFront distribution for video delivery
- Presigned URLs for private videos
- Public URLs for shareable videos

### Deployment Process

**No automatic CI/CD on push to main** - deployments are manual via `make start` script.

**Local Development & Deployment**:
- Use `make start` script (similar to root repo's Makefile)
- Script handles: dependency installation, database setup, migrations, starting services
- Manual deployment to Railway/Vercel when ready

**Railway Backend**:
- Manual deployment via Railway CLI or dashboard
- Build from Dockerfile or detect Python
- Run migrations manually (via Railway CLI or startup script)
- Health checks via `/health` endpoint

**Vercel Frontend**:
- Manual deployment via Vercel CLI or dashboard
- Build via Vite
- Environment variables from Vercel dashboard
- Preview deployments for PRs (optional)

**One-Time Setup**:
- Database migrations (run via Railway CLI or startup script)
- S3 bucket setup (via AWS Console)
- CloudFront distribution setup (via AWS Console)

### Environment Variables (Production)

**Railway Backend**:
```bash
# Database (auto-provided by Railway PostgreSQL addon)
DATABASE_URL=postgresql://...

# Redis (Railway Redis addon)
REDIS_URL=${{Redis.REDIS_URL}}
RQ_WORKER_QUEUE=ai_music_video

# AWS S3
S3_BUCKET_NAME=vibecraft-videos
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1  # Or your preferred region

# CloudFront (optional, for public video URLs)
CLOUDFRONT_DOMAIN=d1234567890.cloudfront.net

# API Keys
REPLICATE_API_TOKEN=...

# Security
SECRET_KEY=...  # For JWT (generate strong random key)
ENVIRONMENT=production

# CORS (for Vercel frontend)
CORS_ORIGINS=https://vibecraft.vercel.app,https://vibecraft.com
```

**Vercel Frontend**:
```bash
# API URL (Railway backend)
VITE_API_URL=https://vibecraft-production.up.railway.app

# Optional: Analytics, error tracking, etc.
VITE_SENTRY_DSN=...  # If using Sentry
```

**AWS S3 + CloudFront Setup**:
1. Create S3 bucket: `vibecraft-videos`
2. Configure bucket policy for CloudFront access
3. Create CloudFront distribution pointing to S3 bucket
4. Configure CORS on S3 bucket for video playback
5. Set up IAM user with S3 read/write permissions

### Security Considerations

- **Secrets Management**: 
  - Railway: Use Railway secrets (encrypted environment variables)
  - Vercel: Use Vercel environment variables
  - Never commit secrets to Git
- **HTTPS**: 
  - Railway: Automatic HTTPS via Railway domain
  - Vercel: Automatic HTTPS
  - CloudFront: HTTPS by default
- **CORS**: 
  - Configure CORS in FastAPI to allow only Vercel domains
  - Use `CORS_ORIGINS` environment variable
- **Rate Limiting**: 
  - Implement in FastAPI middleware (per-user quotas)
  - Database-based rate limiting (Redis used for job queue only, not rate limiting)
- **Input Validation**: 
  - Pydantic schemas for all API inputs
  - File upload validation (size, type, duration)
- **SQL Injection**: 
  - SQLModel uses parameterized queries (safe)
- **XSS**: 
  - React automatically escapes content
  - Sanitize any user-generated content
- **S3 Security**:
  - Use IAM roles with least privilege
  - Presigned URLs for private videos (time-limited)
  - CloudFront signed URLs for public videos (optional)
- **Database Security**:
  - Railway PostgreSQL: Automatic backups, encrypted at rest
  - Use connection pooling
  - No direct database access from frontend

---

## MVP Checkpoint Validation

Before deployment, verify all MVP requirements:

- [ ] **Working video generation**: Can generate music videos end-to-end
- [ ] **Prompt to video flow**: Text input → video output works
- [ ] **Audio visual sync**: Transitions align with beats
- [ ] **Multi clip composition**: 3-5 clips stitched together
- [ ] **Consistent visual style**: Clips share cohesive aesthetic
- [ ] **Deployed pipeline**: API or web interface accessible
- [ ] **Sample outputs**: At least 2 videos demonstrating capability
- [ ] **Evaluator recommendations**: 3 sample videos (upbeat, slow, complex transitions)

---

## Next Steps

1. Review and refine this plan with developer
2. Confirm understanding of each phase
3. Begin Phase 0: Foundation & Setup
4. Proceed phase by phase, confirming at each step
5. Generate sample videos in Phase 16
6. Deploy after Phase 16 (testing) or Phase 18 (full deployment)
7. Validate MVP checkpoint requirements before demo
