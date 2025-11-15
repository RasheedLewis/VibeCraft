# 🎧 **VibeCraft — AI-Powered Music Video Generator**

### *Transform any song into a cinematic, beat-synced visual experience.*

VibeCraft is an end-to-end AI video generation pipeline built for musicians and creators.
Upload a song → get a full music video.
Generate visuals for individual sections → assemble a complete track-long video with beat-matched transitions and a cohesive aesthetic.

Built during an accelerated competition sprint, VibeCraft demonstrates what modern multimodal AI can do when paired with an elegant pipeline, thoughtful UX, and a synesthetic design philosophy.

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

VibeCraft turns audio into cinema — no editing timeline, expensive software, or motion graphics expertise required.

---

# 🚀 **Live Demo**

**(Insert deployed link here)**

Upload a track → watch it turn into motion.

---

# 🧩 **Architecture Overview**

VibeCraft is built on a modular, scalable pipeline optimized for both cost and performance.

```
Audio Upload → Music Analysis → Scene Planning → Section Video Generation → 
Composition Engine → Final 1080p Music Video
```

### **Tech Stack**

* **Frontend:** React + TypeScript + Vite
* **Backend:** Python + FastAPI
* **Workers:** Celery/RQ + Redis
* **AI Models:** Replicate (video), Whisper (lyrics), librosa (BPM), Essentia (beat tracking)
* **Storage:** Amazon S3 (audio, clips, final renders)
* **Video Engine:** FFmpeg (transitions, muxing, grading)
* **Database:** PostgreSQL

### **High-Level Pipeline**

* **Audio preprocessing:** ffmpeg + librosa
* **Music analysis:** BPM, beat grid, mood vector, genre classifier
* **Scene planning:** AI-driven visual template selection
* **Video generation:** Section-level clips via Replicate’s video models
* **Composition:** Beat-synced cuts, color grading LUTs
* **Output:** 1080p MP4/WebM, 30+ FPS

---

# 🔥 **Key Features (Technical)**

### 🎶 **Music Intelligence Engine**

* BPM via autocorrelation
* Beat grid detection
* Novelty-based structural segmentation
* Repetition grouping for chorus detection
* Whisper-powered lyric extraction
* Audio embeddings → mood & genre classifier

### 🎞 **Scene Planner**

* Converts `SongAnalysis` → `SceneSpec`
* Maps moods → color palettes
* Maps genres → camera motions
* Maps sections → shot pacing
* Ensures cohesive look across all scenes

### 🤖 **AI Video Generation**

* Deterministic seeds for visual consistency
* Style tokens per template (e.g., lofi, neon, dreamy, cyberpunk)
* Parallelized clip generation to reduce cost/time

### 🎛 **Composition Engine**

* Aligns cuts with beat grid
* Avoids audio drift
* Enforces style continuity
* Normalizes FPS + resolution
* Final muxing with original audio

---

# 🎛 **Key Features (User-Facing)**

* Beautiful dark-mode UI designed for musicians
* Section cards with lyric snippets
* Generate/regenerate individual section videos
* Lock in favorite clips for final assembly
* Real-time progress feedback
* Fast preview-to-final workflow
* Seamless 1-click full-video generation

---

# 🎨 **Branding & Design System**

VibeCraft is built on a synesthetic design philosophy:

> **“See your sound. Feel your visuals.”**

### **Visual Identity**

* Deep violet-black surfaces
* Neon gradients (violet → magenta → aqua)
* Ambient glow edges
* Waveform and prism iconography

### **Motion**

* Pulse bars
* Wave sweeps
* Beat flashes
* Ambient particle drift

### **Typography**

* *Inter* for UI
* *Space Grotesk* for titles

---

# 📂 **Repository Structure**

```
vibecraft/
  backend/
    app/
      api/                 # REST endpoints
      services/            # audio, analysis, generation, composition
      workers/             # Celery/RQ job workers
      models/              # DB models
      schemas/             # Pydantic contracts
      main.py              # FastAPI entry
  frontend/
    src/
      api/                 # TS fetch clients
      pages/               # Upload, SongProfile, Gallery
      components/          # SectionCards, Buttons, VideoPreviews
      types/               # Shared TS interfaces
      App.tsx
  infra/
    docker/
    compose.yml
  README.md
  DESIGN_SYSTEM.md
```

---

# 🛠 **Installation & Local Development**

### **Prerequisites**

* Python 3.10+
* Node 18+
* Poetry or pip
* Docker (optional but recommended)

---

## **Backend Setup**

```bash
cd backend
poetry install
poetry run uvicorn app.main:app --reload
```

or with pip:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## **Frontend Setup**

```bash
cd frontend
npm install
npm run dev
```

---

# 🧪 **MVP Features Implemented**

* [x] Audio-only upload
* [x] BPM + beat grid detection
* [x] Section segmentation
* [x] Lyric alignment
* [x] Mood + genre inference
* [x] Section-level generation
* [x] Full-song video assembly
* [x] Beat-synced transitions
* [x] Fully deployed version
* [x] Sample output videos

---

# 📈 **Roadmap**

See `ROADMAP.md` for full PR/sprint plan. Highlights:

* Character-consistency template
* Dynamic storyboard generation
* Multi-model fallback
* Artist-focused presets
* Video style marketplace
* Mobile upload support
* Export to TikTok/Reels directly

---

# 🏆 **Why VibeCraft Stands Out**

### **For musicians**

* No editing timeline needed
* Visuals automatically match emotional tone
* You can iterate on each section, not the whole video
* Fast enough to use during creative flow
* Beautiful defaults, infinite customizations

### **For engineers**

* Modular, scalable architecture
* Clear API boundaries
* Async job orchestration
* Smart caching & cost controls
* Deterministic scene planning

### **For judges/investors**

* Strong product vision
* Real technical depth
* Polished UX + cohesive branding
* Practical, real-world use cases
* Huge market demand (artists, labels, creators, brands)

---

# 🎤 **Created for Music Creators. Built by Passion. Driven by AI.**

Whether you're an indie artist making visuals for your first EP, a producer crafting lofi loops, or a label needing scalable video content — **VibeCraft brings your sound to life.**

If you like this project, ⭐️ star the repo or follow along for more updates.

