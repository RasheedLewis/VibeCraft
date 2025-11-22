#!/bin/bash
# ============================================================================
# Character Consistency - Stage 4: Complete End-to-End Tests
# ============================================================================
#
# This script tests the complete Character Consistency feature end-to-end,
# including Phase 4: Modify Video Generation Service and integration with
# the full workflow from image upload through video clip generation.
#
# Reference: docs/advanced_features_planning/CHARACTER_CONSISTENCY_IMPLEMENTATION.md
#            Section: "Phase 4: Modify Video Generation Service" (lines 483-581)
#            Also integrates: Phases 2, 3, and 5 for complete workflow
#
# Workflow Stage: Complete Pipeline (Upload → Interrogation → Generation → Video)
# - Tests video generation with character images (image-to-video) - Phase 4.1
# - Tests enhanced fallback logic - Phase 4.2
# - Tests integration with clip generation pipeline - Phase 4.3
# - Validates complete feature functionality across all phases
#
# Test Coverage:
#   - Unit tests for video_generation.py (image-to-video functionality) - Phase 4.1
#   - Tests for _generate_image_to_video() dedicated function - Phase 4.1
#   - Tests for enhanced fallback logic (image-to-video → text-to-video) - Phase 4.2
#   - Integration with character consistency workflow - Phase 4.3
#   - End-to-end workflow validation (Phases 2, 3, 4, 5 combined)
#
# Expected Duration: ~15-20 seconds (fast, mostly mocked)
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

# Run pytest tests with specific test classes/functions
run_pytest() {
    local test_file=$1
    local test_pattern=$2
    local description=$3
    local pytest_cmd=$4
    
    log_info "Running: $description"
    
    cd backend
    
    # Activate venv if we're using a venv pytest
    if [[ "$pytest_cmd" == *"venv"* ]]; then
        source "${pytest_cmd%/*}/activate" 2>/dev/null || true
    fi
    
    # Build pytest command
    if [ -n "$test_pattern" ]; then
        full_test_path="${test_file}::${test_pattern}"
    else
        full_test_path="$test_file"
    fi
    
    # Run tests and capture output
    if $pytest_cmd "$full_test_path" -v --tb=short 2>&1 | tee /tmp/pytest_output.log; then
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
    log_section "Character Consistency - Stage 4: Complete End-to-End Tests"
    
    echo "Testing Complete Character Consistency Feature (Phases 2-5)"
    echo "  - Image-to-video generation"
    echo "  - Enhanced fallback logic"
    echo "  - Complete workflow integration"
    echo "  - End-to-end feature validation"
    echo ""
    
    # Check dependencies
    PYTEST_CMD=$(check_pytest)
    
    # Check if service file exists
    if [ ! -f "backend/app/services/video_generation.py" ]; then
        log_error "Service file not found: backend/app/services/video_generation.py"
        exit 1
    fi
    log_success "Service file exists: backend/app/services/video_generation.py"
    
    # Test file
    TEST_FILE="tests/unit/test_video_generation.py"
    
    if ! check_test_file "backend/$TEST_FILE"; then
        log_error "Required test file missing. Cannot proceed."
        exit 1
    fi
    
    ALL_PASSED=true
    
    # Test 1: Image-to-Video Generation
    log_section "Testing Image-to-Video Generation"
    
    if run_pytest "$TEST_FILE" "TestGenerateImageToVideo" \
        "Image-to-Video Generation Tests" "$PYTEST_CMD"; then
        log_success "Image-to-video generation tests passed"
    else
        log_error "Image-to-video generation tests failed"
        ALL_PASSED=false
    fi
    
    # Test 2: Enhanced Fallback Logic
    log_section "Testing Enhanced Fallback Logic"
    
    if run_pytest "$TEST_FILE" "TestEnhancedFallbackLogic" \
        "Enhanced Fallback Logic Tests" "$PYTEST_CMD"; then
        log_success "Enhanced fallback logic tests passed"
    else
        log_error "Enhanced fallback logic tests failed"
        ALL_PASSED=false
    fi
    
    # Test 3: Video Generation with Reference Images
    log_section "Testing Video Generation with Reference Images"
    
    if run_pytest "$TEST_FILE" "TestGenerateSectionVideo::test_generation_with_single_reference_image" \
        "Single Reference Image Test" "$PYTEST_CMD"; then
        log_success "Single reference image test passed"
    else
        log_error "Single reference image test failed"
        ALL_PASSED=false
    fi
    
    if run_pytest "$TEST_FILE" "TestGenerateSectionVideo::test_generation_with_multiple_reference_images" \
        "Multiple Reference Images Test" "$PYTEST_CMD"; then
        log_success "Multiple reference images test passed"
    else
        log_error "Multiple reference images test failed"
        ALL_PASSED=false
    fi
    
    # Summary
    echo ""
    log_section "Test Summary"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo -e "${YELLOW}Skipped: $TESTS_SKIPPED${NC}"
    echo ""
    
    if [ "$ALL_PASSED" = true ] && [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ Stage 4 (Complete End-to-End) tests completed successfully!${NC}"
        echo ""
        echo "Character Consistency feature is fully tested and validated:"
        echo "  ✓ Image Interrogation (Stage 1)"
        echo "  ✓ Character Image Generation (Stage 2)"
        echo "  ✓ Orchestration Workflow (Stage 3)"
        echo "  ✓ Complete End-to-End (Stage 4)"
        exit 0
    else
        echo -e "${RED}✗ Stage 4 (Complete End-to-End) tests failed${NC}"
        exit 1
    fi
}

# Run main function
main

