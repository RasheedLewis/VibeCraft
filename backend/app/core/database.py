from collections.abc import Generator, Iterable
from contextlib import contextmanager

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.models import DEFAULT_USER_ID, SongClip, User

settings = get_settings()
# Disable GSS/Kerberos authentication to prevent crashes in forked processes (RQ workers)
# This is a known issue on macOS where GSS initialization crashes during fork
database_url = settings.database_url
connect_args = {}
if database_url.startswith("postgresql"):
    # Convert postgresql:// to postgresql+psycopg:// to use psycopg3 driver
    if database_url.startswith("postgresql://") and "+psycopg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    # Disable GSS via connection string and connect_args
    if "gssencmode" not in database_url:
        separator = "&" if "?" in database_url else "?"
        database_url = f"{database_url}{separator}gssencmode=disable"
    # Also pass via connect_args for psycopg3
    connect_args["gssencmode"] = "disable"
engine = create_engine(database_url, echo=False, connect_args=connect_args)

EXPECTED_SONG_COLUMNS: set[str] = {
    "id",
    "user_id",
    "title",
    "original_filename",
    "original_file_size",
    "original_content_type",
    "original_s3_key",
    "processed_s3_key",
    "processed_sample_rate",
    "waveform_json",
    "duration_sec",
    "description",
    "attribution",
        "composed_video_s3_key",
        "composed_video_poster_s3_key",
        "composed_video_duration_sec",
        "composed_video_fps",
    "created_at",
    "updated_at",
}

EXPECTED_SONG_CLIP_COLUMNS: set[str] = {
    "id",
    "song_id",
    "clip_index",
    "start_sec",
    "end_sec",
    "duration_sec",
    "start_beat_index",
    "end_beat_index",
    "num_frames",
    "fps",
    "status",
    "source",
    "video_url",
    "prompt",
    "style_seed",
    "rq_job_id",
    "replicate_job_id",
    "error",
    "created_at",
    "updated_at",
}


def init_db() -> None:
    _ensure_song_schema()
    _ensure_song_clip_schema()
    SQLModel.metadata.create_all(bind=engine)
    
    # Try to create default user, but handle missing columns gracefully
    # This allows the app to start even if migrations haven't been run yet
    try:
        with Session(engine) as session:
            # Use raw SQL to check if user exists to avoid model column issues
            from sqlalchemy import text
            result = session.execute(
                text("SELECT id FROM users WHERE id = :user_id"),
                {"user_id": str(DEFAULT_USER_ID)}
            )
            if not result.fetchone():
                # Insert using raw SQL to avoid model column issues
                session.execute(
                    text("INSERT INTO users (id, display_name, email) VALUES (:id, :display_name, :email)"),
                    {
                        "id": str(DEFAULT_USER_ID),
                        "display_name": "Default User",
                        "email": None
                    }
                )
                session.commit()
    except Exception as e:
        # If this fails (e.g., missing columns), log but don't crash
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not create default user (this is OK if migrations haven't run): {e}")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


def _ensure_song_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if "songs" not in table_names:
        return

    column_names = _get_column_names(inspector.get_columns("songs"))
    if EXPECTED_SONG_COLUMNS.issubset(column_names):
        return

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS songs CASCADE"))


def _ensure_song_clip_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    if SongClip.__tablename__ not in table_names:
        return

    column_names = _get_column_names(inspector.get_columns(SongClip.__tablename__))
    if EXPECTED_SONG_CLIP_COLUMNS.issubset(column_names):
        return

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS song_clips CASCADE"))


def _get_column_names(columns: Iterable[dict[str, object]]) -> set[str]:
    return {str(column["name"]) for column in columns if "name" in column}

