import { useCallback, useEffect, useState } from 'react'
import { apiClient } from '../lib/apiClient'
import type { SongRead } from '../types/song'

interface AudioSelection {
  startSec: number
  endSec: number
}

interface UseAudioSelectionOptions {
  songId: string | null
  songDetails: SongRead | null
}

export function useAudioSelection({ songId, songDetails }: UseAudioSelectionOptions) {
  const [audioSelection, setAudioSelection] = useState<AudioSelection | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  // Load existing selection when song loads
  useEffect(() => {
    if (
      songDetails?.selected_start_sec !== undefined &&
      songDetails?.selected_start_sec !== null &&
      songDetails?.selected_end_sec !== undefined &&
      songDetails?.selected_end_sec !== null
    ) {
      setAudioSelection({
        startSec: songDetails.selected_start_sec,
        endSec: songDetails.selected_end_sec,
      })
    }
  }, [songDetails])

  const saveSelection = useCallback(
    async (startSec: number, endSec: number) => {
      if (!songId) return

      setAudioSelection({ startSec, endSec })
      setIsSaving(true)

      try {
        await apiClient.patch(`/songs/${songId}/selection`, {
          start_sec: startSec,
          end_sec: endSec,
        })
      } catch (err) {
        console.error('Failed to save audio selection:', err)
        // Don't show error to user - selection is saved locally
      } finally {
        setIsSaving(false)
      }
    },
    [songId],
  )

  const reset = useCallback(() => {
    setAudioSelection(null)
    setIsSaving(false)
  }, [])

  return {
    audioSelection,
    setAudioSelection,
    saveSelection,
    isSaving,
    reset,
  }
}
