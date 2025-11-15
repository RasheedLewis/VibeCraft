from collections.abc import Generator

from collections.abc import Iterable

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.models import DEFAULT_USER_ID, User, Song

settings = get_settings()
engine = create_engine(settings.database_url, echo=False)

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

