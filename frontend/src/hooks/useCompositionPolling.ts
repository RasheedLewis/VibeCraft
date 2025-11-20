import { useState, useCallback, useRef, useEffect } from 'react'
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

  // Use refs to store songId to avoid recreating fetchStatus on every render
  const songIdRef = useRef(songId)
  useEffect(() => {
    songIdRef.current = songId
  }, [songId])

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

  // Use ref for songId to prevent fetchStatus from being recreated
  const fetchStatus = useCallback(
    async (jobId: string): Promise<JobStatusResponse<null>> => {
      const currentSongId = songIdRef.current
      if (!currentSongId) {
        throw new Error('Song ID is required for composition polling')
      }
      const { data } = await apiClient.get<CompositionJobStatusResponse>(
        `/songs/${currentSongId}/compose/${jobId}/status`,
      )
      // Convert CompositionJobStatusResponse to JobStatusResponse format
      return {
        jobId: data.jobId ?? jobId,
        songId: data.songId ?? currentSongId,
        status: data.status,
        progress: data.progress ?? 0,
        error: data.error ?? null,
        result: null,
      }
    },
    [], // Empty deps - songId is accessed via ref
  )

  // Only enable polling if all conditions are met
  // Don't recalculate enabled here - use the prop directly to avoid unnecessary effect re-runs
  useJobPolling<null>({
    jobId,
    enabled: enabled && !!jobId && !!songId,
    pollInterval: 3000,
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
