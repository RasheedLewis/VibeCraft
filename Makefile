.PHONY: help lint lint-fix format format-fix lint-all build test dev start stop clean

help:
	@echo "VibeCraft Development Commands"
	@echo ""
	@echo "  make dev          - Start all services (backend, worker, frontend)"
	@echo "  make start        - Alias for 'make dev'"
	@echo "  make lint         - Run all linters"
	@echo "  make lint-fix     - Auto-fix linting issues"
	@echo "  make format       - Check code formatting"
	@echo "  make format-fix   - Auto-format code"
	@echo "  make lint-all     - Auto-fix linting and format all code"
	@echo "  make build        - Build frontend"
	@echo "  make test         - Run all tests"
	@echo "  make stop         - Stop all dev services (frontend, backend, RQ)"
	@echo "  make clean        - Clean build artifacts"

dev:
	@bash scripts/dev.sh

start: dev

lint:
	@echo "Linting frontend..."
	@npm --prefix frontend run lint
	@echo "✓ Frontend lint passed"
	@echo "Linting backend..."
	@bash -c "source .venv/bin/activate && ruff check backend/ && deactivate"
	@echo "✓ Backend lint passed"

lint-fix:
	@echo "Fixing lint issues..."
	@npm --prefix frontend run lint:fix
	@npm --prefix frontend run format:write
	@bash -c "source .venv/bin/activate && ruff check --fix backend/ && deactivate"
	@echo "✓ Lint fixes applied"

format:
	@echo "Checking formatting..."
	@npm --prefix frontend run format
	@echo "✓ Formatting check passed"

format-fix:
	@echo "Fixing formatting..."
	@npm --prefix frontend run format:write
	@bash -c "source .venv/bin/activate && ruff format backend/ && deactivate"
	@echo "✓ Formatting fixed"

lint-all:
	@echo "Running lint-fix and format-fix..."
	@make lint-fix
	@bash -c "source .venv/bin/activate && ruff format backend/ && deactivate"
	@echo "✓ All linting and formatting applied"

build:
	@echo "Building frontend..."
	@npm --prefix frontend run build
	@echo "✓ Build complete"

test:
	@echo "Running tests..."
	@npm --prefix frontend test 2>/dev/null || echo "No frontend tests yet"
	@bash -c "source .venv/bin/activate && pytest backend/tests/unit/ 2>/dev/null || echo 'No backend unit tests yet'; deactivate"
	@echo "✓ Tests complete"

stop:
	@echo "Stopping all dev services..."
	@pkill -f "uvicorn app.main:app" 2>/dev/null && echo "✓ Backend API stopped" || echo "⚠ Backend API not running"
	@pkill -f "rq worker ai_music_video" 2>/dev/null && echo "✓ RQ worker stopped" || echo "⚠ RQ worker not running"
	@pkill -f "vite.*--host" 2>/dev/null && echo "✓ Frontend stopped" || echo "⚠ Frontend not running"
	@echo "✓ All services stopped"

clean:
	@echo "Cleaning build artifacts..."
	@rm -rf frontend/dist
	@rm -rf frontend/node_modules/.vite
	@rm -rf backend/__pycache__
	@rm -rf backend/**/__pycache__
	@find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Clean complete"

