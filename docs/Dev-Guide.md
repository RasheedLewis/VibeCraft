# Developer Guide

Quick setup guide for VibeCraft development. See `Architecture.md` for architecture details.

## Prerequisites

- **macOS or Linux** with POSIX shell
- **Python 3.10-3.12** (3.13+ has compatibility issues; install 3.12: `brew install python@3.12` or `sudo apt install python3.12`)
- **Node.js 20+** and npm 10+
- **Docker Desktop** (for Postgres/Redis)
- **ffmpeg** (`brew install ffmpeg`)

## Quick Setup

From repository root:

```bash
# Create virtual environment (use python3.12 if default is 3.13+)
python3.12 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
npm --prefix frontend install
```

## Environment Configuration

Create `backend/.env`:

```bash
DATABASE_URL=postgresql+psycopg://postgres:postgres@127.0.0.1:5432/ai_music_video
REDIS_URL=redis://localhost:6379/0
RQ_WORKER_QUEUE=ai_music_video
S3_BUCKET_NAME=your-bucket-name
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_REGION=us-east-2
REPLICATE_API_TOKEN=your-replicate-token
OPENAI_API_KEY=your-openai-key
# Optional: WHISPER_API_TOKEN, LYRICS_API_KEY, AUDJUST_BASE_URL, AUDJUST_API_KEY
```

Create `frontend/.env`:
```bash
VITE_API_BASE_URL=http://localhost:8000
```

## Local Infrastructure

Start Postgres and Redis:

```bash
docker rm -f ai-music-video-postgres ai-music-video-redis 2>/dev/null || true
docker run --name ai-music-video-postgres \
  -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=ai_music_video -p 5432:5432 -d postgres:16
docker run --name ai-music-video-redis -p 6379:6379 -d redis:7
docker ps | grep -E "(ai-music-video-postgres|ai-music-video-redis)"
```

**Note:** Use `127.0.0.1` instead of `localhost` in `DATABASE_URL` if you encounter psycopg3 connection issues.

## Running the Application

**Recommended:** `make start` (runs pre-flight checks, starts backend on :8000, 4 RQ workers, frontend on :5173, logs to `logs/`)

**Manual start:**
```bash
# Backend API
cd backend && source ../.venv/bin/activate && uvicorn app.main:app --reload

# RQ Worker (separate terminal, macOS: export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES)
source .venv/bin/activate && cd backend && rq worker ai_music_video

# Frontend
cd frontend && npm run dev -- --host
```

## Development Workflow

```bash
make migrate        # Database migrations (also runs on startup)
make lint / lint-fix / format / format-fix / lint-all  # Code quality
make test           # Run tests
make stop           # Stop all services
```

## Project Structure

- `backend/app/`: `api/v1/` (endpoints), `core/` (config/db/logging), `models/` (ORM), `schemas/` (Pydantic), `services/` (business logic), `workers/` (RQ tasks)
- `frontend/src/`: `components/`, `pages/`, `api/`, `hooks/`, `types/`

## Key Configuration

**Video Composition** (`backend/app/services/video_composition.py`): Default 1920×1080/1080×1920 @ 24fps, CRF 23, preset "medium". Adjust file size: CRF 26-28 (~30-50% smaller), slower preset (~10-20% smaller), or 1280×720 (~40% smaller).

**Beat-Synced Effects:** `BEAT_EFFECT_TEST_MODE=true make start-dev` (exaggerated effects), `SAVE_NO_EFFECTS_VIDEO=true make start-dev` (comparison video).

**Replicate Verification:** `python scripts/check_replicate_models.py [--list]`

## Troubleshooting

**Backend won't start:** Check `logs/backend.log`, verify `.env`, ensure Postgres/Redis running (`docker ps`), Python 3.10-3.12, ffmpeg installed.

**Worker not processing:** Check `REDIS_URL`, verify worker running (`ps aux | grep "rq worker"`), check `logs/worker.log`, clear queue: `python -c "from app.core.queue import get_queue; get_queue().empty()"`

**Frontend can't connect:** Verify `VITE_API_BASE_URL`, check backend: `curl http://localhost:8000/healthz`, check CORS in `backend/app/main.py`, browser console.

**Video generation fails:** Verify `REPLICATE_API_TOKEN`, check job: `https://replicate.com/p/{job_id}`, query DB: `docker exec ai-music-video-postgres psql -U postgres -d ai_music_video -c "SELECT replicate_job_id, error_message, status FROM song_clips WHERE status = 'failed' ORDER BY created_at DESC LIMIT 1;"`, check worker logs.

**Database connection:** Use `127.0.0.1` not `localhost`, verify Postgres running, check port 5432.

**macOS fork safety:** `export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` if RQ workers crash.

## API Testing

```bash
curl http://localhost:8000/healthz
curl -X POST http://localhost:8000/api/v1/songs -H "Content-Type: multipart/form-data" -F "file=@/path/to/audio.mp3"
curl http://localhost:8000/api/v1/songs
```

## Deployment

**System Dependencies:** Backend Dockerfile needs `ffmpeg` and `libsndfile1`.

**Environment Variables:** Backend requires `DATABASE_URL`, `REDIS_URL`, S3 credentials, `REPLICATE_API_TOKEN`, `OPENAI_API_KEY`. Frontend requires `VITE_API_BASE_URL` (set at build time).

**Processes:** Both API server (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`) and RQ worker (`rq worker ai_music_video --url $REDIS_URL`) required.

**Considerations:** Long-running tasks (30+ min), 4GB+ RAM recommended, configure CORS for production, use `/healthz` for monitoring.

## Next Steps

Review `Architecture.md` for architecture, explore `backend/app/services/` for business logic, check `frontend/src/pages/` for UI, see `Makefile` for commands.
