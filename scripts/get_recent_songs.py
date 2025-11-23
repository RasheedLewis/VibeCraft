#!/usr/bin/env python3
"""Get recent songs from database."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.database import session_scope
from app.models.song import Song
from sqlmodel import select

with session_scope() as session:
    songs = session.exec(select(Song).order_by(Song.created_at.desc()).limit(5)).all()
    print("Recent songs:")
    for s in songs:
        print(f"  ID: {s.id}")
        print(f"    Created: {s.created_at}")
        print(f"    Has composed video: {bool(s.composed_video_s3_key)}")
        print()

