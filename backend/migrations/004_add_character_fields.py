"""Migration 004: Add character consistency fields to songs table.

This migration adds fields for character reference images, consistency flags,
and generated character images for the character consistency feature.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.core.database import engine


def migrate() -> None:
    """Add character consistency fields to songs table if they don't exist."""
    inspector = inspect(engine)
    
    if "songs" not in inspector.get_table_names():
        raise RuntimeError("songs table does not exist")
    
    existing_columns = {col["name"] for col in inspector.get_columns("songs")}
    
    database_url = str(engine.url)
    is_postgres = database_url.startswith("postgresql")
    
    character_fields = [
        ("character_reference_image_s3_key", "VARCHAR(1024)"),
        ("character_consistency_enabled", "BOOLEAN DEFAULT FALSE"),
        ("character_interrogation_prompt", "TEXT"),
        ("character_generated_image_s3_key", "VARCHAR(1024)"),
    ]
    
    with engine.begin() as conn:
        for field_name, field_type in character_fields:
            if field_name not in existing_columns:
                if is_postgres:
                    alter_sql = f'ALTER TABLE songs ADD COLUMN IF NOT EXISTS {field_name} {field_type}'
                else:
                    alter_sql = f'ALTER TABLE songs ADD COLUMN {field_name} {field_type}'
                
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


