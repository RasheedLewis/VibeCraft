import { useState, useCallback, useEffect } from 'react'
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

  // Poll clip summary only when clips actually exist
  // Don't poll at all until we know there are clips to check
  useEffect(() => {
    if (!songId) {
      // Use setTimeout to avoid synchronous setState in effect
      setTimeout(() => {
        setSummary(null)
      }, 0)
      return
    }

    // CRITICAL: Don't poll if we don't have clips yet - wait until clips are generated
    // Only poll if summary exists and has clips, or if we're checking for the first time
    // But we should only do an initial check, not continuous polling
    if (!summary || !summary.clips || summary.clips.length === 0) {
      // Only do a single initial check to see if clips exist
      // Don't start continuous polling until clips exist
      if (summary === null) {
        // First time - do a single fetch to check if clips exist
        // Use setTimeout to avoid synchronous setState in effect
        setTimeout(() => {
          void fetchClipSummary(songId)
        }, 0)
      }
      return
    }

    // Stop polling if composed video exists
    if (summary.composedVideoUrl) {
      return
    }

    // Stop polling if all clips are completed
    if (summary.completedClips === summary.totalClips && summary.totalClips > 0) {
      return
    }

    let cancelled = false
    let timeoutId: number | undefined

    // Poll counter for debugging (temporary)
    let pollCount = 0
    
    const pollClipSummary = async () => {
      try {
        pollCount += 1
        console.log(`[POLL-COUNT] useClipPolling pollClipSummary #${pollCount} for songId: ${songId}`)
        
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

        // CRITICAL: Don't poll at all if there's an active job - useJobPolling handles that
        // useJobPolling now updates summary during processing via onComplete callback
        if (jobId && (status === 'queued' || status === 'processing')) {
          return
        }

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

    // Only start polling if clips exist
    pollClipSummary()

    return () => {
      cancelled = true
      if (timeoutId) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [songId, jobId, status, summary, fetchClipSummary])

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
