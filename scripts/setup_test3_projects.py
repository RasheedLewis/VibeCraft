#!/usr/bin/env python3
"""Setup test3@example.com with 5 projects for testing 5-project limit."""

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, select, create_engine

from app.core.config import get_settings
from app.models import Song, SongAnalysisRecord, User


def get_database_url():
    """Get database URL, allowing override via environment variable."""
    settings = get_settings()
    return os.getenv("DATABASE_URL_OVERRIDE") or settings.database_url


def main():
    db_url = get_database_url()
    engine = create_engine(db_url)
    
    with Session(engine) as session:
        # Find test3@example.com user
        user_stmt = select(User).where(User.email == "test3@example.com")
        user = session.exec(user_stmt).first()
        
        if not user:
            print("❌ User test3@example.com not found")
            return
        
        print(f"✅ Found user: {user.email} (id: {user.id})")
        
        # Find their first song
        song_stmt = select(Song).where(Song.user_id == user.id).order_by(Song.created_at.desc())
        original_song = session.exec(song_stmt).first()
        
        if not original_song:
            print("❌ No songs found for test3@example.com")
            return
        
        print(f"✅ Found song: {original_song.id} - {original_song.title}")
        
        # Create or update analysis record for the original song
        analysis_stmt = select(SongAnalysisRecord).where(SongAnalysisRecord.song_id == original_song.id)
        analysis_record = session.exec(analysis_stmt).first()
        
        # Create a basic analysis JSON if it doesn't exist
        if not analysis_record:
            # Create a minimal valid analysis JSON
            analysis_json = json.dumps({
                "durationSec": original_song.duration_sec or 30.0,
                "bpm": 120.0,
                "beatTimes": [0.0, 0.5, 1.0, 1.5, 2.0],
                "sections": [
                    {
                        "id": "section-1",
                        "type": "verse",
                        "startSec": 0.0,
                        "endSec": original_song.duration_sec or 30.0,
                        "confidence": 0.9,
                    }
                ],
                "moodPrimary": "energetic",
                "moodTags": ["energetic", "upbeat"],
                "moodVector": {
                    "energy": 0.8,
                    "valence": 0.7,
                    "danceability": 0.9,
                    "tension": 0.3,
                },
                "lyricsAvailable": False,
            })
            
            analysis_record = SongAnalysisRecord(
                song_id=original_song.id,
                analysis_json=analysis_json,
                bpm=120.0,
                duration_sec=original_song.duration_sec or 30.0,
            )
            session.add(analysis_record)
            session.commit()
            print(f"✅ Created analysis record for song {original_song.id}")
        else:
            print(f"✅ Analysis record already exists for song {original_song.id}")
        
        # Count existing songs
        existing_songs_stmt = select(Song).where(Song.user_id == user.id)
        existing_songs = session.exec(existing_songs_stmt).all()
        current_count = len(existing_songs)
        print(f"📊 Current song count: {current_count}")
        
        # Clone the song to reach 5 total
        songs_to_create = 5 - current_count
        
        if songs_to_create <= 0:
            print(f"✅ User already has {current_count} songs (>= 5)")
            return
        
        print(f"📝 Creating {songs_to_create} clone(s)...")
        
        for i in range(songs_to_create):
            new_song_id = uuid4()
            new_song = Song(
                id=new_song_id,
                user_id=user.id,
                title=f"{original_song.title}_clone_{i+1}",
                original_filename=f"{original_song.original_filename}_clone_{i+1}",
                original_file_size=original_song.original_file_size,
                original_content_type=original_song.original_content_type,
                original_s3_key=f"songs/{new_song_id}/original.mp3",
                processed_s3_key=original_song.processed_s3_key,
                processed_sample_rate=original_song.processed_sample_rate,
                waveform_json=original_song.waveform_json,
                duration_sec=original_song.duration_sec,
                description=original_song.description,
                attribution=original_song.attribution,
                video_type=original_song.video_type,
                character_consistency_enabled=original_song.character_consistency_enabled,
            )
            session.add(new_song)
            session.commit()
            session.refresh(new_song)
            
            # Create analysis record for the cloned song
            analysis_json = json.dumps({
                "durationSec": new_song.duration_sec or 30.0,
                "bpm": 120.0,
                "beatTimes": [0.0, 0.5, 1.0, 1.5, 2.0],
                "sections": [
                    {
                        "id": "section-1",
                        "type": "verse",
                        "startSec": 0.0,
                        "endSec": new_song.duration_sec or 30.0,
                        "confidence": 0.9,
                    }
                ],
                "moodPrimary": "energetic",
                "moodTags": ["energetic", "upbeat"],
                "moodVector": {
                    "energy": 0.8,
                    "valence": 0.7,
                    "danceability": 0.9,
                    "tension": 0.3,
                },
                "lyricsAvailable": False,
            })
            
            new_analysis = SongAnalysisRecord(
                song_id=new_song_id,
                analysis_json=analysis_json,
                bpm=120.0,
                duration_sec=new_song.duration_sec or 30.0,
            )
            session.add(new_analysis)
            session.commit()
            
            print(f"  ✅ Created clone {i+1}: {new_song_id} - {new_song.title}")
        
        # Verify final count
        final_songs_stmt = select(Song).where(Song.user_id == user.id)
        final_songs = session.exec(final_songs_stmt).all()
        final_count = len(final_songs)
        print(f"\n✅ Complete! User now has {final_count} songs with analysis")


if __name__ == "__main__":
    main()

