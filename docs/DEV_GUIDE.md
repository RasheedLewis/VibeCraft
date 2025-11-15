# Developer Guide

This guide walks new contributors through setting up the AI Music Video project locally. It complements the architecture overview in `ARCH.md`, the roadmap in `ROADMAP.md`, and the detailed requirements in `PRD.md`.

---

## 1. Prerequisites

- macOS or Linux with a recent POSIX shell
- Python 3.10+ with `venv`
- Node.js 20+ and npm 10+
- Docker Desktop (for Postgres/Redis containers or future Compose flow)
- `ffmpeg` installed locally (`brew install ffmpeg`)

> Tip: Run everything from the repo root (`ai-music-video/`).

---

## 2. Repository Bootstrap

Run these from the repository root (`ai-music-video/`) to stand up the Python and Node environments.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
npm --prefix frontend install
```

> `npm --prefix frontend install` keeps the command runnable from the repo root. `npm install` inside `frontend/` works the same if you prefer to `cd` first.

---

## 2.1 Optional Package Managers (Poetry / pnpm)

- **Poetry**: `poetry install` from `backend/` (after generating a `pyproject.toml`) creates an isolated virtualenv automatically. Activate with `poetry shell` before running backend commands.
- **pnpm**: `pnpm install --dir frontend` installs frontend dependencies with pnpm’s content-addressable store. Add `.npmrc` / `.pnpmfile.cjs` as needed to share settings with the team.

Stick with the pip + npm defaults unless your team standardizes on these alternatives.

---

## 2.2 Environment Templates

Copy the provided samples before running the apps:

```bash
cp docs/backend.env.example backend/.env
cp docs/frontend.env.example frontend/.env
```

Populate the blanks with your own credentials (S3, Replicate, etc.).

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
cd ./backend
source ../.venv/bin/activate
uvicorn app.main:app --reload
```

In a separate shell:

```bash
source ./.venv/bin/activate
cd ./backend
rq worker ai_music_video
```

> Swap the worker command for Celery if you adopt it instead of RQ.

---

## 5. Frontend Runtime

Start the Vite dev server for the React + TypeScript UI.

```bash
cd ./frontend
npm run dev -- --host
```

Visit `http://localhost:5173` to confirm the scaffolded app loads.

---

## 6. Optional: Docker Compose Flow

Later (when /infra exists)...

When the Compose stack is ready, you can run everything together:

```bash
cd ./infra
docker compose up --build
```

---

## 7. Next Steps

1. Add `.env` and `.env.example` files with keys for Postgres, Redis, S3, Replicate, and any AI providers.
2. Scaffold FastAPI routers, schemas, and services as outlined in `PRD.md`.
3. Implement frontend pages and components per the roadmap (Upload, Song Profile, Section cards, Gallery).

Refer back to `PRD.md` and `ROADMAP.md` for task-level details once your environment boots cleanly.

