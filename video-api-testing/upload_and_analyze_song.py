#!/usr/bin/env python3
"""Upload and analyze a song file."""

import sys
import time
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from uuid import UUID
from sqlmodel import Session, select
from app.core.database import engine
from app.models.song import Song
from app.models.analysis import AnalysisJob
from app.services.song_analysis import enqueue_song_analysis, get_job_status
from app.services.audio_preprocessing import preprocess_audio


def upload_song(audio_path: Path) -> UUID:
    """Upload a song file and return the song ID."""
    print(f"📤 Uploading: {audio_path.name}")
    
    # Read file
    with open(audio_path, "rb") as f:
        file_bytes = f.read()
    
    # Preprocess
    print("🔄 Preprocessing audio...")
    suffix = audio_path.suffix or ".mp3"
    preprocess_result = preprocess_audio(file_bytes=file_bytes, original_suffix=suffix)
    
    print(f"   Duration: {preprocess_result.duration_sec:.2f}s")
    print(f"   Sample rate: {preprocess_result.sample_rate}Hz")
    
    # Create song record
    song_title = audio_path.stem or "Untitled Song"
    
    with Session(engine) as session:
        from app.core.config import get_settings
        settings = get_settings()
        
        # For local testing, we'll skip S3 upload and just store locally
        # But we need the song record
        song = Song(
            user_id="test-user",  # Default user
            title=song_title,
            original_filename=audio_path.name,
            original_file_size=len(file_bytes),
            original_content_type="audio/mpeg",
            duration_sec=preprocess_result.duration_sec,
            original_s3_key=f"local/{audio_path.name}",  # Placeholder
            processed_s3_key=f"local/processed_{audio_path.stem}.wav",  # Placeholder
            processed_sample_rate=preprocess_result.sample_rate,
            waveform_json=preprocess_result.waveform_json,
        )
        session.add(song)
        session.commit()
        session.refresh(song)
        
        print(f"✅ Song uploaded: {song.id}")
        print(f"   Title: {song.title}")
        return song.id


def analyze_song(song_id: UUID) -> dict:
    """Analyze a song and wait for completion."""
    print(f"\n🔍 Starting analysis for song {song_id}...")
    
    # Enqueue analysis
    job_response = enqueue_song_analysis(song_id)
    job_id = job_response.job_id
    print(f"   Job ID: {job_id}")
    
    # Poll for completion
    max_wait = 300  # 5 minutes
    start_time = time.time()
    poll_interval = 2.0
    
    while time.time() - start_time < max_wait:
        status_response = get_job_status(job_id)
        
        print(f"   Status: {status_response.status} (progress: {status_response.progress}%)", end="\r")
        
        if status_response.status == "completed":
            print(f"\n✅ Analysis complete!")
            return status_response.result or {}
        elif status_response.status == "failed":
            error = status_response.error or "Unknown error"
            print(f"\n❌ Analysis failed: {error}")
            return {}
        
        time.sleep(poll_interval)
    
    print(f"\n⏱️  Timeout after {max_wait}s")
    return {}


def main():
    if len(sys.argv) < 2:
        print("Usage: python upload_and_analyze_song.py <audio_file>")
        sys.exit(1)
    
    audio_path = Path(sys.argv[1])
    if not audio_path.exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)
    
    try:
        # Upload
        song_id = upload_song(audio_path)
        
        # Analyze
        result = analyze_song(song_id)
        
        if result:
            print("\n📊 Analysis Results:")
            print(f"   BPM: {result.get('bpm', 'N/A')}")
            print(f"   Duration: {result.get('durationSec', 'N/A')}s")
            print(f"   Mood: {result.get('moodPrimary', 'N/A')}")
            print(f"   Genre: {result.get('primaryGenre', 'N/A')}")
            print(f"   Lyrics Available: {result.get('lyricsAvailable', False)}")
        
        print(f"\n🎉 Done! Song ID: {song_id}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

