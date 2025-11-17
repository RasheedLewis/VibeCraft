"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes_auth import router as auth_router
from app.api.v1.routes_songs import router as songs_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    settings = get_settings()

    def validate_environment() -> None:
        """Validate required environment variables on startup.

        Raises:
            ValueError: If required environment variables are missing.
        """
        errors = []

        # Required for production
        if settings.environment == "production":
            if not settings.aws_access_key_id:
                errors.append("AWS_ACCESS_KEY_ID is required in production")
            if not settings.aws_secret_access_key:
                errors.append("AWS_SECRET_ACCESS_KEY is required in production")
            if not settings.replicate_api_token:
                errors.append("REPLICATE_API_TOKEN is required in production")
            if settings.secret_key == "change-me-in-production":
                errors.append("SECRET_KEY must be changed from default in production")

        # Warn about missing optional variables
        if not settings.replicate_api_token:
            errors.append(
                "REPLICATE_API_TOKEN is not set (video generation will not work)"
            )

        if errors:
            error_msg = "Environment validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            if settings.environment == "production":
                raise ValueError(error_msg)
            # In development, just log warnings
            import logging

            logger = logging.getLogger(__name__)
            for error in errors:
                logger.warning(error)

    # Validate environment variables
    validate_environment()

    # Initialize database (handle connection errors gracefully)
    try:
        init_db()
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("Server will start but database operations will fail until database is available")

    # Register routers
    app.include_router(auth_router, prefix=f"{settings.api_v1_prefix}/auth", tags=["auth"])
    app.include_router(songs_router, prefix=f"{settings.api_v1_prefix}/songs", tags=["songs"])

    yield

    # Shutdown (if needed in the future)
    pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    configure_logging(settings.api_log_level)

    app = FastAPI(
        title=settings.project_name,
        version=settings.project_version,
        description="VibeCraft v2 - AI Music Video Generation API",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint."""
        return {"status": "ok"}

    return app


app = create_app()
