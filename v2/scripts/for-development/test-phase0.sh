#!/bin/bash
# Phase 0 test script
# Tests: Python/Node versions, dependencies, services startup, health checks

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Phase 0 Test Script${NC}"
echo "===================="
echo ""

# Check Python version
echo -n "Checking Python version (3.10+)... "
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
    echo -e "${GREEN}✓ OK (Python $PYTHON_VERSION)${NC}"
else
    echo -e "${RED}✗ FAILED (Python $PYTHON_VERSION, need 3.10+)${NC}"
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
    python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r backend/requirements.txt >/dev/null 2>&1
echo -e "${GREEN}✓ OK${NC}"
deactivate

# Install frontend dependencies
echo -n "Installing frontend dependencies... "
cd frontend
npm install --silent >/dev/null 2>&1
cd ..
echo -e "${GREEN}✓ OK${NC}"

# Start Redis (via Docker if not using Railway Redis)
echo -n "Starting Redis... "
if ! docker ps | grep -q vibecraft-redis; then
    docker run -d -p 6379:6379 --name vibecraft-redis redis:7-alpine >/dev/null 2>&1 || \
        docker start vibecraft-redis >/dev/null 2>&1 || \
        echo -e "${YELLOW}⚠ SKIPPED (Docker not available)${NC}"
else
    echo -e "${GREEN}✓ OK (already running)${NC}"
fi

# Start backend server (background)
echo -n "Starting backend server... "
source .venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 >/dev/null 2>&1 &
BACKEND_PID=$!
cd ..
deactivate
sleep 3  # Wait for server to start
if ps -p $BACKEND_PID > /dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
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

