#!/usr/bin/env python3
"""Standalone script to run migrations with better error handling."""

import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

def main():
    # Debug: Print DATABASE_URL (masked)
    db_url = os.getenv("DATABASE_URL", "NOT SET")
    if db_url != "NOT SET":
        # Mask password in URL
        if "@" in db_url:
            parts = db_url.split("@")
            if len(parts) == 2:
                user_pass = parts[0].split("://")[-1]
                masked = db_url.replace(user_pass, "***", 1)
                print(f"DATABASE_URL: {masked}")
            else:
                print(f"DATABASE_URL: {db_url[:50]}...")
        else:
            print(f"DATABASE_URL: {db_url[:50]}...")
    else:
        print("ERROR: DATABASE_URL environment variable is not set!")
        print("\nTo set it manually:")
        print("1. Go to Railway Dashboard → PostgreSQL service → Variables")
        print("2. Copy the DATABASE_URL value")
        print("3. Run: DATABASE_URL='<value>' python run_migrations.py")
        sys.exit(1)
    
    # Check if it looks like a reference variable
    if "${{" in db_url or "${" in db_url:
        print("\nWARNING: DATABASE_URL appears to be a reference variable that didn't resolve!")
        print("This means Railway's reference variable syntax isn't working in this context.")
        print("\nTry one of these:")
        print("1. Get the actual DATABASE_URL from Railway Dashboard → PostgreSQL → Variables")
        print("2. Set it manually: DATABASE_URL='<actual-url>' python run_migrations.py")
        sys.exit(1)
    
    # Check if hostname is missing
    if "://" in db_url:
        scheme, rest = db_url.split("://", 1)
        if "@" in rest:
            user_pass, host_db = rest.split("@", 1)
            if "/" in host_db:
                host_port, db = host_db.split("/", 1)
                if ":" in host_port:
                    host, port = host_port.split(":", 1)
                    if not host or host.strip() == "":
                        print("\nERROR: Database hostname is empty in DATABASE_URL!")
                        print("This usually means the reference variable didn't resolve.")
                        sys.exit(1)
    
    print("\nRunning migrations...")
    try:
        from app.core.migrations import run_migrations
        run_migrations()
        print("\n✓ Migrations completed successfully!")
    except Exception as e:
        print(f"\n✗ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

