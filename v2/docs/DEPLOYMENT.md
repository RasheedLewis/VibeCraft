# VibeCraft v2 Deployment Guide

This guide covers deployment of VibeCraft v2 to production environments.

## Overview

VibeCraft v2 uses the following infrastructure:
- **Backend API**: Railway
- **Background Workers**: Railway (separate service)
- **Frontend**: Vercel
- **Database**: Railway PostgreSQL addon
- **Redis**: Railway Redis addon
- **Storage & CDN**: AWS S3 + CloudFront

## Prerequisites

- Railway account
- Vercel account
- AWS account (for S3 and CloudFront)
- Git repository with VibeCraft v2 code

## Local Development Setup

### 1. Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your environment variables in `.env`

3. Install dependencies:
   ```bash
   make install
   ```

### 2. Start Local Services

#### Option 1: Using Docker Compose (Recommended)

Start PostgreSQL and Redis:
```bash
cd infra
docker-compose up -d
```

#### Option 2: Using Local Services

- PostgreSQL: Install and run locally
- Redis: `docker run -d -p 6379:6379 --name vibecraft-redis redis:7-alpine`

### 3. Run Development Server

Start all services:
```bash
make start
# or
make dev
```

This will:
- Run pre-flight checks (linting, building, testing)
- Start backend API on http://localhost:8000
- Start RQ worker
- Start frontend on http://localhost:5173
- Start Redis (via Docker if not running)

## Production Deployment

### Backend API (Railway)

1. **Create Railway Project**
   - Go to Railway dashboard
   - Create new project
   - Connect Git repository

2. **Add PostgreSQL Addon**
   - Add PostgreSQL addon to project
   - Note the `DATABASE_URL` from addon settings

3. **Add Redis Addon**
   - Add Redis addon to project
   - Note the `REDIS_URL` from addon settings

4. **Configure Environment Variables**
   Set the following in Railway:
   ```
   DATABASE_URL=<from PostgreSQL addon>
   REDIS_URL=<from Redis addon>
   RQ_WORKER_QUEUE=ai_music_video
   S3_BUCKET_NAME=vibecraft-videos
   AWS_ACCESS_KEY_ID=<your-aws-key>
   AWS_SECRET_ACCESS_KEY=<your-aws-secret>
   AWS_REGION=us-east-1
   REPLICATE_API_TOKEN=<your-replicate-token>
   SECRET_KEY=<generate-strong-random-key>
   ENVIRONMENT=production
   CORS_ORIGINS=https://your-frontend-domain.vercel.app
   ```

5. **Configure Build Settings**
   - Root Directory: `/backend`
   - Build Command: (none, Railway will auto-detect Python)
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

6. **Deploy**
   - Railway will auto-deploy on git push
   - Or trigger manual deploy from dashboard

### RQ Worker (Railway - Separate Service)

1. **Create New Railway Service**
   - In same Railway project
   - Use same Git repository

2. **Configure Environment Variables**
   - Share same environment variables as backend API
   - Or set individually (same values)

3. **Configure Start Command**
   ```
   rq worker ai_music_video
   ```

4. **Deploy**
   - Railway will auto-deploy on git push

### Frontend (Vercel)

1. **Create Vercel Project**
   - Go to Vercel dashboard
   - Import Git repository
   - Set root directory to `frontend`

2. **Configure Build Settings**
   - Framework Preset: Vite
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Install Command: `npm install`

3. **Configure Environment Variables**
   ```
   VITE_API_URL=https://your-backend.railway.app
   ```

4. **Deploy**
   - Vercel will auto-deploy on git push

### AWS S3 + CloudFront Setup

1. **Create S3 Bucket**
   - Bucket name: `vibecraft-videos` (or your preferred name)
   - Region: `us-east-1` (or your preferred region)
   - Block public access: Enabled (we'll use presigned URLs)

2. **Create IAM User**
   - Create IAM user with programmatic access
   - Attach policy with S3 read/write permissions
   - Save access key ID and secret access key

3. **Create CloudFront Distribution** (Optional)
   - Create distribution pointing to S3 bucket
   - Configure CORS for video playback
   - Note CloudFront domain

4. **Update Environment Variables**
   - Add `CLOUDFRONT_DOMAIN` to Railway backend if using CloudFront

### Database Migrations

Run migrations on Railway:

**Option 1: Via Railway CLI**
```bash
railway run alembic upgrade head
```

**Option 2: Via Railway Shell**
```bash
railway shell
alembic upgrade head
```

**Option 3: On Startup** (if configured)
- Add migration command to startup script

## Monitoring

### Railway Logs
- View backend API logs in Railway dashboard
- View RQ worker logs in Railway dashboard (worker service)

### Vercel Logs
- View frontend logs in Vercel dashboard

### Health Checks
- Backend: `https://your-backend.railway.app/health`
- Frontend: Vercel automatically monitors

## Troubleshooting

### Backend Issues
- Check Railway logs for errors
- Verify environment variables are set correctly
- Check database connection (verify DATABASE_URL)
- Check Redis connection (verify REDIS_URL)

### Worker Issues
- Check worker logs in Railway
- Verify worker can connect to Redis
- Verify worker can connect to database
- Check job queue status

### Frontend Issues
- Check Vercel build logs
- Verify `VITE_API_URL` is set correctly
- Check browser console for errors

### S3 Issues
- Verify AWS credentials are correct
- Check IAM user permissions
- Verify bucket name matches `S3_BUCKET_NAME`
- Check bucket region matches `AWS_REGION`

## Security Considerations

- **Secrets**: Never commit secrets to Git
- **CORS**: Configure `CORS_ORIGINS` to only allow your frontend domain
- **HTTPS**: Railway and Vercel provide HTTPS automatically
- **Database**: Use strong passwords, enable SSL
- **JWT Secret**: Generate strong random key for `SECRET_KEY`

## Scaling

### Backend API
- Railway can scale horizontally (multiple instances)
- Configure in Railway dashboard

### RQ Workers
- Create multiple worker services in Railway
- Each worker processes jobs from same Redis queue
- Scale based on job queue length

### Frontend
- Vercel automatically scales
- Edge network provides global distribution

## Cost Optimization

- Use Railway's free tier for development
- Monitor S3 storage usage
- Monitor Replicate API usage
- Set up CloudWatch alarms for AWS costs

