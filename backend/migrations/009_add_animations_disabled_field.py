"""Migration 009: Add animations_disabled field to users table.

This migration adds an animations_disabled field that stores the user's preference
for disabling animations in the UI.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.core.database import engine


def migrate() -> None:
    """Add animations_disabled field to users table if it doesn't exist."""
    inspector = inspect(engine)
    
    if "users" not in inspector.get_table_names():
        raise RuntimeError("users table does not exist")
    
    existing_columns = {col["name"] for col in inspector.get_columns("users")}
    
    database_url = str(engine.url)
    is_postgres = database_url.startswith("postgresql")
    
    field_name = "animations_disabled"
    field_type = "BOOLEAN DEFAULT FALSE"
    
    with engine.begin() as conn:
        if field_name not in existing_columns:
            if is_postgres:
                alter_sql = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {field_name} {field_type}"
            else:
                alter_sql = f"ALTER TABLE users ADD COLUMN {field_name} {field_type}"
            
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

