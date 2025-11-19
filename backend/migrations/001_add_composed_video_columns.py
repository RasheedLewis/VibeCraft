"""Migration 001: Add composed_video columns to songs table.

This migration adds the following columns to the songs table:
- composed_video_s3_key (VARCHAR(1024), nullable)
- composed_video_poster_s3_key (VARCHAR(1024), nullable)
- composed_video_duration_sec (FLOAT, nullable)
- composed_video_fps (INTEGER, nullable)

These columns were added to the Song model for MVP-03 but the database
schema wasn't updated. This migration adds them safely without dropping data.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text

from app.core.database import engine


def migrate() -> None:
    """Add composed_video columns to songs table if they don't exist."""
    inspector = inspect(engine)
    
    # Check if songs table exists
    if "songs" not in inspector.get_table_names():
        raise RuntimeError("songs table does not exist")
    
    # Get existing columns
    existing_columns = {col["name"] for col in inspector.get_columns("songs")}
    
    # Columns to add
    columns_to_add = {
        "composed_video_s3_key": "VARCHAR(1024)",
        "composed_video_poster_s3_key": "VARCHAR(1024)",
        "composed_video_duration_sec": "FLOAT",
        "composed_video_fps": "INTEGER",
    }
    
    # Check which columns are missing
    missing_columns = {
        col: sql_type
        for col, sql_type in columns_to_add.items()
        if col not in existing_columns
    }
    
    if not missing_columns:
        print("  All composed_video columns already exist")
        return
    
    # Determine database type for ALTER TABLE syntax
    database_url = str(engine.url)
    is_postgres = database_url.startswith("postgresql")
    
    with engine.begin() as conn:
        for column_name, sql_type in missing_columns.items():
            if is_postgres:
                # PostgreSQL syntax
                alter_sql = f'ALTER TABLE songs ADD COLUMN IF NOT EXISTS {column_name} {sql_type}'
            else:
                # Fallback for other databases
                alter_sql = f'ALTER TABLE songs ADD COLUMN {column_name} {sql_type}'
            
            try:
                conn.execute(text(alter_sql))
                print(f"  ✓ Added column: {column_name}")
            except Exception as e:
                # Check if column already exists
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print(f"  ⚠ Column {column_name} already exists (skipping)")
                else:
                    raise RuntimeError(f"Failed to add column {column_name}: {e}") from e

