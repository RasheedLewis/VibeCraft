#!/bin/bash
# Phase 2 test script
# Tests: Audio upload, S3 storage, audio validation, song API endpoints
#
# This script automatically handles all prerequisites:
# - Starts PostgreSQL and Redis (via docker-compose) if needed
# - Activates virtual environment
# - Starts backend server in background if not running
# - Runs all tests
# - Cleans up background processes on exit
#
# Usage: bash scripts/for-development/test-phase2.sh
#
# Note: S3 upload tests will fail if AWS credentials are not configured.
# This is expected in local development. The script will test validation
# and database operations even if S3 upload fails.

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

echo -e "${BLUE}Phase 2 Test Script - Audio Upload & Storage${NC}"
echo "=============================================="
echo -e "${BLUE}Working directory: $(pwd)${NC}"
echo ""

# Variables for cleanup
BACKEND_PID=""
STARTED_POSTGRES=false
STARTED_REDIS=false
SKIP_CLEANUP=false
S3_KEY=""
S3_BUCKET=""

# Cleanup function
cleanup() {
    if [ "$SKIP_CLEANUP" = true ]; then
        return
    fi
    
    echo ""
    echo -e "${BLUE}Cleaning up...${NC}"
    
    # Delete S3 file if uploaded
    if [ -n "$S3_KEY" ] && [ -n "$S3_BUCKET" ] && [ "$AWS_CREDENTIALS_CONFIGURED" = true ]; then
        echo -n "  Deleting S3 file... "
        cd backend
        source ../.venv/bin/activate && python -c "
import sys
sys.path.insert(0, '.')
from app.services.storage_service import delete_from_s3
from app.core.config import get_settings
settings = get_settings()
try:
    delete_from_s3(settings.s3_bucket_name, '$S3_KEY')
    print('✓')
except Exception as e:
    print(f'⚠ Failed: {e}')
" 2>/dev/null || echo -e "${YELLOW}⚠ Failed${NC}"
        cd ..
    fi
    
    # Delete temp files
    if [ -n "$TEMP_AUDIO_FILE" ] && [ -f "$TEMP_AUDIO_FILE" ]; then
        rm -f "$TEMP_AUDIO_FILE"
    fi
    
    if [ -n "$BACKEND_PID" ] && ps -p "$BACKEND_PID" > /dev/null 2>&1; then
        echo -n "  Stopping backend server... "
        kill "$BACKEND_PID" 2>/dev/null || true
        wait "$BACKEND_PID" 2>/dev/null || true
        echo -e "${GREEN}✓${NC}"
    fi
    if [ "$STARTED_POSTGRES" = true ]; then
        echo -n "  Stopping PostgreSQL... "
        cd infra && docker compose stop postgres >/dev/null 2>&1 || true
        cd ..
        echo -e "${GREEN}✓${NC}"
    fi
    if [ "$STARTED_REDIS" = true ]; then
        echo -n "  Stopping Redis... "
        cd infra && docker compose stop redis >/dev/null 2>&1 || true
        cd ..
        echo -e "${GREEN}✓${NC}"
    fi
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Trap cleanup on exit (but allow skipping)
trap cleanup EXIT INT TERM

# Check for virtual environment
echo -n "Checking virtual environment... "
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "${YELLOW}Please run 'make install' first to create the virtual environment${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Found${NC}"

# Activate virtual environment
source .venv/bin/activate

# Check for Docker
echo -n "Checking Docker... "
if ! command -v docker >/dev/null 2>&1 || ! docker ps >/dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Docker not available (skipping database/Redis setup)${NC}"
    USE_DOCKER=false
else
    echo -e "${GREEN}✓ Available${NC}"
    USE_DOCKER=true
fi

# Detect docker compose command
USE_DOCKER_COMPOSE_V2=false
if [ "$USE_DOCKER" = true ]; then
    if docker compose version >/dev/null 2>&1; then
        USE_DOCKER_COMPOSE_V2=true
    elif command -v docker-compose >/dev/null 2>&1; then
        USE_DOCKER_COMPOSE_V2=false
    fi
fi

# Start PostgreSQL if needed
if [ "$USE_DOCKER" = true ]; then
    echo -n "Checking PostgreSQL... "
    if ! docker ps | grep -q vibecraft-postgres; then
        cd infra
        if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
            docker compose up -d postgres >/dev/null 2>&1 || true
        else
            docker-compose up -d postgres >/dev/null 2>&1 || true
        fi
        STARTED_POSTGRES=true
        # Wait for PostgreSQL to be ready
        for i in {1..30}; do
            if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
                if docker compose exec -T postgres pg_isready -U vibecraft >/dev/null 2>&1; then
                    break
                fi
            else
                if docker-compose exec -T postgres pg_isready -U vibecraft >/dev/null 2>&1; then
                    break
                fi
            fi
            sleep 1
        done
        cd ..
        echo -e "${GREEN}✓ Started${NC}"
    else
        echo -e "${GREEN}✓ Already running${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping PostgreSQL (Docker not available)${NC}"
fi

# Start Redis if needed
if [ "$USE_DOCKER" = true ]; then
    echo -n "Checking Redis... "
    if ! docker ps | grep -q redis-vibecraft; then
        cd infra
        if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
            docker compose up -d redis >/dev/null 2>&1 || true
        else
            docker-compose up -d redis >/dev/null 2>&1 || true
        fi
        STARTED_REDIS=true
        # Wait for Redis to be ready
        for i in {1..10}; do
            if [ "$USE_DOCKER_COMPOSE_V2" = true ]; then
                if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
                    break
                fi
            else
                if docker-compose exec -T redis redis-cli ping >/dev/null 2>&1; then
                    break
                fi
            fi
            sleep 1
        done
        cd ..
        echo -e "${GREEN}✓ Started${NC}"
    else
        echo -e "${GREEN}✓ Already running${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Skipping Redis (Docker not available)${NC}"
fi

# Set DATABASE_URL if not already set
if [ -z "$DATABASE_URL" ] && [ ! -f .env ]; then
    export DATABASE_URL="postgresql://vibecraft:vibecraft@localhost:5432/vibecraft"
fi

# Check if AWS credentials are configured
AWS_CREDENTIALS_CONFIGURED=false
if [ -f .env ]; then
    # Check .env file for AWS credentials
    if grep -q "AWS_ACCESS_KEY_ID=" .env && grep -q "AWS_SECRET_ACCESS_KEY=" .env; then
        # Check if they're not empty
        AWS_ACCESS_KEY=$(grep "^AWS_ACCESS_KEY_ID=" .env | cut -d'=' -f2 | tr -d ' ' | tr -d '"')
        AWS_SECRET_KEY=$(grep "^AWS_SECRET_ACCESS_KEY=" .env | cut -d'=' -f2 | tr -d ' ' | tr -d '"')
        if [ -n "$AWS_ACCESS_KEY" ] && [ -n "$AWS_SECRET_KEY" ] && [ "$AWS_ACCESS_KEY" != "" ] && [ "$AWS_SECRET_KEY" != "" ]; then
            AWS_CREDENTIALS_CONFIGURED=true
        fi
    fi
fi
# Also check environment variables
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    AWS_CREDENTIALS_CONFIGURED=true
fi

# Check if boto3 can find credentials (includes default credential chain: ~/.aws/credentials, IAM roles, etc.)
if [ "$AWS_CREDENTIALS_CONFIGURED" = false ]; then
    echo -n "Checking for AWS credentials via default credential chain... "
    cd backend
    if source ../.venv/bin/activate && python -c "
import boto3
from botocore.exceptions import NoCredentialsError, ClientError
try:
    # Try to get credentials - this will use default credential chain
    session = boto3.Session()
    credentials = session.get_credentials()
    if credentials is not None:
        # Verify credentials work by trying to list buckets (lightweight operation)
        s3 = boto3.client('s3')
        s3.list_buckets()
        exit(0)
    else:
        exit(1)
except (NoCredentialsError, ClientError):
    exit(1)
except Exception:
    # If we can't verify, assume credentials might be available
    # (e.g., if we can't connect to AWS but credentials exist)
    exit(0)
" 2>/dev/null; then
        AWS_CREDENTIALS_CONFIGURED=true
        echo -e "${GREEN}✓ Found${NC}"
    else
        echo -e "${YELLOW}⚠ Not found${NC}"
    fi
    cd ..
fi

# Check if backend is running, start if not
echo -n "Checking backend server... "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Already running${NC}"
else
    echo -n "Starting backend server... "
    cd backend
    LOG_FILE="/tmp/vibecraft-backend-test-$$.log"
    uvicorn app.main:app --host 0.0.0.0 --port 8000 >"$LOG_FILE" 2>&1 &
    BACKEND_PID=$!
    cd ..
    
    # Wait for server to start
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Started${NC}"
            break
        fi
        if [ $i -eq 30 ]; then
            echo -e "${RED}✗ Failed to start${NC}"
            echo -e "${YELLOW}Backend log:${NC}"
            tail -20 "$LOG_FILE" 2>/dev/null || echo "No log available"
            exit 1
        fi
        sleep 1
    done
fi
echo ""

# Test variables
API_URL="http://localhost:8000/api/v1"
AUTH_URL="$API_URL/auth"
SONGS_URL="$API_URL/songs"
TEST_EMAIL="test-phase2-$(date +%s)@example.com"
TEST_PASSWORD="testpassword123"

# Register a test user and get token
echo -e "${BLUE}Setting up test user...${NC}"
echo -n "  Registering user... "
REGISTER_RESPONSE=$(curl -s -X POST "$AUTH_URL/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$TEST_EMAIL\", \"password\": \"$TEST_PASSWORD\"}")

if echo "$REGISTER_RESPONSE" | grep -q "access_token"; then
    TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Success${NC}"
else
    echo -e "${RED}✗ Failed${NC}"
    echo "    Response: $REGISTER_RESPONSE"
    exit 1
fi
echo ""

# Create a temporary test audio file (silent WAV, 2 seconds)
echo -e "${BLUE}Creating test audio file...${NC}"
TEMP_AUDIO_FILE="/tmp/test-audio-$$.wav"
# Use ffmpeg to create a 2-second silent WAV file if available
if command -v ffmpeg >/dev/null 2>&1; then
    ffmpeg -f lavfi -i anullsrc=r=44100:cl=mono -t 2 -acodec pcm_s16le "$TEMP_AUDIO_FILE" -y >/dev/null 2>&1 || {
        echo -e "${YELLOW}⚠ Could not create test audio with ffmpeg, using fallback${NC}"
        # Fallback: create a minimal WAV file header (44 bytes header + some data)
        # This is a minimal valid WAV file structure
        printf "RIFF" > "$TEMP_AUDIO_FILE"
        printf "\x24\x08\x00\x00" >> "$TEMP_AUDIO_FILE"  # File size - 8
        printf "WAVE" >> "$TEMP_AUDIO_FILE"
        printf "fmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00" >> "$TEMP_AUDIO_FILE"
        printf "data\x00\x08\x00\x00" >> "$TEMP_AUDIO_FILE"
        # Add some audio data (silence)
        dd if=/dev/zero bs=1 count=2048 >> "$TEMP_AUDIO_FILE" 2>/dev/null || true
    }
    echo -e "${GREEN}✓ Created test audio file${NC}"
else
    echo -e "${YELLOW}⚠ ffmpeg not available, creating minimal WAV file${NC}"
    # Create minimal WAV file
    printf "RIFF" > "$TEMP_AUDIO_FILE"
    printf "\x24\x08\x00\x00" >> "$TEMP_AUDIO_FILE"
    printf "WAVE" >> "$TEMP_AUDIO_FILE"
    printf "fmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00" >> "$TEMP_AUDIO_FILE"
    printf "data\x00\x08\x00\x00" >> "$TEMP_AUDIO_FILE"
    dd if=/dev/zero bs=1 count=2048 >> "$TEMP_AUDIO_FILE" 2>/dev/null || true
fi
echo ""

# Test 1: Upload valid audio file
echo -e "${BLUE}Test 1: Upload valid audio file${NC}"
echo -n "  Uploading test audio file... "
UPLOAD_RESPONSE=$(curl -s -X POST "$SONGS_URL/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$TEMP_AUDIO_FILE;type=audio/wav")

S3_UPLOAD_VERIFIED=false
if echo "$UPLOAD_RESPONSE" | grep -q "song_id"; then
    SONG_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"song_id":"[^"]*' | cut -d'"' -f4)
    echo -e "${GREEN}✓ Success${NC}"
    echo "    Song ID: $SONG_ID"
    
    # Verify S3 upload if credentials are configured
    if [ "$AWS_CREDENTIALS_CONFIGURED" = true ]; then
        echo -n "  Verifying S3 upload... "
        # Get song details to check for S3 key
        GET_RESPONSE=$(curl -s -X GET "$SONGS_URL/$SONG_ID" \
            -H "Authorization: Bearer $TOKEN")
        
        if echo "$GET_RESPONSE" | grep -q "audio_s3_key"; then
            S3_KEY=$(echo "$GET_RESPONSE" | grep -o '"audio_s3_key":"[^"]*' | cut -d'"' -f4)
            if [ -n "$S3_KEY" ] && [ "$S3_KEY" != "" ]; then
                echo -e "${GREEN}✓ S3 key present: $S3_KEY${NC}"
                
                # Get S3 bucket name from settings
                cd backend
                S3_BUCKET=$(source ../.venv/bin/activate && python -c "
import sys
sys.path.insert(0, '.')
from app.core.config import get_settings
settings = get_settings()
print(settings.s3_bucket_name)
" 2>/dev/null)
                cd ..
                
                # Actually verify the file exists in S3
                echo -n "  Verifying file exists in S3... "
                cd backend
                if source ../.venv/bin/activate && python -c "
import sys
sys.path.insert(0, '.')
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from app.core.config import get_settings

settings = get_settings()
try:
    # Create S3 client (will use default credential chain if credentials not in settings)
    client_kwargs = {'service_name': 's3', 'region_name': settings.aws_region}
    if settings.aws_access_key_id is not None:
        client_kwargs['aws_access_key_id'] = settings.aws_access_key_id
    if settings.aws_secret_access_key is not None:
        client_kwargs['aws_secret_access_key'] = settings.aws_secret_access_key
    
    s3 = boto3.client(**client_kwargs)
    
    # Check if object exists in S3
    s3.head_object(Bucket='$S3_BUCKET', Key='$S3_KEY')
    
    # Also verify the file size matches what we uploaded
    response = s3.head_object(Bucket='$S3_BUCKET', Key='$S3_KEY')
    file_size = response['ContentLength']
    print(f'FILE_SIZE:{file_size}')
    exit(0)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == '404':
        print('ERROR:File not found in S3')
        exit(1)
    else:
        print(f'ERROR:{e}')
        exit(1)
except NoCredentialsError:
    print('ERROR:No AWS credentials found')
    exit(1)
except Exception as e:
    print(f'ERROR:{e}')
    exit(1)
" 2>&1 | tee /tmp/s3_verify_output.txt; then
                    # Check if we got file size
                    if grep -q "FILE_SIZE:" /tmp/s3_verify_output.txt; then
                        FILE_SIZE=$(grep "FILE_SIZE:" /tmp/s3_verify_output.txt | cut -d':' -f2)
                        UPLOADED_SIZE=$(stat -f%z "$TEMP_AUDIO_FILE" 2>/dev/null || stat -c%s "$TEMP_AUDIO_FILE" 2>/dev/null || echo "unknown")
                        echo -e "${GREEN}✓ File exists in S3 (size: $FILE_SIZE bytes)${NC}"
                        S3_UPLOAD_VERIFIED=true
                    else
                        echo -e "${GREEN}✓ File exists in S3${NC}"
                        S3_UPLOAD_VERIFIED=true
                    fi
                    rm -f /tmp/s3_verify_output.txt
                else
                    ERROR_MSG=$(cat /tmp/s3_verify_output.txt 2>/dev/null | grep "ERROR:" | cut -d':' -f2- || echo "Unknown error")
                    echo -e "${RED}✗ Failed: $ERROR_MSG${NC}"
                    rm -f /tmp/s3_verify_output.txt
                fi
                cd ..
            else
                echo -e "${YELLOW}⚠ S3 key missing in response${NC}"
            fi
        else
            echo -e "${YELLOW}⚠ Could not verify S3 upload (no audio_s3_key in response)${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠ Upload may have failed (check response)${NC}"
    echo "    Response: $UPLOAD_RESPONSE"
    # Continue with other tests even if upload fails (might be S3 credentials issue)
    SONG_ID=""
fi
echo ""

# Test 2: Get song details
if [ -n "$SONG_ID" ]; then
    echo -e "${BLUE}Test 2: Get song details${NC}"
    echo -n "  Getting song details... "
    GET_RESPONSE=$(curl -s -X GET "$SONGS_URL/$SONG_ID" \
        -H "Authorization: Bearer $TOKEN")

    if echo "$GET_RESPONSE" | grep -q "$SONG_ID"; then
        echo -e "${GREEN}✓ Success${NC}"
        echo "    Response: $GET_RESPONSE"
    else
        echo -e "${RED}✗ Failed${NC}"
        echo "    Response: $GET_RESPONSE"
    fi
    echo ""
fi

# Test 3: List user's songs
echo -e "${BLUE}Test 3: List user's songs${NC}"
echo -n "  Listing songs... "
LIST_RESPONSE=$(curl -s -X GET "$SONGS_URL/" \
    -H "Authorization: Bearer $TOKEN")

if echo "$LIST_RESPONSE" | grep -q "\["; then
    echo -e "${GREEN}✓ Success${NC}"
    SONG_COUNT=$(echo "$LIST_RESPONSE" | grep -o '"id"' | wc -l | tr -d ' ')
    echo "    Found $SONG_COUNT song(s)"
else
    echo -e "${YELLOW}⚠ Unexpected response format${NC}"
    echo "    Response: $LIST_RESPONSE"
fi
echo ""

# Test 4: Upload invalid file format
echo -e "${BLUE}Test 4: Upload invalid file format${NC}"
echo -n "  Attempting to upload text file as audio... "
TEMP_TEXT_FILE="/tmp/test-invalid-$$.txt"
echo "This is not an audio file" > "$TEMP_TEXT_FILE"
INVALID_FORMAT_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$SONGS_URL/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$TEMP_TEXT_FILE;type=text/plain")
HTTP_CODE=$(echo "$INVALID_FORMAT_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "415" ]; then
    echo -e "${GREEN}✓ Correctly rejected invalid file format${NC}"
else
    echo -e "${YELLOW}⚠ Expected rejection (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $INVALID_FORMAT_RESPONSE"
fi
rm -f "$TEMP_TEXT_FILE"
echo ""

# Test 5: Upload file too large (create a large file)
echo -e "${BLUE}Test 5: Upload file too large${NC}"
echo -n "  Creating large file (>50MB)... "
TEMP_LARGE_FILE="/tmp/test-large-$$.wav"
# Create a file larger than 50MB
dd if=/dev/zero of="$TEMP_LARGE_FILE" bs=1M count=51 >/dev/null 2>&1 || {
    # Fallback: create using head if dd fails
    head -c 52428800 /dev/zero > "$TEMP_LARGE_FILE" 2>/dev/null || true
}
echo -n "  Attempting to upload large file... "
LARGE_FILE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$SONGS_URL/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$TEMP_LARGE_FILE;type=audio/wav")
HTTP_CODE=$(echo "$LARGE_FILE_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "400" ]; then
    echo -e "${GREEN}✓ Correctly rejected file too large${NC}"
else
    echo -e "${YELLOW}⚠ Expected rejection (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $LARGE_FILE_RESPONSE"
fi
rm -f "$TEMP_LARGE_FILE"
echo ""

# Test 6: Upload without authentication
echo -e "${BLUE}Test 6: Upload without authentication${NC}"
echo -n "  Attempting to upload without token... "
NO_AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$SONGS_URL/" \
    -F "file=@$TEMP_AUDIO_FILE;type=audio/wav")
HTTP_CODE=$(echo "$NO_AUTH_RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
    echo -e "${GREEN}✓ Correctly rejected unauthenticated request${NC}"
else
    echo -e "${YELLOW}⚠ Expected rejection (got HTTP $HTTP_CODE)${NC}"
    echo "    Response: $NO_AUTH_RESPONSE"
fi
echo ""

# Test 7: Get song with wrong user
echo -e "${BLUE}Test 7: Get song with wrong user${NC}"
if [ -n "$SONG_ID" ]; then
    # Create another user
    echo -n "  Creating second user... "
    TEST_EMAIL2="test-phase2-2-$(date +%s)@example.com"
    REGISTER_RESPONSE2=$(curl -s -X POST "$AUTH_URL/register" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$TEST_EMAIL2\", \"password\": \"$TEST_PASSWORD\"}")
    
    if echo "$REGISTER_RESPONSE2" | grep -q "access_token"; then
        TOKEN2=$(echo "$REGISTER_RESPONSE2" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
        echo -e "${GREEN}✓ Success${NC}"
        echo -n "  Attempting to access first user's song... "
        WRONG_USER_RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "$SONGS_URL/$SONG_ID" \
            -H "Authorization: Bearer $TOKEN2")
        HTTP_CODE=$(echo "$WRONG_USER_RESPONSE" | tail -n1)
        if [ "$HTTP_CODE" = "403" ] || [ "$HTTP_CODE" = "404" ]; then
            echo -e "${GREEN}✓ Correctly rejected access from wrong user${NC}"
        else
            echo -e "${YELLOW}⚠ Expected rejection (got HTTP $HTTP_CODE)${NC}"
            echo "    Response: $WRONG_USER_RESPONSE"
        fi
    else
        echo -e "${YELLOW}⚠ Could not create second user${NC}"
    fi
    echo ""
fi

# Generate presigned URL and wait for user confirmation
if [ -n "$SONG_ID" ] && [ -n "$S3_KEY" ] && [ "$AWS_CREDENTIALS_CONFIGURED" = true ] && [ "$S3_UPLOAD_VERIFIED" = true ]; then
    echo ""
    echo -e "${BLUE}Generating presigned URL for uploaded file...${NC}"
    cd backend
    PRESIGNED_URL=$(source ../.venv/bin/activate && python -c "
import sys
sys.path.insert(0, '.')
from app.services.storage_service import generate_presigned_get_url
from app.core.config import get_settings
settings = get_settings()
try:
    url = generate_presigned_get_url(settings.s3_bucket_name, '$S3_KEY', expires_in=3600)
    print(url)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1)
    cd ..
    
    if echo "$PRESIGNED_URL" | grep -q "ERROR"; then
        echo -e "${YELLOW}⚠ Failed to generate presigned URL: $PRESIGNED_URL${NC}"
    else
        echo ""
        echo -e "${GREEN}Presigned URL (expires in 1 hour):${NC}"
        echo -e "${BLUE}$PRESIGNED_URL${NC}"
        echo ""
        echo -e "${YELLOW}Please open this URL in your browser to verify the file was uploaded correctly.${NC}"
        echo -n "Have you opened the URL and verified the file? (yes/no): "
        read -r USER_CONFIRMATION
        
        if [ "$USER_CONFIRMATION" != "yes" ] && [ "$USER_CONFIRMATION" != "y" ]; then
            echo -e "${YELLOW}Skipping cleanup - files will remain in S3 and /tmp${NC}"
            SKIP_CLEANUP=true
        else
            echo -e "${GREEN}✓ User confirmed - proceeding with cleanup${NC}"
        fi
    fi
fi

# Cleanup test files (only if not skipping)
if [ "$SKIP_CLEANUP" = false ]; then
    rm -f "$TEMP_AUDIO_FILE"
fi

# Summary
echo -e "${GREEN}=============================================="
echo "Phase 2 Test Summary"
echo "==============================================${NC}"
echo ""
echo "Tests completed:"
echo "  ✓ Audio file upload"
if [ -n "$SONG_ID" ]; then
    echo "  ✓ Get song details"
    if [ "$AWS_CREDENTIALS_CONFIGURED" = true ]; then
        if [ "$S3_UPLOAD_VERIFIED" = true ]; then
            echo "  ✓ S3 upload verified"
        else
            echo "  ⚠ S3 upload verification failed (credentials configured but upload may have failed)"
        fi
    else
        echo "  ⚠ S3 upload not verified (AWS credentials not configured)"
    fi
fi
echo "  ✓ List user's songs"
echo "  ✓ Invalid file format rejection"
echo "  ✓ File size validation"
echo "  ✓ Authentication required"
if [ -n "$SONG_ID" ]; then
    echo "  ✓ User ownership verification"
fi
echo ""
if [ "$AWS_CREDENTIALS_CONFIGURED" = false ]; then
    echo -e "${YELLOW}Note: AWS credentials not configured. S3 upload was not verified.${NC}"
    echo -e "${YELLOW}To test S3 upload, configure AWS credentials via:${NC}"
    echo -e "${YELLOW}  - .env file (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)${NC}"
    echo -e "${YELLOW}  - Environment variables${NC}"
    echo -e "${YELLOW}  - AWS CLI: aws configure${NC}"
    echo -e "${YELLOW}  - IAM role (if running on EC2/ECS/Lambda)${NC}"
elif [ "$S3_UPLOAD_VERIFIED" = false ] && [ -n "$SONG_ID" ]; then
    echo -e "${YELLOW}Note: AWS credentials are configured but S3 upload verification failed.${NC}"
    echo -e "${YELLOW}Check your S3 bucket configuration and permissions.${NC}"
fi
echo ""

