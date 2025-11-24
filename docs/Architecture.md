flowchart LR
  %% CLIENT
  subgraph Client["Client"]
    U[User Browser\nReact + TypeScript]
  end

  %% BACKEND
  subgraph Backend["Python Backend (FastAPI + Workers)"]
    API[REST API Layer\n/auth, /songs, /songs/{id}/*,\n/jobs, /videos, /scenes,\n/template-characters, /config]
    AUTH[Authentication\nJWT-based, user management\n+ project listing max 5]
    RL[Rate Limiting\nPer-user/IP limits]

    subgraph AudioPipeline["Audio & Music Intelligence"]
      APS[Audio Preprocess Service\n(ffmpeg + librosa)]
      AS[Audio Selection Service\n30s segment selection\nfor short_form videos]
      MAS[Music Analysis Service\nBPM · Beats · Sections · Genre · Mood · Lyrics]
    end

    subgraph VideoPipeline["Video Planning & Generation"]
      CP[Clip Planner\n(beat-aligned boundaries)\nsupports full_length & short_form]
      SP[Scene Planner\n(builds prompts from analysis)\n+ template selection]
      VGP[Video Provider Pattern\nMinimaxHailuoProvider\n+ extensible base]
      CC[Character Consistency\nImage interrogation\n+ generation + pose selection]
      TC[Template Characters\nPre-generated character sets]
      VGE[Video Generation Engine\nProvider-based\n+ 9:16 & 16:9 support]
      BFA[Beat Filter Applicator\nFlash · Color Burst · Zoom\nGlitch · Brightness Pulse]
      CE[Composition Engine\nffmpeg concat + transitions + mux\n+ beat-synced effects]
      CT[Cost Tracking\nPer-song generation costs]
    end

    JS[Job Orchestrator / Workers\nRQ (Redis Queue)\n+ job status tracking]
    DB[(Postgres / DB\nUsers · Songs · Analyses\nSongClips · SectionVideos\nJobs · TemplateCharacters)]
    ST[(Object Storage\nS3: audio · clips · finals\n+ character images)]
  end

  %% EXTERNAL SERVICES
  subgraph External["External AI / Music APIs"]
    REP[Video Models on Replicate\n(minimax/hailuo-2.3)\nvia provider pattern]
    LYR[Lyrics / Music APIs\n(Whisper, Musixmatch, etc.)]
    AI_VISION[AI Vision API\n(OpenAI GPT-4o Vision)\nfor image interrogation\noptional, Replicate fallback]
    AI_IMG[AI Image Generation\n(Replicate SDXL)\nfor character images]
  end

  %% FLOWS

  %% Authentication
  U -->|"0. Login/Register"| API --> AUTH
  AUTH -->|"JWT token"| U
  API -->|"validate token"| AUTH
  API -->|"rate limit check"| RL

  %% Upload & Analysis
  U -->|"1. Upload audio file"| API
  API -->|"store raw audio"| ST
  API -->|"enqueue preprocess job"| JS
  JS --> APS
  APS -->|"processed audio\n+ waveform"| ST
  APS --> MAS
  MAS -->|"SongAnalysis\n(sections, bpm, mood, lyrics)"| DB
  MAS -->|"optional track/lyrics lookup"| LYR

  U -->|"2. Select video type\n(full_length/short_form)"| API
  U -->|"2b. Audio selection\n(short_form only, 30s max)"| API --> AS
  AS -->|"store selection\n(start_sec, end_sec)"| DB

  U -->|"3. Fetch analysis\n& Song Profile UI"| API --> DB

  %% Character consistency (optional)
  U -->|"3b. Upload character image\n(optional)"| API --> ST
  API -->|"enqueue character job"| JS
  JS --> CC
  CC -->|"interrogate image\n(GPT-4o Vision)"| AI_VISION
  CC -->|"generate consistent image\n(Replicate SDXL)"| AI_IMG
  CC -->|"store character images"| ST
  CC -->|"update song metadata"| DB

  %% Clip generation
  U -->|"4. Plan Clips"| API
  API -->|"calculate beat-aligned boundaries"| CP
  CP -->|"store clip plans"| DB
  
  U -->|"5. Generate Clips"| API
  API -->|"enqueue clip generation jobs"| JS
  JS -->|"build SceneSpec from\nSongAnalysis + clip + template"| SP
  SP --> VGE
  VGE --> VGP
  VGP -->|"call video model\n(text-to-video or image-to-video)"| REP
  VGE -->|"check character consistency"| CC
  VGE -->|"load template characters"| TC
  REP -->|"clip video"| VGE
  VGE -->|"store clip video"| ST
  VGE -->|"SongClip metadata\n+ cost tracking"| DB
  VGE --> CT
  U -->|"preview clips"| API --> ST

  %% Composition
  U -->|"6. Compose Video"| API
  API -->|"enqueue composition job"| JS
  JS -->|"get all completed SongClips"| DB
  JS -->|"compose timeline\nwith beat-aligned cuts"| CE
  CE -->|"apply beat-synced effects"| BFA
  BFA -->|"beat times from analysis"| DB
  CE -->|"final 1080p MP4 (H.264/AAC)\n16:9 or 9:16 aspect ratio"| ST
  ST -->|"download/stream URL"| U

  %% Data persistence paths
  API --> DB
  JS --> DB
  CE --> DB
  CC --> DB
  CT --> DB

---

# Architecture Overview

VibeCraft is a full-stack AI music video generation platform built with a modular, scalable architecture. The system processes audio files through multiple stages: analysis, planning, generation, and composition, producing beat-synced music videos in both 16:9 (full-length) and 9:16 (short-form) formats.

## Core Components

### Authentication & User Management

- **JWT-based authentication** with email/password registration and login
- **User model** with preferences (e.g., animations disabled)
- **Project listing** limited to 5 most recent songs per user
- **Rate limiting** middleware for API protection
- **Protected routes** requiring authentication tokens

### Audio Processing Pipeline

1. **Audio Preprocessing** (`audio_preprocessing.py`)
   - FFmpeg-based format conversion and normalization
   - Waveform generation for visualization
   - Audio file storage in S3

2. **Audio Selection** (`audio_selection.py`) - *Short-form videos only*
   - Interactive 30-second segment selection UI
   - Validates selection bounds (9-30 seconds)
   - Stores `selected_start_sec` and `selected_end_sec` in Song model
   - Used to extract segment before analysis and clip generation

3. **Music Analysis** (`song_analysis.py`)
   - **BPM detection** via autocorrelation
   - **Beat grid** extraction using librosa
   - **Section segmentation** (intro, verse, chorus, bridge, outro)
   - **Genre classification** via audio embeddings
   - **Mood extraction** (valence, energy, danceability)
   - **Lyric transcription** via Whisper API
   - Conditionally runs section inference (only for `full_length` videos)

### Video Generation Pipeline

1. **Video Type Selection**
   - `full_length`: 16:9 aspect ratio, uses section-based generation
   - `short_form`: 9:16 aspect ratio, uses clip-based generation with audio selection

2. **Clip Planning** (`clip_planning.py`)
   - Calculates beat-aligned clip boundaries
   - Supports both video types with different strategies
   - Uses selected audio segment for short-form videos

3. **Scene Planning** (`scene_planner.py`)
   - Converts `SongAnalysis` → `SceneSpec`
   - Maps moods → color palettes
   - Maps genres → camera motions
   - Template selection (abstract, environment, character, minimal)
   - Ensures cohesive visual style across scenes

4. **Video Provider Pattern** (`video_providers/`)
   - **Abstract base class** (`VideoGenerationProvider`) for extensibility
   - **MinimaxHailuoProvider** implementation
   - Supports both text-to-video and image-to-video generation
   - Handles aspect ratio and resolution selection (768p for 16:9, 1080p for 9:16)
   - Easy to swap providers or add new ones

5. **Character Consistency** (`character_consistency.py`)
   - **Image interrogation** via OpenAI GPT-4o Vision (optional, falls back to Replicate)
   - **Consistent character generation** using Replicate Stable Diffusion XL
   - **Pose selection** (A or B) for character variations
   - **Image-to-video** generation using reference character images
   - Optional feature that enhances visual continuity

6. **Template Characters** (`template_characters.py`)
   - Pre-generated character sets with multiple poses
   - Uploaded via admin API
   - Used as fallback or primary character source

7. **Video Generation** (`video_generation.py`)
   - Orchestrates provider calls
   - Handles polling for async video generation
   - Manages seed values for reproducibility
   - Supports both text-to-video and image-to-video modes
   - 9:16 image padding/processing for short-form videos

### Composition Engine

1. **Video Composition** (`video_composition.py`)
   - Concatenates clips with beat-aligned cuts
   - Normalizes FPS and resolution
   - Applies transitions between clips
   - Muxes with original audio track

2. **Beat-Synced Effects** (`beat_filter_applicator.py`, `beat_filters.py`)
   - **Beat Filter Applicator** centralizes effect application logic
   - **Effect types**:
     - Flash (brightness pulse)
     - Color burst (hue/saturation shift)
     - Zoom pulse (scale animation)
     - Glitch (digital artifacts)
     - Brightness pulse (smooth fade)
   - **Beat alignment** using tolerance windows
   - **Test mode** for exaggerated effects (3x intensity)
   - Applies effects to every Nth beat (configurable)

3. **Cost Tracking** (`cost_tracking.py`)
   - Tracks generation costs per song
   - Stores `total_generation_cost_usd` in Song model
   - Aggregates costs from video generation API calls

## Data Models

### Core Models

- **User**: Authentication, preferences, project ownership
- **Song**: Audio metadata, video type, template, character settings, cost tracking
- **SongAnalysis**: BPM, beats, sections, genre, mood, lyrics
- **SongClip**: Individual generated video clips (for short-form)
- **SectionVideo**: Section-level videos (for full-length)
- **Job**: Async job status tracking
- **TemplateCharacter**: Pre-generated character assets

### Storage

- **PostgreSQL**: All metadata, analysis results, job status
- **S3**: Audio files, video clips, final compositions, character images

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - User registration
- `POST /login` - User login
- `GET /me` - Current user info
- `PATCH /me/animations` - Update animations preference

### Songs (`/api/v1/songs`)
- `GET /` - List user's songs (max 5)
- `POST /` - Upload audio file
- `GET /{song_id}` - Get song details
- `GET /{song_id}/public` - Public read-only access
- `PATCH /{song_id}/video-type` - Set video type
- `PATCH /{song_id}/selection` - Set audio selection (short-form)
- `PATCH /{song_id}/template` - Set visual template
- `POST /{song_id}/analyze` - Trigger analysis
- `GET /{song_id}/analysis` - Get analysis results
- `POST /{song_id}/clips/plan` - Plan clips
- `POST /{song_id}/clips/generate` - Generate clips
- `GET /{song_id}/clips` - List clips
- `POST /{song_id}/compose` - Compose final video
- `POST /{song_id}/character-image` - Upload character reference
- `POST /{song_id}/character-image/generate` - Generate consistent character
- `PATCH /{song_id}/character-pose` - Select character pose
- `DELETE /{song_id}` - Delete song

### Videos (`/api/v1/videos`)
- `POST /generate` - Direct video generation
- `GET /{section_id}/video` - Get section video

### Template Characters (`/api/v1/template-characters`)
- `GET /` - List available template characters
- `POST /` - Upload template character set

### Jobs (`/api/v1/jobs`)
- `GET /{job_id}` - Get job status

### Config (`/api/v1/config`)
- `GET /features` - Get feature flags

## Job Queue System

- **RQ (Redis Queue)** for async job processing
- **Job types**:
  - Audio preprocessing
  - Music analysis
  - Clip generation (parallelized)
  - Character image generation
  - Video composition
- **Job status tracking** with progress updates
- **Timeout handling** (20-30 minutes per job)

## Key Features

### Dual Video Types
- **Full-length videos** (16:9): Section-based generation, uses entire track
- **Short-form videos** (9:16): Clip-based generation, 30-second audio selection

### Character Consistency
- Optional feature for maintaining character appearance across clips
- Image interrogation + AI generation workflow
- Pose selection for character variations

### Beat Synchronization
- Beat-aligned clip boundaries
- Beat-synced visual effects during composition
- Configurable effect types and intensities

### Cost Management
- Per-song cost tracking
- Aggregated generation costs
- Useful for billing and optimization

### Template System
- Visual style templates (abstract, environment, character, minimal)
- Pre-generated character sets
- Cohesive aesthetic across scenes

## Technology Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Python + FastAPI + SQLModel
- **Workers**: RQ (Redis Queue)
- **Database**: PostgreSQL
- **Storage**: Amazon S3
- **Video Processing**: FFmpeg
- **Audio Analysis**: librosa, Essentia
- **AI Models**: 
  - Replicate (Minimax Hailuo 2.3 for video, SDXL for character images)
  - OpenAI (GPT-4o Vision for image interrogation, optional with Replicate fallback)
  - Whisper (via Replicate) for lyrics
- **Authentication**: JWT tokens

## Environment Variables

### Required
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `S3_BUCKET_NAME` - S3 bucket name
- `S3_ACCESS_KEY_ID` - AWS access key
- `S3_SECRET_ACCESS_KEY` - AWS secret key
- `S3_REGION` - AWS region
- `REPLICATE_API_TOKEN` - Replicate API token (for video generation and character images)

### Optional
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o Vision image interrogation
  - **Note**: Character consistency feature works without this (falls back to Replicate)
  - Only needed if you want to use OpenAI's vision model for analyzing character images
- `WHISPER_API_TOKEN` - Whisper API token (if using external Whisper service)
- `LYRICS_API_KEY` - Musixmatch or similar lyrics API key
- `PORT` - Server port (auto-set by Railway)

## Deployment

- **Backend**: Railway (Docker container)
- **Frontend**: Railway (Nginx static hosting)
- **Database**: Railway PostgreSQL
- **Redis**: Railway Redis
- **Storage**: AWS S3

See `README.md` for production URLs and deployment commands.
