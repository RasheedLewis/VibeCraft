#!/usr/bin/env python3
"""Analyze a local song file directly (bypasses S3 and API)."""

import sys
import json
import tempfile
from pathlib import Path
from uuid import uuid4

# Add current directory to path (we're in backend/)
sys.path.insert(0, str(Path(__file__).parent))

from sqlmodel import Session
from app.core.database import engine
from app.models.song import Song
from app.models.analysis import SongAnalysisRecord
from app.schemas.analysis import SongAnalysis
import librosa
from app.services.genre_mood_analysis import compute_genre, compute_mood_features, compute_mood_tags
from app.services.lyric_extraction import extract_and_align_lyrics

# Import _detect_sections directly
from app.services.song_analysis import _detect_sections


def analyze_local_song(audio_path: Path) -> dict:
    """Analyze a local audio file."""
    print(f"🔍 Analyzing: {audio_path.name}")
    
    # Load audio
    print("   Loading audio...")
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    duration = float(librosa.get_duration(y=y, sr=sr))
    print(f"   Duration: {duration:.2f}s, Sample rate: {sr}Hz")
    
    # Beat tracking
    print("   Detecting beats...")
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    tempo_float = float(tempo) if hasattr(tempo, '__float__') else float(tempo[0]) if hasattr(tempo, '__len__') else 0.0
    beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
    beat_times = [round(time, 4) for time in beat_times]
    print(f"   BPM: {tempo_float:.1f}, Beats: {len(beat_times)}")
    
    # Section detection
    print("   Detecting sections...")
    sections = _detect_sections(y, sr, duration)
    print(f"   Sections: {len(sections)}")
    
    # Mood and genre
    print("   Computing mood and genre...")
    mood_vector = compute_mood_features(audio_path, tempo if tempo else None)
    primary_mood, mood_tags = compute_mood_tags(mood_vector)
    primary_genre, sub_genres, _ = compute_genre(audio_path, tempo if tempo else None, mood_vector)
    print(f"   Mood: {primary_mood}, Genre: {primary_genre}")
    
    # Lyrics
    print("   Extracting lyrics...")
    lyrics_available = False
    section_lyrics_models = []
    try:
        lyrics_available, aligned = extract_and_align_lyrics(audio_path, sections)
        section_lyrics_models = aligned
        print(f"   Lyrics: {'Available' if lyrics_available else 'Not available'}")
    except Exception as e:
        print(f"   Lyrics extraction failed: {e}")
        lyrics_available = False
    
    # Build analysis
    tempo_value = float(tempo) if hasattr(tempo, '__float__') else float(tempo[0]) if hasattr(tempo, '__len__') and len(tempo) > 0 else None
    analysis = SongAnalysis(
        durationSec=duration,
        bpm=tempo_value,
        beatTimes=beat_times,
        sections=sections,
        moodPrimary=primary_mood,
        moodTags=mood_tags,
        moodVector=mood_vector,
        primaryGenre=primary_genre,
        subGenres=sub_genres,
        lyricsAvailable=lyrics_available,
        sectionLyrics=section_lyrics_models,
    )
    
    return analysis.model_dump()


def create_song_record(audio_path: Path) -> str:
    """Create a song record in the database."""
    song_title = audio_path.stem or "Untitled Song"
    
    with Session(engine) as session:
        from app.models import DEFAULT_USER_ID
        song = Song(
            user_id=DEFAULT_USER_ID,
            title=song_title,
            original_filename=audio_path.name,
            original_file_size=audio_path.stat().st_size,
            original_content_type="audio/mpeg",
            duration_sec=0.0,  # Will be updated
            original_s3_key=f"local/{audio_path.name}",
            processed_s3_key=f"local/{audio_path.stem}.wav",
            processed_sample_rate=22050,
        )
        session.add(song)
        session.commit()
        session.refresh(song)
        return song.id


def save_analysis(song_id: str, analysis_dict: dict):
    """Save analysis to database."""
    with Session(engine) as session:
        from app.models.song import Song
        song = session.get(Song, song_id)
        if song:
            song.duration_sec = analysis_dict.get('durationSec', 0.0)
            session.add(song)
        
        analysis_json = json.dumps(analysis_dict)
        
        # Check if analysis exists
        from app.models.analysis import SongAnalysisRecord
        from sqlmodel import select
        statement = select(SongAnalysisRecord).where(SongAnalysisRecord.song_id == song_id)
        record = session.exec(statement).first()
        
        if record:
            record.analysis_json = analysis_json
            record.bpm = analysis_dict.get('bpm')
            record.duration_sec = analysis_dict.get('durationSec', 0.0)
        else:
            record = SongAnalysisRecord(
                song_id=song_id,
                analysis_json=analysis_json,
                bpm=analysis_dict.get('bpm'),
                duration_sec=analysis_dict.get('durationSec', 0.0),
            )
        
        session.add(record)
        session.commit()
        print(f"✅ Analysis saved to database")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_local_song.py <audio_file>")
        sys.exit(1)
    
    audio_path = Path(sys.argv[1])
    if not audio_path.exists():
        print(f"Error: File not found: {audio_path}")
        sys.exit(1)
    
    try:
        # Create song record
        print("📤 Creating song record...")
        song_id = create_song_record(audio_path)
        print(f"   Song ID: {song_id}")
        
        # Analyze
        analysis_dict = analyze_local_song(audio_path)
        
        # Save to database
        save_analysis(song_id, analysis_dict)
        
        # Print summary
        print("\n📊 Analysis Summary:")
        print(f"   BPM: {analysis_dict.get('bpm', 'N/A')}")
        print(f"   Duration: {analysis_dict.get('durationSec', 0):.2f}s")
        print(f"   Mood: {analysis_dict.get('moodPrimary', 'N/A')}")
        print(f"   Genre: {analysis_dict.get('primaryGenre', 'N/A')}")
        print(f"   Sections: {len(analysis_dict.get('sections', []))}")
        print(f"   Lyrics: {'Available' if analysis_dict.get('lyricsAvailable') else 'Not available'}")
        
        print(f"\n🎉 Done! Song ID: {song_id}")
        print(f"   You can now query prompts with:")
        print(f"   psql postgresql://postgres:postgres@127.0.0.1:5433/ai_music_video -f video-api-testing/get_prompt_and_lyrics_simple.sql")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

