#!/usr/bin/env python3
"""Database query utility script.

Combines functionality for querying analysis jobs, songs, and composed videos.
Supports multiple commands via subcommands.

Usage:
    # Check recent analysis jobs
    python scripts/db_query.py jobs [--limit N]

    # List recent songs
    python scripts/db_query.py songs [--limit N]

    # Get presigned URLs for composed videos
    python scripts/db_query.py videos [--status STATUS]

    # Override database URL
    DATABASE_URL_OVERRIDE="postgresql://..." python scripts/db_query.py songs
"""

import argparse
import os
import sys
from pathlib import Path


def _ensure_venv():
    """Ensure we're running with the backend virtual environment.
    
    If not already in a venv, attempts to find and use backend/venv/bin/python.
    Re-executes the script with the venv Python if found.
    """
    # Check if we're already in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        # Already in a venv
        return
    
    # Check if VIRTUAL_ENV is set
    if os.environ.get('VIRTUAL_ENV'):
        return
    
    # Try to find and use backend/venv
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    venv_python = project_root / "backend" / "venv" / "bin" / "python"
    
    if venv_python.exists() and venv_python.is_file():
        # Re-execute with venv Python
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    
    # If we get here, no venv was found - let imports fail with a clear error
    # This allows the script to still work if dependencies are installed globally


# Ensure venv before importing dependencies
_ensure_venv()

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from collections import defaultdict
from uuid import UUID

import httpx
from sqlmodel import Session, SQLModel, create_engine, select, text

from app.core.config import get_settings
from app.core.database import session_scope
from app.core.queue import get_queue
from app.models import (
    AnalysisJob,
    ClipGenerationJob,
    ComposedVideo,
    CompositionJob,
    Song,
    SongAnalysisRecord,
    SongClip,
)
from app.repositories import ClipRepository, SongRepository
from app.services.composition_job import cancel_job
from app.services.storage import generate_presigned_get_url


def _get_database_url():
    """Get database URL, allowing override via environment variable."""
    settings = get_settings()
    return os.getenv("DATABASE_URL_OVERRIDE") or settings.database_url


def _mask_password_in_url(url: str) -> str:
    """Mask password in database URL for display."""
    if "@" not in url:
        return url
    
    parts = url.split("@")
    if ":" in parts[0] and "//" in parts[0]:
        user_pass = parts[0].split("//")[1]
        if ":" in user_pass:
            user = user_pass.split(":")[0]
            return url.replace(user_pass, f"{user}:***", 1)
    return url


def _get_session():
    """Get database session, handling DATABASE_URL_OVERRIDE if needed."""
    database_url = _get_database_url()
    
    if os.getenv("DATABASE_URL_OVERRIDE"):
        # Parse connection string for psycopg
        db_url = database_url
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        
        engine = create_engine(db_url, echo=False)
        return Session(engine)
    else:
        # Use default session_scope context manager
        return session_scope()


def cmd_jobs(limit: int = 3):
    """Check recent analysis jobs."""
    with _get_session() as session:
        jobs = session.exec(
            select(AnalysisJob)
            .order_by(AnalysisJob.created_at.desc())
            .limit(limit)
        ).all()
        
        print(f"Recent analysis jobs (last {len(jobs)}):")
        print()
        for j in jobs:
            print(f"  Job: {j.id[:30]}...")
            print(f"    Status: {j.status}")
            print(f"    Progress: {j.progress}%")
            if j.error:
                print(f"    Error: {j.error}")
            print()


def cmd_songs(limit: int = 5):
    """List recent songs."""
    with _get_session() as session:
        songs = session.exec(
            select(Song)
            .order_by(Song.created_at.desc())
            .limit(limit)
        ).all()
        
        print(f"Recent songs (last {len(songs)}):")
        print()
        for s in songs:
            print(f"  ID: {s.id}")
            print(f"    Created: {s.created_at}")
            print(f"    Title: {s.title or s.original_filename or 'N/A'}")
            print(f"    Has composed video: {bool(s.composed_video_s3_key)}")
            print()


def cmd_videos(status: str = "completed"):
    """Get presigned S3 URLs for composed videos."""
    settings = get_settings()
    database_url = _get_database_url()
    
    # Show connection info
    db_display = _mask_password_in_url(database_url)
    print(f"Connecting to database: {db_display.split('@')[-1] if '@' in db_display else db_display}")
    print(f"Using S3 bucket: {settings.s3_bucket_name}")
    print()
    
    with _get_session() as session:
        # First check all videos to see what we have
        all_videos = session.exec(select(ComposedVideo)).all()
        print(f"Total composed videos in database: {len(all_videos)}")
        if all_videos:
            print("Status breakdown:")
            status_counts = {}
            for v in all_videos:
                status_counts[v.status] = status_counts.get(v.status, 0) + 1
            for stat, count in status_counts.items():
                print(f"  {stat}: {count}")
            print()
        
        # Get videos by status
        statement = select(ComposedVideo).where(
            ComposedVideo.status == status
        ).order_by(ComposedVideo.created_at.desc())
        composed_videos = session.exec(statement).all()
        
        if not composed_videos:
            print(f"No {status} composed videos found.")
            return
        
        print(f"Found {len(composed_videos)} {status} composed video(s):\n")
        
        for video in composed_videos:
            try:
                # Generate presigned URL (valid for 1 hour)
                presigned_url = generate_presigned_get_url(
                    bucket_name=settings.s3_bucket_name,
                    key=video.s3_key,
                    expires_in=3600,
                )
                print(presigned_url)
            except Exception as e:
                print(f"Error generating URL for video {video.id}: {e}", file=sys.stderr)


def cmd_clips(song_id_str: str, verify_compose: bool = False):
    """Show clip status summary for a song."""
    try:
        song_id = UUID(song_id_str)
    except ValueError:
        print(f"Error: Invalid song ID format: {song_id_str}")
        return
    
    with _get_session() as session:
        try:
            song = SongRepository.get_by_id(song_id)
            print(f"Song: {song.title or song.original_filename}")
            print(f"Song ID: {song_id}\n")
        except Exception as e:
            print(f"Error: Song not found: {e}")
            return
        
        clips = ClipRepository.get_by_song_id(song_id)
        if not clips:
            print(f"No clips found for song {song_id}")
            return
        
        print(f"Total clips: {len(clips)}\n")
        
        # Count by status
        status_counts = {}
        for clip in clips:
            status_counts[clip.status] = status_counts.get(clip.status, 0) + 1
        
        print("Status summary:")
        for status, count in sorted(status_counts.items()):
            print(f"  {status}: {count}")
        
        print("\nClip details:")
        for clip in sorted(clips, key=lambda c: c.clip_index):
            has_video = "✓" if clip.video_url else "✗"
            print(f"  Clip #{clip.clip_index + 1}: {clip.status} | Video: {has_video} | {clip.start_sec:.1f}s - {clip.end_sec:.1f}s")
            if clip.video_url:
                print(f"    URL: {clip.video_url[:80]}...")
        
        # Check completed clips
        completed = ClipRepository.get_completed_by_song_id(song_id)
        print(f"\n✅ Completed clips with video URLs: {len(completed)}/{len(clips)}")
        
        if len(completed) == len(clips) and len(clips) > 0:
            print("\n🎉 All clips are completed and ready for composition!")
        elif len(completed) > 0:
            print(f"\n⚠️  {len(clips) - len(completed)} clips still in progress...")
        else:
            print("\n⏳ No clips completed yet...")
        
        # Verify compose if requested
        if verify_compose:
            print("\n" + "=" * 80)
            print("Composition verification:")
            if not completed:
                print("❌ No completed clips found! Cannot compose.")
            else:
                print(f"✅ Found {len(completed)} completed clips that will be used for composition:\n")
                for clip in sorted(completed, key=lambda c: c.clip_index):
                    print(f"  Clip #{clip.clip_index + 1}:")
                    print(f"    ID: {clip.id}")
                    print(f"    Time: {clip.start_sec:.1f}s - {clip.end_sec:.1f}s ({clip.duration_sec:.1f}s)")
                    print(f"    Video URL: {clip.video_url[:80] if clip.video_url else 'None'}...")
                
                if len(completed) > 1:
                    created_times = [clip.created_at for clip in completed]
                    min_time = min(created_times)
                    max_time = max(created_times)
                    time_diff = (max_time - min_time).total_seconds()
                    
                    if time_diff < 60:
                        print(f"\n✅ All clips were created within {time_diff:.1f} seconds (same generation)")
                    else:
                        print(f"\n⚠️  Clips span {time_diff:.1f} seconds - may be from different generations")
                
                print(f"\n🎬 Ready to compose with {len(completed)} clips!")
                print(f"   Total duration: {sum(c.duration_sec for c in completed):.1f}s")


def cmd_clips_urls(song_id_str: str):
    """Check if clip video URLs are accessible."""
    try:
        song_id = UUID(song_id_str)
    except ValueError:
        print(f"Error: Invalid song ID format: {song_id_str}")
        return
    
    print(f'Checking clips for song: {song_id}\n')
    print('=' * 80)
    
    with _get_session() as session:
        try:
            song = SongRepository.get_by_id(song_id)
        except Exception as e:
            print(f"Error: Song not found: {e}")
            return
        
        clips = ClipRepository.get_by_song_id(song_id)
        
        if not clips:
            print(f"No clips found for song {song_id}")
            return
        
        print(f'Found {len(clips)} clips\n')
        
        accessible_count = 0
        inaccessible_count = 0
        no_url_count = 0
        
        for clip in sorted(clips, key=lambda c: c.clip_index):
            print(f'Clip {clip.clip_index}:')
            print(f'  ID: {clip.id}')
            print(f'  Status: {clip.status}')
            
            if clip.video_url:
                print(f'  Video URL: {clip.video_url[:100]}...')
                
                # Check if URL is accessible
                try:
                    response = httpx.head(clip.video_url, timeout=10.0, follow_redirects=True)
                    if response.status_code == 200:
                        print(f'  ✅ URL is accessible (HEAD: {response.status_code})')
                        accessible_count += 1
                    else:
                        print(f'  ❌ URL returned status {response.status_code}')
                        # Try GET with range to verify
                        try:
                            headers = {'Range': 'bytes=0-0'}
                            get_response = httpx.get(clip.video_url, headers=headers, timeout=10.0, follow_redirects=True)
                            if get_response.status_code in (200, 206):
                                print(f'  ✅ URL is accessible (GET: {get_response.status_code})')
                                accessible_count += 1
                            else:
                                print(f'  ❌ URL returned status {get_response.status_code}')
                                inaccessible_count += 1
                        except Exception as e:
                            print(f'  ❌ GET request failed: {e}')
                            inaccessible_count += 1
                except httpx.HTTPStatusError as e:
                    print(f'  ❌ HTTP Error: {e.response.status_code}')
                    try:
                        error_body = e.response.read().decode('utf-8', errors='ignore')[:200]
                        print(f'     Error: {error_body}')
                    except:
                        pass
                    inaccessible_count += 1
                except Exception as e:
                    print(f'  ❌ Connection failed: {type(e).__name__}: {e}')
                    inaccessible_count += 1
            else:
                print(f'  ⚠️  No video URL')
                no_url_count += 1
            
            print()
        
        print('=' * 80)
        print(f'Summary:')
        print(f'  Total clips: {len(clips)}')
        print(f'  ✅ Accessible URLs: {accessible_count}')
        print(f'  ❌ Inaccessible URLs: {inaccessible_count}')
        print(f'  ⚠️  No URL: {no_url_count}')
        print(f'  Completed status: {len([c for c in clips if c.status == "completed"])}')


def cmd_composition_jobs(song_id_str: str):
    """Find composition jobs for a song."""
    try:
        song_id = UUID(song_id_str)
    except ValueError:
        print(f"Error: Invalid song ID format: {song_id_str}")
        return
    
    with _get_session() as session:
        jobs = session.exec(
            select(CompositionJob)
            .where(CompositionJob.song_id == song_id)
            .order_by(CompositionJob.created_at.desc())
        ).all()
        
        if not jobs:
            print(f"No composition jobs found for song {song_id}")
            return
        
        print(f"Found {len(jobs)} composition job(s) for song {song_id}:\n")
        for job in jobs:
            print(f"  Job ID: {job.id}")
            print(f"  Status: {job.status}")
            print(f"  Progress: {job.progress}%")
            print(f"  Created: {job.created_at}")
            if job.error:
                print(f"  Error: {job.error}")
            print()
        
        active_jobs = [j for j in jobs if j.status in ['queued', 'processing']]
        if active_jobs:
            print(f"Active jobs: {len(active_jobs)}")
            print(f"\nTo cancel: python scripts/db_query.py cancel-composition {song_id_str}")


def cmd_songs_ready():
    """Find songs that have all clips completed."""
    with _get_session() as session:
        completed_clips = session.exec(
            select(SongClip)
            .where(SongClip.status == "completed")
            .where(SongClip.video_url.isnot(None))
        ).all()
        
        # Group by song_id
        songs_clips = defaultdict(list)
        for clip in completed_clips:
            songs_clips[clip.song_id].append(clip)
        
        print(f'Found {len(completed_clips)} completed clips across {len(songs_clips)} songs\n')
        
        ready_songs = []
        partial_songs = []
        
        for song_id, clips in sorted(songs_clips.items(), key=lambda x: len(x[1]), reverse=True):
            try:
                song = SongRepository.get_by_id(song_id)
                song_title = song.title if song else "Unknown"
            except Exception:
                song_title = "Unknown"
            
            # Count total clips for this song
            all_clips = ClipRepository.get_by_song_id(song_id)
            total_clips = len(all_clips)
            completed_count = len(clips)
            
            if completed_count == total_clips and total_clips > 0:
                ready_songs.append((song_id, song_title, completed_count, total_clips))
            else:
                partial_songs.append((song_id, song_title, completed_count, total_clips))
        
        if ready_songs:
            print("✅ Songs ready for composition (all clips completed):\n")
            for song_id, title, completed, total in ready_songs:
                print(f"  {title}")
                print(f"    ID: {song_id}")
                print(f"    Clips: {completed}/{total} completed")
                print(f"    URL: http://localhost:5173/?songId={song_id}")
                print()
        
        if partial_songs:
            print("⚠️  Songs with partial clips:\n")
            for song_id, title, completed, total in partial_songs[:10]:  # Limit to 10
                print(f"  {title}: {completed}/{total} completed (ID: {song_id})")
            if len(partial_songs) > 10:
                print(f"  ... and {len(partial_songs) - 10} more")
        
        print('=' * 80)
        print(f'Total ready: {len(ready_songs)} songs')
        print(f'Total with partial: {len(partial_songs)} songs')


def cmd_clear_composed(song_id_str: str):
    """Clear composed video fields from a song."""
    try:
        song_id = UUID(song_id_str)
    except ValueError:
        print(f"Error: Invalid song ID format: {song_id_str}")
        return
    
    try:
        song = SongRepository.get_by_id(song_id)
        print(f"Song: {song.title or song.original_filename}")
        print(f"Song ID: {song_id}\n")
        
        had_composed = bool(song.composed_video_s3_key)
        if not had_composed:
            print("ℹ️  Song doesn't have a composed video - nothing to clear")
            return
        
        print("Current composed video fields:")
        print(f"  s3_key: {song.composed_video_s3_key}")
        print(f"  poster_s3_key: {song.composed_video_poster_s3_key}")
        print(f"  duration_sec: {song.composed_video_duration_sec}")
        print(f"  fps: {song.composed_video_fps}\n")
        
        song.composed_video_s3_key = None
        song.composed_video_poster_s3_key = None
        song.composed_video_duration_sec = None
        song.composed_video_fps = None
        SongRepository.update(song)
        
        print("✅ Cleared composed video fields!")
        print(f"   You can now click 'Compose' for song: {song_id}")
        print(f"   URL: http://localhost:5173/?songId={song_id}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


def cmd_cancel_composition(song_id_str: str):
    """Cancel active composition job for a song."""
    try:
        song_id = UUID(song_id_str)
    except ValueError:
        print(f"Error: Invalid song ID format: {song_id_str}")
        return
    
    with _get_session() as session:
        active_jobs = session.exec(
            select(CompositionJob)
            .where(CompositionJob.song_id == song_id)
            .where(CompositionJob.status.in_(["queued", "processing"]))
            .order_by(CompositionJob.created_at.desc())
        ).all()
        
        if not active_jobs:
            print(f"No active composition jobs found for song {song_id_str}")
            return
        
        job = active_jobs[0]
        print(f"Found active job: {job.id} (status: {job.status})")
        
        try:
            cancel_job(job.id)
            print(f"✅ Cancelled composition job: {job.id}")
        except Exception as e:
            print(f"❌ Failed to cancel job: {e}")
            import traceback
            traceback.print_exc()


def cmd_kill_jobs():
    """Clear all pending jobs from the RQ queue."""
    try:
        queue = get_queue()
        queue_name = queue.name
        
        job_count = len(queue)
        
        if job_count > 0:
            queue.empty()
            print(f'✅ Cleared {job_count} pending job(s) from queue: {queue_name}')
        else:
            print(f'✅ Queue {queue_name} is already empty (0 jobs)')
    except Exception as e:
        print(f'❌ Error clearing queue: {e}')
        import traceback
        traceback.print_exc()


def cmd_kill_composition_jobs():
    """Cancel all active composition jobs."""
    cancelled_count = 0
    
    # Cancel all active composition jobs in database
    try:
        with _get_session() as session:
            active_jobs = session.exec(
                select(CompositionJob)
                .where(CompositionJob.status.in_(['queued', 'processing']))
            ).all()
            
            print(f'Found {len(active_jobs)} active composition jobs in database')
            for job in active_jobs:
                try:
                    cancel_job(job.id)
                    print(f'✅ Cancelled composition job: {job.id} (song: {job.song_id})')
                    cancelled_count += 1
                except Exception as e:
                    print(f'❌ Failed to cancel {job.id}: {e}')
    except Exception as e:
        print(f'❌ Error accessing database: {e}')
        import traceback
        traceback.print_exc()
    
    # Also cancel composition jobs in RQ queue
    try:
        queue = get_queue()
        jobs = queue.jobs
        composition_jobs = [j for j in jobs if j.id and j.id.startswith('composition-')]
        print(f'\nFound {len(composition_jobs)} composition jobs in RQ queue')
        for job in composition_jobs:
            try:
                job.cancel()
                print(f'✅ Cancelled RQ job: {job.id}')
                cancelled_count += 1
            except Exception as e:
                print(f'❌ Failed to cancel RQ job {job.id}: {e}')
    except Exception as e:
        print(f'⚠️  Could not access RQ queue: {e}')
    
    print(f'\n✅ Total cancelled: {cancelled_count} composition jobs')


def cmd_clear_all(confirm: bool = False):
    """Clear all data from database tables and RQ queue.
    
    Args:
        confirm: If True, skip confirmation prompt. Defaults to False.
    """
    if not confirm:
        response = input('⚠️  This will DELETE ALL DATA from your local database. Continue? (yes/no): ')
        if response.lower() != 'yes':
            print('Cancelled.')
            return
    
    print('Clearing all database data and RQ jobs...\n')
    
    # Clear RQ queue first
    try:
        queue = get_queue()
        queue_name = queue.name
        job_count = len(queue)
        if job_count > 0:
            queue.empty()
            print(f'✅ Cleared {job_count} job(s) from RQ queue: {queue_name}')
        else:
            print(f'✅ RQ queue {queue_name} is already empty')
    except Exception as e:
        print(f'⚠️  Could not clear RQ queue: {e}')
    
    print()
    
    # Clear database tables (in order to respect foreign key constraints)
    with _get_session() as session:
        from app.models import (
            AnalysisJob,
            ClipGenerationJob,
            ComposedVideo,
            CompositionJob,
            SectionVideo,
            Song,
            SongAnalysisRecord,
            SongClip,
            User,
        )
        
        # Clear in order to respect foreign key constraints
        # User should be cleared last since Songs reference users
        tables_to_clear = [
            ('ComposedVideo', ComposedVideo),
            ('CompositionJob', CompositionJob),
            ('SongClip', SongClip),
            ('SectionVideo', SectionVideo),
            ('AnalysisJob', AnalysisJob),
            ('SongAnalysisRecord', SongAnalysisRecord),
            ('ClipGenerationJob', ClipGenerationJob),
            ('Song', Song),
            ('User', User),
        ]
        
        for table_name, model in tables_to_clear:
            try:
                result = session.exec(text(f'DELETE FROM {model.__tablename__}'))
                session.commit()
                print(f'✅ Cleared {table_name} ({model.__tablename__})')
            except Exception as e:
                print(f'❌ Failed to clear {table_name}: {e}')
                session.rollback()
        
        # Verify counts
        print()
        print('Verifying all tables are empty...')
        for table_name, model in tables_to_clear:
            result = session.exec(text(f'SELECT COUNT(*) as count FROM {model.__tablename__}'))
            row = result.one()
            count = row.count if hasattr(row, 'count') else row[0] if isinstance(row, tuple) else row
            if count > 0:
                print(f'  ⚠️  {table_name}: {count} rows remaining')
            else:
                print(f'  ✅ {table_name}: empty')
    
    print()
    print('=' * 80)
    print('✅ Database cleared successfully!')
    print('✅ RQ queue cleared successfully!')


def main():
    """Main entry point with subcommand parsing."""
    parser = argparse.ArgumentParser(
        description="Database query utility for VibeCraft",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check recent analysis jobs
  python scripts/db_query.py jobs

  # List recent songs
  python scripts/db_query.py songs --limit 10

  # Get presigned URLs for completed videos
  python scripts/db_query.py videos

  # Check clip status for a song
  python scripts/db_query.py clips <song_id>

  # Check if clip URLs are accessible
  python scripts/db_query.py clips-urls <song_id>

  # Find songs ready for composition
  python scripts/db_query.py songs-ready

  # Override database URL
  DATABASE_URL_OVERRIDE="postgresql://..." python scripts/db_query.py songs
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)
    
    # Jobs subcommand
    jobs_parser = subparsers.add_parser("jobs", help="Check recent analysis jobs")
    jobs_parser.add_argument(
        "--limit",
        type=int,
        default=3,
        help="Number of jobs to show (default: 3)"
    )
    
    # Songs subcommand
    songs_parser = subparsers.add_parser("songs", help="List recent songs")
    songs_parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Number of songs to show (default: 5)"
    )
    
    # Videos subcommand
    videos_parser = subparsers.add_parser("videos", help="Get presigned URLs for composed videos")
    videos_parser.add_argument(
        "--status",
        type=str,
        default="completed",
        help="Filter by status (default: completed)"
    )
    
    # Clips subcommand
    clips_parser = subparsers.add_parser("clips", help="Show clip status for a song")
    clips_parser.add_argument("song_id", help="Song ID")
    clips_parser.add_argument(
        "--verify-compose",
        action="store_true",
        help="Verify which clips will be used for composition"
    )
    
    # Clips URLs subcommand
    clips_urls_parser = subparsers.add_parser("clips-urls", help="Check if clip video URLs are accessible")
    clips_urls_parser.add_argument("song_id", help="Song ID")
    
    # Composition jobs subcommand
    comp_jobs_parser = subparsers.add_parser("composition-jobs", help="Find composition jobs for a song")
    comp_jobs_parser.add_argument("song_id", help="Song ID")
    
    # Songs ready subcommand
    subparsers.add_parser("songs-ready", help="Find songs with all clips completed")
    
    # Clear composed subcommand
    clear_comp_parser = subparsers.add_parser("clear-composed", help="Clear composed video fields from a song")
    clear_comp_parser.add_argument("song_id", help="Song ID")
    
    # Cancel composition subcommand
    cancel_comp_parser = subparsers.add_parser("cancel-composition", help="Cancel active composition job for a song")
    cancel_comp_parser.add_argument("song_id", help="Song ID")
    
    # Kill jobs subcommand
    subparsers.add_parser("kill-jobs", help="Clear all pending jobs from RQ queue")
    
    # Kill composition jobs subcommand
    subparsers.add_parser("kill-composition-jobs", help="Cancel all active composition jobs")
    
    # Clear all subcommand
    clear_all_parser = subparsers.add_parser("clear-all", help="Clear all database data and RQ jobs (DESTRUCTIVE)")
    clear_all_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Skip confirmation prompt (use with caution!)",
    )
    
    args = parser.parse_args()
    
    if args.command == "jobs":
        cmd_jobs(args.limit)
    elif args.command == "songs":
        cmd_songs(args.limit)
    elif args.command == "videos":
        cmd_videos(args.status)
    elif args.command == "clips":
        cmd_clips(args.song_id, args.verify_compose)
    elif args.command == "clips-urls":
        cmd_clips_urls(args.song_id)
    elif args.command == "composition-jobs":
        cmd_composition_jobs(args.song_id)
    elif args.command == "songs-ready":
        cmd_songs_ready()
    elif args.command == "clear-composed":
        cmd_clear_composed(args.song_id)
    elif args.command == "cancel-composition":
        cmd_cancel_composition(args.song_id)
    elif args.command == "kill-jobs":
        cmd_kill_jobs()
    elif args.command == "kill-composition-jobs":
        cmd_kill_composition_jobs()
    elif args.command == "clear-all":
        cmd_clear_all(confirm=getattr(args, 'confirm', False))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

