# Memory

Working on phase: 1
DO NOT modify anything outside of v2/ — ALL of our work will be done in v2/
You MUST tell me how to run the test script you created, which is always the last sub-phase.
Read MASTER_PLAN, ARCHITECTURE, and then only the part of IMPLEMENTATION_PHASES corresponding to the phase for you to develop, and then read the below:

## Phase 1: 2-Agent Split Strategy

**If running with 2 agents, use this split. Each agent should self-select based on their assigned role or pick one that's not taken.**

### Agent Assignment (Self-Select One)

#### **Backend Auth Agent**
**Focus**: User model, authentication service, API routes, middleware, test script
- Subtasks: 1.1, 1.2, 1.3, 1.4, 1.5, 1.9 (backend), 1.10
- Files to create:
  - `v2/backend/app/models/user.py` (User model with password hashing)
  - `v2/backend/app/schemas/auth.py` (RegisterRequest, LoginRequest, AuthResponse, UserRead)
  - `v2/backend/app/services/auth_service.py` (register, authenticate, JWT token creation/verification)
  - `v2/backend/app/api/v1/routes_auth.py` (register, login, logout, /me endpoints)
  - `v2/backend/app/api/deps.py` (get_current_user dependency)
  - `v2/scripts/for-development/test-phase1.sh` (test script)
- Files to update:
  - `v2/backend/app/main.py` (include auth router)
  - `v2/backend/requirements.txt` (add python-jose[cryptography], passlib[bcrypt], python-multipart if not present)
- Can start immediately (no dependencies on frontend)
- **Dependencies**: Phase 0 must be complete (database, main.py structure)

#### **Frontend Auth Agent**
**Focus**: Auth API client, login/register pages, auth context/state, routing
- Subtasks: 1.6, 1.7, 1.8, 1.9 (frontend)
- Files to create:
  - `v2/frontend/src/api/auth.ts` (register, login, logout, getCurrentUser, token storage)
  - `v2/frontend/src/pages/LoginPage.tsx` (email/password form, validation, error handling)
  - `v2/frontend/src/pages/RegisterPage.tsx` (email/password form, password confirmation, validation)
  - `v2/frontend/src/contexts/AuthContext.tsx` (optional - can use React Query instead)
- Files to update:
  - `v2/frontend/src/App.tsx` (add auth routes, protected route wrapper, redirect logic)
  - `v2/frontend/src/api/client.ts` (or create if needed - add auth headers to API client)
- Can start immediately (no dependencies on backend, but will need backend API to be ready for testing)
- **Dependencies**: Phase 0 must be complete (frontend structure, React Query setup)

### Coordination Mechanism

**REQUIRED**: Use the coordination script to claim roles and avoid conflicts.

**Before starting work**:
1. Check available roles: `bash v2/scripts/agent-coordinator.sh list`
2. Claim a role: `bash v2/scripts/agent-coordinator.sh claim <role>`
   - Available roles: `backend-auth`, `frontend-auth`
   - Script will fail if role is already taken - pick a different role
3. If role is taken, pick a different available role

**While working**:
- Check status: `bash v2/scripts/agent-coordinator.sh status`
- Both agents can work in parallel (backend and frontend are independent)
- Frontend agent: Can start building UI components, but will need backend API ready for integration testing

**After completing work**:
1. Mark role as complete: `bash v2/scripts/agent-coordinator.sh complete <role>`
2. Test integration: Once both agents complete, verify end-to-end auth flow works

**Coordination Files**:
- Status file: `v2/.agent-status.json` (tracks role assignments and progress)
- Lock files: `v2/.agent-locks/*.lock` (prevents conflicts)
- Coordinator script: `v2/scripts/agent-coordinator.sh` (helper commands)

**Note**: Update the coordinator script roles if needed - current roles may still reference Phase 0 roles (`backend`, `frontend`, `infrastructure`). For Phase 1, use `backend-auth` and `frontend-auth`.
