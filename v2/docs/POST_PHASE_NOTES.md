# POST-PHASE REVIEW

This document outlines the testing strategy for VibeCraft, starting with PER-PHASE notes on test-script and UI, and at the end a summary of integration tests and unit tests for the whole repo.

---

## POST-PHASE TESTING & UI NOTES

Each phase has a dedicated test script in `v2/scripts/for-development/test-phaseX.sh` that verifies all functionality for that phase. UI should be inspected and evaluated after each phase to ensure design system compliance, usability, and proper error handling.

### Phase 0: Foundation & Setup

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase0.sh`
- **Git Checkout** (optional): `git checkout <phase-0-commit-hash>`
- **UI Notes**: N/A (no UI components)

### Phase 1: Authentication

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase1.sh`
- **Git Checkout** (optional): `git checkout <phase-1-commit-hash>`
- **UI Notes**: Login/Register pages - verify form validation, error messages, redirects, design system compliance

### Phase 2: Audio Upload & Storage

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase2.sh`
- **Git Checkout** (optional): `git checkout <phase-2-commit-hash>`
- **UI Notes**: Upload page - verify drag & drop, file validation, progress indicators, error handling

### Phase 3: Audio Analysis

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase3.sh`
- **Git Checkout** (optional): `git checkout <phase-3-commit-hash>`
- **UI Notes**: Analysis progress overlay - verify milestone-based progress (25%, 50%, 70%, 85%, 100%), error display

### Phase 4: Section Management

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase4.sh`
- **Git Checkout** (optional): `git checkout <phase-4-commit-hash>`
- **UI Notes**: Section editor - verify timeline interaction, beat snapping, validation feedback, warning dialogs

### Phase 5: Prompt Generation & Video Type Selection

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase5.sh`
- **Git Checkout** (optional): `git checkout <phase-5-commit-hash>`
- **UI Notes**: Video type selector & prompt editor - verify dropdown, prompt editing, save functionality

### Phase 6: Clip Planning

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase6.sh`
- **Git Checkout** (optional): `git checkout <phase-6-commit-hash>`
- **UI Notes**: N/A (backend-only, no UI changes)

### Phase 7: Video Generation

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase7.sh`
- **Git Checkout** (optional): `git checkout <phase-7-commit-hash>`
- **UI Notes**: Generation progress - verify percentage-based progress (0-80%), error handling, quota checks

### Phase 8: Video Normalization

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase8.sh`
- **Git Checkout** (optional): `git checkout <phase-8-commit-hash>`
- **UI Notes**: N/A (backend-only, no UI changes)

### Phase 9: Video Composition

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase9.sh`
- **Git Checkout** (optional): `git checkout <phase-9-commit-hash>`
- **UI Notes**: Composition progress - verify milestone-based progress (80%, 90%, 95%, 100%), error handling

### Phase 10: Regeneration

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase10.sh`
- **Git Checkout** (optional): `git checkout <phase-10-commit-hash>`
- **UI Notes**: Regeneration dialog - verify options (section/clip), regeneration count display, confirmation

### Phase 11: Finalization & Cleanup

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase11.sh`
- **Git Checkout** (optional): `git checkout <phase-11-commit-hash>`
- **UI Notes**: Finalize button - verify warning dialogs (upfront and after clicking), disabled state when finalized

### Phase 12: Rate Limiting & Storage Management

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase12.sh`
- **Git Checkout** (optional): `git checkout <phase-12-commit-hash>`
- **UI Notes**: Quota display - verify usage indicators (videos: X/15, storage: X GB/5 GB), error messages

### Phase 13: Video Library & Sharing

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase13.sh`
- **Git Checkout** (optional): `git checkout <phase-13-commit-hash>`
- **UI Notes**: Video library - verify video cards, shareable URLs, delete functionality, empty state, in-progress videos with auto-resume

### Phase 14: Frontend - Video Player & Lyrics

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase14.sh`
- **Git Checkout** (optional): `git checkout <phase-14-commit-hash>`
- **UI Notes**: Video player & lyrics - verify playback, lyrics display (or empty if no lyrics), pause/regenerate flow

### Phase 15: Progress Overlay & UI Polish

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase15.sh`
- **Git Checkout** (optional): `git checkout <phase-15-commit-hash>`
- **UI Notes**: Progress overlay polish - verify all three progress types (analysis, generation, regeneration), polling, auto-resume, error display

### Phase 16: End-to-End Testing & Sample Videos

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase16.sh`
- **Git Checkout** (optional): `git checkout <phase-16-commit-hash>`
- **UI Notes**: E2E UI flow - verify complete user journey from upload to final video, all error cases, sample videos

### Phase 17: Production Deployment Configuration

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase17.sh`
- **Git Checkout** (optional): `git checkout <phase-17-commit-hash>`
- **UI Notes**: N/A (configuration-only, no UI changes)

### Phase 18: Production Deployment & Monitoring

- [ ] Test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-phase18.sh`
- **Git Checkout** (optional): `git checkout <phase-18-commit-hash>`
- **UI Notes**: Production UI verification - verify all functionality works in production environment, error handling, monitoring

---

## Integration Tests

**Scope**: Minimal integration tests focusing on critical service interactions.

- **Authentication flow**: Register → Login → Protected route access
- **Audio upload → Analysis → Section creation**: Full pipeline from upload to sectioning
- **Clip generation → Composition**: End-to-end video generation with real Replicate API calls (test account)
- **Regeneration flow**: Section/clip regeneration with quota tracking
- **Finalization → Cleanup**: Verify intermediates are cleaned up (or logged if delete fails)

**Note**: Integration tests use test database, LocalStack for S3 (or test S3 bucket), local Redis, and test Replicate account.

---

## Unit Tests

**Scope**: Comprehensive unit tests for logic and edge cases.

### Backend Services

- **Authentication Service**: Password hashing, token generation/verification, edge cases (invalid credentials, expired tokens)
- **Audio Analysis Services**:
  - BPM detection: Edge cases (no beats, very slow/fast BPM)
  - Beat alignment: Edge cases (irregular beats, silence)
  - Genre/mood analysis: Various audio types
  - Lyric extraction: No lyrics detected, partial lyrics, word-splitting across sections
- **Section Management**: Validation logic (3-10 sections, duration constraints, beat snapping, overlaps)
- **Clip Planning**: Duration matching algorithm (exact sum = section duration), edge cases (very short/long sections)
- **Video Generation**: Error handling (API failures, retries, rate limits), progress tracking
- **Video Normalization**: Resolution/FPS conversion, edge cases (already normalized, mismatched formats)
- **Video Composition**: Duration mismatch handling, audio sync, edge cases (empty clips, single clip)
- **Regeneration Service**: Limit enforcement, regeneration count tracking, failed attempt handling
- **Finalization Service**: Cleanup logic, transaction boundaries, error handling (S3 delete failures)
- **Quota Service**: Limit enforcement, race condition handling, quota calculation accuracy

### Frontend Components

- **Form Validation**: Input validation, error display
- **Progress Tracking**: Polling logic, progress calculation, auto-resume
- **Error Handling**: User-friendly error messages, retry logic
- **State Management**: Auth state, video state, regeneration state

---

## E2E Test Script

Full pipeline test covering all phases:
1. Register user
2. Upload audio
3. Analyze song
4. Create sections
5. Generate prompts
6. Plan clips
7. Generate clips
8. Compose video
9. Finalize video

- [ ] E2E test script complete & passes
- **Command**: `bash v2/scripts/for-development/test-e2e.sh`
- **Git Checkout** (optional): `git checkout <e2e-test-commit-hash>`
