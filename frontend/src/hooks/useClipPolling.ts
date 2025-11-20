import { useState, useCallback, useEffect, useLayoutEffect, useRef } from 'react'
import { apiClient } from '../lib/apiClient'
import type { ClipGenerationSummary, JobStatusResponse } from '../types/song'
import { useJobPolling } from './useJobPolling'
import { normalizeClipStatus } from '../utils/status'
import { isClipGenerationSummary } from '../utils/validation'
import { extractErrorMessage } from '../utils/validation'

export function useClipPolling(songId: string | null) {
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<
    'idle' | 'queued' | 'processing' | 'completed' | 'failed'
  >('idle')
  const [progress, setProgress] = useState<number>(0)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<ClipGenerationSummary | null>(null)

  const fetchClipSummary = useCallback(
    async (songId: string) => {
      try {
        const { data } = await apiClient.get<ClipGenerationSummary>(
          `/songs/${songId}/clips/status`,
        )
        setSummary(data)
        summaryRef.current = data

        // If all clips are completed, stop any ongoing polling
        if (data.totalClips > 0 && data.completedClips === data.totalClips) {
          pollingRef.current = false
          if (timeoutIdRef.current) {
            window.clearTimeout(timeoutIdRef.current)
            timeoutIdRef.current = undefined
          }
        }

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
      } catch (err) {
        const message = extractErrorMessage(err, 'Unable to load clip status.')
        if (jobId) {
          setError((prev) => prev ?? message)
        } else {
          console.warn('[clip-summary]', message)
        }
      }
    },
    [jobId],
  )

  const onStatusUpdate = useCallback(
    (
      statusValue: 'queued' | 'processing' | 'completed' | 'failed',
      progressValue: number,
    ) => {
      setStatus(statusValue)
      setProgress(progressValue)
    },
    [],
  )

  const onComplete = useCallback(
    (result: ClipGenerationSummary | null) => {
      if (result && isClipGenerationSummary(result)) {
        setSummary(result)
        // If all clips are completed, don't fetch again - we're done
        if (result.completedClips === result.totalClips && result.totalClips > 0) {
          return
        }
      }
      if (songId) {
        void fetchClipSummary(songId)
      }
    },
    [songId, fetchClipSummary],
  )

  const onError = useCallback(
    (errorMessage: string) => {
      setError(errorMessage)
      // Retry polling on error
      setTimeout(() => {
        if (jobId && songId) {
          void fetchClipSummary(songId)
        }
      }, 5000)
    },
    [jobId, songId, fetchClipSummary],
  )

  const fetchJobStatus = useCallback(async (jobId: string) => {
    const { data } = await apiClient.get<JobStatusResponse<ClipGenerationSummary>>(
      `/jobs/${jobId}`,
    )
    return data
  }, [])

  useJobPolling<ClipGenerationSummary>({
    jobId,
    enabled: !!jobId && !!songId,
    pollInterval: 3000,
    onStatusUpdate,
    onComplete,
    onError,
    fetchStatus: fetchJobStatus,
  })

  // Use refs to track state and avoid re-render loops
  const hasClipsRef = useRef(false)
  const pollingRef = useRef(false)
  const lastJobIdRef = useRef<string | null>(null)
  const timeoutIdRef = useRef<number | undefined>(undefined)
  const statusRef = useRef(status)
  const jobIdRef = useRef(jobId)
  const songIdRef = useRef(songId)
  const summaryRef = useRef(summary)

  // Update refs when values change (but don't trigger effect re-run)
  // Using useLayoutEffect for synchronous ref updates
  // Note: Ref mutations are intentional here - refs are meant to be mutable
  useLayoutEffect(() => {
    statusRef.current = status
    jobIdRef.current = jobId
    songIdRef.current = songId
    // eslint-disable-next-line react-hooks/immutability
    summaryRef.current = summary
  }, [status, jobId, songId, summary])

  // Poll clip summary to detect when clips are created
  // We need to poll even when there's an active job, so we can detect when clips exist
  useEffect(() => {
    const currentSongId = songIdRef.current
    if (!currentSongId) {
      // Use a function to update refs to avoid linter warnings
      const cleanup = () => {
        hasClipsRef.current = false
        pollingRef.current = false
        lastJobIdRef.current = null
        const timeout = timeoutIdRef.current
        if (timeout) {
          window.clearTimeout(timeout)
          timeoutIdRef.current = undefined
        }
      }
      cleanup()
      setTimeout(() => {
        setSummary(null)
      }, 0)
      return
    }

    // Only start polling when:
    // 1. We have a jobId
    // 2. The job is active (queued or processing)
    // 3. We're not already polling
    const currentJobId = jobIdRef.current
    const currentStatus = statusRef.current
    const jobIdChanged = currentJobId !== lastJobIdRef.current

    // If jobId changed, reset state
    if (jobIdChanged && currentJobId) {
      lastJobIdRef.current = currentJobId
      hasClipsRef.current = false
      // Reset polling flag when job changes
      // eslint-disable-next-line react-hooks/immutability
      pollingRef.current = false
    }

    // If we already have a summary showing all clips completed, don't start polling
    const currentSummary = summaryRef.current
    if (
      currentSummary &&
      currentSummary.totalClips > 0 &&
      currentSummary.completedClips === currentSummary.totalClips
    ) {
      // All clips are done - no need to poll
      return
    }

    // Start polling if:
    // - We have a jobId and it's active, AND
    // - We're not already polling
    // We poll both to detect clips initially AND to get status updates after clips exist
    const shouldStartPolling =
      currentJobId &&
      (currentStatus === 'queued' || currentStatus === 'processing') &&
      !pollingRef.current

    if (!shouldStartPolling) {
      return
    }

    // Ensure lastJobIdRef is set
    if (!lastJobIdRef.current) {
      lastJobIdRef.current = currentJobId
    }

    // Double-check we're not already polling (race condition guard)
    if (pollingRef.current) {
      return
    }

    // Mark that we're starting to poll BEFORE starting the async operation
    pollingRef.current = true
    hasClipsRef.current = false

    const pollInterval = 3000 // Poll every 3 seconds
    let cancelled = false

    const pollClipSummary = async () => {
      if (cancelled) {
        pollingRef.current = false
        return
      }

      const currentSongId = songIdRef.current
      const currentJobId = jobIdRef.current
      const currentStatus = statusRef.current

      if (!currentSongId) {
        pollingRef.current = false
        return
      }

      try {
        const { data } = await apiClient.get<ClipGenerationSummary>(
          `/songs/${currentSongId}/clips/status`,
        )
        if (cancelled) {
          pollingRef.current = false
          return
        }

        setSummary(data)

        // If all clips are completed, STOP polling immediately
        if (data.totalClips > 0 && data.completedClips === data.totalClips) {
          hasClipsRef.current = true
          pollingRef.current = false
          // Don't schedule another poll - all clips are done
          return
        }

        // If clips now exist, mark them as detected
        if (data.totalClips > 0) {
          hasClipsRef.current = true
          // Continue polling to get updates on individual clip statuses
          // Poll less frequently now (every 5 seconds instead of 3)
          const updateInterval = 5000
          // Only continue polling if job is still active (check refs, not state)
          if (
            currentJobId &&
            (currentStatus === 'queued' || currentStatus === 'processing')
          ) {
            timeoutIdRef.current = window.setTimeout(pollClipSummary, updateInterval)
          } else {
            pollingRef.current = false
          }
          return
        }

        // Keep polling until clips are created
        // Only continue if job is still active (check refs, not state)
        if (
          currentJobId &&
          (currentStatus === 'queued' || currentStatus === 'processing')
        ) {
          timeoutIdRef.current = window.setTimeout(pollClipSummary, pollInterval)
        } else {
          pollingRef.current = false
        }
      } catch {
        if (cancelled) {
          pollingRef.current = false
          return
        }
        // On error, retry after a delay
        timeoutIdRef.current = window.setTimeout(pollClipSummary, pollInterval * 2)
      }
    }

    // Start polling immediately
    pollClipSummary()

    return () => {
      cancelled = true

      pollingRef.current = false
      if (timeoutIdRef.current) {
        window.clearTimeout(timeoutIdRef.current)
        timeoutIdRef.current = undefined
      }
    }
    // Only re-run when songId changes (not status or jobId)
  }, [songId])

  return {
    jobId,
    status,
    progress,
    error,
    summary,
    setJobId,
    setStatus,
    setError,
    fetchClipSummary,
  }
}
