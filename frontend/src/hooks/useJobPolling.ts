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

  useEffect(() => {
    if (!jobId || !enabled) return

    cancelledRef.current = false
    let timeoutId: number | undefined

    const pollStatus = async () => {
      try {
        const response = await fetchStatus(jobId)
        if (cancelledRef.current) return

        const normalizedStatus = normalizeJobStatus(response.status)
        const progress =
          normalizedStatus === 'completed' ? 100 : clamp(response.progress ?? 0, 0, 99)

        onStatusUpdate?.(normalizedStatus, progress)

        if (normalizedStatus === 'completed') {
          onComplete?.(response.result ?? null)
          return
        }

        if (normalizedStatus === 'failed') {
          onError?.(response.error ?? 'Job failed')
          return
        }

        timeoutId = window.setTimeout(pollStatus, pollInterval)
      } catch (err) {
        if (!cancelledRef.current) {
          const errorMessage =
            err instanceof Error ? err.message : 'Unable to fetch job status.'
          onError?.(errorMessage)
        }
      }
    }

    pollStatus()

    return () => {
      cancelledRef.current = true
      if (timeoutId) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [jobId, enabled, pollInterval, onStatusUpdate, onComplete, onError, fetchStatus])
}
