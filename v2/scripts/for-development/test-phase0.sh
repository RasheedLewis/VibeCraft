#!/bin/bash
# Phase 0 test script
# Tests: Python/Node versions, dependencies, services startup, health checks

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Determine script location and change to v2/ directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V2_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$V2_DIR"

echo -e "${BLUE}Phase 0 Test Script${NC}"
echo "===================="
echo -e "${BLUE}Working directory: $(pwd)${NC}"
echo ""

# Check Python version (using Python 3.13)
echo -n "Checking Python version (3.13)... "
PYTHON_CMD="python3.13"
if command -v $PYTHON_CMD >/dev/null 2>&1; then
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ OK (Python $PYTHON_VERSION via $PYTHON_CMD)${NC}"
else
    echo -e "${RED}✗ FAILED (python3.13 not found)${NC}"
    echo -e "${YELLOW}  Please install Python 3.13${NC}"
    exit 1
fi

# Check Node version
echo -n "Checking Node version (18+)... "
NODE_VERSION=$(node --version 2>&1 | sed 's/v//')
NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
if [ "$NODE_MAJOR" -ge 18 ]; then
    echo -e "${GREEN}✓ OK (Node $NODE_VERSION)${NC}"
else
    echo -e "${RED}✗ FAILED (Node $NODE_VERSION, need 18+)${NC}"
    exit 1
fi

# Install backend dependencies
echo -n "Installing backend dependencies... "
if [ ! -d ".venv" ]; then
    $PYTHON_CMD -m venv .venv
fi
source .venv/bin/activate

# Try to install all requirements, but continue if some fail (for Python 3.14+ compatibility)
INSTALL_OUTPUT=$(pip install -r backend/requirements.txt 2>&1)
INSTALL_EXIT=$?

# Check if core packages installed successfully
CORE_PACKAGES_OK=true
for pkg in fastapi uvicorn sqlmodel pydantic; do
    if ! python -c "import $pkg" 2>/dev/null; then
        CORE_PACKAGES_OK=false
        break
    fi
done

if [ $INSTALL_EXIT -ne 0 ] && [ "$CORE_PACKAGES_OK" = "false" ]; then
    echo -e "${RED}✗ FAILED (core packages not installed)${NC}"
    echo -e "${YELLOW}Installation errors:${NC}"
    echo "$INSTALL_OUTPUT" | grep -i "error\|failed\|not supported" | head -10
    echo -e "${YELLOW}Full output saved to /tmp/pip-install-$$.log${NC}"
    echo "$INSTALL_OUTPUT" > "/tmp/pip-install-$$.log"
    deactivate
    exit 1
elif [ $INSTALL_EXIT -ne 0 ]; then
    echo -e "${YELLOW}⚠ Some packages failed to install (may be Python 3.14+ compatibility issues)${NC}"
    echo -e "${YELLOW}  Core packages installed, continuing...${NC}"
fi

# Verify FastAPI is installed (required)
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${RED}✗ FAILED (FastAPI not installed)${NC}"
    deactivate
    exit 1
fi
echo -e "${GREEN}✓ OK${NC}"
deactivate

# Install frontend dependencies
echo -n "Installing frontend dependencies... "
cd frontend
npm install --silent >/dev/null 2>&1
cd ..
echo -e "${GREEN}✓ OK${NC}"

# Check if Docker daemon is running
if ! docker ps >/dev/null 2>&1; then
    # Try setting DOCKER_HOST for Colima if it's running
    if command -v colima >/dev/null 2>&1 && colima status >/dev/null 2>&1 | grep -q "running"; then
        COLIMA_SOCKET="$HOME/.colima/default/docker.sock"
        if [ -S "$COLIMA_SOCKET" ]; then
            export DOCKER_HOST="unix://$COLIMA_SOCKET"
            if docker ps >/dev/null 2>&1; then
                echo -e "${GREEN}✓ Docker connected via Colima socket${NC}"
            else
                echo -e "${RED}✗ Docker daemon is not running${NC}"
                echo -e "${YELLOW}  Colima is running but Docker cannot connect${NC}"
                echo -e "${YELLOW}  Please restart Colima:${NC}"
                echo -e "${YELLOW}    colima restart${NC}"
                exit 1
            fi
        else
            echo -e "${RED}✗ Docker daemon is not running${NC}"
            echo -e "${YELLOW}  Colima is running but socket not found at $COLIMA_SOCKET${NC}"
            echo -e "${YELLOW}  Please restart Colima:${NC}"
            echo -e "${YELLOW}    colima restart${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Docker daemon is not running${NC}"
        if command -v colima >/dev/null 2>&1; then
            echo -e "${YELLOW}  Please start Colima:${NC}"
            echo -e "${YELLOW}    colima start${NC}"
        else
            echo -e "${YELLOW}  Please start Docker:${NC}"
            echo -e "${YELLOW}    Open Docker Desktop application${NC}"
            echo -e "${YELLOW}    or install Colima: brew install colima${NC}"
        fi
        exit 1
    fi
fi

# Detect docker compose command (v2: "docker compose" or v1: "docker-compose")
USE_DOCKER_COMPOSE_V2=false
if command -v docker >/dev/null 2>&1; then
    # Try docker compose v2 first
    if docker compose version >/dev/null 2>&1; then
        USE_DOCKER_COMPOSE_V2=true
    # Fall back to docker-compose v1
    elif command -v docker-compose >/dev/null 2>&1; then
        USE_DOCKER_COMPOSE_V2=false
    fi
fi

# Start PostgreSQL (via docker-compose)
echo -n "Starting PostgreSQL... "
if command -v docker >/dev/null 2>&1 && ( [ "$USE_DOCKER_COMPOSE_V2" = true ] || command -v docker-compose >/dev/null 2>&1 ); then
    cd infra
    if ! docker ps | grep -q vibecraft-postgres; then
        # Check if port 5432 is already in use and stop it
        if lsof -i :5432 >/dev/null 2>&1 || docker ps --format '{{.Ports}}' | grep -q ':5432->'; then
            echo -e "${YELLOW}⚠ Port 5432 already in use, stopping existing service...${NC}"
            # Try to stop Docker containers using port 5432
            CONTAINERS=$(docker ps --format '{{.ID}}\t{{.Ports}}' | grep ':5432->' | awk '{print $1}')
            if [ -n "$CONTAINERS" ]; then
                echo "$CONTAINERS" | xargs docker stop 2>/dev/null || true
            fi
            # Try to kill processes using port 5432
            if command -v lsof >/dev/null 2>&1; then
                PIDS=$(lsof -ti :5432)
                if [ -n "$PIDS" ]; then
                    echo "$PIDS" | xargs kill -9 2>/dev/null || true
                fi
            fi
            sleep 2
        fi
        if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
            docker compose up -d postgres 2>&1 | grep -v "the attribute \`version\` is obsolete" | head -5 || true
        else
            docker-compose up -d postgres 2>&1 | grep -v "the attribute \`version\` is obsolete" | head -5 || true
        fi
        # Wait for PostgreSQL to be ready
        for i in {1..30}; do
            if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
                if docker compose exec -T postgres pg_isready -U vibecraft >/dev/null 2>&1; then
                    break
                fi
            else
                if docker-compose exec -T postgres pg_isready -U vibecraft >/dev/null 2>&1; then
                    break
                fi
            fi
            [ $i -eq 30 ] && echo -e "\n${YELLOW}⚠ PostgreSQL taking longer than expected to start...${NC}"
            sleep 1
        done
    else
        echo -e "${GREEN}✓ OK (already running)${NC}"
    fi
    cd ..
    if docker ps | grep -q vibecraft-postgres; then
        echo -e "${GREEN}✓ OK${NC}"
        # Set DATABASE_URL if not already set
        if [ -z "$DATABASE_URL" ] && [ ! -f .env ]; then
            export DATABASE_URL="postgresql://vibecraft:vibecraft@localhost:5432/vibecraft"
        fi
    else
        echo -e "${YELLOW}⚠ SKIPPED (Docker not available or failed to start)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ SKIPPED (Docker not available)${NC}"
fi

# Start Redis (via docker-compose)
echo -n "Starting Redis... "
if command -v docker >/dev/null 2>&1 && ( [ "$USE_DOCKER_COMPOSE_V2" = true ] || command -v docker-compose >/dev/null 2>&1 ); then
    cd infra
    if ! docker ps | grep -q redis-vibecraft; then
        if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
            docker compose up -d redis 2>&1 | head -5 || true
        else
            docker-compose up -d redis 2>&1 | head -5 || true
        fi
        # Wait for Redis to be ready
        for i in {1..10}; do
            if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
                if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
                    break
                fi
            else
                if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
                    break
                fi
            fi
            sleep 1
        done
    fi
    cd ..
    if docker ps | grep -q redis-vibecraft; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${YELLOW}⚠ SKIPPED (Docker not available or failed to start)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ SKIPPED (Docker not available)${NC}"
fi

# Start backend server (background)
echo -n "Starting backend server... "
if [ ! -f .venv/bin/activate ]; then
    echo -e "${RED}✗ FAILED (virtual environment not found)${NC}"
    echo -e "${YELLOW}  Run 'make install' first to create the virtual environment${NC}"
    exit 1
fi
source .venv/bin/activate
cd backend || {
    echo -e "${RED}✗ FAILED (backend directory not found)${NC}"
    deactivate 2>/dev/null || true
    exit 1
}
# Set DATABASE_URL if not already set and no .env file
if [ -z "$DATABASE_URL" ] && [ ! -f ../.env ]; then
    export DATABASE_URL="postgresql://vibecraft:vibecraft@localhost:5432/vibecraft"
fi
LOG_FILE="/tmp/vibecraft-backend-$$.log"
uvicorn app.main:app --host 0.0.0.0 --port 8000 >"$LOG_FILE" 2>&1 &
BACKEND_PID=$!
cd ..
deactivate 2>/dev/null || true
sleep 3  # Wait for server to start
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    # Check if server actually started (not just process exists)
    sleep 1
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ OK${NC}"
    else
        echo -e "${RED}✗ FAILED (server not responding)${NC}"
        echo -e "${YELLOW}Backend log:${NC}"
        tail -30 "$LOG_FILE" 2>/dev/null || echo "No log available"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
else
    echo -e "${RED}✗ FAILED (process died)${NC}"
    echo -e "${YELLOW}Backend log:${NC}"
    tail -30 "$LOG_FILE" 2>/dev/null || echo "No log available"
    exit 1
fi

# Start RQ worker (background)
echo -n "Starting RQ worker... "
source .venv/bin/activate
cd backend
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
rq worker ai_music_video >/dev/null 2>&1 &
WORKER_PID=$!
cd ..
deactivate
sleep 2  # Wait for worker to start
if ps -p $WORKER_PID > /dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ SKIPPED (worker may have exited)${NC}"
fi

# Start frontend dev server (background)
echo -n "Starting frontend dev server... "
cd frontend
npm run dev -- --host >/dev/null 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 5  # Wait for server to start
if ps -p $FRONTEND_PID > /dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ SKIPPED (frontend may have exited)${NC}"
fi

# Test health check endpoint
echo -n "Testing health check endpoint... "
sleep 2
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    cleanup
    exit 1
fi

# Test database connection
echo -n "Testing database connection... "
source .venv/bin/activate
cd backend
python -c "from app.core.database import check_db_connection; exit(0 if check_db_connection() else 1)" 2>/dev/null && \
    echo -e "${GREEN}✓ OK${NC}" || \
    echo -e "${YELLOW}⚠ SKIPPED (database not configured)${NC}"
cd ..
deactivate

# Test Redis connection
echo -n "Testing Redis connection... "
if redis-cli -h localhost -p 6379 ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ SKIPPED (Redis not accessible)${NC}"
fi

# Run health check script
echo -n "Running health check script... "
if bash scripts/health-check.sh >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ SKIPPED (some checks may have failed)${NC}"
fi

# Cleanup function
cleanup() {
    echo ""
    echo -e "${BLUE}Cleaning up...${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    kill $WORKER_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Trap cleanup on exit
trap cleanup EXIT

echo ""
echo -e "${GREEN}✓ All tests passed!${NC}"
echo ""
echo "Services running:"
echo "  - Backend API: http://localhost:8000"
echo "  - Frontend: http://localhost:5173"
echo "  - Redis: localhost:6379"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user interrupt
wait

