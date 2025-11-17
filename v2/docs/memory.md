# Memory

DO NOT modify anything outside of v2/ — ALL of our work will be done in v2/
Working on phase: 0
Read MASTER_PLAN, ARCHITECTURE, and then only the part of IMPLEMENTATION_PHASES corresponding to the phase for you to develop, and then read the below:

## Phase 0: 3-Agent Split Strategy

**If running with 3 agents, use this split. Each agent should self-select based on their assigned role or pick one that's not taken.**

### Agent Assignment (Self-Select One)

#### **Backend Foundation Agent**
**Focus**: Backend structure, dependencies, core files, main application
- Subtasks: 0.1, 0.2, 0.3, 0.4
- Files to create:
  - `v2/backend/app/` directory structure with all `__init__.py` files
  - `v2/backend/requirements.txt`
  - `v2/backend/app/core/config.py`
  - `v2/backend/app/core/database.py`
  - `v2/backend/app/core/logging.py`
  - `v2/backend/app/models/job.py`
  - `v2/backend/app/main.py`
- Can start immediately (no dependencies)

#### **Frontend Foundation Agent**
**Focus**: Frontend bootstrap, dependencies, configuration, entry points
- Subtasks: 0.5, 0.6, 0.7, 0.8
- Files to create/update:
  - Bootstrap `v2/frontend/` with Vite
  - `v2/frontend/tailwind.config.ts`
  - Update `v2/frontend/package.json`, `vite.config.ts`, `tsconfig.json`
  - Update `v2/frontend/src/main.tsx`, `App.tsx`
- Can start immediately (no dependencies, works in parallel with Backend Agent)

#### **Infrastructure & DevOps Agent**
**Focus**: Environment config, deployment infrastructure, testing, documentation
- Subtasks: 0.9, 0.10, 0.11, 0.12
- Files to create:
  - `v2/.env.example`
  - `v2/Makefile`
  - `v2/scripts/dev.sh`
  - `v2/infra/docker-compose.yml`
  - `v2/infra/Dockerfile.backend`
  - `v2/scripts/health-check.sh`
  - `v2/docs/DEPLOYMENT.md`
  - `v2/scripts/for-development/test-phase0.sh`
- Files to update:
  - `v2/backend/app/main.py` (add environment validation)
  - `v2/README.md`
- **IMPORTANT**: Wait for Backend and Frontend agents to complete first, then:
  1. Add environment validation to `main.py` (created by Backend Agent)
  2. Create Makefile/scripts that reference both backend and frontend
  3. Create test scripts that verify both setups

### Coordination Notes
- Backend and Frontend agents can work in parallel
- Infrastructure agent must wait for both to finish
- If conflicts arise, communicate via file comments or coordinate through shared understanding of the split
