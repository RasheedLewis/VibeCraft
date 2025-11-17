"""Structured logging configuration."""

from logging.config import dictConfig


def configure_logging(level: str = "info") -> None:
    """Configure application logging.

    Args:
        level: Log level (debug, info, warning, error, critical)
    """
    log_level = level.upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "structured": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "structured",
                    "level": log_level,
                }
            },
            "root": {
                "handlers": ["console"],
                "level": log_level,
            },
            "loggers": {
                # Reduce noise from third-party libraries
                "sqlalchemy.engine": {
                    "level": "WARNING",
                },
                "uvicorn.access": {
                    "level": "INFO",
                },
            },
        }
    )

