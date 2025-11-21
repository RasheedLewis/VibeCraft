# Logging Guide for E2E Testing

This document describes where logs are written and how to inspect them during E2E testing.

## Log File Locations

When running the development environment via `scripts/dev.sh`, logs are written to the `logs/` directory at the project root:

```
logs/
├── backend.log      # Backend API server logs (uvicorn)
├── worker.log       # RQ worker logs (job execution)
├── frontend.log     # Frontend dev server logs (Vite)
└── combined.log    # (Currently not populated automatically)
```

**Note:** The `logs/` directory is gitignored and created automatically by the dev script.

## Backend Logs (`logs/backend.log`)

### What's Logged

1. **Uvicorn Access Logs** (stdout)
   - HTTP request/response logs
   - Format: `%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s`
   - Example: `2025-11-21 11:13:15 - 127.0.0.1:54321 - "POST /api/v1/songs HTTP/1.1" 201`

2. **Uvicorn Error Logs** (stderr)
   - Server errors, exceptions
   - Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

3. **Application Logs** (stderr)
   - All Python `logger.info()`, `logger.error()`, `logger.warning()`, `logger.exception()` calls
   - Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

### Key Logging Points

**API Routes (`backend/app/api/v1/routes_songs.py`):**
- `logger.exception()` on upload errors (line 176, 203)
- `logger.exception()` on composition errors (line 608)

**Song Analysis Service (`backend/app/services/song_analysis.py`):**
- `logger.info()` - Job enqueuing, status updates, progress
- `logger.warning()` - Configuration issues, missing data
- `logger.error()` - Missing audio keys
- `logger.exception()` - Analysis failures (line 165)
- Look for: `🔵 [ANALYSIS]`, `✅ [ANALYSIS]`, `❌ [ANALYSIS]`, `⚠️ [ANALYSIS]` prefixes

**Section Inference (`backend/app/services/section_inference.py`):**
- `logger.info()` - Section detection details, clustering results
- `logger.warning()` - No chorus/verse candidates found

**Audjust Client (`backend/app/services/audjust_client.py`):**
- Errors are raised as exceptions (no direct logging, but exceptions will appear in logs)

**Clip Generation (`backend/app/services/clip_generation.py`):**
- Uses `logger` from module (check for clip-related errors)

### Logging Configuration

- **Config File:** `backend/logging_config.json`
- **Python Config:** `backend/app/core/logging.py`
- **Log Level:** Controlled by `API_LOG_LEVEL` env var (default: "info")
- **SQLAlchemy:** Set to WARNING level to reduce noise

## Worker Logs (`logs/worker.log`)

### What's Logged

All output from RQ worker processes, including:

1. **Job Execution Logs**
   - When jobs are picked up
   - Progress updates
   - Completion/failure messages
   - Exception tracebacks

2. **Service Logs**
   - All `logger.*()` calls from services executed in worker context
   - Song analysis pipeline logs
   - Clip generation logs
   - Video composition logs

### Key Things to Look For

**Song Analysis Jobs:**
- Look for: `🚀 [ANALYSIS] RQ WORKER PICKED UP JOB - song_id=...`
- Look for: `❌ [ANALYSIS] Song analysis failed`
- Look for: Audjust API errors or fallback to internal detection

**Clip Generation Jobs:**
- Job enqueuing messages
- Processing errors
- Queue name verification (should include `:clip-generation` suffix)

## Frontend Logs (`logs/frontend.log`)

### What's Logged

1. **Vite Dev Server Output**
   - Build errors
   - HMR (Hot Module Reload) messages
   - Server startup messages

2. **Browser Console Logs** (NOT in log file)
   - `console.log()`, `console.error()`, `console.warn()` calls
   - These appear in browser DevTools, not in `frontend.log`

### Frontend Console Logging Points

**UploadPage (`frontend/src/pages/UploadPage.tsx`):**
- `console.log('[compose] ...')` - Composition job lifecycle
- `console.log('[generate-clips] ...')` - Clip generation lifecycle
- `console.error('[compose] Failed to start composition:', err)`
- `console.error('[generate-clips] Error:', err)`
- `console.error('Upload failed', err)`
- `console.info('Regenerate clip requested', clip.id)`

**Note:** These console logs appear in the browser DevTools console, not in `frontend.log`.

## How to Inspect Logs During E2E Testing

### Real-time Monitoring

```bash
# Watch backend logs
tail -f logs/backend.log

# Watch worker logs
tail -f logs/worker.log

# Watch both simultaneously
tail -f logs/backend.log logs/worker.log

# Watch all logs
tail -f logs/*.log
```

### Search for Errors

```bash
# Find all errors in backend
grep -i error logs/backend.log

# Find exceptions with tracebacks
grep -A 10 "Traceback" logs/backend.log logs/worker.log

# Find specific song_id
grep "song_id=<uuid>" logs/backend.log logs/worker.log

# Find analysis job issues
grep "\[ANALYSIS\]" logs/worker.log

# Find clip retry issues
grep "retry" logs/backend.log logs/worker.log -i
```

### Common Error Patterns to Look For

1. **Audjust API Issues:**
   - `AudjustConfigurationError` - Missing API credentials
   - `AudjustRequestError` - HTTP errors, missing sections
   - Look in `logs/worker.log` during song analysis

2. **Section Inference Issues:**
   - `No chorus candidates found` - Warning in section inference
   - `No verse clusters detected` - Warning in section inference
   - Look in `logs/worker.log` during song analysis

3. **Clip Retry Issues:**
   - `ClipNotFoundError` - Clip doesn't exist
   - `ValueError` - Clip already processing/queued
   - Look in `logs/backend.log` for API errors

4. **Queue Issues:**
   - Queue name mismatches (should include `:clip-generation` suffix)
   - Job not found errors
   - Look in `logs/worker.log` and `logs/backend.log`

5. **Database Issues:**
   - SQLAlchemy errors (usually in `logs/backend.log`)
   - Connection errors
   - Transaction rollback messages

### Browser DevTools Console

During E2E testing, also check the browser console (F12 → Console tab) for:
- Frontend errors
- API call failures
- State update issues
- React errors

## Log Format Examples

### Backend Log Format
```
2025-11-21 11:13:15 - app.services.song_analysis - INFO - 🔵 [ANALYSIS] Enqueuing analysis job - song_id=123e4567-e89b-12d3-a456-426614174000
2025-11-21 11:13:16 - app.services.song_analysis - ERROR - ❌ [ANALYSIS] Song analysis failed for song_id=123e4567-e89b-12d3-a456-426614174000, job_id=abc123
```

### Worker Log Format
```
2025-11-21 11:13:20 - app.services.song_analysis - INFO - ================================================================================
2025-11-21 11:13:20 - app.services.song_analysis - INFO - 🚀 [ANALYSIS] RQ WORKER PICKED UP JOB - song_id=123e4567-e89b-12d3-a456-426614174000
```

### Access Log Format
```
2025-11-21 11:13:15 - 127.0.0.1:54321 - "POST /api/v1/songs HTTP/1.1" 201
2025-11-21 11:13:16 - 127.0.0.1:54321 - "GET /api/v1/songs/123e4567-e89b-12d3-a456-426614174000/analysis HTTP/1.1" 200
```

## Tips for Debugging

1. **Start with worker logs** - Most processing happens in workers
2. **Check timestamps** - Correlate frontend actions with backend/worker logs
3. **Search for song_id** - Use the song UUID to trace all related logs
4. **Look for exception tracebacks** - Full stack traces are in logs
5. **Check both backend and worker** - API errors in backend, processing errors in worker
6. **Monitor browser console** - Frontend errors and API responses

## Environment Variables

- `API_LOG_LEVEL` - Controls backend log level (default: "info")
  - Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
  - Set in `backend/.env` or environment

