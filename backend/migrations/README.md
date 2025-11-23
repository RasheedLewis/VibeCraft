# Database Migrations

This directory contains database migration scripts that update the schema incrementally.

## Migration Naming Convention

Migrations must be named with a version number prefix:
- `001_description.py`
- `002_another_change.py`
- `003_yet_another_change.py`

The version number determines the order in which migrations are applied.

## Migration Structure

Each migration file must contain a `migrate()` function:

```python
from sqlalchemy import inspect, text
from app.core.database import engine

def migrate() -> None:
    """Description of what this migration does."""
    # Your migration code here
    pass
```

## Running Migrations

Run all pending migrations:
```bash
make migrate
```

Or directly:
```bash
cd backend
source ../.venv/bin/activate
python -m app.core.migrations
```

## Migration Tracking

The migration system tracks applied migrations in a `schema_migrations` table:
- Each migration version is recorded after successful application
- Only pending migrations (versions higher than current) are applied
- Migrations are applied in order by version number

## Creating a New Migration

1. Create a new file in `backend/migrations/` with the next version number
2. Name it descriptively: `XXX_description.py`
3. Implement the `migrate()` function
4. Test it locally
5. Commit the migration file

Example:
```python
# backend/migrations/002_add_user_email_column.py

def migrate() -> None:
    """Add email column to users table."""
    from sqlalchemy import inspect, text
    from app.core.database import engine
    
    inspector = inspect(engine)
    existing_columns = {col["name"] for col in inspector.get_columns("users")}
    
    if "email" not in existing_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN email VARCHAR(255)"))
```

