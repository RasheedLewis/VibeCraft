from collections.abc import Generator, Iterable
from contextlib import contextmanager

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.models import DEFAULT_USER_ID, User

settings = get_settings()
# Disable GSS/Kerberos authentication to prevent crashes in forked processes (RQ workers)
# This is a known issue on macOS where GSS initialization crashes during fork
database_url = settings.database_url
connect_args = {}
if database_url.startswith("postgresql"):
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
    "created_at",
    "updated_at",
}


def init_db() -> None:
    _ensure_song_schema()
    SQLModel.metadata.create_all(bind=engine)
    with Session(engine) as session:
        if not session.get(User, DEFAULT_USER_ID):
            session.add(
                User(
                    id=DEFAULT_USER_ID,
                    display_name="Default User",
                    email=None,
                )
            )
            session.commit()


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


def _get_column_names(columns: Iterable[dict[str, object]]) -> set[str]:
    return {str(column["name"]) for column in columns if "name" in column}

