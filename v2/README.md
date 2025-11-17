# VibeCraft v2 — Simplified & Lean

**A clean rebuild focused on MVP essentials.**

## Core Purpose

Transform audio into music videos through a simple pipeline:
1. **Upload** audio file
2. **Analyze** music (BPM, beats)
3. **Plan** video clips (beat-aligned, 3-5 clips)
4. **Generate** AI video clips
5. **Compose** clips into final video
6. **Download** result

## MVP Requirements

1. ✅ **Audio-visual sync** — Video transitions align with beats
2. ✅ **Multi-clip composition** — 3-5 clips stitched together
3. ✅ **Consistent visual style** — Cohesive aesthetic across clips

## Architecture Principles

- **Minimal** — Only what's needed for MVP
- **Modular** — Clear boundaries between components
- **Sequenced** — Build incrementally, test at each step
- **Clear** — Self-documenting code and structure

## Project Structure

```
v2/
├── docs/
│   ├── ARCHITECTURE.md      # System design & data flow
│   ├── BUILD_PLAN.md        # Sequenced implementation plan
│   └── API.md               # API contracts
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entrypoint
│   │   ├── models/          # Database models (minimal)
│   │   ├── api/             # REST endpoints
│   │   └── services/        # Business logic
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/           # Upload, Status, Result
│   │   └── api/             # API client
│   └── package.json
└── README.md
```

## Getting Started

See `docs/MASTER_PLAN.md` for complete requirements, architecture, and implementation plan.

