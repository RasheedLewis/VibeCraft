"""Database configuration and session management."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

settings = get_settings()

# Disable GSS/Kerberos authentication to prevent crashes in forked processes (RQ workers)
# This is a known issue on macOS where GSS initialization crashes during fork
database_url = settings.database_url
connect_args = {}
if database_url.startswith("postgresql://") or database_url.startswith("postgresql+psycopg://"):
    # Convert postgresql:// to postgresql+psycopg:// for psycopg3
    if database_url.startswith("postgresql://") and not database_url.startswith("postgresql+psycopg://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    # Disable GSS via connection string and connect_args
    if "gssencmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}gssencmode=disable"
    # Also pass via connect_args for psycopg3
    connect_args["gssencmode"] = "disable"

engine = create_engine(database_url, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Initialize database by creating all tables."""
    SQLModel.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    """Dependency for FastAPI to get database session."""
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def check_db_connection() -> bool:
    """Check if database connection is working."""
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False

