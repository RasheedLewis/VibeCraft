"""Migration 002: Add audio selection fields to songs table.

This migration adds the following columns to the songs table:
- selected_start_sec (FLOAT, nullable)
- selected_end_sec (FLOAT, nullable)

These columns allow users to select up to 30 seconds from their uploaded audio
for clip generation. Both fields are optional to maintain backward compatibility.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text

from app.core.database import engine


def migrate() -> None:
    """Add audio selection fields to songs table if they don't exist."""
    inspector = inspect(engine)
    
    # Check if songs table exists
    if "songs" not in inspector.get_table_names():
        raise RuntimeError("songs table does not exist")
    
    # Get existing columns
    existing_columns = {col["name"] for col in inspector.get_columns("songs")}
    
    # Columns to add
    columns_to_add = {
        "selected_start_sec": "FLOAT",
        "selected_end_sec": "FLOAT",
    }
    
    # Check which columns are missing
    missing_columns = {
        col: sql_type
        for col, sql_type in columns_to_add.items()
        if col not in existing_columns
    }
    
    if not missing_columns:
        print("  All audio selection columns already exist")
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
                # SQLite syntax (SQLite 3.25.0+ supports ADD COLUMN)
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

