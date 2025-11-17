# Quick Deploy Guide

This is a condensed version of the deployment process. For detailed instructions, see `DEPLOYMENT_CHECKLIST.md`.

## Prerequisites Checklist

- [ ] Railway account (https://railway.app)
- [ ] AWS account with S3 access
- [ ] Replicate API token (you already have this from development)
- [ ] Railway CLI installed: `npm install -g @railway/cli`

## Quick Start (5 Steps)

### Step 1: Railway Setup

```bash
railway login
railway init
# Follow prompts to create project and link GitHub repo
```

### Step 2: Add Database & Redis

In Railway dashboard:
- Click "New" → "Database" → "Add PostgreSQL"
- Click "New" → "Database" → "Add Redis"

These automatically provide `DATABASE_URL` and `REDIS_URL` environment variables.

### Step 3: AWS S3 Setup

**Note:** You're using your existing development S3 bucket. You already have access, so no need to create new IAM credentials.

Make sure you have:
- Your existing S3 bucket name: `ai-music-video`
- AWS Access Key ID and Secret Access Key (from development)
- The bucket region: `us-east-2`

### Step 4: Deploy Backend API

```bash
cd backend
railway service create backend-api
railway link backend-api
```

Then in Railway dashboard → backend-api → Variables, add:
- `S3_BUCKET_NAME=ai-music-video`
- `S3_ACCESS_KEY_ID=your-existing-key`
- `S3_SECRET_ACCESS_KEY=your-existing-secret`
- `S3_REGION=us-east-2`
- `REPLICATE_API_TOKEN=your-existing-replicate-token`
- `RQ_WORKER_QUEUE=ai_music_video`
- `FFMPEG_BIN=ffmpeg`
- `LIBROSA_CACHE_DIR=.cache/librosa`

Then deploy:
```bash
railway up
```

### Step 5: Deploy Worker & Frontend

**Worker:**
```bash
cd backend
railway service create rq-worker
railway link rq-worker
# Copy all env vars from backend-api
# Set Start Command: rq worker ai_music_video --url $REDIS_URL
railway up --service rq-worker
```

**Frontend:**
```bash
cd frontend
railway service create frontend
railway link frontend
# Set VITE_API_BASE_URL=https://your-backend.railway.app
railway up
```

## Verify Deployment

1. Backend: `https://your-backend.railway.app/healthz` → `{"status":"ok"}`
2. Frontend: Open frontend URL in browser
3. Test: Upload an audio file and verify it processes

## Common Issues

- **Backend won't start**: Check all environment variables are set
- **Worker not processing**: Verify `REDIS_URL` is set correctly
- **S3 errors**: Check IAM credentials and bucket name
- **Frontend can't connect**: Verify `VITE_API_BASE_URL` is correct

## Next Steps

See `DEPLOYMENT_CHECKLIST.md` for:
- Detailed step-by-step instructions
- Troubleshooting guide
- Post-deployment configuration
- Monitoring setup

