#!/bin/bash
# Health check script for VibeCraft v2 services

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "Running health checks..."

# Check backend health
echo -n "Checking backend API... "
if curl -f http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    exit 1
fi

# Check database connection
echo -n "Checking database connection... "
cd backend
source ../.venv/bin/activate
python -c "from app.core.database import check_db_connection; exit(0 if check_db_connection() else 1)" 2>/dev/null && \
    echo -e "${GREEN}✓ OK${NC}" || \
    echo -e "${YELLOW}⚠ SKIPPED (database not configured)${NC}"
deactivate
cd ..

# Check Redis connection
echo -n "Checking Redis connection... "
if redis-cli -h localhost -p 6379 ping >/dev/null 2>&1; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ SKIPPED (Redis not running)${NC}"
fi

# Check S3 access (if configured)
echo -n "Checking S3 access... "
cd backend
source ../.venv/bin/activate
python -c "
import os
from app.core.config import get_settings
settings = get_settings()
if settings.aws_access_key_id and settings.aws_secret_access_key:
    import boto3
    try:
        s3 = boto3.client('s3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        s3.head_bucket(Bucket=settings.s3_bucket_name)
        exit(0)
    except:
        exit(1)
else:
    exit(2)
" 2>/dev/null
case $? in
    0) echo -e "${GREEN}✓ OK${NC}" ;;
    1) echo -e "${RED}✗ FAILED${NC}" ;;
    2) echo -e "${YELLOW}⚠ SKIPPED (S3 not configured)${NC}" ;;
esac
deactivate
cd ..

echo -e "\n${GREEN}Health checks complete!${NC}"

