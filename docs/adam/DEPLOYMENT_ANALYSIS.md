# Backend Deployment: Ease & Tricky Issues Analysis

## Easiest Option: **Railway or Render** 🏆

### Why They're Easiest:

1. **Zero-config deployment** - Connect GitHub repo, auto-detects Python
2. **Built-in Postgres & Redis** - One-click add-ons
3. **Automatic builds** - Detects requirements.txt, builds automatically
4. **Worker support** - Can run multiple processes (API + workers)
5. **Environment variables** - Simple UI for config
6. **Free tier** - Good for MVP/testing

### Setup Time: ~30 minutes

## Tricky Issues for VibeCraft (All Platforms)

### 🔴 Critical Issues

#### 1. **FFmpeg System Dependency**
**Problem:** `ffmpeg` is a system binary, not a Python package. Most platforms don't include it by default.

**Solutions:**
- **Railway/Render**: Add buildpack or Dockerfile with `apt-get install ffmpeg`
- **ECS/Fargate**: Include in Dockerfile
- **Elastic Beanstalk**: Use `.ebextensions` config to install via yum/apt

**Example Dockerfile addition:**
```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
```

#### 2. **Librosa Native Dependencies**
**Problem:** `librosa` requires system libraries (libsndfile, soundfile, etc.)

**Solutions:**
- Add to Dockerfile: `apt-get install -y libsndfile1`
- Or use pre-built Docker images with audio processing libraries

#### 3. **Long-Running Tasks (30+ minutes)**
**Problem:** Video generation can take 30+ minutes. Many platforms have timeouts:
- **Railway**: 5-minute HTTP timeout (but workers can run longer)
- **Render**: 30-minute timeout (may need to chunk work)
- **ECS/Fargate**: No timeout (good!)
- **Elastic Beanstalk**: No timeout (good!)

**Solution:** Use background workers (RQ/Celery/Trigger.dev) that don't have HTTP timeouts

#### 4. **Memory Requirements**
**Problem:** Audio/video processing is memory-intensive:
- librosa loading audio files
- FFmpeg processing
- Video generation

**Solutions:**
- **Railway/Render**: Upgrade to higher tier (2GB+ RAM)
- **ECS/Fargate**: Configure task memory (2-4GB recommended)
- **Elastic Beanstalk**: Use larger instance types

#### 5. **File Upload Size Limits**
**Problem:** Audio files can be large (10-50MB+)

**Solutions:**
- Stream uploads directly to S3 (don't buffer in memory)
- Use presigned URLs for direct client → S3 uploads
- Configure nginx/reverse proxy body size limits

#### 6. **Worker Process Management**
**Problem:** Need to run both API server AND worker processes

**Solutions:**
- **Railway/Render**: Use Procfile or separate services
  ```
  web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  worker: rq worker ai_music_video
  ```
- **ECS/Fargate**: Separate task definitions for API and workers
- **Elastic Beanstalk**: Use `.ebextensions` to start workers

#### 7. **Redis Connection**
**Problem:** Workers need Redis, but it's often on a different host

**Solutions:**
- Use managed Redis (ElastiCache, Railway Redis, Render Redis)
- Set `REDIS_URL` environment variable correctly
- Handle connection retries in worker code

### 🟡 Medium Issues

#### 8. **Environment Variables**
**Problem:** Many secrets needed (Replicate, S3, Postgres, Redis, etc.)

**Solution:** Use platform's secrets management, never commit to git

#### 9. **Database Migrations**
**Problem:** Need to run migrations on deploy

**Solutions:**
- Add migration step to deployment script
- Use Alembic or SQLModel's `init_db()` on startup (careful in production!)

#### 10. **CORS Configuration**
**Problem:** Frontend on Amplify, backend elsewhere - need CORS setup

**Solution:** Configure `allow_origins` in FastAPI CORS middleware with frontend URL

#### 11. **Health Checks**
**Problem:** Platform needs to know if app is healthy

**Solution:** Already have `/healthz` endpoint, configure platform to use it

### 🟢 Minor Issues

#### 12. **Logging**
**Problem:** Need to see logs in production

**Solutions:**
- Most platforms have built-in log viewers
- Consider structured logging (JSON) for better searchability

#### 13. **Rate Limiting**
**Problem:** Prevent abuse of expensive video generation

**Solution:** Add rate limiting middleware (slowapi, fastapi-limiter)

## Platform-Specific Issues

### Railway
- ✅ Easiest setup
- ⚠️ Free tier limited (500 hours/month)
- ⚠️ Need Dockerfile for ffmpeg
- ⚠️ HTTP timeout (but workers OK)

### Render
- ✅ Very similar to Railway
- ⚠️ 30-minute worker timeout (may need workarounds)
- ⚠️ Need Dockerfile for ffmpeg

### AWS ECS/Fargate
- ✅ No timeouts, full control
- ⚠️ More complex setup (Docker, ECR, task definitions)
- ⚠️ Need to set up RDS, ElastiCache separately
- ⚠️ More AWS knowledge required
- ✅ Best for production scale

### AWS Elastic Beanstalk
- ✅ Easier than ECS (Python platform)
- ⚠️ Still need to configure workers
- ⚠️ Need `.ebextensions` for ffmpeg
- ⚠️ Less flexible than ECS

### Fly.io
- ✅ Good Docker support
- ⚠️ Need to configure volumes for cache
- ⚠️ Global deployment adds complexity

### DigitalOcean App Platform
- ✅ Simple, cost-effective
- ⚠️ Similar to Railway/Render
- ⚠️ Need Dockerfile for ffmpeg

## Recommended Approach

### For MVP (Fastest to Deploy):
1. **Railway or Render** - Easiest, get running in 30 minutes
2. Use their managed Postgres + Redis
3. Create Dockerfile with ffmpeg
4. Use Procfile for API + workers

### For Production (Most Scalable):
1. **AWS ECS/Fargate** - Best long-term, but more setup
2. Use RDS Postgres + ElastiCache Redis
3. Separate task definitions for API and workers
4. Auto-scaling groups

## Quick Start Checklist

- [ ] Create Dockerfile with ffmpeg + librosa deps
- [ ] Create Procfile (or equivalent) for API + workers
- [ ] Set up managed Postgres
- [ ] Set up managed Redis
- [ ] Configure S3 bucket and credentials
- [ ] Set all environment variables
- [ ] Test worker process starts correctly
- [ ] Test long-running task (video generation)
- [ ] Configure CORS for frontend domain
- [ ] Set up health check endpoint
- [ ] Configure logging
- [ ] Test file uploads (large files)

## Dockerfile Template

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .

# Expose port
EXPOSE 8000

# Default command (override in platform config)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Procfile Template

```
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: rq worker ai_music_video
```

