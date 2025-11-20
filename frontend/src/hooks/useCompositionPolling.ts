import { useState, useEffect } from 'react'
import { apiClient } from '../lib/apiClient'
import type { CompositionJobStatusResponse } from '../types/song'
import { extractErrorMessage } from '../utils/validation'

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

  useEffect(() => {
    if (!jobId || !songId || !enabled) return

    let cancelled = false
    let timeoutId: number | undefined

    const poll = async () => {
      try {
        const { data } = await apiClient.get<CompositionJobStatusResponse>(
          `/songs/${songId}/compose/${jobId}/status`,
        )
        if (cancelled) return

        setProgress(data.progress ?? 0)

        if (data.status === 'completed') {
          setIsComplete(true)
          return
        }

        if (data.status === 'failed') {
          setError(data.error ?? 'Composition failed')
          setIsComplete(true)
          return
        }

        timeoutId = window.setTimeout(poll, 2000)
      } catch (err) {
        if (!cancelled) {
          setError(extractErrorMessage(err, 'Unable to fetch composition progress.'))
          timeoutId = window.setTimeout(poll, 5000)
        }
      }
    }

    poll()

    return () => {
      cancelled = true
      if (timeoutId) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [jobId, songId, enabled])

  return {
    progress,
    error,
    isComplete,
  }
}
