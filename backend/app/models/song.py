from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Song(SQLModel, table=True):
    __tablename__ = "songs"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    audio_url: str = Field(max_length=1024)
    description: Optional[str] = Field(default=None)
    duration_sec: Optional[float] = Field(default=None)
    # Attribution (optional, for royalty-free music credits)
    attribution: Optional[str] = Field(default=None, max_length=512)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

