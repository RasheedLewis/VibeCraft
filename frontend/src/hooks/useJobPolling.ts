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

  useEffect(() => {
    if (!jobId || !enabled) return

    cancelledRef.current = false
    // Clear any existing timeout before starting new polling
    if (timeoutIdRef.current !== undefined) {
      window.clearTimeout(timeoutIdRef.current)
      timeoutIdRef.current = undefined
    }

    // Poll counter for debugging (temporary)
    const pollCountRef = useRef(0)
    
    const pollStatus = async () => {
      try {
        pollCountRef.current += 1
        console.log(`[POLL-COUNT] useJobPolling poll #${pollCountRef.current} for jobId: ${jobId}`)
        
        const response = await fetchStatus(jobId)
        if (cancelledRef.current) return

        const normalizedStatus = normalizeJobStatus(response.status)
        const progress =
          normalizedStatus === 'completed' ? 100 : clamp(response.progress ?? 0, 0, 99)

        onStatusUpdate?.(normalizedStatus, progress)

        // Update result during processing, not just on completion
        // This allows the UI to show individual clip statuses in real-time
        if (response.result) {
          onComplete?.(response.result)
        }

        if (normalizedStatus === 'completed') {
          return
        }

        if (normalizedStatus === 'failed') {
          onError?.(response.error ?? 'Job failed')
          return
        }

        // Store timeout ID in ref so cleanup can access it
        timeoutIdRef.current = window.setTimeout(pollStatus, pollInterval)
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
      if (timeoutIdRef.current !== undefined) {
        window.clearTimeout(timeoutIdRef.current)
        timeoutIdRef.current = undefined
      }
    }
  }, [jobId, enabled, pollInterval, onStatusUpdate, onComplete, onError, fetchStatus])
}
