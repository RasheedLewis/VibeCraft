FROM python:3.12-slim

# Install system dependencies
# - ffmpeg: Required for audio/video processing
# - libsndfile1: Required for librosa audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Default command for API service
# Override in Railway for worker service: rq worker ai_music_video --url $REDIS_URL
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

