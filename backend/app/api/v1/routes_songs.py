from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.models.song import Song
from app.schemas.song import SongCreate, SongRead

router = APIRouter()


@router.get("/", response_model=List[SongRead], summary="List songs")
def list_songs(db: Session = Depends(get_db)) -> List[Song]:
    statement = select(Song).order_by(Song.created_at.desc())
    return db.exec(statement).all()


@router.post("/", response_model=SongRead, status_code=status.HTTP_201_CREATED, summary="Create song")
def create_song(payload: SongCreate, db: Session = Depends(get_db)) -> Song:
    song = Song(**payload.model_dump())
    db.add(song)
    db.commit()
    db.refresh(song)
    return song


@router.get("/{song_id}", response_model=SongRead, summary="Get song")
def get_song(song_id: int, db: Session = Depends(get_db)) -> Song:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    return song

