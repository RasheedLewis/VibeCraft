# Polling System Flow Documentation

This document breaks down how polling works in the VibeCraft frontend application, with
specific line references for verification.

## Overview

The app uses a multi-layered polling system to track the status of asynchronous jobs:

1. **Analysis Polling** - Tracks song analysis jobs
2. **Clip Polling** - Tracks clip generation jobs (most complex)
3. **Composition Polling** - Tracks video composition jobs

All polling hooks are initialized in `UploadPage.tsx` and coordinate to update the UI.

---

## Core Polling Hook: `useJobPolling`

**Location:** `frontend/src/hooks/useJobPolling.ts`

This is the generic, reusable polling hook that all other polling hooks use (except composition).

### How It Works

1. **Initialization** (lines 31-39):
   - Checks if `jobId` and `enabled` are truthy
   - Resets cancellation flag
   - Clears any existing timeout

2. **Polling Loop** (lines 41-71):
   - Calls `fetchStatus(jobId)` to get job status
   - Normalizes status and calculates progress (lines 46-48)
   - Calls `onStatusUpdate` callback with status and progress (line 50)
   - If completed: calls `onComplete` and stops (lines 52-54)
   - If failed: calls `onError` and stops (lines 57-59)
   - Otherwise: schedules next poll using `setTimeout` (line 63)

3. **Cleanup** (lines 75-81):
   - Sets cancellation flag
   - Clears timeout to prevent memory leaks

### Key Parameters

- `pollInterval`: Default 3000ms (3 seconds) - line 22
- `fetchStatus`: Function that fetches job status from `/jobs/{jobId}` endpoint
- `onStatusUpdate`: Callback when status changes
- `onComplete`: Callback when job completes
- `onError`: Callback when job fails or fetch fails

---

## Analysis Polling: `useAnalysisPolling`

**Location:** `frontend/src/hooks/useAnalysisPolling.ts`

Uses `useJobPolling` to poll analysis jobs.

### Flow

1. **Initialization in UploadPage** (line 67):

   ```67:67:frontend/src/pages/UploadPage.tsx
   const analysisPolling = useAnalysisPolling(result?.songId ?? null)
   ```

2. **Starting Analysis** (lines 76-95):
   - `startAnalysis()` is called after upload completes (line 588 in UploadPage)
   - POSTs to `/songs/{songId}/analyze` to start job
   - Sets `jobId` state (line 87)
   - Sets status to 'queued' or 'processing' (line 88)

3. **Job Polling Setup** (lines 66-74):
   - Uses `useJobPolling` with:
     - `fetchStatus`: GET `/jobs/{jobId}` (lines 59-64)
     - `onStatusUpdate`: Updates state and progress (lines 34-40)
     - `onComplete`: Sets analysis data (lines 42-52)
     - `onError`: Sets error state (lines 54-57)

4. **Manual Fetch** (lines 17-32):
   - `fetchAnalysis()` can be called to directly fetch completed analysis
   - GET `/songs/{songId}/analysis`
   - Used when loading from URL params (line 399 in UploadPage)

### State Management

- `state`: 'idle' | 'queued' | 'processing' | 'completed' | 'failed' (line 8)
- `jobId`: Current job ID being polled (line 11)
- `progress`: 0-100 (line 12)
- `data`: SongAnalysis object when complete (line 13)
- `error`: Error message if failed (line 14)

---

## Clip Polling: `useClipPolling` (Most Complex)

**Location:** `frontend/src/hooks/useClipPolling.ts`

This is the most complex polling hook because it uses **two polling mechanisms**:

1. **Job-based polling** (via `useJobPolling`) when there's an active job
2. **Summary-based polling** (custom useEffect) as a fallback

### Dual Polling Strategy

#### Part 1: Job-Based Polling (lines 96-104)

When a clip generation job is active, it uses `useJobPolling`:

```96:104:frontend/src/hooks/useClipPolling.ts
  useJobPolling<ClipGenerationSummary>({
    jobId,
    enabled: !!jobId && !!songId,
    pollInterval: 3000,
    onStatusUpdate,
    onComplete,
    onError,
    fetchStatus: fetchJobStatus,
  })
```

- `fetchJobStatus`: GET `/jobs/{jobId}` (lines 89-94)
- `onStatusUpdate`: Updates status and progress (lines 53-62)
- `onComplete`: Fetches updated clip summary (lines 64-74)
- `onError`: Sets error and retries after 5s (lines 76-87)

#### Part 2: Summary-Based Polling (lines 108-190)

This is a fallback that polls the clip summary endpoint directly when:

- There's no active job ID
- Clips exist but job tracking is unavailable

**Key Conditions** (lines 108-146):

1. **No songId**: Resets summary and exits (lines 109-115)
2. **Active job exists**: Exits early - job polling handles it (lines 118-120)
3. **No clips yet**: Does single initial fetch, doesn't poll (lines 125-136)
4. **Composed video exists**: Stops polling (lines 139-141)
5. **All clips completed**: Stops polling (lines 144-146)

**Polling Loop** (lines 151-179):

```151:179:frontend/src/hooks/useClipPolling.ts
    const pollClipSummary = async () => {
      try {
        const { data } = await apiClient.get<ClipGenerationSummary>(
          `/songs/${songId}/clips/status`,
        )
        if (cancelled) return

        // Stop polling if composed video now exists
        if (data.composedVideoUrl) {
          setSummary(data)
          return
        }

        setSummary(data)

        // Only continue polling if there are still active clips and no jobId
        const hasActiveClips =
          data.totalClips > 0 && data.completedClips < data.totalClips
        if (hasActiveClips && !jobId) {
          timeoutId = window.setTimeout(pollClipSummary, 5000)
        }
      } catch {
        if (cancelled) return
        // On error, only retry if no active job and clips exist
        if (!jobId && summary && summary.clips && summary.clips.length > 0) {
          timeoutId = window.setTimeout(pollClipSummary, 10000)
        }
      }
    }
```

- Polls every 5 seconds when active (line 170)
- Retries every 10 seconds on error (line 176)
- Stops when composed video exists or all clips complete

### Job ID Discovery

The hook can discover job IDs from clip data (lines 27-39):

```27:39:frontend/src/hooks/useClipPolling.ts
        // Update clip job status if there's an active job
        if (data.clips && data.clips.length > 0) {
          const hasActiveJob = data.clips.some(
            (clip) =>
              normalizeClipStatus(clip.status) === 'processing' ||
              normalizeClipStatus(clip.status) === 'queued',
          )
          if (hasActiveJob && !jobId) {
            const firstClipWithJob = data.clips.find((clip) => clip.rqJobId)
            if (firstClipWithJob?.rqJobId) {
              setJobId(firstClipWithJob.rqJobId)
              setStatus('processing')
            }
          }
        }
```

### Initialization in UploadPage

```68:68:frontend/src/pages/UploadPage.tsx
  const clipPolling = useClipPolling(result?.songId ?? null)
```

### Starting Clip Generation

When user clicks "Generate Clips" (lines 201-270 in UploadPage):

1. Plans clips if needed (line 243)
2. Fetches updated summary (line 250)
3. POSTs to `/songs/{songId}/clips/generate` (line 258)
4. Sets jobId and status from response (lines 261-262)

### Loading from URL

When loading a song from URL params (lines 387-453 in UploadPage):

1. Fetches clip summary (line 404)
2. Tries to get active job from `/songs/{songId}/clips/job` (lines 408-423)
3. Falls back to checking clips for `rqJobId` (lines 426-442)

---

## Clip Polling: Problem Analysis & Solution

**Status**: ✅ **OPTIMIZED** - Current implementation is working correctly

### Historical Problem

The clip polling system originally had a check to prevent duplicate polling when an active job exists. However, this check was removed because it prevented individual clip statuses from updating in the UI:

- Clips showed "Awaiting generation" even when they were actively processing
- The UI couldn't show which specific clip was being generated (e.g., "Generating clip 3 of 8")
- Users had no visibility into individual clip progress

### Root Cause

The job status endpoint (`/jobs/{jobId}`) **does include individual clip statuses** in its `result` field, but:

1. **Timing Issue**: `useJobPolling` only called `onComplete` when the job status changed to "completed"
   - While the job was "processing", it only called `onStatusUpdate` with aggregate progress
   - Individual clip statuses were in `result`, but `onStatusUpdate` didn't receive the full result

2. **Update Frequency**: 
   - `useJobPolling` polls every 3 seconds
   - But it only updated `summary` state via `onComplete` callback
   - `onComplete` was only called when job completes, not during processing

3. **State Management Gap**:
   - `useJobPolling` manages `status` and `progress` (aggregate)
   - But `summary` (with individual clip statuses) was only updated on completion
   - The UI needs `summary.clips[].status` to show individual clip progress

### The Solution (Current Implementation)

**Option 2** was implemented: Modified `useJobPolling` to call `onComplete` with the full result during processing, not just on completion.

#### Implementation Details

1. **`useJobPolling` Enhancement** (`frontend/src/hooks/useJobPolling.ts`, lines 62-66):
```62:66:frontend/src/hooks/useJobPolling.ts
        // Update result during processing, not just on completion
        // This allows the UI to show individual clip statuses in real-time
        if (response.result) {
          onComplete?.(response.result)
        }
```

2. **Check Restored** (`frontend/src/hooks/useClipPolling.ts`, lines 191-195):
```191:195:frontend/src/hooks/useClipPolling.ts
        // CRITICAL: Don't poll at all if there's an active job - useJobPolling handles that
        // useJobPolling now updates summary during processing via onComplete callback
        if (jobId && (status === 'queued' || status === 'processing')) {
          return
        }
```

### Why It Works Now

1. **Single Polling Source**: When a job is active, only `/jobs/{jobId}` is polled
   - `useJobPolling` polls every 3 seconds
   - On each poll, it calls `onComplete` with the full `ClipGenerationSummary` (if available)
   - This updates the `summary` state with individual clip statuses in real-time

2. **Fallback Polling**: When no job is active, `pollClipSummary` handles updates
   - Only polls `/songs/{songId}/clips/status` when there's no active job
   - Provides redundancy for edge cases where job tracking is unavailable

3. **Individual Clip Status Updates**:
   - `useJobPolling`'s `onComplete` callback updates `summary` state every 3 seconds during processing
   - Each clip's status (queued/processing/completed) is immediately reflected
   - UI can show "Generating clip 3 of 8" accurately

### Benefits

- ✅ Individual clip statuses update in real-time
- ✅ Better user experience with granular progress visibility
- ✅ UI accurately reflects which clips are processing
- ✅ **No duplicate API calls** - optimal performance
- ✅ **No race conditions** - single source of truth during active jobs
- ✅ Lower server load - only one endpoint polled when job is active

### How Polling Works Now

#### Active Job Scenario (Most Common)

When a clip generation job is active (`jobId` exists):

1. **`useJobPolling`** polls `/jobs/{jobId}` every 3 seconds
2. On each poll:
   - Calls `onStatusUpdate` with aggregate status and progress
   - **Calls `onComplete` with full `ClipGenerationSummary`** (if `result` is present)
   - This updates `summary` state with individual clip statuses
3. **`pollClipSummary`** is skipped (check on line 193 prevents it)
4. Result: Single polling source, real-time updates, no duplicates

#### No Active Job Scenario

When no job is active (`jobId` is null):

1. **`useJobPolling`** is disabled (no `jobId`)
2. **`pollClipSummary`** polls `/songs/{songId}/clips/status` every 5 seconds
3. Provides fallback for cases where job tracking is unavailable
4. Stops when all clips complete or composed video exists

#### Polling Flow Diagram

```
Active Job Exists?
├─ YES → useJobPolling (every 3s)
│         ├─ Updates status/progress (aggregate)
│         └─ Updates summary (individual clips) via onComplete
│         └─ pollClipSummary SKIPPED (check on line 193)
│
└─ NO → pollClipSummary (every 5s)
         └─ Updates summary directly
         └─ Stops when all clips complete or composed video exists
```

### Original Design Intent

From commit `9363a8e` - "Refactor polling system and add comprehensive documentation" (Thu Nov 20 11:06:42 2025):

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

The check was added to **prevent duplicate polling**:
- When `jobId` exists, `useJobPolling` is already polling `/jobs/{jobId}`
- The job status endpoint returns the same `ClipGenerationSummary` in its `result` field
- Polling both endpoints simultaneously would create duplicate API calls, potential race conditions, and unnecessary server load

The original design gap has been fixed: `useJobPolling` now properly updates the `summary` state during processing, allowing the check to prevent duplicate polling while still providing real-time individual clip status updates.

---

## Composition Polling: `useCompositionPolling`

**Location:** `frontend/src/hooks/useCompositionPolling.ts`

This hook has its own custom polling implementation (doesn't use `useJobPolling`).

### Flow

1. **Initialization in UploadPage** (lines 76-80):

   ```76:80:frontend/src/pages/UploadPage.tsx
   const compositionPolling = useCompositionPolling({
     jobId: composeJobId,
     songId: result?.songId ?? null,
     enabled: compositionEnabled,
   })
   ```

2. **Polling Implementation** (lines 21-64):
   - Only runs when `jobId`, `songId`, and `enabled` are all truthy (line 22)
   - Polls `/songs/{songId}/compose/{jobId}/status` (line 29)
   - Updates progress (line 34)
   - Stops when status is 'completed' or 'failed' (lines 36-45)
   - Polls every 2 seconds (line 47)
   - Retries every 5 seconds on error (line 51)

3. **Starting Composition** (lines 158-199 in UploadPage):
   - POSTs to `/songs/{songId}/clips/compose/async` (line 187)
   - Sets `composeJobId` from response (line 191)

4. **Completion Handling** (lines 99-151 in UploadPage):
   - When `compositionPolling.isComplete` is true:
     - Fetches updated clip summary to get `composedVideoUrl`
     - Resets `isComposing` and `composeJobId` state
     - Has retry logic if composed video not immediately available

---

## Polling Coordination in UploadPage

**Location:** `frontend/src/pages/UploadPage.tsx`

All three polling hooks are initialized and their states are synchronized:

### Initialization (lines 67-80)

```67:80:frontend/src/pages/UploadPage.tsx
  // Use polling hooks with bugfixes
  const analysisPolling = useAnalysisPolling(result?.songId ?? null)
  const clipPolling = useClipPolling(result?.songId ?? null)

  // Memoize enabled to prevent unnecessary re-renders
  const compositionEnabled = useMemo(
    () => !!composeJobId && !!result?.songId,
    [composeJobId, result?.songId],
  )

  const compositionPolling = useCompositionPolling({
    jobId: composeJobId,
    songId: result?.songId ?? null,
    enabled: compositionEnabled,
  })
```

### State Synchronization (lines 82-94)

```82:94:frontend/src/pages/UploadPage.tsx
  // Sync analysis state
  const analysisState = analysisPolling.state
  const analysisProgress = analysisPolling.progress
  const analysisData = analysisPolling.data
  const analysisError = analysisPolling.error
  const isFetchingAnalysis = analysisPolling.isFetching

  // Sync clip state
  const clipJobId = clipPolling.jobId
  const clipJobStatus = clipPolling.status
  const clipJobProgress = clipPolling.progress
  const clipJobError = clipPolling.error
  const clipSummary = clipPolling.summary
```

### Workflow Sequence

1. **Upload** → `handleFileUpload` (lines 531-602)
   - Uploads file
   - Starts analysis: `analysisPolling.startAnalysis()` (line 588)
   - Fetches clip summary: `clipPolling.fetchClipSummary()` (line 591)

2. **Analysis Completes** → UI shows song profile (line 745)

3. **Generate Clips** → `handleGenerateClips` (lines 201-270)
   - Plans clips
   - Starts generation job
   - Sets clip polling jobId

4. **Clips Complete** → User can compose

5. **Compose** → `handleComposeClips` (lines 158-199)
   - Starts composition job
   - Sets `composeJobId`

6. **Composition Completes** → `useEffect` handles completion (lines 99-151)
   - Fetches updated clip summary
   - Resets composition state

---

## Key Polling Intervals

| Hook | Interval | Location |
| :--- | :------- | :------- |
| `useJobPolling` | 3000ms (3s) | `useJobPolling.ts:22` |
| `useClipPolling` (summary fallback) | 5000ms (5s) | `useClipPolling.ts:170` |
| `useCompositionPolling` | 2000ms (2s) | `useCompositionPolling.ts:47` |

---

## Error Handling & Retries

### Job Polling Errors

- Calls `onError` callback (line 68 in `useJobPolling.ts`)
- Does NOT automatically retry (stops polling)

### Clip Summary Polling Errors

- Retries after 10 seconds (line 176 in `useClipPolling.ts`)
- Only retries if clips exist and no active job

### Composition Polling Errors

- Retries after 5 seconds (line 51 in `useCompositionPolling.ts`)

### Clip Job Polling Errors

- Retries after 5 seconds via `onError` callback (line 80 in `useClipPolling.ts`)

---

## Cleanup & Memory Management

All polling hooks properly clean up:

1. **useJobPolling**: Clears timeout and sets cancellation flag (lines 75-81)
2. **useClipPolling**: Clears timeout and sets cancellation flag (lines 184-189)
3. **useCompositionPolling**: Clears timeout and sets cancellation flag (lines 58-63)

Cleanup happens when:

- Component unmounts
- Dependencies change (jobId, songId, enabled, etc.)
- Polling completes or fails

---

## Verification Checklist

To verify the polling system works correctly, check these key points:

1. **Analysis Polling**:
   - ✅ Line 67 in UploadPage: Hook initialized
   - ✅ Line 588: `startAnalysis()` called after upload
   - ✅ Lines 66-74 in useAnalysisPolling: Job polling configured
   - ✅ Line 399: Manual fetch when loading from URL

2. **Clip Polling**:
   - ✅ Line 68 in UploadPage: Hook initialized
   - ✅ Lines 96-104: Job polling configured
   - ✅ Lines 108-190: Summary polling fallback
   - ✅ Line 261: JobId set when generation starts
   - ✅ Lines 118-120: Summary polling skips when job active

3. **Composition Polling**:
   - ✅ Lines 76-80 in UploadPage: Hook initialized
   - ✅ Line 191: JobId set when composition starts
   - ✅ Lines 99-151: Completion handling

4. **Cleanup**:
   - ✅ All hooks have cleanup functions
   - ✅ Timeouts are cleared on unmount
   - ✅ Cancellation flags prevent race conditions
