import { useState, useCallback, useEffect, useRef } from 'react'
import { apiClient } from '../lib/apiClient'
import type { ClipGenerationSummary, JobStatusResponse } from '../types/song'
import { useJobPolling } from './useJobPolling'
import { normalizeClipStatus } from '../utils/status'
import { isClipGenerationSummary } from '../utils/validation'
import { extractErrorMessage } from '../utils/validation'
import { pollingManager } from '../utils/pollingManager'

export function useClipPolling(songId: string | null) {
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<
    'idle' | 'queued' | 'processing' | 'completed' | 'failed'
  >('idle')
  const [progress, setProgress] = useState<number>(0)
  const [error, setError] = useState<string | null>(null)
  const [summary, setSummary] = useState<ClipGenerationSummary | null>(null)

  // Use refs to track current values without causing re-renders
  const songIdRef = useRef(songId)
  const jobIdRef = useRef(jobId)
  const statusRef = useRef(status)
  const summaryRef = useRef(summary)
  const subscriptionIdRef = useRef<string | null>(null)
  const subscribeTimeoutRef = useRef<number | undefined>(undefined)

  // Update refs when values change
  useEffect(() => {
    songIdRef.current = songId
    jobIdRef.current = jobId
    statusRef.current = status
    summaryRef.current = summary
  }, [songId, jobId, status, summary])

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
          // Unsubscribe from polling
          if (subscriptionIdRef.current) {
            pollingManager.unsubscribe(subscriptionIdRef.current)
            subscriptionIdRef.current = null
          }
        }

        // Update clip job status if there's an active job
        if (data.clips && data.clips.length > 0) {
          const hasActiveJob = data.clips.some(
            (clip: { status: string }) =>
              normalizeClipStatus(clip.status) === 'processing' ||
              normalizeClipStatus(clip.status) === 'queued',
          )
          if (hasActiveJob && !jobIdRef.current) {
            const firstClipWithJob = data.clips.find(
              (clip: { rqJobId?: string }) => clip.rqJobId,
            )
            if (firstClipWithJob?.rqJobId) {
              setJobId(firstClipWithJob.rqJobId)
              setStatus('processing')
            }
          }
        }
      } catch (err) {
        const message = extractErrorMessage(err, 'Unable to load clip status.')
        if (jobIdRef.current) {
          setError((prev) => prev ?? message)
        } else {
          console.warn('[clip-summary]', message)
        }
      }
    },
    // Empty deps: uses refs (jobIdRef, subscriptionIdRef) and state setters (stable)
    [],
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
        if (jobIdRef.current && songIdRef.current) {
          void fetchClipSummary(songIdRef.current)
        }
      }, 5000)
    },
    [fetchClipSummary],
  )

  const fetchJobStatus = useCallback(async (jobId: string) => {
    const { data } = await apiClient.get<JobStatusResponse<ClipGenerationSummary>>(
      `/jobs/${jobId}`,
    )
    return data
  }, [])

  // useJobPolling handles polling when we have an active job
  useJobPolling<ClipGenerationSummary>({
    jobId,
    enabled: !!jobId && !!songId,
    pollInterval: 3000,
    onStatusUpdate,
    onComplete,
    onError,
    fetchStatus: fetchJobStatus,
  })

  // Register/unregister with global polling manager
  useEffect(() => {
    const currentSongId = songIdRef.current
    const currentJobId = jobIdRef.current
    const currentStatus = statusRef.current
    const currentSummary = summaryRef.current

    // Clean up any existing subscription
    if (subscriptionIdRef.current) {
      pollingManager.unsubscribe(subscriptionIdRef.current)
      subscriptionIdRef.current = null
    }

    // Don't poll if no songId
    if (!currentSongId) {
      return
    }

    // If all clips are completed, no need to poll
    if (
      currentSummary &&
      currentSummary.totalClips > 0 &&
      currentSummary.completedClips === currentSummary.totalClips
    ) {
      if (jobId !== null) {
        setJobId(null)
        setStatus('completed')
      }
      return
    }

    // CRITICAL: Only poll clip summary when we DON'T have an active job
    // useJobPolling already handles polling when jobId exists and status is active
    const hasActiveJob =
      currentJobId && (currentStatus === 'queued' || currentStatus === 'processing')

    if (hasActiveJob) {
      // useJobPolling is handling this - don't duplicate polling
      return
    }

    // Use consistent subscription ID based on songId to prevent duplicates
    // If the same songId subscribes multiple times (React Strict Mode), it replaces the old subscription
    const subscriptionId = `clip-polling-${currentSongId}`

    // CRITICAL: Always unsubscribe any existing subscription first
    // This handles both React Strict Mode double-mounting and multiple hook instances
    if (subscriptionIdRef.current) {
      pollingManager.unsubscribe(subscriptionIdRef.current)
      subscriptionIdRef.current = null
    }

    // Also unsubscribe if subscription already exists (defensive check)
    if (pollingManager.hasSubscription(subscriptionId)) {
      pollingManager.unsubscribe(subscriptionId)
    }

    // Clear any pending subscribe timeout (debounce)
    if (subscribeTimeoutRef.current !== undefined) {
      window.clearTimeout(subscribeTimeoutRef.current)
      subscribeTimeoutRef.current = undefined
    }

    // DEBOUNCE: Wait 150ms before subscribing to give cleanup time to run
    // This prevents React Strict Mode double-mounting from creating duplicate subscriptions
    subscribeTimeoutRef.current = window.setTimeout(() => {
      subscribeTimeoutRef.current = undefined

      // Double-check conditions haven't changed during the debounce delay
      const stillCurrentSongId = songIdRef.current
      const stillCurrentJobId = jobIdRef.current
      const stillCurrentStatus = statusRef.current

      if (!stillCurrentSongId || stillCurrentSongId !== currentSongId) {
        return // SongId changed, don't subscribe
      }

      // If job started during debounce, don't subscribe (useJobPolling will handle it)
      if (
        stillCurrentJobId &&
        (stillCurrentStatus === 'queued' || stillCurrentStatus === 'processing')
      ) {
        return
      }

      subscriptionIdRef.current = subscriptionId

      // Register with global polling manager
      // The manager makes the HTTP request directly, we just provide a handler
      const url = `/songs/${currentSongId}/clips/status`

      pollingManager.subscribe(
        subscriptionId,
        url,
        async (data: unknown) => {
          // Type assertion - we know this is ClipGenerationSummary from the URL
          const clipData = data as ClipGenerationSummary
          // DRASTIC: Double-check we're still the active subscription
          // If subscription was replaced, don't process the response
          if (subscriptionIdRef.current !== subscriptionId) {
            console.log('[clip-polling] Subscription replaced, ignoring response')
            return
          }

          const songId = songIdRef.current
          const currentJobId = jobIdRef.current
          const currentStatus = statusRef.current

          // Check if we should still process this response
          if (!songId) {
            pollingManager.unsubscribe(subscriptionId)
            subscriptionIdRef.current = null
            return
          }

          // If job started, unsubscribe (useJobPolling will handle it)
          if (
            currentJobId &&
            (currentStatus === 'queued' || currentStatus === 'processing')
          ) {
            pollingManager.unsubscribe(subscriptionId)
            subscriptionIdRef.current = null
            return
          }

          setSummary(clipData)
          summaryRef.current = clipData

          // If all clips are completed, stop polling
          if (
            clipData.totalClips > 0 &&
            clipData.completedClips === clipData.totalClips
          ) {
            pollingManager.unsubscribe(subscriptionId)
            subscriptionIdRef.current = null
            setJobId(null)
            setStatus('completed')
            return
          }

          // Check if a job started (clips exist but we don't have jobId)
          if (clipData.clips && clipData.clips.length > 0 && !currentJobId) {
            const firstClipWithJob = clipData.clips.find(
              (clip: { rqJobId?: string }) => clip.rqJobId,
            )
            if (firstClipWithJob?.rqJobId) {
              setJobId(firstClipWithJob.rqJobId)
              setStatus('processing')
              // Now useJobPolling will take over - unsubscribe
              pollingManager.unsubscribe(subscriptionId)
              subscriptionIdRef.current = null
              return
            }
          }
        },
        5000, // Poll every 5 seconds (less frequent since useJobPolling handles active jobs)
      )
    }, 150) // 150ms debounce delay

    // Cleanup: unsubscribe when effect re-runs or component unmounts
    return () => {
      // Clear pending subscribe timeout
      if (subscribeTimeoutRef.current !== undefined) {
        window.clearTimeout(subscribeTimeoutRef.current)
        subscribeTimeoutRef.current = undefined
      }

      // Unsubscribe if already subscribed
      if (subscriptionIdRef.current) {
        pollingManager.unsubscribe(subscriptionIdRef.current)
        subscriptionIdRef.current = null
      }
    }
    // Only re-run when songId changes or when jobId becomes null (job completed)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [songId, jobId === null ? 'no-job' : 'has-job'])

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
