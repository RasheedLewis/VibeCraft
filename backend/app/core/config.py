from functools import lru_cache
from typing import Optional

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    project_name: str = "AI Music Video API"
    project_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_log_level: str = Field(default="info", alias="API_LOG_LEVEL")

    database_url: str = Field(
        default="sqlite:///./app.db",
        alias="DATABASE_URL",
    )

    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    rq_worker_queue: str = Field(default="ai_music_video", alias="RQ_WORKER_QUEUE")

    s3_endpoint_url: Optional[HttpUrl] = Field(default=None, alias="S3_ENDPOINT_URL")
    s3_bucket_name: str = Field(default="ai-music-video", alias="S3_BUCKET_NAME")
    s3_access_key_id: Optional[str] = Field(default=None, alias="S3_ACCESS_KEY_ID")
    s3_secret_access_key: Optional[str] = Field(default=None, alias="S3_SECRET_ACCESS_KEY")
    s3_region: Optional[str] = Field(default=None, alias="S3_REGION")

    replicate_api_token: Optional[str] = Field(default=None, alias="REPLICATE_API_TOKEN")
    whisper_api_token: Optional[str] = Field(default=None, alias="WHISPER_API_TOKEN")
    lyrics_api_key: Optional[str] = Field(default=None, alias="LYRICS_API_KEY")

    ffmpeg_bin: str = Field(default="ffmpeg", alias="FFMPEG_BIN")
    librosa_cache_dir: str = Field(default=".cache/librosa", alias="LIBROSA_CACHE_DIR")

    @field_validator("s3_endpoint_url", mode="before")
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty strings to None for optional URL fields."""
        if v == "" or v is None:
            return None
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

