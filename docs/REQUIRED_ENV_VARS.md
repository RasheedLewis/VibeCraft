# Required Environment Variables for Railway

## Actually Required Variables

### Backend API & Worker Services

**Required:**
- `S3_BUCKET_NAME=ai-music-video`
- `S3_REGION=us-east-2`
- `REPLICATE_API_TOKEN=<your-token>`

**S3 Credentials (choose one option):**

**Option 1: Use custom S3 variables (if you have them):**
- `S3_ACCESS_KEY_ID=<your-key>`
- `S3_SECRET_ACCESS_KEY=<your-secret>`

**Option 2: Use standard AWS environment variables (if you don't have S3_SECRET_ACCESS_KEY):**
- `AWS_ACCESS_KEY_ID=<your-key>`
- `AWS_SECRET_ACCESS_KEY=<your-secret>`

Note: If you use Option 2, you may need to update the code to check for `AWS_ACCESS_KEY_ID` as a fallback, or boto3 will automatically use these if `S3_ACCESS_KEY_ID` is not set.

**Auto-provided by Railway (don't set manually):**
- `DATABASE_URL` (from PostgreSQL addon)
- `REDIS_URL` (from Redis addon)
- `PORT` (set automatically by Railway)

### Optional Variables (have defaults, only set if you want to override)

- `API_HOST` (default: "0.0.0.0")
- `API_LOG_LEVEL` (default: "info")
- `FFMPEG_BIN` (default: "ffmpeg" - already installed in Docker)
- `LIBROSA_CACHE_DIR` (default: ".cache/librosa")
- `RQ_WORKER_QUEUE` (default: "ai_music_video")
- `S3_ENDPOINT_URL` (leave empty for AWS S3)
- `WHISPER_API_TOKEN` (optional)
- `LYRICS_API_KEY` (optional)

## Minimal Setup for Railway

**Minimum required variables:**
```
S3_BUCKET_NAME=ai-music-video
S3_REGION=us-east-2
AWS_ACCESS_KEY_ID=<your-key>
AWS_SECRET_ACCESS_KEY=<your-secret>
REPLICATE_API_TOKEN=<your-token>
```

Note: If using `AWS_ACCESS_KEY_ID` instead of `S3_ACCESS_KEY_ID`, the code may need a small update to check for the standard AWS env vars as a fallback.

