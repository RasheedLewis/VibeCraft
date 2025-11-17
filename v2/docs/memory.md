# Memory

Working on phase: 2
DO NOT modify anything outside of v2/ — ALL of our work will be done in v2/
You MUST tell me how to run the test script you created, which is always the last sub-phase
Read MASTER_PLAN, ARCHITECTURE, and then only the part of IMPLEMENTATION_PHASES corresponding to the phase for you to develop, and then read the below:

## Phase 2: 2-Agent Split Strategy

### **Backend Upload Agent**
**Focus**: Song model, storage service, audio validation, API routes, test script
- Subtasks: 2.1, 2.2, 2.3, 2.4, 2.5, 2.8 (backend), 2.9
- Files to create:
  - `v2/backend/app/models/song.py` (Song model with user relationship)
  - `v2/backend/app/schemas/song.py` (SongUploadResponse, SongRead, SongCreate)
  - `v2/backend/app/services/storage_service.py` (S3 upload/download, presigned URLs, delete)
  - `v2/backend/app/services/audio_validation.py` (file format, size, duration validation)
  - `v2/backend/app/api/v1/routes_songs.py` (POST /api/songs, GET /api/songs/{id}, GET /api/songs)
  - `v2/scripts/for-development/test-phase2.sh` (test script)
- Files to update:
  - `v2/backend/app/main.py` (include songs router)
  - `v2/backend/app/models/__init__.py` (export Song model)
- Can start immediately (no dependencies on frontend)
- **Dependencies**: Phase 1 must be complete (authentication, User model)
- **Note**: Requires AWS S3 credentials configured (can use LocalStack for local testing)

### **Frontend Upload Agent**
**Focus**: Upload API client, upload page UI, file handling
- Subtasks: 2.6, 2.7, 2.8 (frontend)
- Files to create:
  - `v2/frontend/src/api/songs.ts` (uploadSong, getSong, listSongs functions)
  - `v2/frontend/src/pages/UploadPage.tsx` (drag & drop, file validation, progress, error handling)
- Files to update:
  - `v2/frontend/src/App.tsx` (add upload route)
- Can start immediately (no dependencies on backend, but will need backend API ready for testing)
- **Dependencies**: Phase 1 must be complete (authentication, routing)
- **UI Testing Required**: Follow UI_TESTING_GUIDE.md to test:
  - File upload with drag & drop
  - File validation (format, size)
  - Upload progress indicator
  - Error messages
  - Success redirect
