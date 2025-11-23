#!/bin/bash
# ============================================================================
# Character Consistency - Stage 3: Orchestration Workflow Tests
# ============================================================================
#
# This script tests Phase 5: Integrate into Clip Generation Pipeline from
# CHARACTER_CONSISTENCY_IMPLEMENTATION.md, which coordinates the full workflow
# from reference image upload through consistent character image generation
# and storage.
#
# Reference: docs/advanced_features_planning/CHARACTER_CONSISTENCY_IMPLEMENTATION.md
#            Section: "Phase 5: Integrate into Clip Generation Pipeline" (lines 582-817)
#            Also covers: "Phase 1: Database & Storage Setup" (lines 124-171)
#
# Workflow Stage: Full Orchestration (Interrogation → Generation → Storage)
# - Tests character_consistency.py orchestration service (Phase 5.1)
# - Tests background job execution (RQ) - Phase 5.2
# - Tests storage helpers for character images - Phase 1.3
# - Tests integration between all components - Phase 5.3
# - Validates end-to-end workflow logic
#
# Test Coverage:
#   - Unit tests for character_consistency.py (orchestration) - Phase 5.1
#   - Unit tests for storage_character.py (S3 helpers) - Phase 1.3
#   - Integration tests for full workflow - Phase 5.3
#   - Background job execution (mocked) - Phase 5.2
#   - Error handling and edge cases
#   - Database integration (may be skipped if DB not available)
#
# Expected Duration: ~10-15 seconds (fast, mostly mocked)
# Dependencies: pytest, Python venv with dependencies installed
# Note: Integration tests may be skipped if DATABASE_URL is not set
#
# ============================================================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
}

log_section() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Check if pytest is available
check_pytest() {
    log_info "Checking pytest availability..."
    
    # Try to find pytest in various locations
    PYTEST_CMD=""
    if command -v pytest >/dev/null 2>&1; then
        PYTEST_CMD="pytest"
    elif [ -f "backend/venv/bin/pytest" ]; then
        PYTEST_CMD="backend/venv/bin/pytest"
    elif [ -f "venv/bin/pytest" ]; then
        PYTEST_CMD="venv/bin/pytest"
    elif [ -f "../VibeCraft/backend/venv/bin/pytest" ]; then
        PYTEST_CMD="../VibeCraft/backend/venv/bin/pytest"
    fi
    
    if [ -z "$PYTEST_CMD" ]; then
        log_error "pytest not found. Please install pytest: pip install pytest"
        exit 1
    fi
    
    log_success "Found pytest: $PYTEST_CMD"
    echo "$PYTEST_CMD"
}

# Check if test file exists
check_test_file() {
    local test_file=$1
    if [ ! -f "$test_file" ]; then
        log_error "Test file not found: $test_file"
        return 1
    fi
    log_success "Test file exists: $test_file"
    return 0
}

# Run pytest tests
run_pytest() {
    local test_file=$1
    local description=$2
    local pytest_cmd=$3
    
    log_info "Running: $description"
    
    cd backend
    
    # Activate venv if we're using a venv pytest
    if [[ "$pytest_cmd" == *"venv"* ]]; then
        source "${pytest_cmd%/*}/activate" 2>/dev/null || true
    fi
    
    # Run tests and capture output
    if $pytest_cmd "$test_file" -v --tb=short 2>&1 | tee /tmp/pytest_output.log; then
        # Check if tests actually passed
        if grep -q "passed\|PASSED" /tmp/pytest_output.log && ! grep -q "FAILED\|ERROR" /tmp/pytest_output.log; then
            log_success "$description"
            cd ..
            return 0
        else
            # Check if failures are just skipped tests
            if grep -q "SKIPPED\|skipped" /tmp/pytest_output.log && ! grep -q "FAILED\|ERROR" /tmp/pytest_output.log; then
                log_warn "$description - Some tests skipped (expected if DB not configured)"
                cd ..
                return 0
            else
                log_error "$description - Some tests failed"
                cd ..
                return 1
            fi
        fi
    else
        log_error "$description - pytest execution failed"
        cd ..
        return 1
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    log_section "Character Consistency - Stage 3: Orchestration Workflow Tests"
    
    echo "Testing Character Consistency Orchestration (Phase 5)"
    echo "  - Full workflow orchestration"
    echo "  - Storage helpers for character images"
    echo "  - Background job execution"
    echo "  - Integration between components"
    echo ""
    
    # Check dependencies
    PYTEST_CMD=$(check_pytest)
    
    # Test files
    TEST_FILES=(
        "tests/unit/test_character_consistency.py"
        "tests/unit/test_storage_character.py"
        "tests/test_character_consistency_integration.py"
    )
    
    # Check if service file exists
    if [ ! -f "backend/app/services/character_consistency.py" ]; then
        log_error "Service file not found: backend/app/services/character_consistency.py"
        exit 1
    fi
    log_success "Service file exists: backend/app/services/character_consistency.py"
    
    # Run tests for each test file
    ALL_PASSED=true
    
    for test_file in "${TEST_FILES[@]}"; do
        if check_test_file "backend/$test_file"; then
            log_section "Running: $(basename $test_file)"
            
            if ! run_pytest "$test_file" "$(basename $test_file)" "$PYTEST_CMD"; then
                ALL_PASSED=false
            fi
        else
            log_warn "Skipping missing test file: $test_file"
            ALL_PASSED=false
        fi
    done
    
    # Summary
    echo ""
    log_section "Test Summary"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo -e "${YELLOW}Skipped: $TESTS_SKIPPED${NC}"
    echo ""
    
    if [ "$ALL_PASSED" = true ] && [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ Stage 3 (Orchestration Workflow) tests completed successfully!${NC}"
        exit 0
    else
        if [ $TESTS_FAILED -eq 0 ]; then
            echo -e "${YELLOW}⚠ Stage 3 (Orchestration Workflow) tests completed with some skipped tests${NC}"
            echo "  (This is expected if DATABASE_URL is not configured)"
            exit 0
        else
            echo -e "${RED}✗ Stage 3 (Orchestration Workflow) tests failed${NC}"
            exit 1
        fi
    fi
}

# Run main function
main

