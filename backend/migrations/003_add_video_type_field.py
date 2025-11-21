"""Migration 003: Add video_type field to songs table.

This migration adds a video_type field that stores the user's choice
between full-length and short-form video generation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.core.database import engine


def migrate() -> None:
    """Add video_type field to songs table if it doesn't exist."""
    inspector = inspect(engine)
    
    if "songs" not in inspector.get_table_names():
        raise RuntimeError("songs table does not exist")
    
    existing_columns = {col["name"] for col in inspector.get_columns("songs")}
    
    if "video_type" not in existing_columns:
        database_url = str(engine.url)
        is_postgres = database_url.startswith("postgresql")
        
        with engine.begin() as conn:
            if is_postgres:
                alter_sql = 'ALTER TABLE songs ADD COLUMN IF NOT EXISTS video_type VARCHAR(32)'
            else:
                alter_sql = 'ALTER TABLE songs ADD COLUMN video_type VARCHAR(32)'
            
            try:
                conn.execute(text(alter_sql))
                print("  ✓ Added column: video_type")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print("  ⚠ Column video_type already exists (skipping)")
                else:
                    raise RuntimeError(f"Failed to add column video_type: {e}") from e
    else:
        print("  Column video_type already exists")

