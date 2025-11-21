"""Application-wide constants."""

# Job configuration
DEFAULT_MAX_CONCURRENCY = 2
QUEUE_TIMEOUT_SEC = 20 * 60  # 20 minutes per clip generation
ANALYSIS_QUEUE_TIMEOUT_SEC = 30 * 60  # 30 minutes for analysis
COMPOSITION_QUEUE_TIMEOUT_SEC = 30 * 60  # 30 minutes for composition

# Upload limits
MAX_DURATION_SECONDS = 7 * 60  # 7 minutes

ALLOWED_CONTENT_TYPES = {
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/ogg",
    "audio/webm",
    "audio/flac",
    "audio/x-flac",
    "audio/aac",
    "audio/mp4",
    "audio/x-m4a",
    "audio/m4a",
}

# Video configuration
DEFAULT_VIDEO_FPS = 24
DEFAULT_CLIP_FPS = 8
GENERATOR_FPS = 8

# Beat alignment
ACCEPTABLE_ALIGNMENT = 0.1  # 100ms acceptable drift

# Replicate models
WHISPER_MODEL = "openai/whisper:8099696689d249cf8b122d833c36ac3f75505c666a395ca40ef26f68e7d3d16e"
VIDEO_MODEL = "minimax/hailuo-2.3"

# Polling configuration
DEFAULT_MAX_POLL_ATTEMPTS = 180
DEFAULT_POLL_INTERVAL_SEC = 5.0

