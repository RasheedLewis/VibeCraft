#!/bin/bash
# Phase 1 test script
# Tests: User registration, login, authentication, JWT tokens
#
# IMPORTANT: Before running this script, start the backend server in a separate terminal:
#
#   cd v2
#   source .venv/bin/activate
#   cd backend  # Must be in backend/ directory for 'app' module to be importable
#   
#   # Set DATABASE_URL if not already set (optional - server will start without it)
#   # export DATABASE_URL="postgresql://vibecraft:vibecraft@localhost:5432/vibecraft"
#   
#   uvicorn app.main:app --reload
#
# Then run this script in another terminal tab/window.
#
# Note: Make sure you're in the 'backend' directory when running uvicorn,
# otherwise you'll get "ModuleNotFoundError: No module named 'app'"
#
# Note: If you don't have a database set up, the server will start but auth
# endpoints will fail. For testing, you can use the docker-compose setup:
#   cd v2/infra && docker compose up -d postgres

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Determine script location and change to v2/ directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
V2_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$V2_DIR"

echo -e "${BLUE}Phase 1 Test Script - Authentication${NC}"
echo "======================================"
echo -e "${BLUE}Working directory: $(pwd)${NC}"
echo ""

# Check if backend is running
echo -n "Checking if backend is running... "
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${RED}✗ Backend is not running${NC}"
    echo -e "${YELLOW}Please start the backend with: cd v2/backend && uvicorn app.main:app --reload${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Backend is running${NC}"
echo ""

# Test variables
API_URL="http://localhost:8000/api/v1/auth"
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="testpassword123"
INVALID_EMAIL="invalid-email"
SHORT_PASSWORD="short"
DUPLICATE_EMAIL=""

# Test 1: Register new user
echo -e "${BLUE}Test 1: Register new user${NC}"
echo -n "  Registering user with email $TEST_EMAIL... "
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Success${NC}"
    TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    USER_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)
    DUPLICATE_EMAIL="$TEST_EMAIL"
    echo "    Token: ${TOKEN:0:20}..."
    echo "    User ID: $USER_ID"
else
    echo -e "${RED}✗ Failed${NC}"
    echo "    Response: $REGISTER_RESPONSE"
    exit 1
fi
echo ""

# Test 2: Register duplicate email
echo -e "${BLUE}Test 2: Register duplicate email${NC}"
echo -n "  Attempting to register duplicate email... "
DUPLICATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$DUPLICATE_EMAIL\", \"password\": \"$TEST_PASSWORD\"}")
HTTP_CODE=$(echo "$DUPLICATE_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ Correctly rejected duplicate email${NC}"
else
    echo -e "${RED}✗ Should have rejected duplicate email (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $DUPLICATE_RESPONSE"
    exit 1
fi
echo ""

# Test 3: Register with invalid email
echo -e "${BLUE}Test 3: Register with invalid email${NC}"
echo -n "  Attempting to register with invalid email... "
INVALID_EMAIL_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$INVALID_EMAIL\", \"password\": \"$TEST_PASSWORD\"}")
HTTP_CODE=$(echo "$INVALID_EMAIL_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ Correctly rejected invalid email${NC}"
else
    echo -e "${RED}✗ Should have rejected invalid email (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $INVALID_EMAIL_RESPONSE"
    exit 1
fi
echo ""

# Test 4: Register with short password
echo -e "${BLUE}Test 4: Register with short password${NC}"
echo -n "  Attempting to register with short password... "
SHORT_PASSWORD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"test2-$(date +%s)@example.com\", \"password\": \"$SHORT_PASSWORD\"}")
HTTP_CODE=$(echo "$SHORT_PASSWORD_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "422" ] || [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ Correctly rejected short password${NC}"
else
    echo -e "${RED}✗ Should have rejected short password (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $SHORT_PASSWORD_RESPONSE"
    exit 1
fi
echo ""

# Test 5: Login with valid credentials
echo -e "${BLUE}Test 5: Login with valid credentials${NC}"
echo -n "  Logging in with valid credentials... "
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✓ Success${NC}"
    LOGIN_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "    Token: ${LOGIN_TOKEN:0:20}..."
else
    echo -e "${RED}✗ Failed${NC}"
    echo "    Response: $LOGIN_RESPONSE"
    exit 1
fi
echo ""

# Test 6: Login with invalid password
echo -e "${BLUE}Test 6: Login with invalid password${NC}"
echo -n "  Attempting to login with wrong password... "
INVALID_PASSWORD_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"wrongpassword\"}")
HTTP_CODE=$(echo "$INVALID_PASSWORD_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ Correctly rejected invalid password${NC}"
else
    echo -e "${RED}✗ Should have rejected invalid password (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $INVALID_PASSWORD_RESPONSE"
    exit 1
fi
echo ""

# Test 7: Login with non-existent email
echo -e "${BLUE}Test 7: Login with non-existent email${NC}"
echo -n "  Attempting to login with non-existent email... "
NONEXISTENT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"nonexistent-$(date +%s)@example.com\", \"password\": \"$TEST_PASSWORD\"}")
HTTP_CODE=$(echo "$NONEXISTENT_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ Correctly rejected non-existent email${NC}"
else
    echo -e "${RED}✗ Should have rejected non-existent email (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $NONEXISTENT_RESPONSE"
    exit 1
fi
echo ""

# Test 8: Get current user with valid token
echo -e "${BLUE}Test 8: Get current user with valid token${NC}"
echo -n "  Getting current user info... "
ME_RESPONSE=$(curl -s -X GET "$API_URL/me" \
    -H "Authorization: Bearer $TOKEN")

if echo "$ME_RESPONSE" | grep -q "$TEST_EMAIL"; then
    echo -e "${GREEN}✓ Success${NC}"
    echo "    Email: $(echo "$ME_RESPONSE" | grep -o '"email":"[^"]*' | cut -d'"' -f4)"
else
    echo -e "${RED}✗ Failed${NC}"
    echo "    Response: $ME_RESPONSE"
    exit 1
fi
echo ""

# Test 9: Get current user with invalid token
echo -e "${BLUE}Test 9: Get current user with invalid token${NC}"
echo -n "  Attempting to get user with invalid token... "
INVALID_TOKEN_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/me" \
    -H "Authorization: Bearer invalid-token-12345")
HTTP_CODE=$(echo "$INVALID_TOKEN_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ Correctly rejected invalid token${NC}"
else
    echo -e "${RED}✗ Should have rejected invalid token (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $INVALID_TOKEN_RESPONSE"
    exit 1
fi
echo ""

# Test 10: Get current user without token
echo -e "${BLUE}Test 10: Get current user without token${NC}"
echo -n "  Attempting to get user without token... "
NO_TOKEN_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$API_URL/me")
HTTP_CODE=$(echo "$NO_TOKEN_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "401" ]; then
    echo -e "${GREEN}✓ Correctly rejected request without token${NC}"
else
    echo -e "${RED}✗ Should have rejected request without token (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $NO_TOKEN_RESPONSE"
    exit 1
fi
echo ""

# All tests passed
echo -e "${GREEN}======================================"
echo "All Phase 1 tests passed! ✓"
echo "======================================${NC}"
echo ""
echo "Summary:"
echo "  ✓ User registration works"
echo "  ✓ Duplicate email rejection works"
echo "  ✓ Email validation works"
echo "  ✓ Password validation works"
echo "  ✓ User login works"
echo "  ✓ Invalid credentials rejection works"
echo "  ✓ JWT token authentication works"
echo "  ✓ Protected routes require authentication"
echo ""

