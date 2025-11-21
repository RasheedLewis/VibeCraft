flowchart LR
  %% CLIENT
  subgraph Client["Client"]
    U[User Browser\nReact + TypeScript]
  end

  %% BACKEND
  subgraph Backend["Python Backend (FastAPI + Workers)"]
    API[REST API Layer\n/songs, /songs/{id}/analysis, /songs/{id}/clips/*, /jobs, /health]

    subgraph AudioPipeline["Audio & Music Intelligence"]
      APS[Audio Preprocess Service\n(ffmpeg + librosa)]
      MAS[Music Analysis Service\nBPM · Beats · Sections · Genre · Mood · Lyrics]
    end

    subgraph VideoPipeline["Video Planning & Generation"]
      CP[Clip Planner\n(beat-aligned boundaries)]
      SP[Scene Planner\n(builds prompts from analysis)]
      VGE[Video Generation Engine\nReplicate wrappers]
      CE[Composition Engine\nffmpeg concat + transitions + mux]
    end

    JS[Job Orchestrator / Workers\nRQ (Redis Queue)]
    DB[(Postgres / DB\nSongs · Analyses · SongClips · Jobs)]
    ST[(Object Storage\nS3: audio · clips · finals)]
  end

  %% EXTERNAL SERVICES
  subgraph External["External AI / Music APIs"]
    REP[Video Models on Replicate\n(minimax/hailuo-2.3)]
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

  %% Clip generation
  U -->|"3. Plan Clips"| API
  API -->|"calculate beat-aligned boundaries"| CP
  CP -->|"store clip plans"| DB
  
  U -->|"4. Generate Clips"| API
  API -->|"enqueue clip generation jobs"| JS
  JS -->|"build SceneSpec from\nSongAnalysis + clip"| SP
  SP --> VGE
  VGE -->|"call video model"| REP
  REP -->|"clip video"| VGE
  VGE -->|"store clip video"| ST
  VGE -->|"SongClip metadata"| DB
  U -->|"preview clips"| API --> ST

  %% Composition
  U -->|"5. Compose Video"| API
  API -->|"enqueue composition job"| JS
  JS -->|"get all completed SongClips"| DB
  JS -->|"compose timeline\nwith beat-aligned cuts"| CE
  CE -->|"final 1080p MP4 (H.264/AAC)"| ST
  ST -->|"download/stream URL"| U

  %% Data persistence paths
  API --> DB
  JS --> DB
  CE --> DB
