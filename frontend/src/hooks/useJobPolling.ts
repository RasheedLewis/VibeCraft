import { useEffect, useRef } from 'react'
import type { JobStatusResponse } from '../types/song'
import { normalizeJobStatus } from '../utils/status'
import { clamp } from '../utils/formatting'

interface UseJobPollingOptions<T> {
  jobId: string | null
  enabled: boolean
  pollInterval?: number
  onStatusUpdate?: (
    status: 'queued' | 'processing' | 'completed' | 'failed',
    progress: number,
  ) => void
  onComplete?: (result: T | null) => void
  onError?: (error: string) => void
  fetchStatus: (jobId: string) => Promise<JobStatusResponse<T>>
}

export function useJobPolling<T>({
  jobId,
  enabled,
  pollInterval = 3000,
  onStatusUpdate,
  onComplete,
  onError,
  fetchStatus,
}: UseJobPollingOptions<T>) {
  const cancelledRef = useRef(false)
  const timeoutIdRef = useRef<number | undefined>(undefined)

  // Use refs to store callbacks to avoid re-running effect when they change
  const onStatusUpdateRef = useRef(onStatusUpdate)
  const onCompleteRef = useRef(onComplete)
  const onErrorRef = useRef(onError)
  const fetchStatusRef = useRef(fetchStatus)

  // Update refs when callbacks change
  useEffect(() => {
    onStatusUpdateRef.current = onStatusUpdate
    onCompleteRef.current = onComplete
    onErrorRef.current = onError
    fetchStatusRef.current = fetchStatus
  }, [onStatusUpdate, onComplete, onError, fetchStatus])

  useEffect(() => {
    if (!jobId || !enabled) {
      return
    }

    cancelledRef.current = false
    // Clear any existing timeout before starting new polling
    if (timeoutIdRef.current !== undefined) {
      window.clearTimeout(timeoutIdRef.current)
      timeoutIdRef.current = undefined
    }

    const pollStatus = async () => {
      try {
        const response = await fetchStatusRef.current(jobId)
        if (cancelledRef.current) return

        const normalizedStatus = normalizeJobStatus(response.status)
        const progress =
          normalizedStatus === 'completed' ? 100 : clamp(response.progress ?? 0, 0, 99)

        onStatusUpdateRef.current?.(normalizedStatus, progress)

        if (normalizedStatus === 'completed') {
          onCompleteRef.current?.(response.result ?? null)
          return
        }

        if (normalizedStatus === 'failed') {
          onErrorRef.current?.(response.error ?? 'Job failed')
          return
        }

        // Store timeout ID in ref so cleanup can access it
        timeoutIdRef.current = window.setTimeout(pollStatus, pollInterval)
      } catch (err) {
        if (!cancelledRef.current) {
          const errorMessage =
            err instanceof Error ? err.message : 'Unable to fetch job status.'
          onErrorRef.current?.(errorMessage)
        }
      }
    }

    pollStatus()

    return () => {
      cancelledRef.current = true
      if (timeoutIdRef.current !== undefined) {
        window.clearTimeout(timeoutIdRef.current)
        timeoutIdRef.current = undefined
      }
    }
  }, [jobId, enabled, pollInterval])
}
