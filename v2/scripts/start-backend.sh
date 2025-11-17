#!/bin/bash
# Start backend server in foreground for better log visibility
# This is useful when either
#  (a) you don't want interleaved frontend/backend/redis logs from `make start`, or
#  (b) you only need to run the backend
# Usage: bash scripts/start-backend.sh

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Determine script location and change to v2/ directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V2_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$V2_DIR"

echo -e "${BLUE}Starting backend server...${NC}"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Run 'make install' first.${NC}"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Set DATABASE_URL if not already set and no .env file
if [ -z "$DATABASE_URL" ] && [ ! -f ".env" ]; then
    export DATABASE_URL="postgresql://vibecraft:vibecraft@localhost:5432/vibecraft"
fi

# Start backend in foreground (logs will be visible)
cd backend
echo -e "${GREEN}Backend API starting on http://localhost:8000${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

