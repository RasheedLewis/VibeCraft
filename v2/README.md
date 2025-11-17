# VibeCraft v2 — Simplified & Lean

**A clean rebuild focused on MVP essentials.**

## Core Purpose

Transform audio into music videos through a simple pipeline:
1. **Upload** audio file
2. **Analyze** music (BPM, beats, genre, mood, lyrics)
3. **Create sections** (user-defined, beat-aligned)
4. **Generate** AI video clips
5. **Compose** clips into final video
6. **Finalize** and share

## MVP Requirements

1. ✅ **Audio-visual sync** — Video transitions align with beats
2. ✅ **Multi-clip composition** — 3-10 clips stitched together
3. ✅ **Consistent visual style** — Cohesive aesthetic across clips
4. ✅ **Working video generation** — End-to-end pipeline
5. ✅ **Deployed pipeline** — API and web interface

## Architecture Principles

- **Minimal** — Only what's needed for MVP
- **Modular** — Clear boundaries between components
- **Sequenced** — Build incrementally, test at each step
- **Clear** — Self-documenting code and structure

## Project Structure

```
v2/
├── docs/
│   ├── MASTER_PLAN.md       # Complete requirements and plan
│   ├── ARCHITECTURE.md      # System design & data flow
│   ├── IMPLEMENTATION_PHASES.md  # Detailed phase breakdown
│   └── DEPLOYMENT.md        # Deployment guide
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entrypoint
│   │   ├── core/            # Configuration, database, logging
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── api/             # REST endpoints
│   │   ├── services/        # Business logic
│   │   └── workers/         # RQ worker functions
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/           # Page components
│   │   ├── components/      # Reusable components
│   │   ├── api/             # API client
│   │   └── types/           # TypeScript types
│   └── package.json
├── scripts/
│   ├── dev.sh               # Development server launcher
│   ├── health-check.sh      # Health check script
│   └── for-development/     # Test scripts
├── infra/
│   ├── docker-compose.yml   # Local development services
│   └── Dockerfile.backend   # Backend Docker image
├── Makefile                 # Development commands
└── README.md
```

## Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** (for frontend)
- **PostgreSQL** (local or Railway)
- **Redis** (local via Docker or Railway)
- **Docker** (optional, for local PostgreSQL/Redis)
- **FFmpeg** (for video/audio processing)
- **AWS Account** (for S3 storage)
- **Replicate API Token** (for video generation)

## Getting Started

### 1. Clone Repository

```bash
git clone <repository-url>
cd vibecraft/v2
```

### 2. Environment Setup

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
# Edit .env with your configuration
```

Required environment variables:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `S3_BUCKET_NAME` - AWS S3 bucket name
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `REPLICATE_API_TOKEN` - Replicate API token
- `SECRET_KEY` - JWT signing key (generate strong random key)

### 3. Install Dependencies

```bash
make install
```

This will:
- Create Python virtual environment
- Install backend dependencies
- Install frontend dependencies

### 4. Start Local Services

#### Option 1: Using Docker Compose (Recommended)

```bash
cd infra
docker-compose up -d
```

This starts PostgreSQL and Redis in Docker containers.

#### Option 2: Using Local Services

- **PostgreSQL**: Install and run locally
- **Redis**: `docker run -d -p 6379:6379 --name vibecraft-redis redis:7-alpine`

### 5. Run Development Server

```bash
make start
# or
make dev
```

This will:
- Run pre-flight checks (linting, building, testing)
- Start backend API on http://localhost:8000
- Start RQ worker (background jobs)
- Start frontend on http://localhost:5173
- Start Redis (via Docker if not running)

### 6. Verify Setup

Open your browser:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **Health Check**: http://localhost:8000/health

Run health checks:
```bash
bash scripts/health-check.sh
```

## Development Commands

```bash
make help          # Show all available commands
make dev           # Start all development services
make start         # Alias for 'make dev'
make install       # Install dependencies
make lint          # Run linters (frontend + backend)
make lint-fix      # Auto-fix linting issues
make format        # Check code formatting
make format-fix    # Auto-format code
make lint-all      # Auto-fix linting and format all code
make build         # Build frontend
make test          # Run tests
make stop          # Stop all dev services
make clean         # Clean build artifacts
```

## Testing

### Phase 0 Test Script

Test Phase 0 setup:
```bash
bash scripts/for-development/test-phase0.sh
```

This tests:
- Python/Node versions
- Dependency installation
- Service startup
- Health checks
- Database/Redis connections

### Manual Testing

1. **Backend Health Check**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Frontend**: Open http://localhost:8000 in browser

3. **Redis**: `redis-cli ping` (should return PONG)

## Deployment

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for complete deployment guide.

**Quick Overview**:
- **Backend API**: Railway
- **Background Workers**: Railway (separate service)
- **Frontend**: Vercel
- **Database**: Railway PostgreSQL addon
- **Redis**: Railway Redis addon
- **Storage**: AWS S3 + CloudFront

## Documentation

- [`docs/MASTER_PLAN.md`](docs/MASTER_PLAN.md) - Complete requirements, architecture, and implementation plan
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) - System design, tech stack, APIs, data models
- [`docs/IMPLEMENTATION_PHASES.md`](docs/IMPLEMENTATION_PHASES.md) - Detailed phase breakdown
- [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) - Deployment guide

## Troubleshooting

### Backend won't start
- Check Python version (need 3.10+)
- Verify virtual environment is activated
- Check database connection (verify `DATABASE_URL`)
- Check Redis connection (verify `REDIS_URL`)

### Frontend won't start
- Check Node version (need 18+)
- Verify dependencies installed (`npm install`)
- Check for port conflicts (5173)

### Redis connection issues
- Verify Redis is running: `docker ps | grep redis`
- Check Redis URL in `.env`
- Try restarting Redis: `docker restart vibecraft-redis`

### Database connection issues
- Verify PostgreSQL is running
- Check `DATABASE_URL` in `.env`
- Verify database exists and user has permissions

## Next Steps

1. Complete Phase 0 setup (this phase)
2. Proceed to Phase 1: Authentication
3. Follow implementation phases in order
4. Test each phase before moving to next

See [`docs/IMPLEMENTATION_PHASES.md`](docs/IMPLEMENTATION_PHASES.md) for detailed phase breakdown.

