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

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
make migrate || {
    echo -e "${RED}✗ Migration failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ Migrations complete${NC}\n"

echo -e "${BLUE}Starting VibeCraft development environment...${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${BLUE}Stopping services...${NC}"
    # Kill all worker processes
    if [ -n "${WORKER_PIDS:-}" ]; then
        for pid in "${WORKER_PIDS[@]}"; do
            kill "$pid" 2>/dev/null || true
        done
    fi
    # Kill other background jobs
    kill $(jobs -p) 2>/dev/null || true
    exit
}
trap cleanup SIGINT SIGTERM

# Create logs directory (use absolute path from project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOG_DIR="${PROJECT_ROOT}/logs"
mkdir -p "${LOG_DIR}"
BACKEND_LOG="${LOG_DIR}/backend.log"
WORKER_LOG="${LOG_DIR}/worker.log"
FRONTEND_LOG="${LOG_DIR}/frontend.log"
COMBINED_LOG="${LOG_DIR}/combined.log"

# Clear old logs
> "${BACKEND_LOG}"
> "${WORKER_LOG}"
> "${FRONTEND_LOG}"
> "${COMBINED_LOG}"

echo -e "${GREEN}Starting backend API on http://localhost:8000${NC}"
echo -e "${BLUE}Backend logs: ${BACKEND_LOG}${NC}"
cd backend
# Use nohup to ensure logs are written even when backgrounded
# Use custom log config to add timestamps to access logs
nohup uvicorn app.main:app --reload --log-config logging_config.json > "${BACKEND_LOG}" 2>&1 &
BACKEND_PID=$!
cd ..

# Clear RQ queue before starting worker
echo -e "${YELLOW}Clearing RQ queue...${NC}"
cd backend
python3 -c "
import os
import sys
sys.path.insert(0, '.')
from app.core.config import get_settings
from app.core.queue import get_queue

try:
    settings = get_settings()
    queue = get_queue()
    queue_name = queue.name
    
    # Count jobs before clearing
    job_count = len(queue)
    
    # Clear the queue
    if job_count > 0:
        queue.empty()
        print(f'✓ Cleared {job_count} pending job(s) from queue: {queue_name}')
    else:
        print(f'✓ Queue {queue_name} is already empty (0 jobs)')
except Exception as e:
    print(f'⚠ Failed to clear queue: {e}')
    sys.exit(1)
" || {
    echo -e "${RED}⚠ Failed to clear queue (continuing anyway)${NC}"
}
cd ..

# Start RQ workers (multiple workers for parallel processing)
# RQ workers process one job at a time, so we need multiple workers for concurrency
NUM_WORKERS=4  # Match DEFAULT_MAX_CONCURRENCY in constants.py
echo -e "${GREEN}Starting ${NUM_WORKERS} RQ workers for parallel processing${NC}"
echo -e "${BLUE}Worker logs: ${WORKER_LOG}${NC}"
cd backend
# Disable Objective-C fork safety checks to prevent crashes in forked processes (macOS issue)
# This is needed when RQ workers fork and try to connect to PostgreSQL
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
# Preserve BEAT_EFFECT_TEST_MODE if set (for exaggerated beat effects testing)
if [ -n "${BEAT_EFFECT_TEST_MODE:-}" ]; then
    export BEAT_EFFECT_TEST_MODE="${BEAT_EFFECT_TEST_MODE}"
    echo -e "${YELLOW}⚠ Beat effect test mode enabled (exaggerated effects)${NC}"
fi
# Preserve SAVE_NO_EFFECTS_VIDEO if set (for comparison video saving)
if [ -n "${SAVE_NO_EFFECTS_VIDEO:-}" ]; then
    export SAVE_NO_EFFECTS_VIDEO="${SAVE_NO_EFFECTS_VIDEO}"
    echo -e "${YELLOW}⚠ Saving no-effects comparison videos enabled${NC}"
fi
# Start multiple worker processes for parallel job processing
WORKER_PIDS=()
for i in $(seq 1 ${NUM_WORKERS}); do
    # Use env to explicitly pass environment variables to nohup (ensures they're preserved)
    nohup env BEAT_EFFECT_TEST_MODE="${BEAT_EFFECT_TEST_MODE:-}" SAVE_NO_EFFECTS_VIDEO="${SAVE_NO_EFFECTS_VIDEO:-}" OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES rq worker ai_music_video > "${WORKER_LOG}.${i}" 2>&1 &
    WORKER_PIDS+=($!)
    echo -e "${BLUE}  Worker ${i} started (PID: $!)${NC}"
done
cd ..

# Start frontend
echo -e "${GREEN}Starting frontend on http://localhost:5173${NC}"
echo -e "${BLUE}Frontend logs: ${FRONTEND_LOG}${NC}"
cd frontend
nohup npm run dev -- --host > "${FRONTEND_LOG}" 2>&1 &
FRONTEND_PID=$!
cd ..

echo -e "\n${GREEN}All services started!${NC}"
echo -e "Backend: http://localhost:8000"
echo -e "Frontend: http://localhost:5173"
echo -e "\n${BLUE}Log files:${NC}"
echo -e "  Backend: ${BACKEND_LOG}"
echo -e "  Workers: ${WORKER_LOG}.1, ${WORKER_LOG}.2, ${WORKER_LOG}.3, ${WORKER_LOG}.4"
echo -e "  Frontend: ${FRONTEND_LOG}"
echo -e "  Combined: ${COMBINED_LOG}"
echo -e "\nPress Ctrl+C to stop all services"

# Wait for all background jobs
wait

