import { useState, useCallback } from 'react'
import { apiClient } from '../lib/apiClient'
import type { CompositionJobStatusResponse, JobStatusResponse } from '../types/song'
import { useJobPolling } from './useJobPolling'

interface UseCompositionPollingOptions {
  jobId: string | null
  songId: string | null
  enabled: boolean
}

export const useCompositionPolling = ({
  jobId,
  songId,
  enabled,
}: UseCompositionPollingOptions) => {
  const [progress, setProgress] = useState<number>(0)
  const [error, setError] = useState<string | null>(null)
  const [isComplete, setIsComplete] = useState<boolean>(false)

  const onStatusUpdate = useCallback(
    (status: 'queued' | 'processing' | 'completed' | 'failed', progressValue: number) => {
      setProgress(progressValue)
      if (status === 'completed' || status === 'failed') {
        setIsComplete(true)
      }
    },
    [],
  )

  const onComplete = useCallback(() => {
    setIsComplete(true)
    setError(null)
  }, [])

  const onError = useCallback((errorMessage: string) => {
    setError(errorMessage)
    setIsComplete(true)
  }, [])

  const fetchStatus = useCallback(
    async (jobId: string): Promise<JobStatusResponse<null>> => {
      const { data } = await apiClient.get<CompositionJobStatusResponse>(
        `/songs/${songId}/compose/${jobId}/status`,
      )
      // Convert CompositionJobStatusResponse to JobStatusResponse format
      return {
        jobId: data.jobId ?? jobId,
        songId: data.songId ?? songId ?? '',
        status: data.status,
        progress: data.progress ?? 0,
        error: data.error ?? null,
        result: null,
      }
    },
    [songId],
  )

  useJobPolling<null>({
    jobId,
    enabled: !!jobId && !!songId && enabled,
    pollInterval: 2000,
    onStatusUpdate,
    onComplete,
    onError,
    fetchStatus,
  })

  return {
    progress,
    error,
    isComplete,
  }
}
