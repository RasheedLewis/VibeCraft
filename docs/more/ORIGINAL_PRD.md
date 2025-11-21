
# **📘 PRD — AI Music Video Generation System (Expanded & Integrating All Requirements)**

**Version:** 1.0
**Category:** Music Video Pipeline
**Scope:** End-to-end music-driven video generation with section-level control
**Owner:** Rasheed / Public Sphere

---

# **1. Product Summary**

The AI Music Video Generator allows a user to upload a song (audio only), automatically analyzes its musical structure, lyrics, genre, and mood, and then generates:

1. **Full-length music videos (1–3 minutes)**
2. **Section-level videos for individual song segments**

The system creates coherent, beat-synced visuals using a template-driven scene planner, AI video models, and a composition engine.

This PRD captures:

* User flows
* System requirements
* Architecture
* API contracts
* Data models
* MVP vs final targets
* “Polish” requirements dictated by the competition rules

---

# **2. Goals & Non-Goals**

## **Goals**

* Allow users to upload any audio track
* Auto-detect sections, tempo, beats, genre, lyrics, and mood
* Allow generating videos for:

  * Entire song
  * Individual sections
* Maintain visual consistency across clips
* Beat-perfect scene transitions
* 1080p video output
* Efficient cost usage
* Simple, intuitive UX

## **Non-Goals**

* Manual video editing (cutting, trimming, frame-level UI)
* Custom character consistency training (future)
* Multi-category pipelines (focus: Music)
* Multi-camera or photoreal 3D film production

---

# **3. User Personas**

### **Creator / Musician**

Wants a fast way to generate visuals for Singles, EPs, YouTube, TikTok.

### **General User**

Just wants to upload a song and get a cool visual.

### **Brand / Label**

Needs consistent style across multiple videos and multiple variations.

---

# **4. User Flows**

## **4.1 Primary Flow — Full Music Video Generation**

1. **Upload audio**
2. System performs **automatic analysis**
3. User sees:

   * Sections timeline
   * Genre & mood
   * Lyrics per section
4. User chooses a style/template
5. User clicks **Generate Full Music Video**
6. System:

   * Builds scene plan
   * Generates per-scene clips
   * Beat-aligns transitions
   * Produces final 1080p video
7. User downloads or shares final video

---

## **4.2 Secondary Flow — Section-Level Video Generation**

1. User views analysis screen
2. Clicks **“Generate Video for Chorus 1”**
3. System:

   * Creates a section-specific scene spec
   * Generates that clip
4. User may:

   * Regenerate
   * Save as best version
   * Insert into full video timeline

---

# **5. Core Features**

## **5.1 Audio Upload & Preprocessing**

* Supported formats: `.mp3`, `.wav`, `.m4a`
* Max length: 6–7 minutes
* Preprocessing:

  * Resample to 44.1kHz mono
  * Generate waveform data
  * Store file in cloud (S3 or equivalent)

---

## **5.2 Automatic Song Analysis Engine**

### **5.2.1 Content Extracted**

| Feature     | Method                                                 |
| ----------- | ------------------------------------------------------ |
| Tempo (BPM) | Essentia / librosa                                     |
| Beat grid   | Onset detection                                        |
| Sections    | Novelty detection + repetition grouping                |
| Lyrics      | External API or Whisper on vocal stem                  |
| Genre       | Embedding classifier (CLAP or metadata)                |
| Mood        | Derived from audio + lyrics (energy, valence, tension) |
| Key/Mode    | FFT/Harmonic analysis                                  |

### **5.2.2 Output**

A `SongAnalysis` object with:

* `sections[]` with timestamps
* `bpm`, `beatGrid[]`
* `primaryGenre`, `subGenres`, `genreConfidence`
* `moodTags`, `moodPrimary`, `moodVector`
* `sectionLyrics[]`
* `durationSec`

---

## **5.3 Section Cards on Analysis Screen**

For each section:

* Title: “Verse 1 (0:15–0:45)”
* Lyrics (first 1–2 lines)
* Mood tags
* Buttons:

  * **Generate Section Video**
  * **Preview**
  * **Regenerate**
  * **Use in Full Video**

---

## **5.4 Section-Level Video Generation**

Each section goes through a pipeline:

1. Create **scene spec**:

   * Template (e.g., Abstract / Environment / Character)
   * Mood → intensity, color palette
   * Genre → camera motion profile
   * Lyrics → motif injection

2. Build prompt

3. Call AI model (Replicate video model)

4. Produce 4–20 second clip

5. Save as `SectionVideo`

6. Expose a preview player

---

## **5.5 Full-Song Video Generation**

Steps:

### **5.5.1 Scene Planner**

* Map each song section → one scene
* Duration = section.end – section.start
* Build entire timeline
* Reuse section videos if the user approved them

### **5.5.2 Clip Generator**

For each scene:

* Generate via AI model OR reuse saved section clip

### **5.5.3 Composition Layer**

* Place clips on timeline
* Add beat-synced transitions:

  * Hard cuts
  * Light flares
  * Zoom cuts
* Normalize:

  * Resolution 1080p
  * FPS 30+
  * Color grading pass

### **5.5.4 Output**

* Final MP4 WebM
* Muxed with original song audio
* No audio drift

---

# **6. System Architecture**

## **6.1 High-Level Pipeline**

```
User Upload
   → Audio Preprocessor
   → Music Analysis Engine
   → SongAnalysis Data Model
   → Scene Planner
   → Section Generator
   → Video Composition Engine
   → Output Renderer
```

---

## **6.2 Detailed Components**

### **6.2.1 Audio Preprocessing Service**

* Convert audio to uniform analysis format
* Extract waveform
* Store file

### **6.2.2 Music Analysis Service**

* Track recognition (if possible)
* BPM detection
* Beat grid
* Section segmentation
* Lyrics transcription & alignment
* Genre classification
* Mood analysis

### **6.2.3 Scene Planner**

Input:

* `SongAnalysis`
* Template selection
  Output:
* `SceneSpec[]`
  Defines:
* Visual theme
* Shot patterns
* Motion intensity
* Prompt tokens

### **6.2.4 Video Generation Engine**

* Wraps Replicate API
* Supports:

  * Prompt
  * Duration
  * Aspect ratio
  * Seed
  * Style tokens

### **6.2.5 Section Video Store**

* Saves `SectionVideo` objects
* Allows selection in full-generation pass

### **6.2.6 Composition Engine**

* Video concatenation
* Beat transitions
* Color grading
* Resolution normalization

### **6.2.7 Output Handler**

* Final rendering
* Muxing
* Cloud storage
* Download URL generation

---

# **7. Data Models**

## **7.1 SongProject**

```ts
interface SongProject {
  id: string;
  audioUrl: string;
  durationSec: number;
  analysis: SongAnalysis;
  sectionVideos: SectionVideo[];
  createdAt: string;
}
```

## **7.2 SongAnalysis**

```ts
interface SongAnalysis {
  durationSec: number;
  bpm: number;
  beatGrid: Beat[];
  sections: SongSection[];
  moodTags: string[];
  moodPrimary: string;
  moodVector: MoodVector;
  primaryGenre?: string;
  subGenres?: string[];
  lyricsAvailable: boolean;
  sectionLyrics?: SectionLyrics[];
}
```

## **7.3 SectionVideo**

```ts
interface SectionVideo {
  id: string;
  songId: string;
  sectionId: string;
  template: string;
  prompt: string;
  durationSec: number;
  videoUrl: string;
  fps: number;
  resolution: { width: number; height: number };
  createdAt: string;
}
```

---

# **8. API Endpoints**

## **8.1 Upload Song**

`POST /api/songs`

## **8.2 Analyze Song**

`POST /api/songs/:songId/analyze`

Returns `SongAnalysis`.

## **8.3 Generate Section Video**

`POST /api/songs/:songId/sections/:sectionId/generate`

## **8.4 Get Job Status**

`GET /api/jobs/:jobId`

## **8.5 Generate Full Video**

`POST /api/songs/:songId/generate-full-video`

---

# **9. MVP Requirements (Mapped to this PRD)**

| Project Requirement  | Fulfilled By                                 |
| -------------------- | -------------------------------------------- |
| Prompt → Video       | Full flow via template + scene planner       |
| Beat sync            | Beat grid → transition engine                |
| 3–5 clip composition | Section-based scenes                         |
| Style consistency    | Global template + style tokens               |
| Deployment           | Web UI + backend                             |
| Sample outputs       | Use section generator + full video generator |

---

# **10. Performance Requirements**

* 1 min video < 10 minutes end-to-end
* Maintain <$200/min cost
* 90%+ success rate
* Retry + fallback logic

---

# **11. Risk & Mitigation**

| Risk                      | Mitigation                       |
| ------------------------- | -------------------------------- |
| Video model inconsistency | Use style tokens + seed reuse    |
| High inference cost       | Cache section clips & embeddings |
| Slow pipeline             | Parallelize clip generation      |
| Audio drift               | Use strict timing metadata       |

---

# **12. Roadmap**

## **MVP (48 Hours)**

* Audio upload
* Song analysis (basic BPM + section detection)
* One template (Abstract Visualizer)
* Section-level generation
* Full-song assembly
* Beat-synced transitions
* Deploy UI + backend

## **Week 1 (Final Submission)**

* Mood-driven prompt shaping
* Genre-aware camera motion presets
* Section reuse workflow
* Advanced transition styles
* Color grading pass
* Lyrics-driven motifs
* Performance optimizations
* Cost analysis + caching

## **Post-Competition**

* Character consistency
* Multiple templates
* Voiceover features
* Multi-model fallback system

---

# **Done.**

Nice, that stack is perfect for what you’re doing. Let’s lock in how TS+React+Python maps onto the roadmap so you can actually start building.

I’ll do three things:

1. Map the **layers** to your stack
2. Propose a **repo / folder structure**
3. Show how a few key PRs look concretely with FastAPI + React TS

---

## 1. Stack layout for this project

**Frontend (TypeScript + React)**

* Vite + React + TS
* Talks to Python backend via REST (JSON)
* Handles:

  * Upload UI
  * Song Profile view
  * Section generation UI
  * Full video generation UI
  * Demo gallery

**Backend (Python)**

* Framework: strongly recommend **FastAPI**
* Responsibilities:

  * File upload → S3 (or similar)
  * Audio preprocessing (librosa / ffmpeg)
  * Music analysis (BPM, sections, mood, genre, lyrics)
  * Scene planner (in Python for easy access to models)
  * AI model orchestration (Replicate, Whisper, etc.)
  * Video composition (ffmpeg)
  * Job orchestration / status API

**Worker layer (Python, same repo)**

* Long-running / heavy tasks:

  * Analysis jobs
  * Clip generation
  * Composition
* Use **RQ** (Redis Queue) or **Celery** + Redis

**Database**

* Postgres (via SQLAlchemy / SQLModel / Prisma-like ORM)
* Stores:

  * Songs
  * SongAnalysis JSON
  * SectionVideo metadata
  * FullVideo metadata
  * Jobs

**Storage**

* S3 / Cloud bucket:

  * Raw audio
  * Preprocessed audio
  * Section clips
  * Final videos

---

## 2. Suggested repo structure (monorepo)

```text
ai-music-video/
  backend/
    app/
      api/
        v1/
          routes_songs.py
          routes_sections.py
          routes_jobs.py
      core/
        config.py
        logging.py
      models/
        song.py
        section_video.py
        job.py
      services/
        audio_preprocess.py
        music_analysis.py
        scene_planner.py
        video_generation.py
        composition.py
        storage.py
      workers/
        worker_main.py
        tasks_analysis.py
        tasks_generate_section.py
        tasks_generate_full.py
      schemas/
        song_schemas.py
        analysis_schemas.py
        section_video_schemas.py
        job_schemas.py
      main.py          # FastAPI entrypoint
    tests/
  frontend/
    src/
      api/
        songs.ts
        sections.ts
        jobs.ts
      components/
        upload/
        songProfile/
        sectionCard/
        progress/
      pages/
        UploadPage.tsx
        SongProfilePage.tsx
        GalleryPage.tsx
      types/
        song.ts
        analysis.ts
        sectionVideo.ts
      main.tsx
      App.tsx
    vite.config.ts
    tsconfig.json
  infra/
    docker/
      backend.Dockerfile
      frontend.Dockerfile
      worker.Dockerfile
    compose.yml
  README.md
```

This fits your roadmap PRs almost 1:1.

---

## 3. Roadmap tweaks for “TypeScript + React + Python”

You don’t need to change the **numbers**, but the implementation details sharpen:

### 🔹 PR-01 — Project Initialization (Python + React)

* Backend:

  * Initialize `backend` with Poetry or pip + venv
  * Install FastAPI, uvicorn, SQLModel/SQLAlchemy, pydantic, ffmpeg-python, librosa
* Frontend:

  * `npm create vite@latest` → React + TS
  * Install React Query / TanStack Query for API calls (nice but optional)

> The rest of the PR list still stands; now we’re just clear that all backend subtasks are Python/FastAPI and all UI is React+TS.

---

## 4. Concrete contracts in Python & TS (so your PRs are consistent)

### 4.1 Backend schema (Python / FastAPI)

**`schemas/analysis_schemas.py`**

```python
from pydantic import BaseModel
from typing import List, Literal, Optional

SongSectionType = Literal[
    "intro", "verse", "pre_chorus", "chorus",
    "bridge", "drop", "solo", "outro", "other"
]

class SongSection(BaseModel):
    id: str
    type: SongSectionType
    startSec: float
    endSec: float
    confidence: float
    repetitionGroup: Optional[str] = None

class MoodVector(BaseModel):
    energy: float
    valence: float
    danceability: float
    tension: float

class SectionLyrics(BaseModel):
    sectionId: str
    startSec: float
    endSec: float
    text: str

class SongAnalysis(BaseModel):
    durationSec: float
    bpm: Optional[float] = None
    sections: List[SongSection]
    moodPrimary: str
    moodTags: List[str]
    moodVector: MoodVector
    primaryGenre: Optional[str] = None
    subGenres: Optional[List[str]] = None
    lyricsAvailable: bool
    sectionLyrics: Optional[List[SectionLyrics]] = None
```

### 4.2 Frontend types (TypeScript)

**`frontend/src/types/analysis.ts`**

```ts
export type SongSectionType =
  | "intro"
  | "verse"
  | "pre_chorus"
  | "chorus"
  | "bridge"
  | "drop"
  | "solo"
  | "outro"
  | "other";

export interface SongSection {
  id: string;
  type: SongSectionType;
  startSec: number;
  endSec: number;
  confidence: number;
  repetitionGroup?: string;
}

export interface MoodVector {
  energy: number;
  valence: number;
  danceability: number;
  tension: number;
}

export interface SectionLyrics {
  sectionId: string;
  startSec: number;
  endSec: number;
  text: string;
}

export interface SongAnalysis {
  durationSec: number;
  bpm?: number;
  sections: SongSection[];
  moodPrimary: string;
  moodTags: string[];
  moodVector: MoodVector;
  primaryGenre?: string;
  subGenres?: string[];
  lyricsAvailable: boolean;
  sectionLyrics?: SectionLyrics[];
}
```

Now your React components can rely on the same shape the backend guarantees.

---

## 5. Example endpoints mapped to your roadmap

### PR-02 / PR-04 (Upload + Analyze) — FastAPI routes

```python
# app/api/v1/routes_songs.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from ..schemas.song_schemas import SongCreateResponse
from ..services import audio_preprocess, music_analysis

router = APIRouter()

@router.post("/songs", response_model=SongCreateResponse)
async def upload_song(file: UploadFile = File(...)):
    song = await audio_preprocess.handle_upload(file)
    return song

@router.post("/songs/{song_id}/analyze")
async def analyze_song(song_id: str, background_tasks: BackgroundTasks):
    # kick off async analysis job and return jobId
    job_id = music_analysis.enqueue_song_analysis(song_id)
    return {"jobId": job_id}
```

### Frontend call (TS + React)

```ts
// src/api/songs.ts
import { SongAnalysis } from "../types/analysis";

export async function uploadSong(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/api/songs", { method: "POST", body: formData });
  return res.json();
}

export async function analyzeSong(songId: string) {
  const res = await fetch(`/api/songs/${songId}/analyze`, { method: "POST" });
  return res.json(); // { jobId }
}

export async function getSongAnalysis(songId: string): Promise<SongAnalysis> {
  const res = await fetch(`/api/songs/${songId}/analysis`);
  return res.json();
}
```

---

## 6. How this ties back to the existing PR roadmap

You don’t need a new roadmap—just mentally tag:

* All **[B]** subtasks → Python/FastAPI + worker
* All **[F]** subtasks → React+TS
* All **[AI]** subtasks → Python services + possibly GPU box / cloud models

If you want, next I can:

* Turn **each PR into concrete GitHub issues** (with labels `[backend]`, `[frontend]`, `[ai]`)
* Or design a **concrete `tasks_generate_section.py`** showing how a section video job runs end-to-end in Python.

