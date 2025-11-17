# VibeCraft Deployment Guide

Complete step-by-step guide for deploying VibeCraft to Railway.

## Quick Reference

**Required Environment Variables:**
- `S3_BUCKET_NAME=ai-music-video`
- `S3_REGION=us-east-2`
- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` (or `S3_ACCESS_KEY_ID`/`S3_SECRET_ACCESS_KEY`)
- `REPLICATE_API_TOKEN`
- `VITE_API_BASE_URL` (frontend only - your backend Railway URL)

**Auto-provided by Railway:**
- `DATABASE_URL` (from PostgreSQL addon)
- `REDIS_URL` (from Redis addon)
- `PORT` (set automatically)

**Service Start Commands:**
- Backend API: (default from Dockerfile - `uvicorn app.main:app`)
- RQ Worker: `rq worker ai_music_video` (no `--url` flag needed, uses `REDIS_URL` env var)
- Frontend: (default from Dockerfile - nginx)

---

## Deployment Checklist

Follow these steps in order:

## Prerequisites

- [ ] GitHub account with VibeCraft repository
- [ ] Railway account (sign up at https://railway.app)
- [ ] AWS account (for S3 storage)
- [ ] Replicate API token (you already have this from development)

## Phase 1: Railway Setup

### 1.1 Install Railway CLI

```bash
npm install -g @railway/cli
```

### 1.2 Login to Railway

```bash
railway login
```

This will open your browser to authenticate.

### 1.3 Create Railway Project

```bash
railway init
```

Follow the prompts:
- Select "Create a new project"
- Name it `vibecraft` (or your preferred name)
- Link it to your GitHub repository

## Phase 2: Database & Redis Setup

### 2.1 Add PostgreSQL Database

In Railway dashboard:
1. Click "New" → "Database" → "Add PostgreSQL"
2. Railway will automatically create the database
3. Note: `DATABASE_URL` is automatically set as an environment variable

### 2.2 Add Redis

In Railway dashboard:
1. Click "New" → "Database" → "Add Redis"
2. Railway will automatically create Redis instance
3. Note: `REDIS_URL` is automatically set as an environment variable

## Phase 3: AWS S3 Setup

**Note:** You're using your existing development S3 bucket for production. You already have access, so no need to create new IAM credentials.

### 3.1 Gather S3 Information

Make sure you have ready:
- Your existing S3 bucket name: `ai-music-video`
- AWS Access Key ID and Secret Access Key (from your development setup)
- The bucket region: `us-east-2`

### 3.2 Configure S3 Bucket CORS (if not already configured)

In S3 bucket → Permissions → CORS, add:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": [
      "https://*.railway.app"
    ],
    "ExposeHeaders": [],
    "MaxAgeSeconds": 3000
  }
]
```

## Phase 4: Backend API Deployment

### 4.1 Create Backend Service

```bash
cd backend
railway service create backend-api
railway link backend-api
```

### 4.2 Set Environment Variables

In Railway dashboard, go to backend-api service → Variables, add:

```bash
# API Configuration (Railway sets PORT automatically)
API_HOST=0.0.0.0
API_LOG_LEVEL=info

# Database (Railway auto-provides, but verify it's set)
# DATABASE_URL is automatically set by Railway PostgreSQL addon

# Redis (Railway auto-provides, but verify it's set)
# REDIS_URL is automatically set by Railway Redis addon

# RQ Worker Queue
RQ_WORKER_QUEUE=ai_music_video

# AWS S3 (use your existing development bucket and credentials)
S3_BUCKET_NAME=ai-music-video
S3_ACCESS_KEY_ID=your-existing-access-key-id
S3_SECRET_ACCESS_KEY=your-existing-secret-access-key
S3_REGION=us-east-2
# Leave empty for AWS S3
S3_ENDPOINT_URL=

# External APIs (use your existing development token)
REPLICATE_API_TOKEN=your-existing-replicate-token
# Optional
WHISPER_API_TOKEN=
LYRICS_API_KEY=

# System Dependencies
FFMPEG_BIN=ffmpeg
LIBROSA_CACHE_DIR=.cache/librosa
```

### 4.3 Configure Service Settings

In Railway dashboard → backend-api → Settings:
- **Root Directory:** `backend`
- **Build Command:** (leave empty, Dockerfile handles it)
- **Start Command:** (leave empty, Dockerfile handles it)
- **Health Check Path:** `/healthz`
- **Health Check Timeout:** 30s

### 4.4 Deploy Backend

```bash
cd backend
railway up
```

Or push to GitHub (if connected):
```bash
git push origin main
```

### 4.5 Verify Backend

1. Get your backend URL from Railway dashboard
2. Test health endpoint: `https://your-backend.railway.app/healthz`
3. Should return: `{"status":"ok"}`

## Phase 5: RQ Worker Deployment

### 5.1 Create Worker Service

```bash
cd backend
railway service create rq-worker
railway link rq-worker
```

### 5.2 Set Environment Variables

Copy all environment variables from backend-api service, plus ensure:
- `REDIS_URL` is set (auto-provided by Railway)
- `RQ_WORKER_QUEUE=ai_music_video`

### 5.3 Configure Service Settings

In Railway dashboard → rq-worker → Settings:
- **Root Directory:** `backend`
- **Build Command:** (leave empty, Dockerfile handles it)
- **Start Command:** `rq worker ai_music_video --url $REDIS_URL`
- **No Health Check** (workers don't serve HTTP)

### 5.4 Deploy Worker

```bash
cd backend
railway up --service rq-worker
```

### 5.5 Verify Worker

1. Check Railway logs for worker service
2. Should see: "Listening for jobs on queue 'ai_music_video'"

## Phase 6: Frontend Deployment

### 6.1 Create Frontend Service

```bash
cd frontend
railway service create frontend
railway link frontend
```

### 6.2 Set Environment Variables

In Railway dashboard → frontend → Variables, add:

```bash
# Backend API URL (use your actual backend Railway URL)
VITE_API_BASE_URL=https://your-backend.railway.app

# Feature flags
VITE_ENABLE_MOCKS=false

# CDN base URL (optional, for S3 CDN)
VITE_CDN_BASE_URL=https://vibecraft-storage.s3.amazonaws.com
```

### 6.3 Configure Service Settings

In Railway dashboard → frontend → Settings:
- **Root Directory:** `frontend`
- **Build Command:** (leave empty, Dockerfile handles it)
- **Start Command:** (leave empty, Dockerfile handles it)
- **Health Check Path:** `/healthz`

### 6.4 Deploy Frontend

```bash
cd frontend
railway up
```

### 6.5 Verify Frontend

1. Get your frontend URL from Railway dashboard
2. Open in browser
3. Should see the VibeCraft upload page

## Phase 7: Post-Deployment Configuration

### 7.1 Update Backend CORS

Update `backend/app/main.py` to allow your frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-frontend.railway.app",
        "http://localhost:5173",  # Keep for local dev
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then redeploy backend:
```bash
cd backend
railway up
```

### 7.2 Run Database Migrations

Connect to backend service and run migrations:

```bash
cd backend
railway run --service backend-api python -m app.core.migrations
```

Or migrations run automatically on startup via `init_db()`.

### 7.3 Test End-to-End

1. Upload a test audio file via frontend
2. Verify it appears in backend
3. Check S3 bucket for uploaded file
4. Trigger analysis job
5. Verify worker processes the job
6. Check logs for any errors

## Phase 8: Monitoring & Optimization

### 8.1 Set Up Monitoring

- [ ] Check Railway logs regularly
- [ ] Set up error alerts (consider Sentry)
- [ ] Monitor S3 storage usage
- [ ] Monitor Railway resource usage

### 8.2 Optimize Costs

- [ ] Review Railway usage and optimize if needed
- [ ] Review S3 storage and lifecycle policies
- [ ] Monitor Replicate API usage

## Troubleshooting

### Backend won't start
- Check logs in Railway dashboard
- Verify all environment variables are set
- Check DATABASE_URL and REDIS_URL are correct

### Worker not processing jobs
- Check REDIS_URL is set correctly
- Verify worker service is running
- Check logs for connection errors

### Frontend can't connect to backend
- Verify VITE_API_BASE_URL is correct
- Check CORS configuration
- Verify backend is running and accessible

### S3 uploads failing
- Verify IAM credentials are correct
- Check bucket policy allows Railway service
- Verify bucket name and region

## Next Steps

After successful deployment:
1. Set up custom domain (optional)
2. Configure SSL certificates (Railway handles this automatically)
3. Set up CI/CD for automatic deployments
4. Configure backup strategy for database
5. Set up monitoring and alerting

## Support

For issues:
- Check Railway logs
- Review `docs/DEPLOYMENT_PLAN.md` for detailed information
- Check `docs/adam/DEPLOYMENT_ANALYSIS.md` for common issues

