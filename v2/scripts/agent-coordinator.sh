#!/bin/bash
# Agent Coordination Script
# Helps agents claim roles, track progress, and coordinate work

set -e

STATUS_FILE="v2/.agent-status.json"
LOCKS_DIR="v2/.agent-locks"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
STATUS_FILE_PATH="$REPO_ROOT/$STATUS_FILE"
LOCKS_DIR_PATH="$REPO_ROOT/$LOCKS_DIR"

# Get worktree ID from current directory or environment
WORKTREE_ID="${WORKTREE_ID:-$(basename "$(pwd)")}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Ensure locks directory exists
mkdir -p "$LOCKS_DIR_PATH"

# Initialize status file if it doesn't exist
init_status_file() {
    if [ ! -f "$STATUS_FILE_PATH" ]; then
        cat > "$STATUS_FILE_PATH" << 'EOF'
{
  "phase": 0,
  "roles": {
    "backend": {
      "assigned": false,
      "agent": null,
      "status": "available",
      "started_at": null,
      "completed_at": null
    },
    "frontend": {
      "assigned": false,
      "agent": null,
      "status": "available",
      "started_at": null,
      "completed_at": null
    },
    "infrastructure": {
      "assigned": false,
      "agent": null,
      "status": "blocked",
      "blocked_by": ["backend", "frontend"],
      "started_at": null,
      "completed_at": null
    }
  }
}
EOF
        echo -e "${GREEN}✓ Initialized status file${NC}"
    fi
}

# Read status file
read_status() {
    if [ -f "$STATUS_FILE_PATH" ]; then
        cat "$STATUS_FILE_PATH"
    else
        echo "{}"
    fi
}

# Write status file (with atomic write)
write_status() {
    local temp_file="${STATUS_FILE_PATH}.tmp"
    echo "$1" > "$temp_file"
    mv "$temp_file" "$STATUS_FILE_PATH"
}

# Check if role is available
is_role_available() {
    local role=$1
    local status=$(read_status)
    local assigned=$(echo "$status" | jq -r ".roles.$role.assigned // false")
    local role_status=$(echo "$status" | jq -r ".roles.$role.status // \"unknown\"")
    local lock_file="$LOCKS_DIR_PATH/${role}-*.lock"
    
    # Check marker file
    if ls $lock_file 2>/dev/null | grep -q .; then
        return 1  # Lock file exists, role is taken
    fi
    
    # Check status file
    if [ "$assigned" = "true" ] || [ "$role_status" != "available" ]; then
        return 1  # Role is assigned or not available
    fi
    
    return 0  # Role is available
}

# Claim a role
claim_role() {
    local role=$1
    
    if [ -z "$role" ]; then
        echo -e "${RED}Error: Role name required${NC}"
        echo "Usage: $0 claim <role>"
        echo "Available roles: backend, frontend, infrastructure"
        exit 1
    fi
    
    init_status_file
    
    # Check if role is available
    if ! is_role_available "$role"; then
        echo -e "${RED}✗ Role '$role' is not available${NC}"
        echo -e "${YELLOW}Current status:${NC}"
        show_status
        exit 1
    fi
    
    # Create marker file (atomic)
    local lock_file="$LOCKS_DIR_PATH/${role}-${WORKTREE_ID}.lock"
    if ! touch "$lock_file" 2>/dev/null; then
        echo -e "${RED}✗ Failed to create lock file${NC}"
        exit 1
    fi
    
    # Update status file
    local status=$(read_status)
    local updated_status=$(echo "$status" | jq \
        ".roles.$role.assigned = true | \
         .roles.$role.agent = \"$WORKTREE_ID\" | \
         .roles.$role.status = \"in_progress\" | \
         .roles.$role.started_at = \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"")
    
    write_status "$updated_status"
    
    echo -e "${GREEN}✓ Claimed role: $role${NC}"
    echo -e "${BLUE}Agent: $WORKTREE_ID${NC}"
    echo -e "${BLUE}Status: in_progress${NC}"
}

# Complete a role
complete_role() {
    local role=$1
    
    if [ -z "$role" ]; then
        echo -e "${RED}Error: Role name required${NC}"
        echo "Usage: $0 complete <role>"
        exit 1
    fi
    
    init_status_file
    
    # Verify agent owns this role
    local status=$(read_status)
    local assigned_agent=$(echo "$status" | jq -r ".roles.$role.agent // \"\"")
    
    if [ "$assigned_agent" != "$WORKTREE_ID" ]; then
        echo -e "${RED}✗ You don't own role '$role' (owned by: $assigned_agent)${NC}"
        exit 1
    fi
    
    # Remove marker file
    local lock_file="$LOCKS_DIR_PATH/${role}-${WORKTREE_ID}.lock"
    rm -f "$lock_file"
    
    # Update status file
    local updated_status=$(echo "$status" | jq \
        ".roles.$role.status = \"completed\" | \
         .roles.$role.completed_at = \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"")
    
    # Check if this unblocks other roles
    # For infrastructure, check if backend and frontend are completed
    if [ "$role" = "backend" ] || [ "$role" = "frontend" ]; then
        local backend_status=$(echo "$updated_status" | jq -r ".roles.backend.status")
        local frontend_status=$(echo "$updated_status" | jq -r ".roles.frontend.status")
        
        if [ "$backend_status" = "completed" ] && [ "$frontend_status" = "completed" ]; then
            updated_status=$(echo "$updated_status" | jq \
                ".roles.infrastructure.status = \"available\" | \
                 .roles.infrastructure.blocked_by = []")
            echo -e "${GREEN}✓ Infrastructure role is now available${NC}"
        fi
    fi
    
    write_status "$updated_status"
    
    echo -e "${GREEN}✓ Completed role: $role${NC}"
}

# Show current status
show_status() {
    init_status_file
    local status=$(read_status)
    
    echo -e "${BLUE}Current Agent Status:${NC}"
    echo ""
    
    echo "$status" | jq -r '.roles | to_entries[] | 
        "\(.key | ascii_upcase): \(.value.status // "unknown")
  Agent: \(.value.agent // "none")
  Assigned: \(.value.assigned // false)
  Started: \(.value.started_at // "N/A")
  Completed: \(.value.completed_at // "N/A")
"'
    
    echo -e "${YELLOW}Active locks:${NC}"
    ls -1 "$LOCKS_DIR_PATH"/*.lock 2>/dev/null | sed 's/.*\//  /' || echo "  (none)"
}

# List available roles
list_available() {
    init_status_file
    local status=$(read_status)
    
    echo -e "${BLUE}Available Roles:${NC}"
    echo ""
    
    echo "$status" | jq -r '.roles | to_entries[] | 
        if .value.status == "available" then
            "  ✓ \(.key) - AVAILABLE"
        elif .value.status == "blocked" then
            "  ⏸ \(.key) - BLOCKED (waiting for: \(.value.blocked_by | join(", ")))"
        elif .value.status == "in_progress" then
            "  ⏳ \(.key) - IN PROGRESS (agent: \(.value.agent))"
        elif .value.status == "completed" then
            "  ✅ \(.key) - COMPLETED (agent: \(.value.agent))"
        else
            "  ? \(.key) - \(.value.status)"
        end'
}

# Cleanup stale locks (older than 1 hour)
cleanup_stale_locks() {
    echo -e "${YELLOW}Cleaning up stale locks...${NC}"
    find "$LOCKS_DIR_PATH" -name "*.lock" -mmin +60 -delete 2>/dev/null || true
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

# Main command handler
case "${1:-}" in
    claim)
        claim_role "$2"
        ;;
    complete)
        complete_role "$2"
        ;;
    status)
        show_status
        ;;
    list)
        list_available
        ;;
    cleanup)
        cleanup_stale_locks
        ;;
    *)
        echo "Agent Coordinator"
        echo ""
        echo "Usage: $0 <command> [args]"
        echo ""
        echo "Commands:"
        echo "  claim <role>      Claim a role (backend, frontend, infrastructure)"
        echo "  complete <role>   Mark a role as completed"
        echo "  status            Show current status of all roles"
        echo "  list              List available roles"
        echo "  cleanup           Remove stale lock files"
        echo ""
        echo "Examples:"
        echo "  $0 claim backend"
        echo "  $0 status"
        echo "  $0 complete backend"
        exit 1
        ;;
esac

