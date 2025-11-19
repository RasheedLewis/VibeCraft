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

from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import get_settings
from app.core.database import session_scope
from app.models.analysis import AnalysisJob
from app.models.composition import ComposedVideo
from app.models.song import Song
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

  # Get URLs for videos with specific status
  python scripts/db_query.py videos --status processing

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
    
    args = parser.parse_args()
    
    if args.command == "jobs":
        cmd_jobs(args.limit)
    elif args.command == "songs":
        cmd_songs(args.limit)
    elif args.command == "videos":
        cmd_videos(args.status)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

