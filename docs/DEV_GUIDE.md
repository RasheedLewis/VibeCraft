# Developer Guide

This guide walks new contributors through setting up the AI Music Video project locally. It complements the architecture overview in `ARCH.md`, the roadmap in `ROADMAP.md`, and the detailed requirements in `PRD.md`.

---

## 1. Prerequisites

- macOS or Linux with a recent POSIX shell
- Python 3.10, 3.11, or 3.12 (3.13+ may have compatibility issues with some packages)
- Node.js 20+ and npm 10+
- Docker Desktop (for Postgres/Redis containers or future Compose flow)
- `ffmpeg` installed locally (`brew install ffmpeg`)

> Tip: Run everything from the repo root (`ai-music-video/`).

### 1.1 Python Version Check & Installation

**Check your current Python version:**

```bash
python3 --version
```

**If you have Python 3.13 or newer**, you'll need to install a compatible version (3.10-3.12):

**On macOS (using Homebrew):**

```bash
# Install Python 3.12 (recommended)
brew install python@3.12

# Verify installation
python3.12 --version
```

**On Linux:**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev

# Or use pyenv for version management
curl https://pyenv.run | bash
pyenv install 3.12.12
pyenv local 3.12.12
```

**If you have Python 3.10, 3.11, or 3.12**, you're all set! Proceed to the next section.

---

## 2. Repository Bootstrap

Run these from the repository root (`ai-music-video/`) to stand up the Python and Node environments.

**Important:** Use the specific Python version you installed (e.g., `python3.12` instead of `python3` if your default `python3` is 3.13+):

```bash
# Use python3.12 (or python3.11/python3.10) if your default python3 is too new
python3.12 -m venv .venv
source .venv/bin/activate

# Note: If you see double parentheses like ((.venv) ) in your prompt, that's normal.
# It means you have another environment active (e.g., conda base). The venv is still active.

# Verify you're using the correct Python version in the venv
python --version  # Should show 3.10, 3.11, or 3.12

# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies
npm --prefix frontend install
```

**Troubleshooting:** If `python3.12` isn't found, make sure you installed it via Homebrew and that `/opt/homebrew/bin` is in your PATH. You can also use the full path: `/opt/homebrew/bin/python3.12 -m venv .venv`

> `npm --prefix frontend install` keeps the command runnable from the repo root. `npm install` inside `frontend/` works the same if you prefer to `cd` first.

---

## 2.1 Optional Package Managers (Poetry / pnpm)

### Poetry (Python)

**Installation:**

The recommended way to install Poetry is using `pipx` (which installs it in an isolated environment):

```bash
pipx install poetry
```

Alternatively, you can use the official installer:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Or on macOS with Homebrew:

```bash
brew install poetry
```

**Usage:**

Once installed, `poetry install` from `backend/` (after generating a `pyproject.toml`) creates an isolated virtualenv automatically. Activate with `poetry shell` before running backend commands.

### pnpm (Node.js)

**Installation:**

```bash
npm install -g pnpm
```

Or on macOS with Homebrew:

```bash
brew install pnpm
```

**Usage:**

`pnpm install --dir frontend` installs frontend dependencies with pnpm's content-addressable store. Add `.npmrc` / `.pnpmfile.cjs` as needed to share settings with the team.

---

**Note:** Stick with the pip + npm defaults unless your team standardizes on these alternatives.

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

**Important:** If containers with these names already exist, remove them first:

```bash
docker rm -f ai-music-video-postgres ai-music-video-redis 2>/dev/null || true
```

**Check if port 5432 is already in use:**

```bash
lsof -i :5432
```

If another Postgres instance is using port 5432, either stop it or use a different port (e.g., `-p 5433:5432` and update `DATABASE_URL` in your `.env` file to use `127.0.0.1:5433` instead of `localhost:5432`).

**Start the containers:**

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

**Verify containers are running:**

```bash
docker ps | grep -E "(ai-music-video-postgres|ai-music-video-redis)"
```

**Note:** If you experience connection issues with psycopg3, use `127.0.0.1` instead of `localhost` in your `DATABASE_URL` (e.g., `postgresql+psycopg://postgres:postgres@127.0.0.1:5432/ai_music_video`).

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

### 4.1 Backend Project Structure

The FastAPI app lives under `backend/app/`:

- `main.py` – application factory, CORS, router registration
- `core/` – configuration, logging, database session helpers
- `api/v1/` – versioned routers (`/health`, `/songs`, etc.)
- `models/` – SQLModel ORM tables (e.g., `Song`)
- `schemas/` – Pydantic request/response models
- `services/` – pipeline logic (audio analysis, scene planning, etc.)
- `workers/` – background task entrypoints (RQ/Celery)

`init_db()` currently auto-creates tables via SQLModel metadata on startup; swap for Alembic migrations once schemas stabilize.

---

### 4.2 Smoke-Test the API

With the server running, use `curl` to verify health and the initial `/songs` routes:

```bash
curl http://localhost:8000/healthz

curl -X POST http://localhost:8000/api/v1/songs \
  -H "Content-Type: application/json" \
  -d '{"title":"Demo Song","audio_url":"https://example.com/audio.mp3"}'

curl http://localhost:8000/api/v1/songs
```

> Rerun `pip install -r backend/requirements.txt` whenever backend dependencies change (e.g., new services or integrations).

---

## 5. Frontend Runtime

Start the Vite dev server for the React + TypeScript UI.

```bash
cd ./frontend
npm run dev -- --host
```

Visit `http://localhost:5173` to confirm the scaffolded app loads.

---

### 5.1 Frontend Linting & Formatting

```bash
npm run lint         # ESLint (TS/React) with Prettier rules enforced
npm run lint:fix     # ESLint with --fix
npm run format       # Prettier check
npm run format:write # Prettier write
```

> These commands rely on the workspace-level `.prettierrc.json` and `.prettierignore` settings.

---

### 5.2 VibeCraft Design System

- Tailwind config: `frontend/tailwind.config.ts` (design tokens from `DESIGN_SYSTEM.md`)
- Global theme file: `frontend/src/styles/vibecraft-theme.css` (imported via `src/index.css`)
- Component library: `frontend/src/components/vibecraft/`
- Example screen: `frontend/src/pages/SongProfilePage.tsx` rendered via `App.tsx`

Run the dev server to explore the themed UI:

```bash
npm run dev -- --host
```

If you add new tokens or components, update the Tailwind config and keep docs in sync with `DESIGN_SYSTEM.md`.

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
