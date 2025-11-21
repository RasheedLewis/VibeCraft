import { useState, useCallback } from 'react'
import { apiClient } from '../lib/apiClient'
import type { SongAnalysis, JobStatusResponse } from '../types/song'
import { useJobPolling } from './useJobPolling'
import { isSongAnalysis } from '../utils/validation'

export function useAnalysisPolling(songId: string | null) {
  const [state, setState] = useState<
    'idle' | 'queued' | 'processing' | 'completed' | 'failed'
  >('idle')
  const [jobId, setJobId] = useState<string | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [data, setData] = useState<SongAnalysis | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isFetching, setIsFetching] = useState<boolean>(false)

  const fetchAnalysis = useCallback(async (songId: string) => {
    setIsFetching(true)
    try {
      const { data } = await apiClient.get<SongAnalysis>(`/songs/${songId}/analysis`)
      setData(data)
      setError(null)
      // If we successfully fetched analysis, it means it's completed
      setState('completed')
      setProgress(100)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load analysis results.')
      setState('failed')
    } finally {
      setIsFetching(false)
    }
  }, [])

  const onStatusUpdate = useCallback(
    (status: 'queued' | 'processing' | 'completed' | 'failed', progressValue: number) => {
      setState(status)
      setProgress(progressValue)
    },
    [],
  )

  const onComplete = useCallback(
    async (result: SongAnalysis | null) => {
      if (result && isSongAnalysis(result)) {
        setData(result)
      } else if (songId) {
        await fetchAnalysis(songId)
      }
      setError(null)
    },
    [songId, fetchAnalysis],
  )

  const onError = useCallback((errorMessage: string) => {
    setError(errorMessage)
    setState('failed')
  }, [])

  const fetchStatus = useCallback(async (jobId: string) => {
    const { data } = await apiClient.get<JobStatusResponse<SongAnalysis>>(
      `/jobs/${jobId}`,
    )
    return data
  }, [])

  useJobPolling<SongAnalysis>({
    jobId,
    enabled: !!jobId && !!songId,
    pollInterval: 3000,
    onStatusUpdate,
    onComplete,
    onError,
    fetchStatus,
  })

  const startAnalysis = useCallback(async (songId: string) => {
    try {
      setState('queued')
      setProgress(0)
      setError(null)
      setData(null)
      setJobId(null)

      const { data } = await apiClient.post<{ jobId: string; status: string }>(
        `/songs/${songId}/analyze`,
      )
      setJobId(data.jobId)
      setState(data.status === 'processing' ? 'processing' : 'queued')
    } catch (err) {
      setState('failed')
      setError(
        err instanceof Error ? err.message : 'Unable to start analysis for this track.',
      )
    }
  }, [])

  return {
    state,
    jobId,
    progress,
    data,
    error,
    isFetching,
    startAnalysis,
    fetchAnalysis,
  }
}
