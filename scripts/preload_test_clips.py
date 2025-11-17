#!/usr/bin/env python3
"""Pre-load test clips into the database for testing composition button.

This script uploads local clip files to S3 and marks them as completed in the database,
allowing you to test the composition button without waiting for clip generation.

The script automatically handles prerequisites:
- Automatically uses backend/venv/bin/python (no need to activate venv manually)
- Checks AWS credentials and bucket accessibility
- Finds song by ID or lists available songs
- Plans clips if they don't exist
- Creates minimal analysis if needed
- Checks if clips already exist (skips upload unless --force)
- Starts backend API, RQ worker, and frontend servers
- Opens browser to http://localhost:5173?songId=<id>

Usage:
    # List available songs
    python scripts/preload_test_clips.py --list-songs

    # Upload clips from Desktop (default names) - auto-detects most recent song
    python scripts/preload_test_clips.py

    # Use clips from samples directory (auto-detects most recent song)
    python scripts/preload_test_clips.py --samples

    # Specify a song ID explicitly
    python scripts/preload_test_clips.py --song-id <song_id>

    # Upload specific clip files
    python scripts/preload_test_clips.py --song-id <song_id> \
        --clips ~/Desktop/clip1.mp4 ~/Desktop/clip2.mp4 ~/Desktop/clip3.mp4 ~/Desktop/clip4.mp4

    # Auto-detect number of clips from files provided
    python scripts/preload_test_clips.py --song-id <song_id> --clips ~/Desktop/clip*.mp4

    # Re-upload clips even if they already exist
    python scripts/preload_test_clips.py --song-id <song_id> --force

    # Delete existing clips before uploading new ones
    python scripts/preload_test_clips.py --song-id <song_id> --cleanup

Note: The script will automatically start servers in the background and open your browser.
      Servers will continue running after the script exits.
      If clips already exist with videos, the script will skip upload unless --force is used.
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional
from uuid import UUID

# Detect and use virtual environment
project_root = Path(__file__).parent.parent
venv_python = project_root / "backend" / "venv" / "bin" / "python"

if venv_python.exists():
    # If we're not already using the venv Python, restart with it
    if sys.executable != str(venv_python):
        # Re-execute with venv Python
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
else:
    print("Warning: Virtual environment not found at backend/venv")
    print("  Attempting to continue with current Python interpreter...")

# Add backend to path
sys.path.insert(0, str(project_root / "backend"))

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

from app.core.config import get_settings
from app.core.database import session_scope
from app.models.analysis import SongAnalysisRecord
from app.models.clip import SongClip
from app.models.song import Song
from app.schemas.analysis import MoodVector, SongAnalysis
from app.services.clip_planning import (
    ClipPlanningError,
    plan_beat_aligned_clips,
    persist_clip_plans,
)
from app.services.song_analysis import get_latest_analysis
from app.services.storage import generate_presigned_get_url, upload_bytes_to_s3
from sqlmodel import select


def check_aws_credentials_and_bucket() -> tuple[str, bool]:
    """Check AWS credentials from config files and bucket accessibility.
    
    Returns:
        Tuple of (bucket_name, is_accessible)
    """
    # Check for AWS config files
    aws_dir = Path.home() / ".aws"
    credentials_file = aws_dir / "credentials"
    config_file = aws_dir / "config"
    
    has_credentials_file = credentials_file.exists()
    has_config_file = config_file.exists()
    
    if not has_credentials_file and not has_config_file:
        print("Error: AWS credentials not found")
        print("  Expected location: ~/.aws/credentials or ~/.aws/config")
        print("  Run 'aws configure' to set up credentials")
        return "", False
    
    # Try to get credentials using boto3 (will use AWS config files)
    try:
        # boto3 will automatically use ~/.aws/credentials and ~/.aws/config
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if not credentials:
            print("Error: AWS credentials not found in config files")
            print("  Run 'aws configure' to set up credentials")
            return "", False
        
        print("✓ AWS credentials found in config files")
    except (NoCredentialsError, ProfileNotFound) as e:
        print(f"Error: Failed to load AWS credentials: {e}")
        print("  Run 'aws configure' to set up credentials")
        return "", False
    
    # Get bucket name from settings
    settings = get_settings()
    bucket_name = settings.s3_bucket_name
    
    if not bucket_name:
        print("Error: S3 bucket name not configured")
        print("  Set S3_BUCKET_NAME in environment or .env file")
        return "", False
    
    print(f"  Bucket: {bucket_name}")
    
    # Test bucket accessibility
    try:
        s3_client = boto3.client("s3", region_name=settings.s3_region)
        s3_client.head_bucket(Bucket=bucket_name)
        print(f"✓ Bucket '{bucket_name}' is accessible")
        return bucket_name, True
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "404":
            print(f"Error: Bucket '{bucket_name}' does not exist")
        elif error_code == "403":
            print(f"Error: Access denied to bucket '{bucket_name}'")
        else:
            print(f"Error: Cannot access bucket '{bucket_name}': {e}")
        return bucket_name, False
    except Exception as e:
        print(f"Error: Failed to check bucket accessibility: {e}")
        return bucket_name, False


def wait_for_backend(max_wait_seconds: int = 30, check_interval: float = 0.5) -> bool:
    """Wait for backend to be ready by polling the health endpoint.
    
    Returns:
        True if backend is ready, False if timeout
    """
    import time
    import urllib.request
    import urllib.error
    
    backend_url = "http://localhost:8000/healthz"
    start_time = time.time()
    
    print("  Waiting for backend to be ready...", end="", flush=True)
    
    while time.time() - start_time < max_wait_seconds:
        try:
            with urllib.request.urlopen(backend_url, timeout=1) as response:
                if response.getcode() == 200:
                    print(" ✓")
                    return True
        except (urllib.error.URLError, OSError, TimeoutError):
            # Backend not ready yet, continue waiting
            pass
        
        time.sleep(check_interval)
        print(".", end="", flush=True)
    
    print(" ✗")
    return False


def start_servers_and_open_browser(song_id: Optional[UUID] = None) -> None:
    """Start backend, RQ worker, and frontend servers, then open browser."""
    import time
    import webbrowser
    from subprocess import Popen
    
    project_root = Path(__file__).parent.parent
    venv_python = project_root / "backend" / "venv" / "bin" / "python"
    venv_bin = project_root / "backend" / "venv" / "bin"
    
    if not venv_python.exists():
        print("Error: Virtual environment not found at backend/venv")
        print("  Please set up the backend virtual environment first")
        return
    
    print("\nStarting backend API...")
    backend_process = Popen(
        [str(venv_python), "-m", "uvicorn", "app.main:app", "--reload"],
        cwd=project_root / "backend",
        stdout=None,  # Let output go to terminal
        stderr=None,  # Let errors go to terminal
    )
    
    # Wait for backend to be ready
    if not wait_for_backend():
        print("\nError: Backend failed to start within 30 seconds")
        print("  Please check backend logs for errors")
        return
    
    print("Starting RQ worker...")
    print("  Note: RQ worker logs will appear below")
    print("  " + "-" * 56)
    worker_process = Popen(
        [str(venv_bin / "rq"), "worker", "ai_music_video", "--verbose"],
        cwd=project_root / "backend",
        env={**os.environ, "OBJC_DISABLE_INITIALIZE_FORK_SAFETY": "YES"},
        stdout=None,  # Let output go to terminal
        stderr=None,  # Let errors go to terminal
    )
    time.sleep(1)
    
    print("Starting frontend dev server...")
    frontend_process = Popen(
        ["npm", "run", "dev", "--", "--host"],
        cwd=project_root / "frontend",
        stdout=None,  # Let output go to terminal
        stderr=None,  # Let errors go to terminal
    )
    time.sleep(3)  # Give frontend time to start
    
    print("\n" + "="*60)
    print("✓ All servers started!")
    print("="*60)
    print("  Backend API: http://localhost:8000")
    print("  Frontend:    http://localhost:5173")
    print("\nOpening browser...")
    
    # Open browser to frontend with song ID if provided
    url = "http://localhost:5173"
    if song_id:
        url = f"{url}?songId={song_id}"
    
    webbrowser.open(url)
    print(f"\nOpened: {url}")
    
    print("\n" + "="*60)
    print("Servers are running in the background.")
    print("="*60)
    print("\n📋 Logs:")
    print("  - Backend API: Check the terminal output above")
    print("  - RQ Worker:   Check the terminal output above (look for 'INFO' messages)")
    print("  - Frontend:    Check the terminal output above")
    print("\n💡 Tip: Watch for RQ worker logs like:")
    print("     'INFO - Enqueued SongClip composition job...'")
    print("     'INFO - SongClip composition failed...' (if errors occur)")
    print("\n⚠️  Press Ctrl+C to stop all servers (or close this terminal)")
    print("   Note: The servers will continue running after this script exits.")
    print("         To stop them, run: make stop")


def check_song_audio_in_s3(song: Song, song_id: UUID) -> tuple[bool, Optional[str]]:
    """Check if song has audio in S3.
    
    Returns:
        Tuple of (has_audio_in_s3, actual_s3_key_if_exists)
    """
    settings = get_settings()
    from app.services.storage import check_s3_object_exists
    
    # Check the stored S3 key first (if it's valid, not a local path)
    audio_key = song.processed_s3_key or song.original_s3_key
    if audio_key and not audio_key.startswith("local/"):
        if check_s3_object_exists(bucket_name=settings.s3_bucket_name, key=audio_key):
            return True, audio_key
    
    # Try common S3 key patterns
    possible_keys = [
        f"songs/{song_id}/original.wav",
        f"songs/{song_id}/original.mp3",
        f"songs/{song_id}/processed.wav",
        f"songs/{song_id}/processed.mp3",
    ]
    
    for key in possible_keys:
        if check_s3_object_exists(bucket_name=settings.s3_bucket_name, key=key):
            return True, key
    
    return False, None


def find_sample_audio_file() -> Optional[Path]:
    """Find a sample audio file to upload.
    
    Returns:
        Path to sample audio file, or None if not found
    """
    project_root = Path(__file__).parent.parent
    sample_audio_paths = [
        project_root / "samples" / "audio" / "country" / "*.mp3",
        project_root / "samples" / "audio" / "country" / "*.wav",
        project_root / "samples" / "compTest" / "testAudio.mp3",
    ]
    
    for pattern in sample_audio_paths:
        matches = list(Path(pattern.parent).glob(pattern.name))
        if matches:
            return matches[0]
    
    return None


def upload_clip_to_s3(clip_path: Path, song_id: UUID, clip_index: int) -> str:
    """Upload a clip file to S3 and return the S3 key."""
    settings = get_settings()
    bucket = settings.s3_bucket_name

    # Read clip file
    clip_bytes = clip_path.read_bytes()

    # Generate S3 key
    s3_key = f"songs/{song_id}/clips/{clip_index:03d}.mp4"

    # Upload to S3
    upload_bytes_to_s3(
        bucket_name=bucket,
        key=s3_key,
        data=clip_bytes,
        content_type="video/mp4",
    )

    # Generate presigned URL (valid for 1 hour, but can be regenerated)
    video_url = generate_presigned_get_url(
        bucket_name=bucket,
        key=s3_key,
        expires_in=3600 * 24 * 7,  # 7 days
    )

    return video_url


def get_clip_duration(clip_path: Path) -> float:
    """Get duration of a video clip using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(clip_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except (subprocess.CalledProcessError, KeyError, ValueError, FileNotFoundError) as e:
        print(f"Warning: Could not get duration for {clip_path.name}: {e}")
        return 4.0  # Default duration


def ensure_song_analysis(song_id: UUID, song_duration: float) -> None:
    """Ensure song has analysis record, creating minimal one if needed."""
    with session_scope() as session:
        analysis = get_latest_analysis(song_id)
        if analysis:
            return

        print(f"  Creating minimal analysis for song...")
        # Create minimal analysis
        minimal_analysis = SongAnalysis(
            durationSec=song_duration,
            bpm=None,
            beatTimes=[],
            sections=[],
            moodPrimary="neutral",  # Required field, use default value
            moodTags=[],
            moodVector=MoodVector(
                energy=0.5,
                valence=0.5,
                danceability=0.5,
                tension=0.5,
            ),
            primaryGenre=None,
            subGenres=[],
            lyricsAvailable=False,
            sectionLyrics=[],
        )

        analysis_json = minimal_analysis.model_dump_json()
        record = SongAnalysisRecord(
            song_id=song_id,
            analysis_json=analysis_json,
            bpm=None,
            duration_sec=song_duration,
        )
        session.add(record)
        session.commit()


def plan_clips_if_needed(song_id: UUID, clip_count: int, song_duration: float) -> None:
    """Plan clips for song if they don't exist or if count doesn't match."""
    with session_scope() as session:
        statement = (
            select(SongClip)
            .where(SongClip.song_id == song_id)
            .order_by(SongClip.clip_index)  # type: ignore[arg-type]
        )
        existing_clips = session.exec(statement).all()

        # If clips exist and count matches, we're good
        if existing_clips and len(existing_clips) == clip_count:
            return
        
        # If clips exist but count doesn't match, delete them and re-plan
        if existing_clips:
            print(f"  Re-planning clips: existing count ({len(existing_clips)}) doesn't match required ({clip_count})")
            for clip in existing_clips:
                session.delete(clip)
            session.commit()
            print("  ✓ Deleted existing clips for re-planning")

        print(f"  Planning {clip_count} clips for song...")

        # Get or create analysis
        analysis = get_latest_analysis(song_id)
        if not analysis:
            ensure_song_analysis(song_id, song_duration)
            analysis = get_latest_analysis(song_id)

        if not analysis:
            raise RuntimeError("Failed to create analysis for song")

        # Plan clips with adaptive constraints based on duration
        # For pre-generated clips, we want to match the actual clip durations
        # Minimum: use the smallest clip duration, but at least 1 second
        # Maximum: use the largest clip duration, but allow some flexibility
        avg_clip_duration = song_duration / clip_count
        min_clip_sec = max(1.0, avg_clip_duration * 0.8)  # 80% of average
        min_clip_sec = min(min_clip_sec, 3.0)  # Cap at 3 seconds minimum
        max_clip_sec = max(min_clip_sec * 1.5, avg_clip_duration * 1.2)  # 120% of average
        max_clip_sec = min(max_clip_sec, 15.0)  # Cap at 15 seconds maximum
        
        print(f"  Planning {clip_count} clips for {song_duration:.1f}s total")
        print(f"  Using adaptive constraints: min={min_clip_sec:.1f}s, max={max_clip_sec:.1f}s per clip")
        
        # Plan clips
        try:
            plans = plan_beat_aligned_clips(
                duration_sec=song_duration,
                analysis=analysis,
                clip_count=clip_count,
                min_clip_sec=min_clip_sec,
                max_clip_sec=max_clip_sec,
                generator_fps=8,
            )
        except ClipPlanningError as e:
            raise RuntimeError(
                f"Failed to plan {clip_count} clips for song duration {song_duration:.1f}s: {e}. "
                f"Try providing fewer clip files or use a longer song."
            ) from e

        # Persist plans
        persist_clip_plans(
            song_id=song_id,
            plans=plans,
            fps=8,
            source="test",
            clear_existing=False,
        )

        print(f"  ✓ Planned {len(plans)} clips")


def list_songs() -> None:
    """List all available songs."""
    with session_scope() as session:
        # Use raw SQL to avoid schema issues with missing columns
        from sqlalchemy import text
        
        try:
            result = session.exec(
                text("SELECT id, title, duration_sec, created_at FROM songs ORDER BY created_at DESC")  # type: ignore[arg-type]
            )
            rows = result.all()
        except Exception as e:
            # Fallback: try with Song model (may fail if schema is outdated)
            try:
                statement = select(Song.id, Song.title, Song.duration_sec, Song.created_at).order_by(Song.created_at.desc())  # type: ignore[arg-type]
                rows = session.exec(statement).all()
            except Exception:
                print(f"Error: Could not query songs table: {e}")
                print("  The database schema may need to be updated")
                return

        if not rows:
            print("No songs found in database")
            return

        print(f"\nAvailable songs ({len(rows)}):")
        print("-" * 80)
        for row in rows:
            if isinstance(row, tuple):
                song_id, title, duration_sec, created_at = row
            else:
                song_id = row.id
                title = row.title if hasattr(row, 'title') else None
                duration_sec = row.duration_sec if hasattr(row, 'duration_sec') else None
                created_at = row.created_at if hasattr(row, 'created_at') else None
            
            duration_str = f"{duration_sec:.1f}s" if duration_sec else "unknown"
            print(f"  {song_id}")
            print(f"    Title: {title or '(untitled)'}")
            print(f"    Duration: {duration_str}")
            if created_at:
                print(f"    Created: {created_at}")
            print()


def check_existing_clips(song_id: UUID) -> tuple[list[SongClip], bool]:
    """Check if clips already exist and have valid video URLs.
    
    Returns:
        Tuple of (existing_clips, all_have_videos)
    """
    with session_scope() as session:
        statement = (
            select(SongClip)
            .where(SongClip.song_id == song_id)
            .order_by(SongClip.clip_index)  # type: ignore[arg-type]
        )
        existing_clips = session.exec(statement).all()
        
        if not existing_clips:
            return [], False
        
        # Check if clips have valid video URLs (not fake test URLs)
        def is_valid_video_url(url: str | None) -> bool:
            if not url:
                return False
            # Reject obviously fake test URLs
            if "example.com" in url or "localhost" in url:
                return False
            # Valid URLs should be S3 presigned URLs or actual S3 URLs
            return True
        
        all_have_videos = all(
            clip.status == "completed" and is_valid_video_url(clip.video_url)
            for clip in existing_clips
        )
        
        return existing_clips, all_have_videos


def delete_composed_video(song: Song, bucket_name: str) -> bool:
    """Delete composed video from S3 and clear database fields.
    
    This allows re-composition during testing.
    
    Returns:
        True if database fields were cleared (needs commit), False otherwise
    """
    settings = get_settings()
    s3_client = boto3.client("s3", region_name=settings.s3_region)
    
    # Delete video file from S3
    if song.composed_video_s3_key:
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=song.composed_video_s3_key)
            print(f"  ✓ Deleted composed video from S3: {song.composed_video_s3_key}")
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code not in ("404", "NoSuchKey"):
                print(f"  ⚠ Warning: Failed to delete video from S3: {error_code}")
    
    # Delete poster file from S3
    if song.composed_video_poster_s3_key:
        try:
            s3_client.delete_object(Bucket=bucket_name, Key=song.composed_video_poster_s3_key)
            print(f"  ✓ Deleted composed poster from S3: {song.composed_video_poster_s3_key}")
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code", "")
            if error_code not in ("404", "NoSuchKey"):
                print(f"  ⚠ Warning: Failed to delete poster from S3: {error_code}")
    
    # Clear database fields
    if song.composed_video_s3_key or song.composed_video_poster_s3_key:
        song.composed_video_s3_key = None
        song.composed_video_poster_s3_key = None
        song.composed_video_duration_sec = None
        song.composed_video_fps = None
        return True  # Indicate that database update is needed
    
    return False  # No composed video existed


def preload_clips(song_id: UUID, clip_paths: list[Path], force: bool = False, cleanup: bool = False) -> None:
    """Upload clips and update database records."""
    # Early checks: AWS credentials and bucket
    print("\nChecking AWS configuration...")
    bucket_name, bucket_accessible = check_aws_credentials_and_bucket()
    if not bucket_accessible:
        sys.exit(1)
    
    # Verify all clip files exist
    for clip_path in clip_paths:
        if not clip_path.exists():
            print(f"Error: Clip file not found: {clip_path}")
            sys.exit(1)

    with session_scope() as session:
        # Verify song exists
        song = session.get(Song, song_id)
        if not song:
            print(f"Error: Song {song_id} not found in database")
            print("\nUse --list-songs to see available songs")
            sys.exit(1)

        print(f"\nSong: {song.title or '(untitled)'} ({song_id})")

        # Delete existing composed video if it exists (to allow re-composition)
        if song.composed_video_s3_key or song.composed_video_poster_s3_key:
            print("  Deleting existing composed video...")
            needs_db_update = delete_composed_video(song, bucket_name)
            if needs_db_update:
                session.add(song)
                session.commit()
                print("  ✓ Cleared composed video fields in database")

        # Check for audio in S3 (required for composition)
        settings = get_settings()
        has_audio, actual_s3_key = check_song_audio_in_s3(song, song_id)
        
        if has_audio:
            print(f"  Audio: Available in S3 ({actual_s3_key})")
            # Update database if key was found but not stored correctly
            current_key = song.processed_s3_key or song.original_s3_key
            if current_key != actual_s3_key or current_key.startswith("local/"):
                print(f"  Updating database with correct S3 key...")
                song.original_s3_key = actual_s3_key
                if song.processed_s3_key and song.processed_s3_key.startswith("local/"):
                    song.processed_s3_key = None
                session.add(song)
                session.commit()
                print(f"  ✓ Updated S3 key in database")
        else:
            # Try to upload sample audio
            sample_audio_path = find_sample_audio_file()
            if sample_audio_path:
                print(f"  Audio: Not in S3, uploading sample audio from {sample_audio_path.name}...")
                try:
                    from app.services.storage import upload_bytes_to_s3
                    
                    # Read the audio file
                    audio_bytes = sample_audio_path.read_bytes()
                    audio_ext = sample_audio_path.suffix or ".mp3"
                    
                    # Upload to S3 with standard key format
                    original_key = f"songs/{song_id}/original{audio_ext}"
                    upload_bytes_to_s3(
                        bucket_name=settings.s3_bucket_name,
                        key=original_key,
                        data=audio_bytes,
                        content_type=f"audio/{audio_ext[1:]}",  # Remove the dot
                    )
                    
                    # Update database
                    song.original_s3_key = original_key
                    session.add(song)
                    session.commit()
                    
                    print(f"  ✓ Uploaded audio to S3: {original_key}")
                    has_audio = True
                    actual_s3_key = original_key
                except Exception as e:
                    print(f"  ✗ Failed to upload audio to S3: {e}")
                    print(f"\n✗ ERROR: Cannot proceed without audio in S3 for composition testing")
                    sys.exit(1)
            else:
                print(f"\n✗ ERROR: No audio available in S3 for composition")
                print(f"  Expected S3 key patterns:")
                print(f"    - songs/{song_id}/original.wav")
                print(f"    - songs/{song_id}/original.mp3")
                print(f"    - songs/{song_id}/processed.wav")
                print(f"    - songs/{song_id}/processed.mp3")
                print(f"  No sample audio found in samples/audio/country/ or samples/compTest/")
                print(f"  Cannot proceed without audio in S3")
                sys.exit(1)

        # Get actual clip durations and count
        clip_count = len(clip_paths)
        clip_durations = [get_clip_duration(path) for path in clip_paths]
        total_clip_duration = sum(clip_durations)
        
        print(f"  Clip files: {clip_count} clips, total duration: {total_clip_duration:.1f}s")
        if clip_durations:
            print(f"    Individual durations: {', '.join(f'{d:.1f}s' for d in clip_durations)}")
        
        # Check if duration is missing or suspiciously matches clip durations (likely wrong)
        should_probe = False
        if not song.duration_sec:
            print(f"  Duration: Missing, probing audio file in S3...")
            should_probe = True
        elif abs(song.duration_sec - total_clip_duration) < 1.0:
            # Duration matches clip durations too closely - likely was set incorrectly
            print(f"  Duration: {song.duration_sec:.1f}s (suspiciously matches clip durations: {total_clip_duration:.1f}s)")
            print(f"  Probing audio file in S3 to get actual duration...")
            should_probe = True
        
        if should_probe:
            # Download audio temporarily to probe duration
            from app.services.storage import download_bytes_from_s3
            import tempfile
            import subprocess
            import json
            
            try:
                audio_bytes = download_bytes_from_s3(
                    bucket_name=bucket_name,
                    key=actual_s3_key,
                )
                # Write to temp file
                audio_extension = Path(actual_s3_key).suffix or ".mp3"
                with tempfile.NamedTemporaryFile(delete=False, suffix=audio_extension) as tmp:
                    tmp.write(audio_bytes)
                    temp_audio_path = Path(tmp.name)
                
                try:
                    # Probe audio duration using ffprobe
                    settings = get_settings()
                    ffprobe_bin = settings.ffmpeg_bin.replace("ffmpeg", "ffprobe")
                    probe_cmd = [
                        ffprobe_bin,
                        "-v", "error",
                        "-show_entries", "format=duration",
                        "-of", "json",
                        str(temp_audio_path),
                    ]
                    result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, timeout=30)
                    probe_data = json.loads(result.stdout)
                    actual_audio_duration = float(probe_data["format"]["duration"])
                    
                    if abs(actual_audio_duration - song.duration_sec) > 1.0:
                        print(f"  Duration: Updated from {song.duration_sec:.1f}s to {actual_audio_duration:.1f}s (from audio file)")
                        song.duration_sec = actual_audio_duration
                        session.add(song)
                        session.commit()
                    else:
                        print(f"  Duration: {actual_audio_duration:.1f}s (confirmed from audio file)")
                finally:
                    # Clean up temp file
                    try:
                        temp_audio_path.unlink(missing_ok=True)
                    except Exception:
                        pass
            except Exception as e:
                print(f"  ⚠ Warning: Failed to probe audio duration: {e}")
                if not song.duration_sec:
                    # Only fallback if duration was missing
                    print(f"  Duration: Using sum of clip durations: {total_clip_duration:.1f}s")
                    song.duration_sec = total_clip_duration
                    session.add(song)
                    session.commit()
        else:
            print(f"  Duration: {song.duration_sec:.1f}s")

        # Use clip durations for planning (not song duration) since we're using pre-generated clips
        # The clips define the actual timing, not the song
        planning_duration = total_clip_duration
        
        # Ensure analysis exists (use clip duration if song duration is missing/wrong)
        analysis_duration = song.duration_sec if song.duration_sec and abs(song.duration_sec - total_clip_duration) > 1.0 else planning_duration
        ensure_song_analysis(song_id, analysis_duration)

        # Check if clips already exist
        existing_clips, all_have_videos = check_existing_clips(song_id)
        
        if existing_clips and all_have_videos and not force:
            print(f"\n✓ Clips already exist and have videos ({len(existing_clips)} clips)")
            print("  Use --force to re-upload clips anyway")
            # Still start servers and open browser
            print(f"\n{'='*60}")
            print("Starting development servers...")
            print(f"{'='*60}")
            start_servers_and_open_browser(song_id)
            return
        
        # Cleanup existing clips if requested
        if cleanup and existing_clips:
            print(f"  Cleaning up {len(existing_clips)} existing clips...")
            for clip in existing_clips:
                session.delete(clip)
            session.commit()
            print("  ✓ Existing clips deleted")
            existing_clips = []
        
        # Plan clips based on actual clip durations, not song duration
        # This ensures the plan matches the actual clip files
        plan_clips_if_needed(song_id, clip_count, planning_duration)

        # Get clips for this song (may have been just created)
        statement = (
            select(SongClip)
            .where(SongClip.song_id == song_id)
            .order_by(SongClip.clip_index)  # type: ignore[arg-type]
        )
        existing_clips = session.exec(statement).all()

        if len(clip_paths) != len(existing_clips):
            print(
                f"\nError: Number of clip files ({len(clip_paths)}) doesn't match "
                f"number of planned clips ({len(existing_clips)})"
            )
            print(f"  Planned clips: {len(existing_clips)}")
            print(f"  Provided files: {len(clip_paths)}")
            print("\nTip: Use --cleanup to delete existing clips and re-plan based on file count")
            sys.exit(1)

        print(f"\nUploading {len(clip_paths)} clips...")

        # Upload each clip and update database
        for idx, (clip_path, db_clip) in enumerate(zip(clip_paths, existing_clips)):
            print(f"  [{idx + 1}/{len(clip_paths)}] Uploading {clip_path.name}...")

            # Upload to S3 and get URL
            video_url = upload_clip_to_s3(clip_path, song_id, db_clip.clip_index)

            # Update database record
            db_clip.video_url = video_url
            db_clip.status = "completed"
            db_clip.error = None
            session.add(db_clip)

        session.commit()

        print(f"\n✓ Successfully pre-loaded {len(clip_paths)} clips!")
        print(f"  All clips are now marked as 'completed' and ready for composition")
        print(f"  You can now test the 'Compose when done' button in the front-end")
        
        # Start servers and open browser
        print(f"\n{'='*60}")
        print("Starting development servers...")
        print(f"{'='*60}")
        start_servers_and_open_browser(song_id)


def main():
    parser = argparse.ArgumentParser(
        description="Pre-load test clips into database for composition testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--song-id",
        type=str,
        help="Song ID (UUID) to associate clips with. If not provided, uses the most recent song. Use --list-songs to see available songs.",
    )
    parser.add_argument(
        "--list-songs",
        action="store_true",
        help="List all available songs and exit",
    )
    parser.add_argument(
        "--clips",
        type=str,
        nargs="+",
        help="Paths to clip files (supports glob patterns). Default: ~/Desktop/clip1.mp4, clip2.mp4, etc.",
    )
    parser.add_argument(
        "--samples",
        action="store_true",
        help="Use clips from samples/compTest/ directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-upload clips even if they already exist with videos",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete existing clips before uploading new ones",
    )

    args = parser.parse_args()

    # Handle list songs
    if args.list_songs:
        list_songs()
        return

    # Auto-detect song ID if not provided
    if not args.song_id:
        print("No song ID provided, auto-detecting most recent song...")
        with session_scope() as session:
            from sqlalchemy import text
            try:
                result = session.exec(
                    text("SELECT id FROM songs ORDER BY created_at DESC LIMIT 1")  # type: ignore[arg-type]
                )
                row = result.first()
                if row:
                    song_id_str = str(row[0]) if isinstance(row, tuple) else str(row.id if hasattr(row, 'id') else row)
                    print(f"  Found most recent song: {song_id_str}")
                    args.song_id = song_id_str
                else:
                    print("Error: No songs found in database")
                    print("  Use --list-songs to see available songs, or upload a song first")
                    sys.exit(1)
            except Exception as e:
                print(f"Error: Could not query songs table: {e}")
                print("  Use --list-songs to see available songs")
                sys.exit(1)

    # Parse song ID
    try:
        song_id = UUID(args.song_id)
    except ValueError:
        print(f"Error: Invalid song ID format: {args.song_id}")
        print("  Song ID must be a valid UUID")
        print("  Use --list-songs to see available songs")
        sys.exit(1)

    # Determine clip paths
    if args.samples:
        # Use samples directory
        project_root = Path(__file__).parent.parent
        samples_dir = project_root / "samples" / "compTest"
        clip_paths = sorted(samples_dir.glob("clip*.mp4"))
        if not clip_paths:
            print(f"Error: No clip*.mp4 files found in {samples_dir}")
            sys.exit(1)
    elif args.clips:
        # Use provided paths (support glob patterns)
        clip_paths = []
        for pattern in args.clips:
            expanded = Path(pattern).expanduser()
            if "*" in str(expanded) or "?" in str(expanded):
                # Glob pattern
                matches = sorted(glob.glob(str(expanded)))
                clip_paths.extend([Path(p) for p in matches])
            else:
                # Direct path
                clip_paths.append(expanded)
        clip_paths = sorted(set(clip_paths))  # Remove duplicates and sort
    else:
        # Default: Desktop
        desktop = Path.home() / "Desktop"
        clip_paths = sorted(desktop.glob("clip*.mp4"))
        if not clip_paths:
            # Fallback to specific names
            clip_paths = [
                desktop / "clip1.mp4",
                desktop / "clip2.mp4",
                desktop / "clip3.mp4",
                desktop / "clip4.mp4",
            ]

    if not clip_paths:
        print("Error: No clip files found")
        print("  Use --clips to specify files, --samples to use sample clips, or")
        print("  place clip*.mp4 files in ~/Desktop")
        sys.exit(1)

    preload_clips(song_id, clip_paths, force=args.force, cleanup=args.cleanup)


if __name__ == "__main__":
    main()

