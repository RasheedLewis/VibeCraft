#!/bin/bash
# Deployment helper script for VibeCraft
# This script helps set up and deploy to Railway

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}VibeCraft Deployment Helper${NC}"
echo -e "${BLUE}==========================${NC}\n"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}Railway CLI not found. Installing...${NC}"
    npm install -g @railway/cli
    echo -e "${GREEN}✓ Railway CLI installed${NC}\n"
else
    echo -e "${GREEN}✓ Railway CLI found${NC}\n"
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Railway. Please log in:${NC}"
    railway login
    echo ""
fi

echo -e "${BLUE}Deployment Steps:${NC}"
echo -e "1. ${GREEN}✓${NC} Railway CLI ready"
echo -e "2. ${YELLOW}→${NC} Create Railway project (run: railway init)"
echo -e "3. ${YELLOW}→${NC} Add PostgreSQL addon"
echo -e "4. ${YELLOW}→${NC} Add Redis addon"
echo -e "5. ${YELLOW}→${NC} Set up AWS S3 bucket and credentials"
echo -e "6. ${YELLOW}→${NC} Deploy backend API service"
echo -e "7. ${YELLOW}→${NC} Deploy RQ worker service"
echo -e "8. ${YELLOW}→${NC} Deploy frontend service"
echo ""
echo -e "${BLUE}For detailed instructions, see: docs/DEPLOYMENT_PLAN.md${NC}\n"

# Ask if user wants to proceed with project creation
read -p "Do you want to create a new Railway project? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Creating Railway project...${NC}"
    railway init
    echo -e "${GREEN}✓ Project created${NC}\n"
fi

echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Add PostgreSQL: ${YELLOW}railway add postgresql${NC}"
echo -e "2. Add Redis: ${YELLOW}railway add redis${NC}"
echo -e "3. Link backend service: ${YELLOW}cd backend && railway link${NC}"
echo -e "4. Set environment variables in Railway dashboard"
echo -e "5. Deploy: ${YELLOW}railway up${NC}"

