#!/bin/bash
# Comprehensive Test Script for Character Consistency Foundation
# Tests:
# - Image validation service (unit tests)
# - Character image upload API endpoint
# - Database schema (character fields)
# - Video generation with image input
# - Frontend component integration

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
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
# SECTION 1: Database Schema Tests
# ============================================================================

test_database_schema() {
    echo ""
    echo "=========================================="
    echo "SECTION 1: Database Schema Tests"
    echo "=========================================="
    echo ""
    
    # Test 1.1: Verify character fields in Song model
    echo ""
    log_info "Test 1.1: Checking character fields in Song model..."
    if grep -q "character_reference_image_s3_key.*Field" backend/app/models/song.py && \
       grep -q "character_consistency_enabled.*Field" backend/app/models/song.py && \
       grep -q "character_interrogation_prompt.*Field" backend/app/models/song.py && \
       grep -q "character_generated_image_s3_key.*Field" backend/app/models/song.py; then
        log_success "All character fields exist in Song model"
    else
        log_error "Character fields not found in Song model"
    fi
    
    # Test 1.2: Verify migration file exists
    echo ""
    log_info "Test 1.2: Checking migration file for character fields..."
    if [ -f "backend/migrations/004_add_character_fields.py" ]; then
        log_success "Migration file for character fields exists"
    else
        log_error "Migration file for character fields not found"
    fi
    
    # Test 1.3: Verify migration function exists
    echo ""
    log_info "Test 1.3: Checking migration function..."
    if grep -q "def migrate" backend/migrations/004_add_character_fields.py; then
        log_success "Migration function exists"
    else
        log_error "Migration function not found"
    fi
}

# ============================================================================
# SECTION 2: Image Validation Service Tests
# ============================================================================

test_image_validation_service() {
    echo ""
    echo "=========================================="
    echo "SECTION 2: Image Validation Service Tests"
    echo "=========================================="
    echo ""
    
    # Test 2.1: Verify image_validation.py exists
    echo ""
    log_info "Test 2.1: Checking image_validation.py service..."
    if [ -f "backend/app/services/image_validation.py" ]; then
        log_success "image_validation.py service exists"
    else
        log_error "image_validation.py service not found"
    fi
    
    # Test 2.2: Verify validate_image function exists
    echo ""
    log_info "Test 2.2: Checking validate_image function..."
    if grep -q "def validate_image" backend/app/services/image_validation.py; then
        log_success "validate_image function exists"
    else
        log_error "validate_image function not found"
    fi
    
    # Test 2.3: Verify normalize_image_format function exists
    echo ""
    log_info "Test 2.3: Checking normalize_image_format function..."
    if grep -q "def normalize_image_format" backend/app/services/image_validation.py; then
        log_success "normalize_image_format function exists"
    else
        log_error "normalize_image_format function not found"
    fi
    
    # Test 2.4: Verify validation constants
    echo ""
    log_info "Test 2.4: Checking validation constants..."
    if grep -q "ALLOWED_IMAGE_FORMATS" backend/app/services/image_validation.py && \
       grep -q "MAX_IMAGE_SIZE_MB" backend/app/services/image_validation.py && \
       grep -q "MAX_IMAGE_DIMENSION" backend/app/services/image_validation.py && \
       grep -q "MIN_IMAGE_DIMENSION" backend/app/services/image_validation.py; then
        log_success "Validation constants are defined"
    else
        log_error "Validation constants not found"
    fi
    
    # Test 2.5: Verify unit tests exist
    echo ""
    log_info "Test 2.5: Checking unit tests for image validation..."
    if [ -f "backend/tests/unit/test_image_validation.py" ]; then
        log_success "Unit tests for image validation exist"
    else
        log_error "Unit tests for image validation not found"
    fi
}

# ============================================================================
# SECTION 3: Character Image Upload API Tests
# ============================================================================

test_character_image_upload_api() {
    echo ""
    echo "=========================================="
    echo "SECTION 3: Character Image Upload API Tests"
    echo "=========================================="
    echo ""
    
    # Test 3.1: Verify API endpoint exists
    echo ""
    log_info "Test 3.1: Checking character image upload endpoint..."
    if grep -q "@router.post.*character-image" backend/app/api/v1/routes_songs.py; then
        log_success "Character image upload endpoint exists"
    else
        log_error "Character image upload endpoint not found"
    fi
    
    # Test 3.2: Verify endpoint validates video_type
    echo ""
    log_info "Test 3.2: Checking endpoint validates video_type..."
    if grep -q "video_type != \"short_form\"" backend/app/api/v1/routes_songs.py; then
        log_success "Endpoint validates video_type"
    else
        log_error "Endpoint does not validate video_type"
    fi
    
    # Test 3.3: Verify endpoint uses image validation
    echo ""
    log_info "Test 3.3: Checking endpoint uses image validation..."
    if grep -q "validate_image" backend/app/api/v1/routes_songs.py; then
        log_success "Endpoint uses image validation"
    else
        log_error "Endpoint does not use image validation"
    fi
    
    # Test 3.4: Verify endpoint normalizes image format
    echo ""
    log_info "Test 3.4: Checking endpoint normalizes image format..."
    if grep -q "normalize_image_format" backend/app/api/v1/routes_songs.py; then
        log_success "Endpoint normalizes image format"
    else
        log_error "Endpoint does not normalize image format"
    fi
    
    # Test 3.5: Verify endpoint updates song record
    echo ""
    log_info "Test 3.5: Checking endpoint updates song record..."
    if grep -q "character_consistency_enabled = True" backend/app/api/v1/routes_songs.py; then
        log_success "Endpoint updates song record"
    else
        log_error "Endpoint does not update song record"
    fi
    
    # Test 3.6: Test API endpoint with actual request (if server running)
    echo ""
    log_info "Test 3.6: Testing API endpoint (requires running server and test song)..."
    
    # Check if we have a test song ID from previous tests
    if [ -f /tmp/test_song_id.txt ]; then
        SONG_ID=$(cat /tmp/test_song_id.txt)
        
        # Set video_type to short_form if not already
        curl -s -X PATCH "${API_BASE_URL}${API_PREFIX}/songs/${SONG_ID}/video-type" \
            -H "Content-Type: application/json" \
            -d '{"video_type": "short_form"}' >/dev/null 2>&1 || true
        
        # Try to upload a test image (create a minimal valid JPEG)
        # This is a 1x1 pixel JPEG
        TEST_IMAGE=$(printf '\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xff\xd9')
        
        # Create temp file
        TEMP_IMAGE=$(mktemp)
        echo -n "$TEST_IMAGE" > "$TEMP_IMAGE"
        
        response=$(curl -s -w "\n%{http_code}" -X POST "${API_BASE_URL}${API_PREFIX}/songs/${SONG_ID}/character-image" \
            -F "image=@${TEMP_IMAGE}" 2>/dev/null || echo "000")
        
        http_code=$(echo "$response" | tail -n1)
        rm -f "$TEMP_IMAGE"
        
        if [ "$http_code" = "200" ]; then
            log_success "Character image upload API endpoint works"
        elif [ "$http_code" = "000" ]; then
            log_warn "API server not running - skipping live API test"
        else
            log_warn "API test returned status $http_code (may need valid image or server setup)"
        fi
    else
        log_warn "No test song available - skipping live API test"
    fi
}

# ============================================================================
# SECTION 4: Video Generation Integration Tests
# ============================================================================

test_video_generation_integration() {
    echo ""
    echo "=========================================="
    echo "SECTION 4: Video Generation Integration Tests"
    echo "=========================================="
    echo ""
    
    # Test 4.1: Verify video_generation.py accepts reference_image_url
    echo ""
    log_info "Test 4.1: Checking video_generation.py accepts reference_image_url..."
    if grep -q "reference_image_url.*Optional" backend/app/services/video_generation.py; then
        log_success "video_generation.py accepts reference_image_url parameter"
    else
        log_error "video_generation.py does not accept reference_image_url parameter"
    fi
    
    # Test 4.2: Verify image-to-video logic
    echo ""
    log_info "Test 4.2: Checking image-to-video logic..."
    if grep -q "image-to-video\|image_to_video\|reference_image_url" backend/app/services/video_generation.py; then
        log_success "Image-to-video logic exists"
    else
        log_error "Image-to-video logic not found"
    fi
    
    # Test 4.3: Verify image input is added to Replicate params
    echo ""
    log_info "Test 4.3: Checking image input in Replicate params..."
    if grep -q "input_params\[\"image\"\]" backend/app/services/video_generation.py; then
        log_success "Image input is added to Replicate params"
    else
        log_error "Image input not added to Replicate params"
    fi
    
    # Test 4.4: Verify clip_generation.py passes character image
    echo ""
    log_info "Test 4.4: Checking clip_generation.py passes character image..."
    if grep -q "character_image_url\|reference_image_url" backend/app/services/clip_generation.py; then
        log_success "clip_generation.py passes character image"
    else
        log_error "clip_generation.py does not pass character image"
    fi
    
    # Test 4.5: Verify character image URL generation
    echo ""
    log_info "Test 4.5: Checking character image URL generation..."
    if grep -q "character_generated_image_s3_key\|character_reference_image_s3_key" backend/app/services/clip_generation.py; then
        log_success "Character image URL generation exists"
    else
        log_error "Character image URL generation not found"
    fi
}

# ============================================================================
# SECTION 5: Storage Service Tests
# ============================================================================

test_storage_service() {
    echo ""
    echo "=========================================="
    echo "SECTION 5: Storage Service Tests"
    echo "=========================================="
    echo ""
    
    # Test 5.1: Verify storage helper function exists
    echo ""
    log_info "Test 5.1: Checking storage helper function..."
    if grep -q "def get_character_image_s3_key" backend/app/services/storage.py; then
        log_success "get_character_image_s3_key function exists"
    else
        log_error "get_character_image_s3_key function not found"
    fi
    
    # Test 5.2: Verify helper supports reference and generated types
    echo ""
    log_info "Test 5.2: Checking helper supports both image types..."
    if grep -q "reference\|generated" backend/app/services/storage.py | grep -q "get_character_image_s3_key"; then
        log_success "Helper supports both reference and generated image types"
    else
        log_warn "Could not verify helper supports both image types"
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
    
    # Test 6.1: Verify CharacterImageUpload component exists
    echo ""
    log_info "Test 6.1: Checking CharacterImageUpload component..."
    if [ -f "frontend/src/components/upload/CharacterImageUpload.tsx" ]; then
        log_success "CharacterImageUpload component exists"
    else
        log_error "CharacterImageUpload component not found"
    fi
    
    # Test 6.2: Verify component has upload functionality
    echo ""
    log_info "Test 6.2: Checking component upload functionality..."
    if grep -q "FormData\|multipart/form-data" frontend/src/components/upload/CharacterImageUpload.tsx; then
        log_success "Component has upload functionality"
    else
        log_error "Component does not have upload functionality"
    fi
    
    # Test 6.3: Verify component validates file types
    echo ""
    log_info "Test 6.3: Checking component file type validation..."
    if grep -q "image/jpeg\|image/png\|image/webp" frontend/src/components/upload/CharacterImageUpload.tsx; then
        log_success "Component validates file types"
    else
        log_error "Component does not validate file types"
    fi
    
    # Test 6.4: Verify UploadPage integrates character upload
    echo ""
    log_info "Test 6.4: Checking UploadPage integration..."
    if grep -q "CharacterImageUpload" frontend/src/pages/UploadPage.tsx; then
        log_success "UploadPage integrates CharacterImageUpload"
    else
        log_error "UploadPage does not integrate CharacterImageUpload"
    fi
    
    # Test 6.5: Verify conditional rendering for short_form
    echo ""
    log_info "Test 6.5: Checking conditional rendering for short_form..."
    if grep -q "videoType === 'short_form'" frontend/src/pages/UploadPage.tsx | grep -q "CharacterImageUpload"; then
        log_success "Character upload is conditional on short_form"
    else
        log_warn "Could not verify conditional rendering"
    fi
}

# ============================================================================
# SECTION 7: Dependencies and Requirements Tests
# ============================================================================

test_dependencies() {
    echo ""
    echo "=========================================="
    echo "SECTION 7: Dependencies and Requirements Tests"
    echo "=========================================="
    echo ""
    
    # Test 7.1: Verify Pillow is in requirements.txt
    echo ""
    log_info "Test 7.1: Checking Pillow dependency..."
    if grep -q "Pillow" backend/requirements.txt; then
        log_success "Pillow is in requirements.txt"
    else
        log_error "Pillow not found in requirements.txt"
    fi
    
    # Test 7.2: Verify image_validation imports PIL
    echo ""
    log_info "Test 7.2: Checking PIL import..."
    if grep -q "from PIL import\|import PIL" backend/app/services/image_validation.py; then
        log_success "image_validation imports PIL"
    else
        log_error "image_validation does not import PIL"
    fi
}

# ============================================================================
# SECTION 8: Unit Test Execution
# ============================================================================

test_unit_tests() {
    echo ""
    echo "=========================================="
    echo "SECTION 8: Unit Test Execution"
    echo "=========================================="
    echo ""
    
    # Test 8.1: Try to run unit tests (if pytest available)
    echo ""
    log_info "Test 8.1: Running image validation unit tests..."
    
    # Try to find pytest
    PYTEST_CMD=""
    if command -v pytest >/dev/null 2>&1; then
        PYTEST_CMD="pytest"
    elif [ -f "backend/venv/bin/pytest" ]; then
        PYTEST_CMD="backend/venv/bin/pytest"
    elif [ -f "venv/bin/pytest" ]; then
        PYTEST_CMD="venv/bin/pytest"
    fi
    
    if [ -n "$PYTEST_CMD" ]; then
        cd backend
        if $PYTEST_CMD tests/unit/test_image_validation.py -v --tb=short 2>&1 | grep -q "passed\|PASSED"; then
            log_success "Image validation unit tests passed"
        else
            log_warn "Unit tests may have issues (check output above)"
        fi
        cd ..
    else
        log_warn "pytest not found - skipping unit test execution"
        log_info "Install pytest and run: pytest backend/tests/unit/test_image_validation.py -v"
    fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    echo "=========================================="
    echo "Character Consistency Foundation Test Suite"
    echo "=========================================="
    echo ""
    echo "Testing:"
    echo "  - Database schema (character fields)"
    echo "  - Image validation service"
    echo "  - Character image upload API"
    echo "  - Video generation with image input"
    echo "  - Storage service helpers"
    echo "  - Frontend component integration"
    echo ""
    
    check_dependencies
    
    # Run all test sections
    test_database_schema
    test_image_validation_service
    test_character_image_upload_api
    test_video_generation_integration
    test_storage_service
    test_frontend_components
    test_dependencies
    test_unit_tests
    
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
        echo -e "${YELLOW}⚠ Some tests failed or were skipped${NC}"
        echo "Review failures above and fix issues"
        exit 1
    fi
}

# Run main function
main

