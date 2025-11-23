#!/usr/bin/env python3
"""Script to get presigned S3 URLs for all final composited videos."""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlmodel import Session, SQLModel, create_engine, select

from app.core.config import get_settings
from app.core.database import session_scope
from app.models.composition import ComposedVideo
from app.services.storage import generate_presigned_get_url


def main():
    settings = get_settings()
    
    # Allow overriding DATABASE_URL via environment variable
    # Usage: DATABASE_URL_OVERRIDE="postgresql://..." python3 scripts/get_final_video_urls.py
    database_url = os.getenv("DATABASE_URL_OVERRIDE") or settings.database_url
    
    # Show which database we're connecting to (mask password)
    db_display = database_url
    if "@" in db_display:
        # Mask password in display
        parts = db_display.split("@")
        if ":" in parts[0] and "//" in parts[0]:
            user_pass = parts[0].split("//")[1]
            if ":" in user_pass:
                user = user_pass.split(":")[0]
                db_display = db_display.replace(user_pass, f"{user}:***", 1)
    
    print(f"Connecting to database: {db_display.split('@')[-1] if '@' in db_display else db_display}")
    print(f"Using S3 bucket: {settings.s3_bucket_name}")
    print()
    
    # Create engine with potentially overridden database URL
    if os.getenv("DATABASE_URL_OVERRIDE"):
        # Parse connection string for psycopg
        db_url = database_url
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
        elif db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
        
        engine = create_engine(db_url, echo=False)
        with Session(engine) as session:
            _query_videos(session, settings)
    else:
        with session_scope() as session:
            _query_videos(session, settings)


def _query_videos(session: Session, settings):
    # First check all videos to see what we have
    all_videos = session.exec(select(ComposedVideo)).all()
    print(f"Total composed videos in database: {len(all_videos)}")
    if all_videos:
        print("Status breakdown:")
        status_counts = {}
        for v in all_videos:
            status_counts[v.status] = status_counts.get(v.status, 0) + 1
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        print()
    
    # Get all completed composed videos
    statement = select(ComposedVideo).where(
        ComposedVideo.status == "completed"
    ).order_by(ComposedVideo.created_at.desc())
    composed_videos = session.exec(statement).all()
    
    if not composed_videos:
        print("No completed composed videos found.")
        return
    
    print(f"Found {len(composed_videos)} completed composed video(s):\n")
    
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


if __name__ == "__main__":
    main()

