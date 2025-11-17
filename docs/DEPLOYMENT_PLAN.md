# VibeCraft Deployment Plan

## Overview

This document outlines the deployment strategy for VibeCraft, an AI-powered music video generation application. The deployment uses **Railway** for backend services, RQ workers, infrastructure, and frontend, with **AWS S3** for object storage.

## Architecture Components

The application consists of:

1. **FastAPI Backend** (`backend/app/main.py`)
   - REST API endpoints for songs, analysis, videos, jobs
   - Health check endpoint at `/healthz`
   - CORS-enabled for frontend access

2. **RQ Workers** (Background job processing)
   - Song analysis jobs
   - Clip generation jobs
   - Video composition jobs
   - Queue: `ai_music_video` (with sub-queues for clip-generation)

3. **PostgreSQL Database**
   - Stores songs, analyses, section videos, composition jobs
   - Managed via SQLModel

4. **Redis** (Job queue backend)
   - Used by RQ for job queuing and coordination

5. **React Frontend** (`frontend/`)
   - Vite-based React + TypeScript application
   - Static build output in `frontend/dist/`

6. **AWS S3** (Object storage)
   - Audio files (original and processed)
   - Video clips and final compositions
   - Waveform JSON data

## Deployment Strategy

### Recommended: Railway for Everything (Including Frontend)

**Pros:**
- Single platform for all services
- Unified logging and monitoring
- Easier environment variable management
- Simpler deployment pipeline
- Built-in service discovery

**Cons:**
- May have slightly higher latency for static assets compared to specialized static hosting

## Railway Deployment

### 1. Backend API Service

**Service Type:** Web Service

**Configuration:**
- **Root Directory:** `backend/`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path:** `/healthz`

**Required Environment Variables:**
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=$PORT  # Railway sets this automatically
API_LOG_LEVEL=info

# Database (from Railway Postgres addon)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Redis (from Railway Redis addon)
REDIS_URL=${{Redis.REDIS_URL}}
RQ_WORKER_QUEUE=ai_music_video

# S3 Configuration
S3_ENDPOINT_URL=  # Leave empty for AWS S3
S3_BUCKET_NAME=your-bucket-name
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_REGION=us-east-1

# External APIs
REPLICATE_API_TOKEN=your-replicate-token
WHISPER_API_TOKEN=  # Optional
LYRICS_API_KEY=  # Optional

# System Dependencies
FFMPEG_BIN=ffmpeg
LIBROSA_CACHE_DIR=.cache/librosa
```

**Dockerfile Required:**
Since Railway needs FFmpeg and system libraries for librosa, create `backend/Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Default command (can be overridden in Railway)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Railway Settings:**
- Use Dockerfile deployment
- Set health check to `/healthz`
- Configure restart policy
- Set memory limit to at least 2GB (for audio/video processing)

### 2. RQ Worker Service

**Service Type:** Worker Service

**Configuration:**
- **Root Directory:** `backend/`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `rq worker ai_music_video --url $REDIS_URL`
- **No Health Check** (workers don't serve HTTP)

**Required Environment Variables:**
```bash
# Same as Backend API, plus:
REDIS_URL=${{Redis.REDIS_URL}}
RQ_WORKER_QUEUE=ai_music_video

# Database access
DATABASE_URL=${{Postgres.DATABASE_URL}}

# S3 access (same as backend)
S3_BUCKET_NAME=your-bucket-name
S3_ACCESS_KEY_ID=your-access-key
S3_SECRET_ACCESS_KEY=your-secret-key
S3_REGION=us-east-1

# External APIs
REPLICATE_API_TOKEN=your-replicate-token
```

**Railway Settings:**
- Use same Dockerfile as backend
- Set memory limit to at least 2GB
- Configure for long-running tasks (no timeout)
- Can scale horizontally (multiple worker instances)

**Note:** Railway workers can run indefinitely, which is perfect for long video generation tasks (30+ minutes).

### 3. PostgreSQL Database

**Service Type:** Database Addon

**Configuration:**
- Add Railway Postgres addon to your project
- Railway automatically provides `DATABASE_URL` environment variable
- Database migrations run automatically via `init_db()` on backend startup (or manually via migration script)

**Migration Strategy:**
The app uses SQLModel's `init_db()` which creates tables on startup. For production, consider:
1. Running migrations manually before first deploy
2. Or using Alembic for more controlled migrations

### 4. Redis

**Service Type:** Redis Addon

**Configuration:**
- Add Railway Redis addon to your project
- Railway automatically provides `REDIS_URL` environment variable
- Used by both backend API (for enqueueing) and workers (for processing)

### 5. Frontend (Railway Option)

**Service Type:** Static Web Service

**Configuration:**
- **Root Directory:** `frontend/`
- **Build Command:** `npm install && npm run build`
- **Start Command:** Serve `dist/` directory
- Railway can auto-detect Vite builds and serve static files

**Required Environment Variables:**
```bash
# API endpoint (Railway backend URL)
VITE_API_BASE_URL=https://your-backend.railway.app

# Feature flags
VITE_ENABLE_MOCKS=false

# CDN base URL (if using S3 CDN)
VITE_CDN_BASE_URL=https://your-bucket.s3.amazonaws.com
```

**Alternative: Nginx Configuration**
If Railway doesn't auto-serve static files, create `frontend/nginx.conf`:

```nginx
server {
    listen $PORT;
    root /app/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

And update Dockerfile:
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## AWS S3 Setup

### 1. Create S3 Bucket

```bash
aws s3 mb s3://vibecraft-storage --region us-east-1
```

### 2. Configure Bucket Policy

Allow your Railway services to read/write:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/railway-service"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::vibecraft-storage/*"
    }
  ]
}
```

### 3. Create IAM User for Railway

1. Create IAM user: `vibecraft-railway`
2. Attach policy with S3 permissions
3. Generate access keys
4. Add keys to Railway environment variables

### 4. Enable CORS (for frontend direct access)

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedOrigins": [
      "https://your-app.railway.app"
    ],
    "ExposeHeaders": [],
    "MaxAgeSeconds": 3000
  }
]
```

## Deployment Steps

### Phase 1: Infrastructure Setup

1. **Create Railway Project**
   ```bash
   # Install Railway CLI
   npm i -g @railway/cli
   railway login
   railway init
   ```

2. **Add Database**
   - In Railway dashboard, add PostgreSQL addon
   - Note the `DATABASE_URL` (auto-injected)

3. **Add Redis**
   - In Railway dashboard, add Redis addon
   - Note the `REDIS_URL` (auto-injected)

4. **Set up S3**
   - Create bucket in AWS
   - Create IAM user and access keys
   - Configure bucket policy and CORS

### Phase 2: Backend Deployment

1. **Create Backend Service**
   ```bash
   railway service create backend-api
   railway link backend-api
   ```

2. **Create Dockerfile**
   - Create `backend/Dockerfile` (see template above)

3. **Set Environment Variables**
   - Add all required variables in Railway dashboard
   - Use Railway's variable references for database/Redis URLs

4. **Deploy**
   ```bash
   cd backend
   railway up
   ```

5. **Verify**
   - Check health endpoint: `https://your-backend.railway.app/healthz`
   - Check logs in Railway dashboard

### Phase 3: Worker Deployment

1. **Create Worker Service**
   ```bash
   railway service create rq-worker
   railway link rq-worker
   ```

2. **Use Same Dockerfile**
   - Workers use same Dockerfile as backend

3. **Set Environment Variables**
   - Copy from backend service
   - Ensure `REDIS_URL` and `RQ_WORKER_QUEUE` are set

4. **Deploy**
   ```bash
   cd backend
   railway up --service rq-worker
   ```

5. **Verify**
   - Check Railway logs for worker startup
   - Enqueue a test job and verify processing

### Phase 4: Frontend Deployment

1. **Create Frontend Service**
   ```bash
   railway service create frontend
   railway link frontend
   ```

2. **Create Dockerfile** (if needed, see nginx option above)

3. **Set Environment Variables**
   - `VITE_API_BASE_URL` = your backend Railway URL

4. **Deploy**
   ```bash
   cd frontend
   railway up
   ```

### Phase 5: Post-Deployment

1. **Run Database Migrations**
   ```bash
   # Connect to Railway backend service
   railway run --service backend-api python -m app.core.migrations
   ```

2. **Test Endpoints**
   - Upload a test song
   - Trigger analysis job
   - Verify worker processes job
   - Check S3 for uploaded files

3. **Configure CORS**
   - Update backend CORS settings with frontend URL

4. **Set up Monitoring**
   - Railway provides built-in logs
   - Consider adding error tracking (Sentry, etc.)

## Environment Variables Reference

### Backend API & Workers

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://...` | Yes |
| `REDIS_URL` | Redis connection string | `redis://...` | Yes |
| `RQ_WORKER_QUEUE` | RQ queue name | `ai_music_video` | Yes |
| `S3_BUCKET_NAME` | S3 bucket name | `vibecraft-storage` | Yes |
| `S3_ACCESS_KEY_ID` | AWS access key | `AKIA...` | Yes |
| `S3_SECRET_ACCESS_KEY` | AWS secret key | `...` | Yes |
| `S3_REGION` | AWS region | `us-east-1` | Yes |
| `S3_ENDPOINT_URL` | Custom S3 endpoint (leave empty for AWS) | `` | No |
| `REPLICATE_API_TOKEN` | Replicate API token | `r8_...` | Yes |
| `WHISPER_API_TOKEN` | Whisper API token (optional) | `...` | No |
| `LYRICS_API_KEY` | Lyrics API key (optional) | `...` | No |
| `FFMPEG_BIN` | FFmpeg binary path | `ffmpeg` | Yes |
| `LIBROSA_CACHE_DIR` | Librosa cache directory | `.cache/librosa` | Yes |
| `API_LOG_LEVEL` | Logging level | `info` | No |

### Frontend

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `VITE_API_BASE_URL` | Backend API URL | `https://api.railway.app` | Yes |
| `VITE_ENABLE_MOCKS` | Enable mock data | `false` | No |
| `VITE_CDN_BASE_URL` | S3 CDN URL for media | `https://bucket.s3.amazonaws.com` | No |

## Scaling Considerations

### Horizontal Scaling

- **Backend API:** Can run multiple instances behind Railway's load balancer
- **Workers:** Can scale to multiple worker instances for parallel job processing
- **Database:** Railway Postgres can be upgraded to higher tiers
- **Redis:** Railway Redis can handle multiple worker connections

### Resource Limits

- **Memory:** Minimum 2GB per service (for audio/video processing)
- **CPU:** Standard tier should suffice for MVP
- **Storage:** S3 handles all file storage (unlimited)
- **Database:** Start with Railway's free tier, upgrade as needed

### Cost Estimation (MVP)

- **Railway:** ~$20-50/month (depending on usage)
  - Backend API: ~$10/month
  - Worker: ~$10/month
  - Postgres: ~$5/month
  - Redis: ~$5/month
  - Frontend: ~$5/month
- **AWS S3:** ~$5-20/month (depending on storage/bandwidth)
- **Replicate API:** Pay-per-use (varies by usage)

## Troubleshooting

### Common Issues

1. **FFmpeg not found**
   - Ensure Dockerfile includes `apt-get install ffmpeg`
   - Verify `FFMPEG_BIN=ffmpeg` in environment

2. **Worker not processing jobs**
   - Check Redis connection (`REDIS_URL`)
   - Verify queue name matches (`RQ_WORKER_QUEUE`)
   - Check worker logs in Railway dashboard

3. **Database connection errors**
   - Verify `DATABASE_URL` is set correctly
   - Check PostgreSQL addon is running
   - Ensure GSS mode is disabled (handled in code)

4. **S3 upload failures**
   - Verify IAM credentials are correct
   - Check bucket policy allows Railway service
   - Verify bucket name and region

5. **CORS errors**
   - Update backend CORS settings with frontend URL
   - Check `allow_origins` includes frontend domain

6. **Long-running tasks timeout**
   - Workers should not timeout (Railway workers run indefinitely)
   - If using HTTP endpoints, ensure they're async and return job ID immediately

## Security Checklist

- [ ] All secrets stored in Railway environment variables (never in code)
- [ ] S3 bucket policy restricts access to Railway services only
- [ ] CORS configured to allow only frontend domain
- [ ] Database uses strong password (Railway auto-generates)
- [ ] Redis requires authentication (Railway auto-configures)
- [ ] API rate limiting considered (add middleware if needed)
- [ ] File upload size limits configured
- [ ] HTTPS enabled for all services (Railway auto-provisions)

## Monitoring & Logging

### Railway Built-in

- **Logs:** Available in Railway dashboard for each service
- **Metrics:** CPU, memory, network usage
- **Health Checks:** Automatic for web services

### Recommended Additions

- **Error Tracking:** Sentry or similar
- **APM:** Consider adding application performance monitoring
- **Uptime Monitoring:** UptimeRobot or similar for health checks

## Rollback Strategy

1. **Railway:** Use Railway's deployment history to rollback to previous version
2. **Database Migrations:** Keep migration scripts reversible
3. **Feature Flags:** Consider adding feature flags for gradual rollouts

## Next Steps

1. Create `backend/Dockerfile`
2. Set up Railway project and addons
3. Configure S3 bucket and IAM
4. Deploy backend API service
5. Deploy worker service
6. Deploy frontend on Railway
7. Run database migrations
8. Test end-to-end workflow
9. Configure monitoring and alerts

## References

- [Railway Documentation](https://docs.railway.app/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [RQ Documentation](https://python-rq.org/)
- Existing deployment analysis: `docs/adam/DEPLOYMENT_ANALYSIS.md`

