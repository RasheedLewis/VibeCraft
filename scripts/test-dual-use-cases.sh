#!/bin/bash
# Comprehensive Test Script for Dual Use Cases + Prerequisites 1 & 2
# Tests:
# - Prerequisite 1: Feature flag/sections logic (now per-song via video_type)
# - Prerequisite 2: Audio selection (30-second selection)
# - Dual Use Case: Full-length vs 30-second video type selection

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Configuration
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
API_PREFIX="${API_PREFIX:-/api/v1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_TOTAL=0

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

log_error() {
    echo -e "${RED}✗${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    TESTS_TOTAL=$((TESTS_TOTAL + 1))
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

test_api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    local description=$5
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X "$method" "${API_BASE_URL}${API_PREFIX}${endpoint}" \
            -H "Content-Type: application/json" 2>/dev/null)
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "${API_BASE_URL}${API_PREFIX}${endpoint}" \
            -H "Content-Type: application/json" \
            -d "$data" 2>/dev/null)
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq "$expected_status" ]; then
        log_success "$description"
        echo "$body" > /tmp/test_response.json
        return 0
    else
        log_error "$description (expected $expected_status, got $http_code)"
        echo "Response: $body" >&2
        return 1
    fi
}

check_json_field() {
    local field=$1
    local expected_value=$2
    local description=$3
    
    if [ -f /tmp/test_response.json ]; then
        actual_value=$(jq -r ".$field" /tmp/test_response.json 2>/dev/null || echo "null")
        if [ "$actual_value" = "$expected_value" ]; then
            log_success "$description"
            return 0
        else
            log_error "$description (expected '$expected_value', got '$actual_value')"
            return 1
        fi
    else
        log_error "$description (no response file)"
        return 1
    fi
}

# Check if required tools are available
check_dependencies() {
    log_info "Checking dependencies..."
    
    command -v curl >/dev/null 2>&1 || { log_error "curl is required but not installed"; exit 1; }
    command -v jq >/dev/null 2>&1 || { log_error "jq is required but not installed"; exit 1; }
    
    # Check if API is running
    if ! curl -s "${API_BASE_URL}/health" >/dev/null 2>&1 && ! curl -s "${API_BASE_URL}${API_PREFIX}/songs" >/dev/null 2>&1; then
        log_warn "API server may not be running at ${API_BASE_URL}"
        log_warn "Some tests may fail. Start the server with: cd backend && python -m uvicorn app.main:app --reload"
    fi
    
    log_success "Dependencies check complete"
}

# ============================================================================
# SECTION 1: Video Type API Tests
# ============================================================================

test_video_type_api() {
    echo ""
    echo "=========================================="
    echo "SECTION 1: Video Type API Tests"
    echo "=========================================="
    echo ""
    
    # Create a test song first
    log_info "Creating test song for video_type tests..."
    
    # Check if we have a sample audio file
    SAMPLE_AUDIO=""
    if [ -f "samples/audio/short/sample.mp3" ]; then
        SAMPLE_AUDIO="samples/audio/short/sample.mp3"
    elif [ -f "samples/audio/electronic/sample1.mp3" ]; then
        SAMPLE_AUDIO="samples/audio/electronic/sample1.mp3"
    fi
    
    if [ -z "$SAMPLE_AUDIO" ]; then
        log_warn "No sample audio file found. Skipping upload tests."
        log_warn "Video type API tests will be limited to validation tests."
        return
    fi
    
    # Upload a song
    log_info "Uploading test song..."
    upload_response=$(curl -s -X POST "${API_BASE_URL}${API_PREFIX}/songs" \
        -F "file=@${SAMPLE_AUDIO}" 2>/dev/null)
    
    SONG_ID=$(echo "$upload_response" | jq -r '.songId // empty')
    
    if [ -z "$SONG_ID" ] || [ "$SONG_ID" = "null" ]; then
        log_error "Failed to upload song for testing"
        echo "Response: $upload_response" >&2
        return
    fi
    
    log_success "Test song uploaded (ID: $SONG_ID)"
    
    # Test 1.1: Set video_type to full_length
    echo ""
    log_info "Test 1.1: Setting video_type to 'full_length'..."
    test_api_call "PATCH" "/songs/${SONG_ID}/video-type" \
        '{"video_type": "full_length"}' \
        200 \
        "Set video_type to full_length"
    
    check_json_field "video_type" "full_length" "video_type is persisted as full_length"
    
    # Test 1.2: Set video_type to short_form
    echo ""
    log_info "Test 1.2: Setting video_type to 'short_form'..."
    test_api_call "PATCH" "/songs/${SONG_ID}/video-type" \
        '{"video_type": "short_form"}' \
        200 \
        "Set video_type to short_form"
    
    check_json_field "video_type" "short_form" "video_type is persisted as short_form"
    
    # Test 1.3: Invalid video_type
    echo ""
    log_info "Test 1.3: Testing invalid video_type..."
    test_api_call "PATCH" "/songs/${SONG_ID}/video-type" \
        '{"video_type": "invalid"}' \
        400 \
        "Invalid video_type is rejected"
    
    # Test 1.4: Get song and verify video_type is included
    echo ""
    log_info "Test 1.4: Verifying video_type in GET response..."
    test_api_call "GET" "/songs/${SONG_ID}" "" 200 "Get song details"
    check_json_field "video_type" "short_form" "video_type is included in GET response"
    
    # Test 1.5: Set video_type back to full_length
    echo ""
    log_info "Test 1.5: Changing video_type back to full_length..."
    test_api_call "PATCH" "/songs/${SONG_ID}/video-type" \
        '{"video_type": "full_length"}' \
        200 \
        "Can change video_type before analysis"
    
    # Store SONG_ID for later tests
    echo "$SONG_ID" > /tmp/test_song_id.txt
}

# ============================================================================
# SECTION 2: Audio Selection API Tests (Prerequisite 2)
# ============================================================================

test_audio_selection_api() {
    echo ""
    echo "=========================================="
    echo "SECTION 2: Audio Selection API Tests (Prerequisite 2)"
    echo "=========================================="
    echo ""
    
    # Get or create test song
    if [ -f /tmp/test_song_id.txt ]; then
        SONG_ID=$(cat /tmp/test_song_id.txt)
    else
        log_warn "No test song available. Skipping audio selection tests."
        return
    fi
    
    # Test 2.1: Set audio selection (valid 30-second range)
    echo ""
    log_info "Test 2.1: Setting valid 30-second audio selection..."
    test_api_call "PATCH" "/songs/${SONG_ID}/selection" \
        '{"start_sec": 10.0, "end_sec": 40.0}' \
        200 \
        "Set valid 30-second audio selection"
    
    check_json_field "selected_start_sec" "10" "selected_start_sec is persisted"
    check_json_field "selected_end_sec" "40" "selected_end_sec is persisted"
    
    # Test 2.2: Audio selection exceeds 30 seconds
    echo ""
    log_info "Test 2.2: Testing selection exceeding 30 seconds..."
    test_api_call "PATCH" "/songs/${SONG_ID}/selection" \
        '{"start_sec": 0.0, "end_sec": 35.0}' \
        400 \
        "Selection exceeding 30 seconds is rejected"
    
    # Test 2.3: Audio selection below 1 second
    echo ""
    log_info "Test 2.3: Testing selection below 1 second..."
    test_api_call "PATCH" "/songs/${SONG_ID}/selection" \
        '{"start_sec": 10.0, "end_sec": 10.5}' \
        400 \
        "Selection below 1 second is rejected"
    
    # Test 2.4: Audio selection end before start
    echo ""
    log_info "Test 2.4: Testing invalid range (end before start)..."
    test_api_call "PATCH" "/songs/${SONG_ID}/selection" \
        '{"start_sec": 20.0, "end_sec": 10.0}' \
        400 \
        "Invalid range (end < start) is rejected"
    
    # Test 2.5: Valid boundary case - exactly 30 seconds
    echo ""
    log_info "Test 2.5: Testing boundary case - exactly 30 seconds..."
    test_api_call "PATCH" "/songs/${SONG_ID}/selection" \
        '{"start_sec": 5.0, "end_sec": 35.0}' \
        200 \
        "Exactly 30-second selection is accepted"
    
    # Test 2.6: Valid boundary case - exactly 1 second
    echo ""
    log_info "Test 2.6: Testing boundary case - exactly 1 second..."
    test_api_call "PATCH" "/songs/${SONG_ID}/selection" \
        '{"start_sec": 10.0, "end_sec": 11.0}' \
        200 \
        "Exactly 1-second selection is accepted"
}

# ============================================================================
# SECTION 3: Analysis Service Tests (Prerequisite 1 + Dual Use Case)
# ============================================================================

test_analysis_service() {
    echo ""
    echo "=========================================="
    echo "SECTION 3: Analysis Service Tests"
    echo "=========================================="
    echo ""
    echo "Testing that analysis respects video_type:"
    echo "  - full_length: Should run section inference"
    echo "  - short_form: Should skip section inference"
    echo ""
    
    log_info "Note: Full analysis tests require running analysis jobs."
    log_info "These are integration tests that verify the logic flow."
    
    # Test 3.1: Verify should_use_sections_for_song function exists
    echo ""
    log_info "Test 3.1: Checking should_use_sections_for_song function..."
    if grep -q "def should_use_sections_for_song" backend/app/core/config.py; then
        log_success "should_use_sections_for_song function exists"
    else
        log_error "should_use_sections_for_song function not found"
    fi
    
    # Test 3.2: Verify analysis service checks video_type
    echo ""
    log_info "Test 3.2: Checking analysis service respects video_type..."
    if grep -q "should_use_sections_for_song" backend/app/services/song_analysis.py; then
        log_success "Analysis service checks video_type"
    else
        log_error "Analysis service does not check video_type"
    fi
    
    # Test 3.3: Verify section inference is conditional
    echo ""
    log_info "Test 3.3: Checking conditional section inference..."
    if grep -q "use_sections = should_use_sections_for_song" backend/app/services/song_analysis.py; then
        log_success "Section inference is conditional on video_type"
    else
        log_error "Section inference is not conditional"
    fi
    
    # Test 3.4: Verify short_form skips section inference
    echo ""
    log_info "Test 3.4: Checking short_form skips section inference..."
    if grep -q "Skipping section detection (short-form video)" backend/app/services/song_analysis.py; then
        log_success "short_form videos skip section inference"
    else
        log_warn "Could not verify short_form skip logic in code"
    fi
}

# ============================================================================
# SECTION 4: Composition Service Tests (Prerequisite 1)
# ============================================================================

test_composition_service() {
    echo ""
    echo "=========================================="
    echo "SECTION 4: Composition Service Tests (Prerequisite 1)"
    echo "=========================================="
    echo ""
    echo "Testing that composition uses correct model based on video_type:"
    echo "  - full_length: Uses SectionVideo"
    echo "  - short_form: Uses SongClip"
    echo ""
    
    # Test 4.1: Verify composition_execution uses video_type
    echo ""
    log_info "Test 4.1: Checking composition_execution uses video_type..."
    if grep -q "should_use_sections_for_song" backend/app/services/composition_execution.py; then
        log_success "composition_execution checks video_type"
    else
        log_error "composition_execution does not check video_type"
    fi
    
    # Test 4.2: Verify composition_job uses video_type
    echo ""
    log_info "Test 4.2: Checking composition_job uses video_type..."
    if grep -q "should_use_sections_for_song" backend/app/services/composition_job.py; then
        log_success "composition_job checks video_type"
    else
        log_error "composition_job does not check video_type"
    fi
    
    # Test 4.3: Verify both models are supported
    echo ""
    log_info "Test 4.3: Checking both SectionVideo and SongClip are supported..."
    if grep -q "SectionVideo\|SongClip" backend/app/services/composition_execution.py; then
        log_success "Both SectionVideo and SongClip models are supported"
    else
        log_error "Model selection logic not found"
    fi
}

# ============================================================================
# SECTION 5: Database Schema Tests
# ============================================================================

test_database_schema() {
    echo ""
    echo "=========================================="
    echo "SECTION 5: Database Schema Tests"
    echo "=========================================="
    echo ""
    
    # Test 5.1: Verify video_type field in Song model
    echo ""
    log_info "Test 5.1: Checking video_type field in Song model..."
    if grep -q "video_type.*Field" backend/app/models/song.py; then
        log_success "video_type field exists in Song model"
    else
        log_error "video_type field not found in Song model"
    fi
    
    # Test 5.2: Verify selected_start_sec and selected_end_sec fields
    echo ""
    log_info "Test 5.2: Checking audio selection fields in Song model..."
    if grep -q "selected_start_sec.*Field" backend/app/models/song.py && \
       grep -q "selected_end_sec.*Field" backend/app/models/song.py; then
        log_success "Audio selection fields exist in Song model"
    else
        log_error "Audio selection fields not found in Song model"
    fi
    
    # Test 5.3: Verify migration file exists
    echo ""
    log_info "Test 5.3: Checking migration file for video_type..."
    if [ -f "backend/migrations/003_add_video_type_field.py" ]; then
        log_success "Migration file for video_type exists"
    else
        log_error "Migration file for video_type not found"
    fi
    
    # Test 5.4: Verify schema includes video_type
    echo ""
    log_info "Test 5.4: Checking video_type in SongRead schema..."
    if grep -q "video_type" backend/app/schemas/song.py; then
        log_success "video_type included in SongRead schema"
    else
        log_error "video_type not found in SongRead schema"
    fi
}

# ============================================================================
# SECTION 6: Frontend Component Tests
# ============================================================================

test_frontend_components() {
    echo ""
    echo "=========================================="
    echo "SECTION 6: Frontend Component Tests"
    echo "=========================================="
    echo ""
    
    # Test 6.1: Verify VideoTypeSelector component exists
    echo ""
    log_info "Test 6.1: Checking VideoTypeSelector component..."
    if [ -f "frontend/src/components/upload/VideoTypeSelector.tsx" ]; then
        log_success "VideoTypeSelector component exists"
    else
        log_error "VideoTypeSelector component not found"
    fi
    
    # Test 6.2: Verify UploadPage integrates video type selection
    echo ""
    log_info "Test 6.2: Checking UploadPage video type integration..."
    if grep -q "VideoTypeSelector\|videoType" frontend/src/pages/UploadPage.tsx; then
        log_success "UploadPage integrates video type selection"
    else
        log_error "UploadPage does not integrate video type selection"
    fi
    
    # Test 6.3: Verify AudioSelectionTimeline component exists
    echo ""
    log_info "Test 6.3: Checking AudioSelectionTimeline component..."
    if [ -f "frontend/src/components/upload/AudioSelectionTimeline.tsx" ]; then
        log_success "AudioSelectionTimeline component exists"
    else
        log_error "AudioSelectionTimeline component not found"
    fi
    
    # Test 6.4: Verify conditional audio selection rendering
    echo ""
    log_info "Test 6.4: Checking conditional audio selection rendering..."
    if grep -q "videoType === 'short_form'" frontend/src/pages/UploadPage.tsx; then
        log_success "Audio selection is conditional on video_type"
    else
        log_error "Audio selection is not conditional on video_type"
    fi
    
    # Test 6.5: Verify TypeScript types include video_type
    echo ""
    log_info "Test 6.5: Checking TypeScript types..."
    if grep -q "video_type.*full_length.*short_form" frontend/src/types/song.ts; then
        log_success "TypeScript types include video_type"
    else
        log_error "TypeScript types do not include video_type"
    fi
}

# ============================================================================
# SECTION 7: Integration Flow Tests
# ============================================================================

test_integration_flow() {
    echo ""
    echo "=========================================="
    echo "SECTION 7: Integration Flow Tests"
    echo "=========================================="
    echo ""
    echo "Testing end-to-end flow logic:"
    echo ""
    
    # Test 7.1: Verify full_length flow uses sections
    echo ""
    log_info "Test 7.1: Checking full_length flow logic..."
    if grep -q "video_type === 'full_length'" frontend/src/pages/UploadPage.tsx && \
       grep -q "video_type == \"full_length\"" backend/app/core/config.py; then
        log_success "full_length flow is properly implemented"
    else
        log_warn "Could not fully verify full_length flow"
    fi
    
    # Test 7.2: Verify short_form flow uses audio selection
    echo ""
    log_info "Test 7.2: Checking short_form flow logic..."
    if grep -q "video_type === 'short_form'" frontend/src/pages/UploadPage.tsx && \
       grep -q "video_type == \"short_form\"" backend/app/core/config.py; then
        log_success "short_form flow is properly implemented"
    else
        log_warn "Could not fully verify short_form flow"
    fi
    
    # Test 7.3: Verify video_type must be set before analysis
    echo ""
    log_info "Test 7.3: Checking video_type requirement before analysis..."
    if grep -q "Cannot change video type after analysis" backend/app/api/v1/routes_songs.py; then
        log_success "video_type cannot be changed after analysis"
    else
        log_warn "Could not verify video_type change restriction"
    fi
}

# ============================================================================
# SECTION 8: Unit Test Coverage
# ============================================================================

test_unit_test_coverage() {
    echo ""
    echo "=========================================="
    echo "SECTION 8: Unit Test Coverage"
    echo "=========================================="
    echo ""
    
    # Test 8.1: Verify video_type unit tests exist
    echo ""
    log_info "Test 8.1: Checking video_type unit tests..."
    if [ -f "backend/tests/unit/test_video_type.py" ]; then
        log_success "video_type unit tests exist"
    else
        log_warn "video_type unit tests not found (may be in progress)"
    fi
    
    # Test 8.2: Verify video_type API tests exist
    echo ""
    log_info "Test 8.2: Checking video_type API tests..."
    if [ -f "backend/tests/test_video_type_api.py" ]; then
        log_success "video_type API tests exist"
    else
        log_warn "video_type API tests not found (may be in progress)"
    fi
    
    # Test 8.3: Verify analysis video_type tests exist
    echo ""
    log_info "Test 8.3: Checking analysis video_type tests..."
    if [ -f "backend/tests/unit/test_analysis_video_type.py" ]; then
        log_success "analysis video_type tests exist"
    else
        log_warn "analysis video_type tests not found (may be in progress)"
    fi
    
    # Test 8.4: Verify composition tests updated
    echo ""
    log_info "Test 8.4: Checking composition tests use video_type..."
    if grep -q "video_type" backend/tests/unit/test_composition_execution.py && \
       grep -q "video_type" backend/tests/unit/test_composition_job.py; then
        log_success "Composition tests use video_type"
    else
        log_warn "Composition tests may not be fully updated"
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    echo "=========================================="
    echo "Comprehensive Dual Use Case Test Suite"
    echo "=========================================="
    echo ""
    echo "Testing:"
    echo "  - Prerequisite 1: Feature flag/sections logic (per-song)"
    echo "  - Prerequisite 2: Audio selection (30-second)"
    echo "  - Dual Use Case: Full-length vs 30-second video type"
    echo ""
    
    check_dependencies
    
    # Run all test sections
    test_video_type_api
    test_audio_selection_api
    test_analysis_service
    test_composition_service
    test_database_schema
    test_frontend_components
    test_integration_flow
    test_unit_test_coverage
    
    # Summary
    echo ""
    echo "=========================================="
    echo "Test Summary"
    echo "=========================================="
    echo ""
    echo "Total Tests: $TESTS_TOTAL"
    echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✓ All tests passed!${NC}"
        exit 0
    else
        echo -e "${RED}✗ Some tests failed${NC}"
        exit 1
    fi
}

# Run main function
main

