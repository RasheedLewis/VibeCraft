flowchart LR
  %% CLIENT
  subgraph Client["Client"]
    U[User Browser\nReact + TypeScript]
  end

  %% BACKEND
  subgraph Backend["Python Backend (FastAPI + Workers)"]
    API[REST API Layer\n/songs, /analysis, /sections, /videos, /jobs]

    subgraph AudioPipeline["Audio & Music Intelligence"]
      APS[Audio Preprocess Service\n(ffmpeg + librosa)]
      MAS[Music Analysis Service\nBPM · Beats · Sections · Genre · Mood · Lyrics]
    end

    subgraph VideoPipeline["Video Planning & Generation"]
      SP[Scene Planner\n(full song + per-section)]
      VGE[Video Generation Engine\nReplicate wrappers]
      CE[Composition Engine\nffmpeg concat + transitions + mux]
    end

    JS[Job Orchestrator / Workers\nRQ/Celery]
    DB[(Postgres / DB\nSongs · Analyses · SectionVideos · Jobs)]
    ST[(Object Storage\nS3: audio · clips · finals)]
  end

  %% EXTERNAL SERVICES
  subgraph External["External AI / Music APIs"]
    REP[Video Models on Replicate]
    LYR[Lyrics / Music APIs\n(Whisper, Musixmatch, etc.)]
  end

  %% FLOWS

  %% Upload & Analysis
  U -->|"1. Upload audio file"| API
  API -->|"store raw audio"| ST
  API -->|"enqueue preprocess job"| JS
  JS --> APS
  APS -->|"processed audio\n+ waveform"| ST
  APS --> MAS
  MAS -->|"SongAnalysis\n(sections, bpm, mood, lyrics)"| DB
  MAS -->|"optional track/lyrics lookup"| LYR

  U -->|"2. Fetch analysis\n& Song Profile UI"| API --> DB

  %% Section-level generation
  U -->|"3. Generate Section Video"| API
  API -->|"enqueue section job"| JS
  JS -->|"build SceneSpec from\nSongAnalysis + template"| SP
  SP --> VGE
  VGE -->|"call video model"| REP
  REP -->|"clip video"| VGE
  VGE -->|"store section clip"| ST
  VGE -->|"SectionVideo metadata"| DB
  U -->|"preview section clip"| API --> ST

  %% Full-song generation
  U -->|"4. Generate Full Music Video"| API
  API -->|"enqueue full-video job"| JS
  JS -->|"assemble full-scene plan\n(reuse approved sections)"| SP
  SP -->|"missing scenes → generate"| VGE
  VGE --> REP
  REP --> VGE
  VGE -->|"all section clips"| ST

  JS -->|"compose timeline\n+ beat-synced transitions"| CE
  CE -->|"final 1080p MP4/WebM"| ST
  ST -->|"download/stream URL"| U

  %% Data persistence paths
  API --> DB
  JS --> DB
  CE --> DB
