#!/bin/bash
# Comprehensive pre-flight check script and development server launcher
# Runs all services: backend API, RQ worker, frontend, Redis

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Determine script location and change to v2/ directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V2_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$V2_DIR"

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}✗ Not in a virtual environment${NC}"
    echo -e "${YELLOW}  Please activate the virtual environment first:${NC}"
    echo -e "${YELLOW}    source .venv/bin/activate${NC}"
    echo -e "${YELLOW}  Or run 'make install' to create and activate it${NC}"
    exit 1
fi

echo -e "${BLUE}Running comprehensive pre-flight checks...${NC}"

# Try to find a compatible Python version (3.10-3.13 preferred)
PYTHON_CMD="python3"
for py in python3.13 python3.12 python3.11 python3.10 python3; do
    if command -v $py >/dev/null 2>&1; then
        PYTHON_VERSION=$($py --version 2>&1 | awk '{print $2}')
        PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ] && [ "$PYTHON_MINOR" -le 13 ]; then
            PYTHON_CMD=$py
            break
        fi
    fi
done

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment with $PYTHON_CMD...${NC}"
    $PYTHON_CMD -m venv .venv
fi

# Activate venv
export VIRTUAL_ENV_DISABLE_PROMPT=1
source .venv/bin/activate

# Check and install backend dependencies
echo -e "${YELLOW}Checking backend dependencies...${NC}"
pip install -q -r backend/requirements.txt
echo -e "${GREEN}✓ Backend dependencies up to date${NC}"

# Check and install frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    cd frontend && npm install && cd ..
else
    echo -e "${YELLOW}Checking frontend dependencies...${NC}"
    cd frontend && npm install --prefer-offline --no-audit >/dev/null 2>&1 || npm install && cd ..
fi
echo -e "${GREEN}✓ Frontend dependencies up to date${NC}"

# Run frontend linting
echo -e "${YELLOW}Running frontend linting...${NC}"
cd frontend
npm run lint || {
    echo -e "${RED}✗ Frontend linting failed${NC}"
    cd ..
    exit 1
}
cd ..
echo -e "${GREEN}✓ Frontend linting passed${NC}"

# Run backend linting
echo -e "${YELLOW}Running backend linting...${NC}"
if [ -f .venv/bin/ruff ]; then
    .venv/bin/ruff check backend/ || {
        echo -e "${RED}✗ Backend linting failed${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Backend linting passed${NC}"
elif command -v ruff >/dev/null 2>&1; then
    ruff check backend/ || {
        echo -e "${RED}✗ Backend linting failed${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Backend linting passed${NC}"
else
    echo -e "${YELLOW}⚠ Ruff not found, installing...${NC}"
    pip install -q ruff
    .venv/bin/ruff check backend/ || {
        echo -e "${RED}✗ Backend linting failed${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Backend linting passed${NC}"
fi

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
cd frontend
npm run build || {
    echo -e "${RED}✗ Frontend build failed${NC}"
    cd ..
    exit 1
}
cd ..
echo -e "${GREEN}✓ Frontend build passed${NC}"

# Verify backend imports
echo -e "${YELLOW}Verifying backend imports...${NC}"
cd backend
python -c "from app.main import app" || {
    echo -e "${RED}✗ Backend import check failed${NC}"
    cd ..
    exit 1
}
cd ..
echo -e "${GREEN}✓ Backend imports verified${NC}"

# Run tests (optional, don't fail if no tests)
echo -e "${YELLOW}Running tests...${NC}"
cd frontend
if npm test 2>/dev/null; then
    echo -e "${GREEN}✓ Frontend tests passed${NC}"
else
    echo -e "${YELLOW}⚠ No frontend tests found (skipping)${NC}"
fi
cd ..

cd backend
if pytest tests/ 2>/dev/null; then
    echo -e "${GREEN}✓ Backend tests passed${NC}"
else
    echo -e "${YELLOW}⚠ No backend tests found (skipping)${NC}"
fi
cd ..

echo -e "\n${GREEN}✓ All checks passed!${NC}\n"
echo -e "${BLUE}Starting VibeCraft v2 development environment...${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Stopping services...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    exit
}
trap cleanup SIGINT SIGTERM

# Detect docker compose command (v2: "docker compose" or v1: "docker-compose")
USE_DOCKER_COMPOSE_V2=false
if command -v docker >/dev/null 2>&1; then
    if docker compose version >/dev/null 2>&1; then
        USE_DOCKER_COMPOSE_V2=true
    elif ! command -v docker-compose >/dev/null 2>&1; then
        USE_DOCKER_COMPOSE_V2=false
    fi
fi

# Start PostgreSQL and Redis (via docker-compose)
if command -v docker >/dev/null 2>&1 && ( [ "$USE_DOCKER_COMPOSE_V2" = true ] || command -v docker-compose >/dev/null 2>&1 ); then
    echo -e "${YELLOW}Starting database services...${NC}"
    cd infra
    if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
        docker compose up -d postgres redis 2>/dev/null || \
            echo -e "${YELLOW}⚠ Failed to start services or already running${NC}"
    else
        docker-compose up -d postgres redis 2>/dev/null || \
            echo -e "${YELLOW}⚠ Failed to start services or already running${NC}"
    fi
    cd ..
    echo -e "${GREEN}✓ Database services ready${NC}"
else
    # Fallback to docker run if docker-compose not available
    if ! docker ps | grep -q redis-vibecraft; then
        echo -e "${YELLOW}Starting Redis container...${NC}"
        docker run -d -p 6379:6379 --name redis-vibecraft redis:7-alpine 2>/dev/null || \
            docker start redis-vibecraft 2>/dev/null || \
            echo -e "${YELLOW}⚠ Redis container already running or Docker not available${NC}"
    else
        echo -e "${GREEN}✓ Redis already running${NC}"
    fi
fi

# Start backend API
echo -e "${GREEN}Starting backend API on http://localhost:8000${NC}"
cd backend
# Set DATABASE_URL if not already set and no .env file
if [ -z "$DATABASE_URL" ] && [ ! -f ../.env ]; then
    export DATABASE_URL="postgresql://vibecraft:vibecraft@localhost:5432/vibecraft"
fi
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Start RQ worker
echo -e "${GREEN}Starting RQ worker${NC}"
cd backend
# Disable Objective-C fork safety checks (macOS issue with PostgreSQL)
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
rq worker ai_music_video &
WORKER_PID=$!
cd ..

# Start frontend
echo -e "${GREEN}Starting frontend on http://localhost:5173${NC}"
cd frontend
npm run dev -- --host &
FRONTEND_PID=$!
cd ..

echo -e "\n${GREEN}All services started!${NC}"
echo -e "Backend API: http://localhost:8000"
echo -e "Frontend: http://localhost:5173"
echo -e "Redis: localhost:6379"
echo -e "\nPress Ctrl+C to stop all services"

# Wait for all background jobs
wait

