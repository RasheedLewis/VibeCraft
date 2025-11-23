import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '../lib/apiClient'
import { extractErrorMessage } from '../utils/validation'
import type { SongRead } from '../types/song'

export type VideoType = 'full_length' | 'short_form'

interface UseVideoTypeSelectionOptions {
  songId: string | null
  songDetails: SongRead | null
  onError?: (error: string) => void
  onAnalysisTriggered?: (jobId: string) => Promise<void>
}

export function useVideoTypeSelection({
  songId,
  songDetails,
  onError,
  onAnalysisTriggered,
}: UseVideoTypeSelectionOptions) {
  const [videoType, setVideoType] = useState<VideoType | null>(null)
  const [isSetting, setIsSetting] = useState(false)

  // Load existing video type when song loads or songDetails updates
  useEffect(() => {
    if (songDetails?.video_type) {
      // Always sync videoType from songDetails when it's available
      setVideoType(songDetails.video_type as VideoType)
    }
    // Note: We don't reset videoType to null if songDetails.video_type is null,
    // because the user might have selected a type that just hasn't been saved yet
  }, [songDetails])

  const setVideoTypeAndTriggerAnalysis = useCallback(
    async (type: VideoType) => {
      if (!songId) return

      setVideoType(type)
      setIsSetting(true)

      try {
        await apiClient.patch(`/songs/${songId}/video-type`, {
          video_type: type,
        })
        // For short_form videos, don't trigger analysis automatically
        // User needs to select audio segment first, then analysis will start
        // For full_length videos, trigger analysis immediately
        if (type === 'full_length') {
          const response = await apiClient.post<{ jobId: string; status: string }>(
            `/songs/${songId}/analyze`,
          )
          // Pass jobId to callback so polling can start
          if (onAnalysisTriggered && response.data.jobId) {
            await onAnalysisTriggered(response.data.jobId)
          }
        }
      } catch (err) {
        console.error('Failed to set video type or start analysis:', err)
        setVideoType(null)

        // Check if this is a 409 Conflict error (analysis already exists)
        const is409Error =
          err &&
          typeof err === 'object' &&
          'response' in err &&
          err.response &&
          typeof err.response === 'object' &&
          'status' in err.response &&
          err.response.status === 409

        let errorMsg = extractErrorMessage(
          err,
          'Failed to set video type or start analysis',
        )

        // Provide more helpful message for 409 errors
        if (is409Error) {
          errorMsg =
            'This song already has analysis completed. Video type cannot be changed after analysis. Please upload a new audio file to test video type selection.'
        }

        onError?.(errorMsg)
      } finally {
        setIsSetting(false)
      }
    },
    [songId, onError, onAnalysisTriggered],
  )

  const reset = useCallback(() => {
    setVideoType(null)
    setIsSetting(false)
  }, [])

  return {
    videoType,
    setVideoType: setVideoTypeAndTriggerAnalysis,
    isSetting,
    reset,
  }
}
