"""Migration 008: Add character_selected_pose field to songs table.

This migration adds a character_selected_pose field that stores the user's selected
pose ('A' or 'B') for character consistency in video generation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.core.database import engine


def migrate() -> None:
    """Add character_selected_pose field to songs table if it doesn't exist."""
    inspector = inspect(engine)
    
    if "songs" not in inspector.get_table_names():
        raise RuntimeError("songs table does not exist")
    
    existing_columns = {col["name"] for col in inspector.get_columns("songs")}
    
    database_url = str(engine.url)
    is_postgres = database_url.startswith("postgresql")
    
    field_name = "character_selected_pose"
    field_type = "VARCHAR(1) DEFAULT 'A'"
    
    with engine.begin() as conn:
        if field_name not in existing_columns:
            if is_postgres:
                alter_sql = f"ALTER TABLE songs ADD COLUMN IF NOT EXISTS {field_name} {field_type}"
            else:
                alter_sql = f"ALTER TABLE songs ADD COLUMN {field_name} {field_type}"
            
            try:
                conn.execute(text(alter_sql))
                print(f"  ✓ Added column: {field_name}")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print(f"  ⚠ Column {field_name} already exists (skipping)")
                else:
                    raise RuntimeError(f"Failed to add column {field_name}: {e}") from e
        else:
            print(f"  Column {field_name} already exists")


if __name__ == "__main__":
    migrate()

