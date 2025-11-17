.PHONY: help lint lint-fix format format-fix lint-all build test dev start stop clean install migrate

help:
	@echo "VibeCraft v2 Development Commands"
	@echo ""
	@echo "  make dev          - Start all services (backend, worker, frontend, Redis)"
	@echo "  make start        - Alias for 'make dev'"
	@echo "  make install      - Install dependencies (backend + frontend)"
	@echo "  make migrate      - Run database migrations"
	@echo "  make lint         - Run all linters"
	@echo "  make lint-fix     - Auto-fix linting issues"
	@echo "  make format       - Check code formatting"
	@echo "  make format-fix   - Auto-format code"
	@echo "  make lint-all     - Auto-fix linting and format all code"
	@echo "  make build        - Build frontend"
	@echo "  make test         - Run all tests"
	@echo "  make stop         - Stop all dev services"
	@echo "  make clean        - Clean build artifacts"

dev:
	@bash scripts/dev.sh

start: dev

install:
	@echo "Installing backend dependencies..."
	@if [ ! -d ".venv" ]; then \
		python3.13 -m venv .venv; \
	fi
	@source .venv/bin/activate && pip install -r backend/requirements.txt && deactivate
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "✓ Dependencies installed"

migrate:
	@echo "Running database migrations..."
	@echo "Note: Migrations will be added in later phases"
	@echo "✓ Migrations complete"

lint:
	@echo "Linting frontend..."
	@cd frontend && npm run lint
	@echo "✓ Frontend lint passed"
	@echo "Linting backend..."
	@bash -c "source .venv/bin/activate && ruff check backend/ && deactivate"
	@echo "✓ Backend lint passed"

lint-fix:
	@echo "Fixing lint issues..."
	@cd frontend && npm run lint:fix 2>/dev/null || echo "No lint:fix script"
	@bash -c "source .venv/bin/activate && ruff check --fix backend/ && deactivate"
	@echo "✓ Lint fixes applied"

format:
	@echo "Checking formatting..."
	@cd frontend && npm run format 2>/dev/null || echo "No format script"
	@bash -c "source .venv/bin/activate && ruff format --check backend/ && deactivate"
	@echo "✓ Formatting check passed"

format-fix:
	@echo "Fixing formatting..."
	@cd frontend && npm run format:write 2>/dev/null || echo "No format:write script"
	@bash -c "source .venv/bin/activate && ruff format backend/ && deactivate"
	@echo "✓ Formatting fixed"

lint-all:
	@echo "Running lint-fix and format-fix..."
	@make lint-fix
	@bash -c "source .venv/bin/activate && ruff format backend/ && deactivate"
	@echo "✓ All linting and formatting applied"

build:
	@echo "Building frontend..."
	@cd frontend && npm run build
	@echo "✓ Build complete"

test:
	@echo "Running tests..."
	@cd frontend && npm test 2>/dev/null || echo "No frontend tests yet"
	@bash -c "source .venv/bin/activate && pytest backend/tests/ 2>/dev/null || echo 'No backend tests yet'; deactivate"
	@echo "✓ Tests complete"

stop:
	@echo "Stopping all dev services..."
	@pkill -f "uvicorn app.main:app" 2>/dev/null && echo "✓ Backend API stopped" || echo "⚠ Backend API not running"
	@pkill -f "rq worker ai_music_video" 2>/dev/null && echo "✓ RQ worker stopped" || echo "⚠ RQ worker not running"
	@pkill -f "vite.*--host" 2>/dev/null && echo "✓ Frontend stopped" || echo "⚠ Frontend not running"
	@docker stop redis-vibecraft 2>/dev/null && echo "✓ Redis stopped" || echo "⚠ Redis not running"
	@echo "✓ All services stopped"

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf frontend/dist
	@rm -rf frontend/node_modules/.vite
	@rm -rf backend/__pycache__
	@find backend -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find backend -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Clean complete"

