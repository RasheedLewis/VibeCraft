#!/bin/bash
# ============================================================================
# Character Consistency - Stage 2: Character Image Generation Tests
# ============================================================================
#
# This script tests Phase 3: Character Image Generation Service from
# CHARACTER_CONSISTENCY_IMPLEMENTATION.md, which creates a standardized
# character image using the interrogated prompt and reference image via
# Replicate's Stable Diffusion XL model.
#
# Reference: docs/advanced_features_planning/CHARACTER_CONSISTENCY_IMPLEMENTATION.md
#            Section: "Phase 3: Character Image Generation Service" (lines 321-482)
#
# Workflow Stage: Prompt + Reference Image → Consistent Character Image
# - Tests Replicate SDXL integration (Phase 3.1)
# - Tests image generation with IP-Adapter/ControlNet (Phase 3.2)
# - Tests polling and status checking (Phase 3.3)
# - Validates image output and metadata
#
# Test Coverage:
#   - Unit tests for character_image_generation.py service
#   - Replicate API integration (mocked) - Phase 3.1
#   - Image generation workflow - Phase 3.2
#   - Polling mechanism for async jobs - Phase 3.3
#   - Error handling (timeouts, API failures, etc.)
#   - Output format validation (URL extraction from various response types)
#
# Expected Duration: ~5-10 seconds (fast, all mocked)
# Dependencies: pytest, Python venv with dependencies installed
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
            log_error "$description - Some tests failed"
            cd ..
            return 1
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
    log_section "Character Consistency - Stage 2: Character Image Generation Tests"
    
    echo "Testing Character Image Generation Service (Phase 3)"
    echo "  - Replicate SDXL integration"
    echo "  - Image generation with prompts"
    echo "  - Polling and status checking"
    echo "  - Output validation"
    echo ""
    
    # Check dependencies
    PYTEST_CMD=$(check_pytest)
    
    # Test file path
    TEST_FILE="tests/unit/test_character_image_generation.py"
    
    # Check if test file exists
    if ! check_test_file "backend/$TEST_FILE"; then
        log_error "Required test file missing. Cannot proceed."
        exit 1
    fi
    
    # Check if service file exists
    if [ ! -f "backend/app/services/character_image_generation.py" ]; then
        log_error "Service file not found: backend/app/services/character_image_generation.py"
        exit 1
    fi
    log_success "Service file exists: backend/app/services/character_image_generation.py"
    
    # Run unit tests
    log_section "Running Character Image Generation Unit Tests"
    
    if run_pytest "$TEST_FILE" "Character Image Generation Service Tests" "$PYTEST_CMD"; then
        log_success "All character image generation tests passed"
    else
        log_error "Some character image generation tests failed"
    fi
    
    # Summary
    echo ""
    log_section "Test Summary"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo -e "${YELLOW}Skipped: $TESTS_SKIPPED${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ Stage 2 (Character Image Generation) tests completed successfully!${NC}"
        exit 0
    else
        echo -e "${RED}✗ Stage 2 (Character Image Generation) tests failed${NC}"
        exit 1
    fi
}

# Run main function
main

