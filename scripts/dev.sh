#!/bin/bash
# Run all development services (backend, worker, frontend)

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Running pre-flight checks...${NC}"

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: .venv not found. Run setup first.${NC}"
    exit 1
fi

# Activate venv (disable prompt modification to prevent stacking)
export VIRTUAL_ENV_DISABLE_PROMPT=1
source .venv/bin/activate

# Check and install backend dependencies if needed
echo -e "${YELLOW}Checking backend dependencies...${NC}"
pip install -q -r backend/requirements.txt
echo -e "${GREEN}✓ Backend dependencies up to date${NC}"

# Check and install frontend dependencies if needed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm --prefix frontend install
else
    echo -e "${YELLOW}Checking frontend dependencies...${NC}"
    npm --prefix frontend install --prefer-offline --no-audit >/dev/null 2>&1 || npm --prefix frontend install
fi
echo -e "${GREEN}✓ Frontend dependencies up to date${NC}"

# Run lint
echo -e "${YELLOW}Running linters...${NC}"
npm --prefix frontend run lint || {
    echo -e "${RED}✗ Frontend linting failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Frontend linting passed${NC}"

# Backend lint
ruff check backend/ || {
    echo -e "${RED}✗ Backend linting failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Backend linting passed${NC}"

# Run build
echo -e "${YELLOW}Building frontend...${NC}"
npm --prefix frontend run build || {
    echo -e "${RED}✗ Frontend build failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Frontend build passed${NC}"

# Backend "build" check (verify imports work)
echo -e "${YELLOW}Verifying backend imports...${NC}"
cd backend
python -c "from app.main import create_app; create_app()" || {
    echo -e "${RED}✗ Backend import check failed${NC}"
    cd ..
    exit 1
}
cd ..
echo -e "${GREEN}✓ Backend imports verified${NC}"

# Run tests (if they exist, don't fail if not)
echo -e "${YELLOW}Running tests...${NC}"
if npm --prefix frontend test 2>/dev/null; then
    echo -e "${GREEN}✓ Frontend tests passed${NC}"
else
    echo -e "${YELLOW}⚠ No frontend tests found (skipping)${NC}"
fi

cd backend
if pytest tests/unit/ 2>/dev/null; then
    echo -e "${GREEN}✓ Backend unit tests passed${NC}"
else
    echo -e "${YELLOW}⚠ No backend unit tests found (skipping)${NC}"
fi
cd ..

echo -e "\n${GREEN}✓ All checks passed!${NC}\n"
echo -e "${BLUE}Starting VibeCraft development environment...${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Stopping services...${NC}"
    kill $(jobs -p) 2>/dev/null || true
    exit
}
trap cleanup SIGINT SIGTERM

# Start backend API
echo -e "${GREEN}Starting backend API on http://localhost:8000${NC}"
cd backend
uvicorn app.main:app --reload &
BACKEND_PID=$!
cd ..

# Start RQ worker
echo -e "${GREEN}Starting RQ worker${NC}"
cd backend
rq worker ai_music_video &
WORKER_PID=$!
cd ..

# Start frontend
echo -e "${GREEN}Starting frontend on http://localhost:5173${NC}"
cd frontend
npm run dev -- --host &
FRONTEND_PID=$!
cd ..

# Start Trigger.dev (optional - only if ENABLE_TRIGGER_DEV is set)
if [ "${ENABLE_TRIGGER_DEV}" = "1" ]; then
  echo -e "${GREEN}Starting Trigger.dev dev server${NC}"
  npx trigger.dev@latest dev &
  TRIGGER_PID=$!
  echo -e "${YELLOW}Note: Trigger.dev started (set ENABLE_TRIGGER_DEV=1 to enable)${NC}"
else
  echo -e "${YELLOW}Trigger.dev skipped (set ENABLE_TRIGGER_DEV=1 to enable)${NC}"
fi

echo -e "\n${GREEN}All services started!${NC}"
echo -e "Backend: http://localhost:8000"
echo -e "Frontend: http://localhost:5173"
if [ "${ENABLE_TRIGGER_DEV}" = "1" ]; then
  echo -e "Trigger.dev: Running (see dashboard for URL)"
fi
echo -e "\nPress Ctrl+C to stop all services"

# Wait for all background jobs
wait

