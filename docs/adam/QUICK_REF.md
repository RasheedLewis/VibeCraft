# Quick Reference

## Do This

`make dev`

`make stop`

```bash
# you can run them individually but may get the venv prefix `((.venv) )` unless you VIRTUAL_ENV_DISABLE_PROMPT=1
# Lint
make lint-all # frontend and backend including format and -fix
make build # frontend only, Python doesn't build
make test
# Terminal 1: Frontend
cd frontend && npm run dev -- --host
# Terminal 2: Backend API
cd backend && source ../.venv/bin/activate && uvicorn app.main:app --reload
# Terminal 3: RQ Worker
cd backend && source ../.venv/bin/activate && rq worker ai_music_video
# Terminal 4: Trigger.dev (optional - only when working on trigger workflows)
npx trigger.dev@latest dev
# Or include Trigger.dev in dev script:
ENABLE_TRIGGER_DEV=1 make dev
```

## Scratchpad

### HIGH PRIORITY: Video APIs Research

- Gotta try out video APIs and get lay of the land for what's fast, and what's pricy

**Test Prompts for Video Generation APIs:**

**Structure:** `[Style], [Camera Motion], [Subject/Action], [Environment], [Mood/Lighting]`

**Example Prompts:**

1. **Energetic/Electronic:**
   - `"Cinematic, dynamic camera movement, neon-lit cityscape at night with pulsing lights, cyberpunk aesthetic, high energy, vibrant colors"`
   - `"Abstract, fast-paced zoom, geometric shapes morphing and pulsing, dark background with neon accents, rhythmic motion"`

2. **Chill/Lo-fi:**
   - `"Dreamy, slow pan, person walking through misty forest at golden hour, soft focus, ambient lighting, peaceful mood"`
   - `"Aesthetic, gentle camera drift, abstract watercolor waves, pastel colors, calm and meditative"`

3. **Rock/Intense:**
   - `"Gritty, handheld camera shake, urban street scene with dramatic shadows, high contrast, intense mood, black and white with color accents"`
   - `"Raw, quick cuts, abstract fire and smoke effects, dark atmosphere, powerful energy"`

4. **Pop/Bright:**
   - `"Vibrant, smooth tracking shot, colorful abstract shapes dancing, bright studio lighting, upbeat and joyful"`
   - `"Stylish, rotating camera, geometric patterns in motion, pastel and neon palette, fun and energetic"`

**Quick Test Prompt (Good Baseline):**

- `"Cinematic, slow camera pan, abstract neon particles floating in dark space, pulsing rhythm, moody lighting, music video aesthetic"`
- `"Otter flying an airplane"`

**Prompt Tips:**

- Include camera motion (pan, zoom, track, rotate)
- Specify style (cinematic, abstract, gritty, dreamy)
- Add mood/energy level
- Mention lighting/color palette
- Keep it concise but descriptive (50-100 words)

### Track Recognition & Analysis Flow

**Branching logic:**

```text
Shazam → determine whether known/unknown track
│
├─ if Known Track:
│  ├─ Spotify API → features
│  └─ ChatGPT → lyrics and song section
│
└─ if Unknown Track:
   └─ Whisper → lyrics
   
└─ maybe in either case:
   └─ Essentia → audio info
```

### Deployment

- **Frontend**: We'll try AWS Amplify to deploy frontend
- **Backend**:
  - **Easiest for MVP**: Railway or Render (see DEPLOYMENT_ANALYSIS.md for details)
  - **Best for Production**: AWS ECS/Fargate
  - **Tricky Issues**: FFmpeg system dependency, librosa native deps, long-running tasks (30+ min), memory requirements, worker process management
  - See `docs/adam/DEPLOYMENT_ANALYSIS.md` for full analysis of ease vs issues
  
  **Backend Components to Deploy:**
  - FastAPI API server (uvicorn)
  - RQ workers (or migrate to Trigger.dev for production)
  - Needs: Postgres (RDS), Redis (ElastiCache), S3 access
  - Dependencies: ffmpeg, librosa, Python packages
