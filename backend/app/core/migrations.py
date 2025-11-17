"""Database migration system.

This module provides a simple migration framework that tracks applied migrations
in a `schema_migrations` table and applies migrations in order.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy import inspect, text

from app.core.database import engine


def get_migration_version() -> Optional[int]:
    """Get the current migration version from the database."""
    inspector = inspect(engine)
    
    # Check if schema_migrations table exists
    if "schema_migrations" not in inspector.get_table_names():
        return None
    
    with engine.begin() as conn:
        result = conn.execute(text("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"))
        row = result.fetchone()
        return row[0] if row else None


def set_migration_version(version: int) -> None:
    """Set the migration version in the database."""
    inspector = inspect(engine)
    
    # Create schema_migrations table if it doesn't exist
    if "schema_migrations" not in inspector.get_table_names():
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE schema_migrations (
                        version INTEGER PRIMARY KEY,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
    
    # Insert or update version
    with engine.begin() as conn:
        # Check if version exists
        result = conn.execute(
            text("SELECT version FROM schema_migrations WHERE version = :version"),
            {"version": version},
        )
        if result.fetchone():
            # Update timestamp
            conn.execute(
                text(
                    "UPDATE schema_migrations SET applied_at = CURRENT_TIMESTAMP WHERE version = :version"
                ),
                {"version": version},
            )
        else:
            # Insert new version
            conn.execute(
                text("INSERT INTO schema_migrations (version) VALUES (:version)"),
                {"version": version},
            )


def get_migration_files() -> list[tuple[int, Path]]:
    """Get all migration files, sorted by version number."""
    migrations_dir = Path(__file__).parent.parent.parent / "migrations"
    
    if not migrations_dir.exists():
        return []
    
    migrations = []
    for file in sorted(migrations_dir.glob("*.py")):
        if file.name.startswith("__"):
            continue
        
        # Extract version number from filename (e.g., "001_add_composed_video_columns.py" -> 1)
        try:
            version_str = file.stem.split("_")[0]
            version = int(version_str)
            migrations.append((version, file))
        except (ValueError, IndexError):
            continue
    
    return sorted(migrations, key=lambda x: x[0])


def run_migrations() -> None:
    """Run all pending migrations."""
    current_version = get_migration_version()
    migration_files = get_migration_files()
    
    if not migration_files:
        print("No migration files found")
        return
    
    # Filter to only pending migrations
    pending = [
        (version, path)
        for version, path in migration_files
        if current_version is None or version > current_version
    ]
    
    if not pending:
        print("✓ Database is up to date")
        return
    
    print(f"Found {len(pending)} pending migration(s)")
    
    for version, migration_path in pending:
        print(f"\nApplying migration {version}: {migration_path.name}...")
        
        # Import and run the migration
        # Add backend directory to path so we can import app modules
        backend_dir = migration_path.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        module_name = f"migrations.{migration_path.stem}"
        
        try:
            module = importlib.import_module(module_name)
            if not hasattr(module, "migrate"):
                print(f"  ✗ Migration {version} missing 'migrate' function")
                continue
            
            # Run migration
            module.migrate()
            
            # Record version
            set_migration_version(version)
            print(f"  ✓ Migration {version} applied successfully")
        except Exception as e:
            print(f"  ✗ Migration {version} failed: {e}")
            raise


if __name__ == "__main__":
    try:
        run_migrations()
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)

