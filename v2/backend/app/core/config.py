"""Application configuration using Pydantic Settings."""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from pydantic import AnyUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Find backend directory (where .env file is located)
# This file is at v2/backend/app/core/config.py, so go up 3 levels to v2/
BACKEND_DIR = Path(__file__).parent.parent.parent.parent
ENV_FILE = (BACKEND_DIR / ".env").resolve()  # Use absolute path
ENV_FILE_PATH: Optional[str]
if ENV_FILE.exists() and os.access(ENV_FILE, os.R_OK):
    ENV_FILE_PATH = str(ENV_FILE)
else:
    ENV_FILE_PATH = None


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Project metadata
    project_name: str = "VibeCraft v2 API"
    project_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    # Server configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_log_level: str = Field(default="info", alias="API_LOG_LEVEL")
    environment: str = Field(default="development", alias="ENVIRONMENT")

    # Database configuration
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/vibecraft",
        alias="DATABASE_URL",
    )

    # Redis configuration
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    rq_worker_queue: str = Field(default="ai_music_video", alias="RQ_WORKER_QUEUE")

    # AWS S3 configuration
    s3_bucket_name: str = Field(default="vibecraft-videos", alias="S3_BUCKET_NAME")
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(
        default=None, alias="AWS_SECRET_ACCESS_KEY"
    )
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    cloudfront_domain: Optional[str] = Field(
        default=None, alias="CLOUDFRONT_DOMAIN"
    )

    # External API keys
    replicate_api_token: Optional[str] = Field(
        default=None, alias="REPLICATE_API_TOKEN"
    )

    # Security
    secret_key: str = Field(
        default="change-me-in-production", alias="SECRET_KEY"
    )  # For JWT signing

    # CORS configuration
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        alias="CORS_ORIGINS",
    )

    # FFmpeg configuration
    ffmpeg_bin: str = Field(default="ffmpeg", alias="FFMPEG_BIN")

    # Librosa cache directory
    librosa_cache_dir: str = Field(default=".cache/librosa", alias="LIBROSA_CACHE_DIR")

    @field_validator(
        "aws_access_key_id",
        "aws_secret_access_key",
        "cloudfront_domain",
        "replicate_api_token",
        mode="before",
    )
    @classmethod
    def empty_string_to_none(cls, value: Any) -> Any:
        """Convert empty strings to None for optional fields."""
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return value
        return []


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()  # type: ignore[call-arg]

