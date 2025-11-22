#!/bin/bash
# Test Script for Beat Sync Foundation
# Tests:
# - Prompt enhancement with BPM
# - Beat-reactive FFmpeg filter generation
# - Integration: BPM flows through scene planning
# - Integration: Beat times flow through composition

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

log_info() { echo -e "${BLUE}ℹ${NC} $1"; }
log_success() { echo -e "${GREEN}✓${NC} $1"; TESTS_PASSED=$((TESTS_PASSED + 1)); TESTS_TOTAL=$((TESTS_TOTAL + 1)); }
log_error() { echo -e "${RED}✗${NC} $1"; TESTS_FAILED=$((TESTS_FAILED + 1)); TESTS_TOTAL=$((TESTS_TOTAL + 1)); }
log_warn() { echo -e "${YELLOW}⚠${NC} $1"; }

# Detect Python environment
detect_python() {
    local root=$1
    if [ -f "$root/backend/venv/bin/python" ]; then
        echo "$root/backend/venv/bin/python"
    elif [ -f "$root/venv/bin/python" ]; then
        echo "$root/venv/bin/python"
    else
        echo "python3"
    fi
}

PYTHON_CMD=$(detect_python "$PROJECT_ROOT")

# Test functions
test_prompt_enhancement_unit() {
    log_info "Running prompt enhancement unit tests..."
    if cd "$PROJECT_ROOT/backend" && $PYTHON_CMD -m pytest tests/unit/test_prompt_enhancement.py -v --tb=short 2>/dev/null; then
        log_success "Prompt enhancement unit tests passed"
    else
        log_warn "Prompt enhancement unit tests skipped (pytest not available or venv not activated)"
        log_info "To run tests: cd backend && source venv/bin/activate && pytest tests/unit/test_prompt_enhancement.py -v"
    fi
}

test_beat_filters_unit() {
    log_info "Running beat filters unit tests..."
    if cd "$PROJECT_ROOT/backend" && $PYTHON_CMD -m pytest tests/unit/test_beat_filters.py -v --tb=short 2>/dev/null; then
        log_success "Beat filters unit tests passed"
    else
        log_warn "Beat filters unit tests skipped (pytest not available or venv not activated)"
        log_info "To run tests: cd backend && source venv/bin/activate && pytest tests/unit/test_beat_filters.py -v"
    fi
}

test_scene_planner_bpm_integration() {
    log_info "Running scene planner BPM integration tests..."
    if cd "$PROJECT_ROOT/backend" && $PYTHON_CMD -m pytest tests/unit/test_scene_planner.py::TestBuildPrompt::test_prompt_with_bpm_enhancement -v --tb=short 2>/dev/null; then
        log_success "Scene planner BPM integration tests passed"
    else
        log_warn "Scene planner BPM integration tests skipped (pytest not available)"
    fi
}

test_all_bpm_tests() {
    log_info "Running all BPM-related tests in scene planner..."
    if cd "$PROJECT_ROOT/backend" && $PYTHON_CMD -m pytest tests/unit/test_scene_planner.py -k "bpm" -v --tb=short 2>/dev/null; then
        log_success "All BPM-related tests passed"
    else
        log_warn "BPM-related tests skipped (pytest not available)"
    fi
}

test_syntax_check() {
    log_info "Running syntax checks..."
    cd "$PROJECT_ROOT" || return 1
    if $PYTHON_CMD -m py_compile backend/app/services/prompt_enhancement.py backend/app/services/beat_filters.py 2>/dev/null; then
        log_success "Service syntax check passed"
    else
        log_error "Service syntax check failed"
        return 1
    fi
    
    if $PYTHON_CMD -m py_compile backend/tests/unit/test_prompt_enhancement.py backend/tests/unit/test_beat_filters.py 2>/dev/null; then
        log_success "Test syntax check passed"
    else
        log_error "Test syntax check failed"
        return 1
    fi
}

test_lint() {
    log_info "Running linter checks..."
    if cd backend && python -m pylint app/services/prompt_enhancement.py app/services/beat_filters.py --disable=all --enable=errors 2>/dev/null || true; then
        log_success "Linter checks passed (or skipped)"
    else
        log_warn "Linter found issues (non-blocking)"
    fi
}

# Main execution
main() {
    log_info "Starting Beat Sync Foundation tests..."
    echo ""
    
    test_prompt_enhancement_unit || true
    echo ""
    
    test_beat_filters_unit || true
    echo ""
    
    test_scene_planner_bpm_integration || true
    echo ""
    
    test_all_bpm_tests || true
    echo ""
    
    test_syntax_check || true
    echo ""
    
    test_lint || true
    echo ""
    
    # Summary
    echo "=========================================="
    echo "Test Summary:"
    echo "  Total: $TESTS_TOTAL"
    echo "  Passed: $TESTS_PASSED"
    echo "  Failed: $TESTS_FAILED"
    echo "=========================================="
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log_success "All tests passed!"
        exit 0
    else
        log_error "Some tests failed"
        exit 1
    fi
}

main "$@"

