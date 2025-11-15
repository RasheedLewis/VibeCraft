from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings
from app.models import DEFAULT_USER_ID, User

settings = get_settings()
engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
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

