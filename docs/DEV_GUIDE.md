# Developer Guide

**Note:** This guide reflects the current implementation. The product vision has evolved since
initial planning, and some early documentation may reference features or approaches that have
changed.

---

This guide walks new contributors through setting up the AI Music Video project locally. It
complements the architecture overview in `ARCH.md`.

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

**Important:** Use the specific Python version you installed (e.g., `python3.12` instead of
`python3` if your default `python3` is 3.13+):

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

**Troubleshooting:** If `python3.12` isn't found, make sure you installed it via Homebrew and
that `/opt/homebrew/bin` is in your PATH. You can also use the full path:
`/opt/homebrew/bin/python3.12 -m venv .venv`

> `npm --prefix frontend install` keeps the command runnable from the repo root. `npm install`
> inside `frontend/` works the same if you prefer to `cd` first.

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

Once installed, `poetry install` from `backend/` (after generating a `pyproject.toml`) creates
an isolated virtualenv automatically. Activate with `poetry shell` before running backend
commands.

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

`pnpm install --dir frontend` installs frontend dependencies with pnpm's content-addressable
store. Add `.npmrc` / `.pnpmfile.cjs` as needed to share settings with the team.

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

### 2.3 Verify Replicate API Configuration

After adding your `REPLICATE_API_TOKEN` to `backend/.env`, verify that the video generation model
is accessible:

```bash
source .venv/bin/activate
python scripts/check_replicate_models.py
```

Or to also list alternative models:

```bash
python scripts/check_replicate_models.py --list
```

This script will:

- Check if your API token is configured
- Verify the Zeroscope v2 XL model exists and is accessible
- Display the latest model version and available input parameters
- (With `--list`) Show alternative text-to-video models

If the model is not found or you get permission errors, check:

- Your API token is correct in `backend/.env`
- Your Replicate account has access to the model
- The model name hasn't changed (check [Replicate's model explorer](https://replicate.com/explore?query=text+to+video))

**Troubleshooting video generation failures:**

If video generation fails, you can check the Replicate job status directly:

1. **Query the database for the job ID and prompt:**

   ```bash
   # PostgreSQL - Get job ID, error, and the prompt that was sent
   docker exec ai-music-video-postgres psql -U postgres -d ai_music_video -c \
     "SELECT replicate_job_id, error_message, status FROM song_clips WHERE status = 'failed' \
     ORDER BY created_at DESC LIMIT 1;"
   
   # Quick prompt view (PostgreSQL) - prompts are stored in clip generation jobs
   docker exec ai-music-video-postgres psql -U postgres -d ai_music_video -c "SELECT id, status, error_message FROM song_clips WHERE song_id = 'your-song-uuid' ORDER BY created_at DESC LIMIT 5;"
   ```

2. **View the job on Replicate:**
   - Open `https://replicate.com/p/{replicate_job_id}` in your browser
   - This shows the full job details, logs, and any error messages from Replicate

3. **Check backend logs** for detailed error messages (the new code captures Replicate's actual
   error messages, not just "Timeout")

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

If another Postgres instance is using port 5432, either stop it or use a different port
(e.g., `-p 5433:5432` and update `DATABASE_URL` in your `.env` file to use `127.0.0.1:5433`
instead of `localhost:5432`).

**Start the containers:**

```bash
docker run --name ai-music-video-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=ai_music_video \
  -p 5432:5432 \
  -d postgres:16

docker run --name ai-music-video-redis -p 6379:6379 -d redis:7
```

**Verify containers are running:**

```bash
docker ps | grep -E "(ai-music-video-postgres|ai-music-video-redis)"
```

**Note:** If you experience connection issues with psycopg3, use `127.0.0.1` instead of
`localhost` in your `DATABASE_URL` (e.g.,
`postgresql+psycopg://postgres:postgres@127.0.0.1:5432/ai_music_video`).

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

> New song analyses (PR-04) run on this RQ worker. Ensure it is running before hitting
> `POST /api/v1/songs/{id}/analyze`; the worker updates job progress and writes results back
> to Postgres.
> Swap the worker command for Celery if you adopt it instead of RQ.

---

### 4.1 Backend Project Structure

The FastAPI app lives under `backend/app/`:

- `main.py` – application factory, CORS, router registration
- `core/` – configuration, logging, database session helpers
- `api/v1/` – versioned routers (`/health`, `/songs`, etc.)
- `models/` – SQLModel ORM tables (e.g., `Song`)
- `schemas/` – Pydantic request/response models
- `services/` – pipeline logic (audio analysis, scene planning, video composition, etc.)
- `workers/` – background task entrypoints (RQ/Celery)

> **Note:** Until authentication is implemented, uploaded songs are associated with a
> placeholder user record whose ID is `default-user`. The default user is created
> automatically on startup (`init_db()`); replace this once real auth is wired up.

`init_db()` currently auto-creates tables via SQLModel metadata on startup; swap for Alembic
migrations once schemas stabilize.

#### 4.2.1 Video Composition Settings

Video composition (MVP-03) normalizes clips to 1080p @ 24fps using H.264 encoding. Default
settings are in `backend/app/services/video_composition.py`:

- **CRF**: 23 (quality setting, 18-28 range, lower = better quality)
- **Preset**: "medium" (encoding speed vs compression tradeoff)
- **Resolution**: 1920×1080 (fixed for MVP)
- **FPS**: 24 (fixed for MVP)

**Controlling file size:**

If composed videos are too large, you can adjust these settings:

1. **Increase CRF** (smaller file, lower quality): Change `DEFAULT_CRF = 23` to `26-28` (~30-50% smaller)
2. **Use slower preset** (better compression, slower): Change `preset="medium"` to `"slow"` or
   `"veryslow"` (~10-20% smaller, 2-5× slower)
3. **Reduce resolution** (smaller file, lower resolution): Change
   `DEFAULT_TARGET_RESOLUTION = (1920, 1080)` to `(1280, 720)` (~40% smaller)
4. **Reduce FPS** (smaller file, less smooth): Change `DEFAULT_TARGET_FPS = 24` to `20` (~15% smaller)

For file size optimization, adjust the settings in `backend/app/services/video_composition.py`
as described above.

---

### 4.2 Smoke-Test the API

With the server running, use `curl` to verify health and the initial `/songs` routes:

```bash
curl http://localhost:8000/healthz

curl -X POST http://localhost:8000/api/v1/songs \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/audio.mp3"

curl http://localhost:8000/api/v1/songs
```

> Rerun `pip install -r backend/requirements.txt` whenever backend dependencies change
> (e.g., new services or integrations).

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
- Light mode palette supported via `html.light` (or `data-theme="light"`) — defaults to OS
  preference when no class is set
- Component library: `frontend/src/components/vibecraft/`
- Example screen: `frontend/src/pages/SongProfilePage.tsx` rendered via `App.tsx`

Run the dev server to explore the themed UI:

```bash
npm run dev -- --host
```

If you add new tokens or components, update the Tailwind config and keep docs in sync with `DESIGN_SYSTEM.md`.

To preview light mode explicitly, add the `light` class to the root HTML element (e.g.
`document.documentElement.classList.add('light')`). Use `dark` to force the night-studio
palette. Removing both classes reverts to the default dark experience.

---

## 5.3 Querying Song Analysis Data (Mood, Energy, Genre)

Song analysis data (mood, energy, genre, sections, lyrics) is generated by PR-05 (Genre & Mood
Classification) and PR-06 (Lyric Extraction). Currently, this data is **not stored in the
database** - it's computed on-demand or accessed via mock data.

### 5.3.1 Current State (Before PR-04)

Until PR-04 (Music Analysis Engine) is complete, song analysis data is available via:

**1. Mock Data Functions (for development/testing):**

```python
from app.services.mock_analysis import (
    get_mock_analysis_by_song_id,
    get_mock_analysis_by_section_id,
    get_mock_analysis_electronic,
    get_mock_analysis_country,
    # ... other genre-specific functions
)

# Get mock analysis for a song
analysis = get_mock_analysis_by_song_id("song-123")

# Access mood/energy data
print(analysis.mood_primary)  # e.g., "energetic"
print(analysis.mood_vector.energy)  # e.g., 0.85
print(analysis.mood_vector.valence)  # e.g., 0.75
print(analysis.primary_genre)  # e.g., "Electronic"
print(analysis.mood_tags)  # e.g., ["energetic", "upbeat", "danceable"]
```

**2. Direct Service Calls (for real analysis):**

```python
from app.services.genre_mood_analysis import (
    compute_mood_features,
    compute_mood_tags,
    compute_genre,
)
from app.services.lyric_extraction import extract_and_align_lyrics

# Compute mood features from audio file
mood_vector = compute_mood_features("path/to/audio.mp3", bpm=128.0)
primary_mood, mood_tags = compute_mood_tags(mood_vector)
primary_genre, sub_genres, confidence = compute_genre("path/to/audio.mp3", bpm=128.0, mood_vector=mood_vector)

# Extract lyrics
lyrics_available, section_lyrics = extract_and_align_lyrics("path/to/audio.mp3", sections)
```

### 5.3.2 Future State (After PR-04)

Once PR-04 is complete, `SongAnalysis` data will be stored in a database table. The table
structure will likely be:

**Expected Table: `song_analyses`**

```sql
CREATE TABLE song_analyses (
    id UUID PRIMARY KEY,
    song_id UUID REFERENCES songs(id),
    duration_sec FLOAT,
    bpm FLOAT,
    mood_primary VARCHAR(64),
    mood_tags JSONB,  -- Array of strings
    mood_vector JSONB,  -- {energy, valence, danceability, tension}
    primary_genre VARCHAR(64),
    sub_genres JSONB,  -- Array of strings
    lyrics_available BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**Querying via SQL:**

```sql
-- Get analysis for a specific song
SELECT 
    mood_primary,
    mood_vector->>'energy' as energy,
    mood_vector->>'valence' as valence,
    mood_vector->>'danceability' as danceability,
    mood_vector->>'tension' as tension,
    primary_genre,
    mood_tags
FROM song_analyses
WHERE song_id = 'your-song-uuid-here';
```

**Querying via Python/SQLModel:**

```python
from app.models.song_analysis import SongAnalysis
from sqlmodel import Session, select

# Get analysis for a song
with Session(engine) as session:
    statement = select(SongAnalysis).where(SongAnalysis.song_id == song_id)
    analysis = session.exec(statement).first()
    
    if analysis:
        print(f"Mood: {analysis.mood_primary}")
        print(f"Energy: {analysis.mood_vector.energy}")
        print(f"Genre: {analysis.primary_genre}")
```

**Querying via API:**

```bash
# Get analysis for a song (once PR-04 endpoint is implemented)
curl http://localhost:8000/api/v1/songs/{song_id}/analysis
```

### 5.3.3 Accessing Section-Level Data

Sections and section lyrics are nested within `SongAnalysis`:

**Via Mock Data:**

```python
analysis = get_mock_analysis_by_song_id("song-123")

# Access sections
for section in analysis.sections:
    print(f"{section.type}: {section.start_sec}-{section.end_sec}s")

# Access section lyrics
if analysis.section_lyrics:
    for lyrics in analysis.section_lyrics:
        print(f"Section {lyrics.section_id}: {lyrics.text[:50]}...")
```

**Via Future Database (after PR-04):**

Sections and lyrics will likely be stored in separate tables:

```sql
-- Sections table
SELECT * FROM song_sections WHERE song_id = 'your-song-uuid';

-- Section lyrics table
SELECT * FROM section_lyrics WHERE song_id = 'your-song-uuid';
```

---

## 6. Optional: Docker Compose Flow

Later (when /infra exists)...

When the Compose stack is ready, you can run everything together:

```bash
cd ./infra
docker compose up --build
```

---

## 7. Deployment

### 7.1 System Dependencies

VibeCraft requires several system-level dependencies that must be installed in production:

#### FFmpeg

FFmpeg is required for audio/video processing. It's a system binary, not a Python package.

**Dockerfile example:**

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Librosa Dependencies

Librosa requires system libraries (`libsndfile1`) which are included in the Dockerfile above.

### 7.2 Environment Variables

**Required for Backend:**

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string (for RQ workers)
- `S3_BUCKET_NAME` - S3 bucket name
- `S3_ACCESS_KEY_ID` - AWS access key
- `S3_SECRET_ACCESS_KEY` - AWS secret key
- `S3_REGION` - AWS region (e.g., `us-east-2`)
- `REPLICATE_API_TOKEN` - Replicate API token
- `RQ_WORKER_QUEUE` - RQ queue name (default: `ai_music_video`)

**Required for Frontend:**

- `VITE_API_BASE_URL` - Backend API URL

**Optional:**

- `WHISPER_API_TOKEN` - For Whisper API (if using)
- `LYRICS_API_KEY` - For lyrics API (if using)
- `API_LOG_LEVEL` - Logging level (default: `info`)
- `FFMPEG_BIN` - Path to ffmpeg binary (default: `ffmpeg`)

### 7.3 Worker Process Management

VibeCraft requires both an API server and background worker processes.

**API Server:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**RQ Worker:**

```bash
rq worker ai_music_video --url $REDIS_URL
```

**Procfile example (for platforms that support it):**

```procfile
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: rq worker ai_music_video --url $REDIS_URL
```

### 7.4 Deployment Considerations

#### Long-Running Tasks

Video generation can take 30+ minutes. Use background workers (RQ/Celery) that don't have
HTTP timeouts. Ensure your deployment platform allows long-running worker processes.

#### Memory Requirements

Audio/video processing is memory-intensive. Recommended:

- **Minimum:** 2GB RAM
- **Recommended:** 4GB+ RAM for production

#### File Upload Size Limits

Audio files can be large (10-50MB+). Consider:

- Stream uploads directly to S3 (don't buffer in memory)
- Use presigned URLs for direct client → S3 uploads
- Configure nginx/reverse proxy body size limits

#### Database Migrations

Migrations run automatically on startup via `init_db()`. For production, consider using Alembic
for more controlled migrations.

#### CORS Configuration

Configure CORS in `backend/app/main.py` to allow your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend-domain.com",
        "http://localhost:5173",  # Keep for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Health Checks

The backend provides a health check endpoint at `/healthz`. Configure your deployment platform
to use this for health monitoring.

### 7.5 Troubleshooting

**Backend won't start:**

- Check logs for errors
- Verify all environment variables are set
- Check `DATABASE_URL` and `REDIS_URL` are correct
- Ensure ffmpeg is installed (check with `which ffmpeg`)

**Worker not processing jobs:**

- Check `REDIS_URL` is set correctly
- Verify worker service is running
- Check logs for connection errors
- Ensure worker is listening to the correct queue name

**Frontend can't connect to backend:**

- Verify `VITE_API_BASE_URL` is correct
- Check CORS configuration
- Verify backend is running and accessible
- Check browser console for errors

**S3 uploads failing:**

- Verify IAM credentials are correct
- Check bucket policy allows your service
- Verify bucket name and region
- Check S3 CORS configuration if uploading from browser

**Video generation failing:**

- Check Replicate API token is valid
- Verify model is accessible
- Check worker logs for detailed error messages
- Ensure sufficient memory is available

---

## 8. Next Steps

1. Add `.env` and `.env.example` files with keys for Postgres, Redis, S3, Replicate, and any AI providers.
2. Scaffold FastAPI routers, schemas, and services following the current architecture.
3. Implement frontend pages and components per the roadmap (Upload, Song Profile, Clip management, Gallery).
