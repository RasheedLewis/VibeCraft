"""Migration 010: Add index on songs.created_at column.

This migration adds a database index on the created_at column to improve
query performance for song listing (ORDER BY created_at DESC).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.core.database import engine


def migrate() -> None:
    """Add index on songs.created_at if it doesn't exist."""
    inspector = inspect(engine)
    
    if "songs" not in inspector.get_table_names():
        raise RuntimeError("songs table does not exist")
    
    # Check if index already exists
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("songs")}
    index_name = "ix_songs_created_at"
    
    database_url = str(engine.url)
    is_postgres = database_url.startswith("postgresql")
    
    with engine.begin() as conn:
        if index_name not in existing_indexes:
            if is_postgres:
                # PostgreSQL: CREATE INDEX IF NOT EXISTS
                create_index_sql = f'CREATE INDEX IF NOT EXISTS {index_name} ON songs (created_at)'
            else:
                # SQLite: CREATE INDEX IF NOT EXISTS (also supported)
                create_index_sql = f'CREATE INDEX IF NOT EXISTS {index_name} ON songs (created_at)'
            
            try:
                conn.execute(text(create_index_sql))
                print(f"  ✓ Created index: {index_name}")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print(f"  ⚠ Index {index_name} already exists (skipping)")
                else:
                    raise RuntimeError(f"Failed to create index {index_name}: {e}") from e
        else:
            print(f"  Index {index_name} already exists")


if __name__ == "__main__":
    migrate()

