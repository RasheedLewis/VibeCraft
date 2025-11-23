# Polling Logic Analysis Report

## Change Made

**File**: `frontend/src/hooks/useClipPolling.ts`  
**Lines**: 117-120 (removed)  
**Date**: Current session

### What Was Removed

```typescript
// CRITICAL: Don't poll at all if there's an active job - useJobPolling handles that
if (jobId && (status === 'queued' || status === 'processing')) {
  return
}
```

## Original Design Intent (from Git History)

### Commit: `9363a8e` - "Refactor polling system and add comprehensive documentation"

**Date**: Thu Nov 20 11:06:42 2025

The original design implemented a **dual polling strategy**:

1. **Job-based polling** (`useJobPolling`) - When an active job exists
   - Polls `/jobs/{jobId}` endpoint
   - Returns `JobStatusResponse` with `result: ClipGenerationSummary`
   - Provides overall batch job status (queued/processing/completed/failed)
   - Provides aggregate progress (completedClips/totalClips)

2. **Summary-based polling** (`pollClipSummary`) - When no job tracking available
   - Polls `/songs/{songId}/clips/status` endpoint
   - Returns `ClipGenerationSummary` directly
   - Provides individual clip statuses

### Why the Check Existed

The check was added to **prevent duplicate polling**:

- When `jobId` exists, `useJobPolling` is already polling `/jobs/{jobId}`
- The job status endpoint returns the same `ClipGenerationSummary` in its `result` field
- Polling both endpoints simultaneously would create:
  - Duplicate API calls (wasteful)
  - Potential race conditions
  - Unnecessary server load

## The Problem

### What Was Broken

When the check was active, individual clip statuses were **not updating in the UI**:

- Clips showed "Awaiting generation" even when they were actively processing
- The UI couldn't show which specific clip was being generated (e.g., "Generating clip 3 of 8")
- Users had no visibility into individual clip progress

### Root Cause Analysis

**The job status endpoint DOES include individual clip statuses**, but:

1. **Timing Issue**: `useJobPolling` calls `onComplete` with the full `ClipGenerationSummary`, but:
   - It only calls `onComplete` when the job status changes to "completed"
   - While the job is "processing", it only calls `onStatusUpdate` with aggregate progress
   - Individual clip statuses are in `result`, but `onStatusUpdate` doesn't receive the full result

2. **Update Frequency**:
   - `useJobPolling` polls every 3 seconds
   - But it only updates `summary` state via `onComplete` callback
   - `onComplete` is only called when job completes, not during processing

3. **State Management Gap**:
   - `useJobPolling` manages `status` and `progress` (aggregate)
   - But `summary` (with individual clip statuses) is only updated on completion
   - The UI needs `summary.clips[].status` to show individual clip progress

## The Fix

### What Changed

Removed the check that prevented clip summary polling when a job is active.

### Why It Works Now

1. **Dual Polling**: Both endpoints now poll simultaneously
   - `/jobs/{jobId}` provides aggregate job status
   - `/songs/{songId}/clips/status` provides individual clip statuses
   - The UI gets real-time updates on both levels

2. **Individual Clip Status Updates**:
   - `pollClipSummary` updates `summary` state every 5 seconds
   - Each clip's status (queued/processing/completed) is immediately reflected
   - UI can show "Generating clip 3 of 8" accurately

### Trade-offs

**Pros**:

- ✅ Individual clip statuses update in real-time
- ✅ Better user experience with granular progress visibility
- ✅ UI accurately reflects which clips are processing

**Cons**:

- ⚠️ Duplicate API calls (both endpoints poll simultaneously)
- ⚠️ Slightly higher server load
- ⚠️ Potential for race conditions if responses arrive out of order

## Recommendations

### Option 1: Keep Current Fix (Simplest)

- Accept the duplicate polling
- The overhead is minimal (2 endpoints every 3-5 seconds)
- Works correctly and provides good UX

### Option 2: Optimize useJobPolling (Better)

Modify `useJobPolling` to call `onComplete` with the full result on every poll, not just on completion:

```typescript
// In useJobPolling.ts
if (normalizedStatus === 'completed') {
  onComplete?.(response.result ?? null)
  return
}
// ADD: Also call onComplete during processing to update summary
if (response.result) {
  onComplete?.(response.result)
}
```

Then restore the check to prevent duplicate polling.

### Option 3: Hybrid Approach (Best)

- Keep `useJobPolling` for aggregate status
- Use `pollClipSummary` only when:
  - No `jobId` exists, OR
  - `jobId` exists but we haven't received a summary update in the last 5 seconds
- This provides redundancy without constant duplicate calls

## Current Status

✅ **Working**: Individual clip statuses update correctly  
⚠️ **Trade-off**: Duplicate API calls (acceptable for now)  
📊 **Performance**: Minimal impact (2 endpoints every 3-5 seconds)

## Conclusion

The original design was sound but had a gap: `useJobPolling` doesn't update the
`summary` state during processing, only on completion. The fix works but creates
duplicate polling. The best long-term solution would be Option 2 or 3 to optimize
the polling strategy.
