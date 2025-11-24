import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging import configure_logging
from app.core.rate_limiting import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    init_db()
    yield
    # Shutdown (if needed in the future)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.api_log_level)

    app = FastAPI(
        title=settings.project_name,
        version=settings.project_version,
        lifespan=lifespan,
    )

    # Parse CORS origins from comma-separated string
    # Strip quotes that might be included in env var value
    import logging
    logger = logging.getLogger(__name__)
    
    # Get raw value for debugging
    raw_cors_origins = os.getenv("CORS_ORIGINS", settings.cors_origins)
    logger.info(f"Raw CORS_ORIGINS env var: {repr(raw_cors_origins)}")
    logger.info(f"Settings cors_origins value: {repr(settings.cors_origins)}")
    
    cors_origins = [
        origin.strip().strip('"').strip("'")
        for origin in settings.cors_origins.split(",") 
        if origin.strip()
    ]
    
    # Log CORS configuration for debugging
    logger.info(f"Parsed CORS origins: {cors_origins}")
    if not cors_origins:
        logger.error("ERROR: No CORS origins configured! CORS will not work.")
        logger.error("Please set CORS_ORIGINS environment variable in Railway.")
    
    # CORS middleware must be added BEFORE rate limiting to handle OPTIONS preflight requests
    # Note: If cors_origins is empty, CORS won't work. This is intentional - we need explicit origins.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add rate limiting middleware (after CORS so OPTIONS requests pass through)
    app.add_middleware(RateLimitMiddleware)

    @app.get("/healthz", tags=["health"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}
    
    @app.get("/debug/cors", tags=["debug"])
    async def debug_cors() -> dict:
        """Debug endpoint to check CORS configuration."""
        return {
            "cors_origins": cors_origins,
            "raw_env_var": os.getenv("CORS_ORIGINS", "NOT SET"),
            "settings_value": settings.cors_origins,
        }

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()

