import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional, Protocol

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find backend directory (where .env file is located)
# This file is at backend/app/core/config.py, so go up 2 levels
BACKEND_DIR = Path(__file__).parent.parent.parent
ENV_FILE = (BACKEND_DIR / ".env").resolve()  # Use absolute path
ENV_FILE_PATH: Optional[str]
if ENV_FILE.exists() and os.access(ENV_FILE, os.R_OK):
    ENV_FILE_PATH = str(ENV_FILE)
else:
    ENV_FILE_PATH = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    project_name: str = "AI Music Video API"
    project_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_log_level: str = Field(default="info", alias="API_LOG_LEVEL")
    
    cors_origins: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins"
    )

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/ai_music_video",
        alias="DATABASE_URL",
    )

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    rq_worker_queue: str = Field(default="ai_music_video", alias="RQ_WORKER_QUEUE")

    s3_endpoint_url: Optional[AnyUrl] = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_bucket_name: str = Field(default="ai-music-video", alias="S3_BUCKET_NAME")
    s3_access_key_id: Optional[str] = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: Optional[str] = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    s3_region: Optional[str] = Field(default=None, alias="S3_REGION")

    audjust_base_url: Optional[AnyUrl] = Field(default=None, alias="AUDJUST_BASE_URL")
    audjust_api_key: Optional[str] = Field(default=None, alias="AUDJUST_API_KEY")
    audjust_upload_path: str = Field(default="/upload", alias="AUDJUST_UPLOAD_PATH")
    audjust_structure_path: str = Field(default="/structure", alias="AUDJUST_STRUCTURE_PATH")
    audjust_timeout_sec: float = Field(default=30.0, alias="AUDJUST_TIMEOUT_SEC")

    replicate_api_token: Optional[str] = Field(default=None, alias="REPLICATE_API_TOKEN")
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    whisper_api_token: Optional[str] = Field(default=None, alias="WHISPER_API_TOKEN")
    lyrics_api_key: Optional[str] = Field(default=None, alias="LYRICS_API_KEY")

    ffmpeg_bin: str = Field(default="ffmpeg", alias="FFMPEG_BIN")
    librosa_cache_dir: str = Field(default=".cache/librosa", alias="LIBROSA_CACHE_DIR")

    enable_sections: bool = Field(default=True, alias="ENABLE_SECTIONS")

    @field_validator(
        "s3_endpoint_url",
        "s3_access_key_id",
        "s3_secret_access_key",
        "s3_region",
        "replicate_api_token",
        "openai_api_key",
        "whisper_api_token",
        "lyrics_api_key",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        if isinstance(value, str) and not value.strip():
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


@lru_cache
def is_sections_enabled() -> bool:
    """Check if section-based generation is enabled."""
    return get_settings().enable_sections


class HasVideoType(Protocol):
    """Protocol for objects with video_type attribute."""

    video_type: str | None


def should_use_sections_for_song(song: HasVideoType | Any) -> bool:
    """Determine if sections should be used for a specific song.

    Args:
        song: Song model instance (or any object with video_type attribute)

    Returns:
        True if sections should be used, False otherwise
    """
    from app.core.constants import VIDEO_TYPE_FULL_LENGTH
    
    video_type = getattr(song, 'video_type', None)
    if video_type:
        return video_type == VIDEO_TYPE_FULL_LENGTH

    # Default to False if video_type is not set
    return False


class BeatEffectConfig(BaseSettings):
    """Configuration for beat-synced visual effects."""
    
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )
    
    enabled: bool = Field(default=True, alias="BEAT_EFFECTS_ENABLED")
    effect_type: str = Field(default="flash", alias="BEAT_EFFECT_TYPE")  # flash, color_burst, zoom_pulse, glitch, brightness_pulse
    flash_intensity: float = Field(default=50.0, alias="BEAT_FLASH_INTENSITY")  # 0-255 pixel value increase
    flash_color: str = Field(default="white", alias="BEAT_FLASH_COLOR")  # white, red, blue, etc.
    color_burst_hue: int = Field(default=0, alias="BEAT_COLOR_BURST_HUE")  # 0-360 degrees
    color_burst_saturation: float = Field(default=1.5, alias="BEAT_COLOR_BURST_SATURATION")
    color_burst_brightness: float = Field(default=0.1, alias="BEAT_COLOR_BURST_BRIGHTNESS")
    zoom_pulse_amount: float = Field(default=1.05, alias="BEAT_ZOOM_PULSE_AMOUNT")  # 1.0 = no zoom, 1.05 = 5% zoom
    zoom_pulse_duration_frames: int = Field(default=3, alias="BEAT_ZOOM_PULSE_DURATION_FRAMES")
    glitch_intensity: float = Field(default=0.3, alias="BEAT_GLITCH_INTENSITY")  # 0.0-1.0
    brightness_pulse_amount: float = Field(default=0.15, alias="BEAT_BRIGHTNESS_PULSE_AMOUNT")  # 0.0-1.0
    tolerance_ms: float = Field(default=20.0, alias="BEAT_EFFECT_TOLERANCE_MS")  # Tolerance window in milliseconds
    
    # Test mode configuration
    test_mode_enabled: bool = Field(
        default=False,
        alias="BEAT_EFFECT_TEST_MODE",
        description="Enable test mode for exaggerated effects"
    )  # Enable test mode for exaggerated effects
    
    @field_validator("test_mode_enabled", mode="before")
    @classmethod
    def parse_test_mode(cls, v: Any) -> bool:
        """Parse test mode from various input types, handling empty strings."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            v = v.strip().lower()
            if v in ("", "false", "0", "no", "off"):
                return False
            if v in ("true", "1", "yes", "on"):
                return True
        return False
    
    test_mode_tolerance_multiplier: float = 3.0  # Test mode tolerance multiplier (150ms vs 50ms)
    test_mode_flash_intensity_multiplier: float = 3.0  # Test mode flash intensity multiplier
    test_mode_glitch_intensity: float = 0.8  # Test mode glitch intensity
    test_mode_color_burst_saturation: float = 2.0  # Test mode color burst saturation
    test_mode_color_burst_brightness: float = 0.2  # Test mode color burst brightness
    test_mode_brightness_pulse: float = 0.3  # Test mode brightness pulse
    test_mode_zoom_pulse: float = 1.15  # Test mode zoom pulse


@lru_cache
def get_beat_effect_config() -> BeatEffectConfig:
    """Get beat effect configuration."""
    return BeatEffectConfig()  # type: ignore[call-arg]

