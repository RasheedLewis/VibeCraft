# 🎧 **VibeCraft — AI-Powered Music Video Generator**

*Transform any song into a cinematic, beat-synced visual experience.*

VibeCraft is an end-to-end AI video generation pipeline built for musicians and creators.
Upload a song → get a full music video.
Generate visuals for individual sections → assemble a complete track-long video with
beat-matched transitions and a cohesive aesthetic.

Built during an accelerated competition sprint, VibeCraft demonstrates what modern multimodal AI
can do when paired with an elegant pipeline, thoughtful UX, and a synesthetic design philosophy.

---

## 🌟 **What VibeCraft Does**

* 🎵 **Upload a song** — MP3, WAV, M4A
* 🧠 **Automatic music intelligence**

  * BPM detection
  * Beat grid
  * Section segmentation (intro, verse, chorus…)
  * Genre classification
  * Mood extraction
  * Lyric transcription/alignment
* 🎬 **Generate AI videos for individual sections**
* 🎨 **Choose a visual template & style**
* ⚡️ **Assemble a complete music video**

  * Beat-synced transitions
  * Cohesive visual aesthetic
  * High-quality 1080p output
* 🎥 **Download or share your final video**

VibeCraft turns audio into cinema — no editing timeline, expensive software, or motion graphics
expertise required.

---

## 🚀 Production Deployment

**Backend API:** `https://backend-api-production-c6ee.up.railway.app`  
**Frontend:** `https://frontend-production-b530.up.railway.app`

[Railway Dashboard](https://railway.app/project/9d147533-96b0-4aeb-ab3a-502138d87ae7) | [Health Check](https://backend-api-production-c6ee.up.railway.app/healthz)

**Redeploy:**

* Backend: `cd backend && railway up`
* Frontend: `cd frontend && railway up`

---

# 🧩 **Architecture Overview**

VibeCraft is built on a modular, scalable pipeline optimized for both cost and performance.

```text
Audio Upload → Music Analysis → Scene Planning → Section Video Generation → 
Composition Engine → Final 1080p Music Video
```

## **Tech Stack**

* **Frontend:** React + TypeScript + Vite + Tailwind CSS
* **Backend:** Python + FastAPI + SQLModel
* **Workers:** RQ (Redis Queue) for async job processing
* **AI Models:** 
  - Replicate (Minimax Hailuo 2.3 for video, SDXL for character images)
  - OpenAI GPT-4o Vision (optional, for image interrogation)
  - Whisper (via Replicate) for lyrics
  - librosa (BPM detection, beat tracking)
* **Storage:** Amazon S3 (audio, clips, final renders, character images)
* **Video Engine:** FFmpeg (transitions, muxing, beat-synced effects)
* **Database:** PostgreSQL

## **High-Level Pipeline**

* **Audio preprocessing:** FFmpeg format conversion + waveform generation
* **Music analysis:** BPM, beat grid, section segmentation, mood vector, genre classifier, lyric transcription
* **Video type selection:** Full-length (16:9) or short-form (9:16) with optional audio segment selection
* **Scene planning:** AI-driven visual template selection + prompt building
* **Video generation:** Clip-level generation via Minimax Hailuo 2.3 (text-to-video or image-to-video)
* **Character consistency:** Optional character image generation and pose selection
* **Composition:** Beat-synced cuts, transitions, beat-synced visual effects
* **Output:** 1080p MP4 (H.264/AAC), 24 FPS, 16:9 or 9:16 aspect ratio

---

# 🔥 **Key Features (Technical)**

## 🎶 **Music Intelligence Engine**

* BPM detection via autocorrelation
* Beat grid extraction using librosa
* Section segmentation (intro, verse, chorus, bridge, outro)
* Genre classification via audio embeddings
* Mood extraction (valence, energy, danceability)
* Whisper-powered lyric transcription and alignment
* Audio selection for short-form videos (30-second segments)

## 🎞 **Scene Planner**

* Converts `SongAnalysis` → `SceneSpec`
* Maps moods → color palettes
* Maps genres → camera motions
* Maps sections → shot pacing
* Ensures cohesive look across all scenes

## 🤖 **AI Video Generation**

* **Provider pattern architecture** for easy model swapping
* **Minimax Hailuo 2.3** via Replicate (text-to-video and image-to-video)
* Deterministic seeds for visual consistency
* Template-based style selection (abstract, environment, character, minimal)
* Character consistency with image interrogation and generation
* Template character sets with multiple poses
* Parallelized clip generation to reduce cost/time
* Support for both 16:9 (full-length) and 9:16 (short-form) aspect ratios

## 🎛 **Composition Engine**

* Beat-aligned clip boundaries and cuts
* Beat-synced visual effects (flash, color burst, zoom, glitch, brightness pulse)
* Configurable effect intensity and frequency
* Avoids audio drift with precise timing
* Normalizes FPS (24fps) and resolution (1080p)
* Transitions between clips
* Final muxing with original audio track
* Cost tracking per song

---

# 🎛 **Key Features (User-Facing)**

* Beautiful dark-mode UI designed for musicians
* JWT-based authentication with user management
* Dual video types: full-length (16:9) or short-form (9:16)
* Audio segment selection for short-form videos (30-second max)
* Section cards with lyric snippets (full-length videos)
* Generate/regenerate individual clips
* Character consistency with optional image upload
* Template character selection
* Lock in favorite clips for final assembly
* Real-time progress feedback via job status
* Fast preview-to-final workflow
* Seamless 1-click full-video generation
* Cost tracking per project

---

# 🎨 **Branding & Design System**

VibeCraft is built on a synesthetic design philosophy:

> **"See your sound. Feel your visuals."**

## **Visual Identity**

* Deep violet-black surfaces
* Neon gradients (violet → magenta → aqua)
* Ambient glow edges
* Waveform and prism iconography

## **Motion**

* Pulse bars
* Wave sweeps
* Beat flashes
* Ambient particle drift

## **Typography**

* *Inter* for UI
* *Space Grotesk* for titles

---

# 📂 **Repository Structure**

```text
VibeCraft/
  backend/
    app/
      api/v1/              # REST endpoints (auth, songs, videos, jobs, etc.)
      core/                 # Config, database, logging, migrations
      services/            # Business logic (audio, analysis, generation, composition)
        video_providers/   # Video generation provider pattern
      workers/             # RQ job workers
      models/              # SQLModel database models
      schemas/             # Pydantic request/response schemas
      repositories/        # Data access layer
      main.py              # FastAPI entry point
    migrations/            # Database migration scripts
    tests/                 # Unit and integration tests
    requirements.txt       # Python dependencies
  frontend/
    src/
      api/                 # API client functions
      pages/               # Main pages (Upload, SongProfile, Gallery)
      components/          # React components
      hooks/               # Custom React hooks
      types/               # TypeScript type definitions
      utils/               # Utility functions
    package.json           # Node dependencies
  docs/                    # Documentation (Architecture.md, Dev-Guide.md)
  scripts/                 # Utility scripts
  Makefile                 # Development commands
  README.md
```

---

# 🛠 **Installation & Local Development**

## **Prerequisites**

* Python 3.10-3.12 (3.13+ has compatibility issues)
* Node.js 20+ and npm 10+
* Docker Desktop (for local Postgres/Redis)
* FFmpeg (`brew install ffmpeg` on macOS)

---

## **Backend Setup**

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables (see Dev-Guide.md for details)
# Create backend/.env with DATABASE_URL, REDIS_URL, S3 credentials, etc.

# Run migrations
python -m app.core.migrations

# Start the API server
uvicorn app.main:app --reload
```

**Note:** You'll also need to run an RQ worker in a separate terminal for async job processing:
```bash
source .venv/bin/activate
cd backend
rq worker ai_music_video
```

---

## **Frontend Setup**

```bash
cd frontend
npm install

# Create frontend/.env with:
# VITE_API_BASE_URL=http://localhost:8000

npm run dev
```

---

## **Quick Start (Recommended)**

Use the Makefile for streamlined development:

```bash
# Start all services (backend, worker, frontend)
make start

# Run database migrations
make migrate

# Run tests
make test

# Stop all services
make stop
```

See `docs/Dev-Guide.md` for detailed setup instructions and troubleshooting.

---

# 🏆 **Why VibeCraft Stands Out**

## **For musicians**

* No editing timeline needed
* Visuals automatically match emotional tone
* Support for both full-length and short-form content
* You can iterate on individual clips, not the whole video
* Fast enough to use during creative flow
* Beautiful defaults with customizable templates
* Character consistency for narrative videos

## **For engineers**

* Modular, scalable architecture with clear separation of concerns
* Provider pattern for easy AI model swapping
* Async job orchestration with RQ (Redis Queue)
* Cost tracking and optimization
* Deterministic scene planning
* Comprehensive test coverage
* Well-documented codebase

## **For judges/investors**

* Strong product vision with dual use cases (full-length + short-form)
* Real technical depth (music analysis, beat synchronization, AI video generation)
* Polished UX + cohesive branding
* Practical, real-world use cases
* Huge market demand (artists, labels, creators, brands, social media)

---

# 📚 **Documentation**

* **[Architecture Guide](docs/Architecture.md)** - Detailed system architecture and component overview
* **[Developer Guide](docs/Dev-Guide.md)** - Setup instructions, development workflow, and troubleshooting

---

# 🎤 **Created for Music Creators. Built by Passion. Driven by AI.**

Whether you're an indie artist making visuals for your first EP, a producer crafting lofi loops,
a label needing scalable video content, or a creator making short-form content — **VibeCraft brings your sound to life.**

If you like this project, ⭐️ star the repo or follow along for more updates.
