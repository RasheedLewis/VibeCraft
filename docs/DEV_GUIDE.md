# Developer Guide

This guide walks new contributors through setting up the AI Music Video project locally. It complements the architecture overview in `ARCH.md`, the roadmap in `ROADMAP.md`, and the detailed requirements in `PRD.md`.

---

## 1. Prerequisites

- macOS or Linux with a recent POSIX shell
- Python 3.10+ with `venv`
- Node.js 20+ and npm 10+
- Docker Desktop (for Postgres/Redis containers or future Compose flow)
- `ffmpeg` installed locally (`brew install ffmpeg`)

> Tip: Run everything from the repo root at `/Users/rasheedlewis/Workspace/gauntlet/ai-music-video`.

---

## 2. Repository Bootstrap

Create the monorepo layout and initialize runtime environments.

```bash
mkdir -p /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/{backend,frontend,infra}
python3 -m venv /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/.venv
source /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/.venv/bin/activate
pip install fastapi "uvicorn[standard]" sqlmodel sqlalchemy pydantic ffmpeg-python librosa python-dotenv
npm create vite@latest /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/frontend -- --template react-ts
cd /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/frontend && npm install @tanstack/react-query axios
```

---

## 3. Local Infrastructure

Spin up Postgres and Redis the backend expects.

```bash
docker run --name ai-music-video-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=ai_music_video \
  -p 5432:5432 \
  -d postgres:16

docker run --name ai-music-video-redis \
  -p 6379:6379 \
  -d redis:7
```

> You can replace these single containers with the `infra/compose.yml` workflow once it exists.

---

## 4. Backend Runtime

Launch the FastAPI app and the background worker (RQ by default).

```bash
cd /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/backend
source ../.venv/bin/activate
uvicorn app.main:app --reload
```

In a separate shell:

```bash
source /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/.venv/bin/activate
cd /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/backend
rq worker ai_music_video
```

> Swap the worker command for Celery if you adopt it instead of RQ.

---

## 5. Frontend Runtime

Start the Vite dev server for the React + TypeScript UI.

```bash
cd /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/frontend
npm run dev -- --host
```

Visit `http://localhost:5173` to confirm the scaffolded app loads.

---

## 6. Optional: Docker Compose Flow

When the Compose stack is ready, you can run everything together:

```bash
cd /Users/rasheedlewis/Workspace/gauntlet/ai-music-video/infra
docker compose up --build
```

---

## 7. Next Steps

1. Add `.env` and `.env.example` files with keys for Postgres, Redis, S3, Replicate, and any AI providers.
2. Scaffold FastAPI routers, schemas, and services as outlined in `PRD.md`.
3. Implement frontend pages and components per the roadmap (Upload, Song Profile, Section cards, Gallery).

Refer back to `PRD.md` and `ROADMAP.md` for task-level details once your environment boots cleanly.

