#!/bin/bash
# Helper script to run database queries
# Usage: ./run_query.sh [query_file.sql] or ./run_query.sh -c "SELECT ..."

set -e

# Find backend .env file
ENV_FILE="../backend/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: Could not find $ENV_FILE"
    exit 1
fi

# Extract and convert DATABASE_URL
DATABASE_URL=$(grep "^DATABASE_URL=" "$ENV_FILE" | cut -d'=' -f2- | sed 's/postgresql+psycopg:/postgresql:/')

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL not found in $ENV_FILE"
    exit 1
fi

# Run query
if [ "$1" = "-c" ]; then
    # Inline query
    psql "$DATABASE_URL" -c "$2"
elif [ -n "$1" ]; then
    # Query file
    psql "$DATABASE_URL" -f "$1"
else
    # Default: run the simple query
    psql "$DATABASE_URL" -f get_prompt_and_lyrics_simple.sql
fi

