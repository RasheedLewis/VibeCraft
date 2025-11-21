import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '../lib/apiClient'
import { extractErrorMessage } from '../utils/validation'
import type { SongRead } from '../types/song'

export type VideoType = 'full_length' | 'short_form'

interface UseVideoTypeSelectionOptions {
  songId: string | null
  songDetails: SongRead | null
  onError?: (error: string) => void
  onAnalysisTriggered?: () => Promise<void>
}

export function useVideoTypeSelection({
  songId,
  songDetails,
  onError,
  onAnalysisTriggered,
}: UseVideoTypeSelectionOptions) {
  const [videoType, setVideoType] = useState<VideoType | null>(null)
  const [isSetting, setIsSetting] = useState(false)

  // Load existing video type when song loads
  useEffect(() => {
    if (songDetails?.video_type) {
      setVideoType(songDetails.video_type as VideoType)
    }
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
        // Trigger analysis automatically after setting video type
        await apiClient.post(`/songs/${songId}/analyze`)
        // Fetch analysis if callback provided
        if (onAnalysisTriggered) {
          await onAnalysisTriggered()
        }
      } catch (err) {
        console.error('Failed to set video type or start analysis:', err)
        setVideoType(null)
        const errorMsg = extractErrorMessage(
          err,
          'Failed to set video type or start analysis',
        )
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
