import React, { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import clsx from 'clsx'
import axios from 'axios'
import { apiClient } from '../lib/apiClient'
import { VCButton } from '../components/vibecraft'
import type { MoodKind } from '../components/vibecraft/SectionMoodTag'
import type {
  ClipGenerationSummary,
  ComposeVideoResponse,
  SongClipStatus,
  SongRead,
  SongUploadResponse,
} from '../types/song'

// Constants
import {
  ACCEPTED_MIME_TYPES,
  MAX_DURATION_SECONDS,
  MAX_AUDIO_FILE_SIZE_MB,
  MAX_AUDIO_FILE_SIZE_BYTES,
} from '../constants/upload'

// Utilities
import { extractErrorMessage } from '../utils/validation'
import { mapMoodToMoodKind } from '../utils/sections'
import { computeDuration } from '../utils/audio'
import { normalizeClipStatus } from '../utils/status'

// Hooks
import { useAnalysisPolling } from '../hooks/useAnalysisPolling'
import { useClipPolling } from '../hooks/useClipPolling'
import { useCompositionPolling } from '../hooks/useCompositionPolling'
import { useVideoTypeSelection } from '../hooks/useVideoTypeSelection'
import { useAudioSelection } from '../hooks/useAudioSelection'
import { useAuth } from '../hooks/useAuth'

// Components
import { BackgroundOrbs } from '../components/upload/BackgroundOrbs'
import { RequirementPill } from '../components/upload/RequirementPill'
import { UploadCard } from '../components/upload/UploadCard'
import {
  WaveformIcon,
  TimerIcon,
  HardDriveIcon,
  ErrorIcon,
} from '../components/upload/Icons'
import { AudioSelectionTimeline } from '../components/upload/AudioSelectionTimeline'
import { VideoTypeSelector } from '../components/upload/VideoTypeSelector'
import { CharacterImageUpload } from '../components/upload/CharacterImageUpload'
import { TemplateCharacterModal } from '../components/upload/TemplateCharacterModal'
import { SelectedTemplateDisplay } from '../components/upload/SelectedTemplateDisplay'
import { SongProfileView } from '../components/song/SongProfileView'
import { ProjectsModal } from '../components/projects/ProjectsModal'
import { AuthModal } from '../components/auth/AuthModal'

type UploadStage = 'idle' | 'dragging' | 'uploading' | 'uploaded' | 'error'

interface UploadMetadata {
  fileName: string
  fileSize: number
  durationSeconds: number | null
}

export const UploadPage: React.FC = () => {
  const { isAuthenticated, isLoading: isAuthLoading } = useAuth()
  const fileInputId = useId()
  const [stage, setStage] = useState<UploadStage>('idle')
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState<number>(0)
  const [metadata, setMetadata] = useState<UploadMetadata | null>(null)
  const [result, setResult] = useState<SongUploadResponse | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const [songDetails, setSongDetails] = useState<SongRead | null>(null)
  const [highlightedSectionId, setHighlightedSectionId] = useState<string | null>(null)
  const [isComposing, setIsComposing] = useState<boolean>(false)
  const [composeJobId, setComposeJobId] = useState<string | null>(null)
  const [playerActiveClipId, setPlayerActiveClipId] = useState<string | null>(null)
  const [playerClipSelectionLocked, setPlayerClipSelectionLocked] =
    useState<boolean>(false)
  const compositionCompleteHandledRef = useRef<string | null>(null)
  const autoScrollCompletedRef = useRef<boolean>(false)
  const uploadAbortControllerRef = useRef<AbortController | null>(null)
  const [templateModalOpen, setTemplateModalOpen] = useState(false)
  const [projectsModalOpen, setProjectsModalOpen] = useState(false)
  const [authModalOpen, setAuthModalOpen] = useState(false)
  const [loginPromptModalOpen, setLoginPromptModalOpen] = useState(false)
  const [videoTypeSelectorVisible, setVideoTypeSelectorVisible] = useState(true)
  const [hideCharacterConsistency, setHideCharacterConsistency] = useState(false)
  const [showNoCharacterConfirm, setShowNoCharacterConfirm] = useState(false)
  const [showProfileHint, setShowProfileHint] = useState(false)

  // Use custom hooks for video type and audio selection
  const videoTypeSelection = useVideoTypeSelection({
    songId: result?.songId ?? null,
    songDetails,
    onError: setError,
    onAnalysisTriggered: async (jobId: string) => {
      // Set the jobId in the polling hook so it starts polling automatically
      analysisPolling.setJobId?.(jobId)
      return Promise.resolve()
    },
  })
  const audioSelection = useAudioSelection({
    songId: result?.songId ?? null,
    songDetails,
  })

  // Use polling hooks with bugfixes
  const analysisPolling = useAnalysisPolling(result?.songId ?? null)
  const clipPolling = useClipPolling(result?.songId ?? null)

  // Sync video type selection state
  const videoType = videoTypeSelection.videoType
  // const isSettingVideoType = videoTypeSelection.isSetting

  // Hide video type selector 3 seconds after analysis begins (fade out)
  // COMMENTED OUT: Timing logic for fade-out
  // useEffect(() => {
  //   if (
  //     videoType &&
  //     (analysisState === 'queued' || analysisState === 'processing') &&
  //     videoTypeSelectorVisible
  //   ) {
  //     const timer = setTimeout(() => {
  //       setVideoTypeSelectorVisible(false)
  //     }, 3000)
  //     return () => clearTimeout(timer)
  //   }
  //   // Reset visibility when videoType becomes null (new upload)
  //   if (!videoType) {
  //     setVideoTypeSelectorVisible(true)
  //   }
  // }, [videoType, analysisState, videoTypeSelectorVisible])

  // Sync audio selection state
  const audioSelectionValue = audioSelection.audioSelection
  const isSavingSelection = audioSelection.isSaving

  // Memoize enabled to prevent unnecessary re-renders
  const compositionEnabled = useMemo(
    () => !!composeJobId && !!result?.songId,
    [composeJobId, result?.songId],
  )

  const compositionPolling = useCompositionPolling({
    jobId: composeJobId,
    songId: result?.songId ?? null,
    enabled: compositionEnabled,
  })

  // Sync analysis state
  const analysisState = analysisPolling.state
  const analysisProgress = analysisPolling.progress
  const analysisData = analysisPolling.data
  const analysisError = analysisPolling.error
  const isFetchingAnalysis = analysisPolling.isFetching

  // Sync clip state
  const clipJobId = clipPolling.jobId
  const clipJobStatus = clipPolling.status
  const clipJobProgress = clipPolling.progress
  const clipJobError = clipPolling.error
  const clipSummary = clipPolling.summary

  // Sync composition progress
  const composeJobProgress = compositionPolling.progress

  useEffect(() => {
    if (compositionPolling.isComplete) {
      // Prevent handling completion multiple times for the same job
      if (compositionCompleteHandledRef.current === composeJobId) {
        return
      }
      compositionCompleteHandledRef.current = composeJobId

      // Don't reset state immediately - wait for clip summary to update with composed video
      // This prevents the button from showing "Compose when done" again
      if (result?.songId) {
        // Fetch updated clip summary which should now include composedVideoUrl
        void clipPolling.fetchClipSummary(result.songId).then(() => {
          // Check if composed video URL is now available in the updated summary
          // We need to wait a moment for the state to update after fetchClipSummary
          setTimeout(() => {
            const updatedSummary = clipPolling.summary
            if (updatedSummary?.composedVideoUrl) {
              // Composed video is available, safe to reset state
              setIsComposing(false)
              setComposeJobId(null)
            } else {
              // Composed video not yet available, wait a bit and retry once more
              setTimeout(() => {
                void clipPolling.fetchClipSummary(result.songId).then(() => {
                  setIsComposing(false)
                  setComposeJobId(null)
                })
              }, 2000)
            }
          }, 500)
        })
      } else {
        setTimeout(() => {
          setIsComposing(false)
          setComposeJobId(null)
        }, 0)
      }
    }
    if (compositionPolling.error) {
      setTimeout(() => {
        setIsComposing(false)
        setComposeJobId(null)
        clipPolling.setError(compositionPolling.error)
      }, 0)
    }
  }, [
    compositionPolling.isComplete,
    compositionPolling.error,
    result?.songId,
    clipPolling,
    composeJobId,
  ])

  const handleCancelClipJob = useCallback(() => {
    if (!clipJobId) return
    clipPolling.setError('Canceling clip generation is not available yet.')
  }, [clipJobId, clipPolling])

  const handleComposeClips = useCallback(async () => {
    if (!result?.songId || !clipSummary) {
      console.warn('[compose] Cannot compose: missing songId or clipSummary', {
        hasSongId: !!result?.songId,
        hasClipSummary: !!clipSummary,
      })
      return
    }
    if (clipSummary.completedClips !== clipSummary.totalClips) {
      console.warn('[compose] Cannot compose: not all clips completed', {
        completed: clipSummary.completedClips,
        total: clipSummary.totalClips,
      })
      return
    }
    if (clipSummary.failedClips > 0 || isComposing) {
      console.warn('[compose] Cannot compose: failed clips or already composing', {
        failedClips: clipSummary.failedClips,
        isComposing,
      })
      return
    }

    try {
      setIsComposing(true)
      clipPolling.setError(null)
      // Reset the completion handler ref for the new job
      compositionCompleteHandledRef.current = null
      const { data } = await apiClient.post<ComposeVideoResponse>(
        `/songs/${result.songId}/clips/compose/async`,
      )
      setComposeJobId(data.jobId)
    } catch (err) {
      console.error('[compose] Failed to start composition:', err)
      clipPolling.setError(
        extractErrorMessage(err, 'Unable to compose clips at this time.'),
      )
      setIsComposing(false)
    }
  }, [result, clipSummary, isComposing, clipPolling])

  const handleGenerateClips = useCallback(async () => {
    if (!result?.songId) return

    // Check if character image is set
    const hasCharacterImage =
      songDetails?.character_consistency_enabled &&
      (songDetails.character_reference_image_s3_key ||
        songDetails.character_pose_b_s3_key)

    // If no character image, show confirmation dialog
    if (!hasCharacterImage && !hideCharacterConsistency) {
      setShowNoCharacterConfirm(true)
      return
    }

    try {
      clipPolling.setError(null)
      // Use selected duration if available, otherwise fall back to full duration
      const selectedDuration =
        songDetails?.selected_start_sec != null && songDetails?.selected_end_sec != null
          ? songDetails.selected_end_sec - songDetails.selected_start_sec
          : null
      const durationEstimate =
        selectedDuration ??
        analysisData?.durationSec ??
        songDetails?.duration_sec ??
        clipSummary?.songDurationSec ??
        clipSummary?.clips.reduce((total, clip) => total + clip.durationSec, 0) ??
        null

      const maxClipSeconds = 6
      const minClips = 3
      const maxClips = 64
      const computedClipCount =
        durationEstimate && durationEstimate > 0
          ? Math.min(
              maxClips,
              Math.max(minClips, Math.ceil(durationEstimate / maxClipSeconds)),
            )
          : minClips

      const needsReplan =
        !clipSummary ||
        clipSummary.totalClips === 0 ||
        clipSummary.completedClips === clipSummary.totalClips ||
        clipSummary.clips.some((clip) => clip.durationSec > maxClipSeconds + 0.1)

      if (needsReplan) {
        await apiClient.post(`/songs/${result.songId}/clips/plan`, null, {
          params: {
            clip_count: computedClipCount,
            max_clip_sec: maxClipSeconds,
          },
        })
        await clipPolling.fetchClipSummary(result.songId)
      }

      const { data } = await apiClient.post<{
        jobId: string
        songId: string
        status: string
      }>(`/songs/${result.songId}/clips/generate`)

      clipPolling.setJobId(data.jobId)
      clipPolling.setStatus(data.status === 'processing' ? 'processing' : 'queued')
    } catch (err) {
      console.error('[generate-clips] Error:', err)
      clipPolling.setError(
        extractErrorMessage(err, 'Unable to start clip generation for this track.'),
      )
    }
  }, [
    result,
    clipSummary,
    analysisData,
    songDetails,
    clipPolling,
    hideCharacterConsistency,
  ])

  const handlePreviewClip = useCallback(
    (clip: SongClipStatus) => {
      if (clip.videoUrl) {
        setPlayerClipSelectionLocked(true)
        setPlayerActiveClipId(clip.id)
        window.open(clip.videoUrl, '_blank', 'noopener,noreferrer')
      } else {
        clipPolling.setError('Preview not available for this clip yet.')
      }
    },
    [clipPolling],
  )

  const handleRegenerateClip = useCallback(
    (clip: SongClipStatus) => {
      console.info('Regenerate clip requested', clip.id)
      clipPolling.setError('Clip regeneration is not available yet.')
    },
    [clipPolling],
  )

  const handleRetryClip = useCallback(
    async (clip: SongClipStatus) => {
      if (!result?.songId) return
      try {
        clipPolling.setError(null)
        clipPolling.setStatus('queued')
        clipPolling.setJobId(null)
        await apiClient.post<SongClipStatus>(
          `/songs/${result.songId}/clips/${clip.id}/retry`,
        )
        await clipPolling.fetchClipSummary(result.songId)
      } catch (err) {
        clipPolling.setError(extractErrorMessage(err, 'Unable to retry clip generation.'))
      }
    },
    [result, clipPolling],
  )

  const handlePlayerClipSelect = useCallback(
    (clipId: string | null) => {
      if (!clipId) {
        setPlayerActiveClipId(null)
        return
      }
      const targetClip = clipSummary?.clips?.find((clip) => clip.id === clipId)
      if (!targetClip) {
        return
      }
      if (!clipSummary?.composedVideoUrl && !targetClip.videoUrl) {
        clipPolling.setError((prev) => prev ?? 'Clip video is still generating.')
        return
      }
      setPlayerClipSelectionLocked(true)
      setPlayerActiveClipId(clipId)
    },
    [clipSummary?.clips, clipSummary?.composedVideoUrl, clipPolling],
  )

  const highlightTimeoutRef = useRef<number | null>(null)
  const summaryMoodKind = useMemo<MoodKind>(
    () => mapMoodToMoodKind(analysisData?.moodPrimary ?? ''),
    [analysisData?.moodPrimary],
  )
  const lyricsBySection = useMemo(() => {
    if (!analysisData?.sectionLyrics || !analysisData.sectionLyrics.length) {
      return new Map<string, string>()
    }
    return new Map(analysisData.sectionLyrics.map((item) => [item.sectionId, item.text]))
  }, [analysisData])

  useEffect(
    () => () => {
      if (highlightTimeoutRef.current) {
        window.clearTimeout(highlightTimeoutRef.current)
        highlightTimeoutRef.current = null
      }
    },
    [],
  )

  const requirementsCopy = useMemo(
    () => ({
      formats: 'MP3, WAV, M4A, FLAC, OGG',
      duration: 'Up to 7 minutes',
      size: 'Up to 100 MB',
    }),
    [],
  )

  const resetState = useCallback(() => {
    // Cancel any ongoing upload
    if (uploadAbortControllerRef.current) {
      uploadAbortControllerRef.current.abort()
      uploadAbortControllerRef.current = null
    }
    setStage('idle')
    setError(null)
    setProgress(0)
    setMetadata(null)
    setResult(null) // This will cause hooks to reset when songId becomes null
    setSongDetails(null)
    setIsComposing(false)
    setComposeJobId(null)
    setPlayerActiveClipId(null)
    setPlayerClipSelectionLocked(false)
    setVideoTypeSelectorVisible(true)
    autoScrollCompletedRef.current = false // Reset scroll flag for new upload

    // Clear persisted state
    localStorage.removeItem('vibecraft_current_song_id')

    videoTypeSelection.reset()
    audioSelection.reset()
    // NOTE: Sections are NOT implemented in the backend right now - cleanup code commented out
    // if (highlightTimeoutRef.current) {
    //   window.clearTimeout(highlightTimeoutRef.current)
    //   highlightTimeoutRef.current = null
    // }
    // setHighlightedSectionId(null)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }, [videoTypeSelection, audioSelection])

  const fetchSongDetails = useCallback(async (songId: string) => {
    try {
      const { data } = await apiClient.get<SongRead>(`/songs/${songId}`)
      setSongDetails(data)
    } catch (err) {
      console.error('Failed to load song details', err)
    }
  }, [])

  // Show profile hint on every page load (reset on refresh)
  useEffect(() => {
    // Always show the hint on mount - use setTimeout to avoid setState in effect
    const timer = setTimeout(() => {
      setShowProfileHint(true)
    }, 0)
    return () => clearTimeout(timer)
  }, [])

  // Animation will show on every page load/refresh

  // Persist songId to localStorage when it changes
  useEffect(() => {
    if (result?.songId) {
      localStorage.setItem('vibecraft_current_song_id', result.songId)
    } else {
      localStorage.removeItem('vibecraft_current_song_id')
    }
  }, [result?.songId])

  // Load song from URL parameter or localStorage on mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const songIdParam =
      urlParams.get('songId') || localStorage.getItem('vibecraft_current_song_id')

    if (songIdParam && !result) {
      const loadSongById = async () => {
        try {
          setStage('uploaded')
          setResult({ songId: songIdParam } as SongUploadResponse)

          await fetchSongDetails(songIdParam)
          // Use fetchAnalysis from the hook
          await analysisPolling.fetchAnalysis(songIdParam)

          const { data: clipData } = await apiClient.get<ClipGenerationSummary>(
            `/songs/${songIdParam}/clips/status`,
          )
          await clipPolling.fetchClipSummary(songIdParam)

          // Try to restore the active clip generation batch job using new endpoint
          try {
            const { data: activeJob } = await apiClient.get<{
              jobId: string
              songId: string
              status: string
            } | null>(`/songs/${songIdParam}/clips/job`)
            if (activeJob?.jobId) {
              clipPolling.setJobId(activeJob.jobId)
              clipPolling.setStatus(
                activeJob.status === 'processing' ? 'processing' : 'queued',
              )
            } else if (
              clipData.completedClips === clipData.totalClips &&
              clipData.totalClips > 0
            ) {
              clipPolling.setStatus('completed')
            }
          } catch {
            // Fallback to old method if new endpoint fails
            if (clipData.clips && clipData.clips.length > 0) {
              const hasActiveJob = clipData.clips.some(
                (clip) => clip.status === 'processing' || clip.status === 'queued',
              )
              if (hasActiveJob) {
                const firstClipWithJob = clipData.clips.find((clip) => clip.rqJobId)
                if (firstClipWithJob?.rqJobId) {
                  clipPolling.setJobId(firstClipWithJob.rqJobId)
                  clipPolling.setStatus('processing')
                }
              } else if (
                clipData.completedClips === clipData.totalClips &&
                clipData.totalClips > 0
              ) {
                clipPolling.setStatus('completed')
              }
            }
          }
        } catch (err) {
          const errorMsg = extractErrorMessage(err, 'Unable to load song.')
          setError(errorMsg)
          setStage('error')
        }
      }

      void loadSongById()
    }
  }, [result, fetchSongDetails, analysisPolling, clipPolling])

  useEffect(() => {
    if (!analysisData && clipSummary?.analysis && result?.songId) {
      // Fetch analysis if we have it in clip summary but not in analysis data
      void analysisPolling.fetchAnalysis(result.songId)
    }
  }, [clipSummary?.analysis, analysisData, result?.songId, analysisPolling])

  // Fetch song details when analysis completes to ensure we have latest data including video_type
  useEffect(() => {
    if (analysisState === 'completed' && result?.songId) {
      // Always refresh songDetails when analysis completes to get latest video_type
      setTimeout(() => {
        void fetchSongDetails(result.songId)
      }, 0)
    }
  }, [analysisState, result?.songId, fetchSongDetails])

  // Scroll to top when transitioning from analysis to character selection
  // Only for short-form videos, only once, only if character image hasn't been chosen
  useEffect(() => {
    // Only scroll for short-form videos
    if (videoType !== 'short_form') {
      return
    }

    // Only scroll once
    if (autoScrollCompletedRef.current) {
      return
    }

    // Only scroll when analysis completes and we have the data
    if (analysisState !== 'completed' || !analysisData || !songDetails) {
      return
    }

    // Only scroll if character image hasn't been chosen yet
    const hasCharacterImage =
      songDetails.character_reference_image_s3_key || songDetails.character_pose_b_s3_key

    if (hasCharacterImage) {
      return
    }

    // Mark as completed before scrolling to prevent double-trigger
    autoScrollCompletedRef.current = true

    // Small delay to ensure the character selection UI has rendered
    const timer = setTimeout(() => {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }, 100)

    return () => clearTimeout(timer)
  }, [analysisState, analysisData, songDetails, videoType])

  // Handler for selection changes - just updates local state, doesn't save yet
  const handleSelectionChange = useCallback(
    (startSec: number, endSec: number) => {
      // Only update local state, don't save to backend until user confirms
      audioSelection.setAudioSelection({ startSec, endSec })
    },
    [audioSelection],
  )

  // Parse waveform data
  const waveformValues = useMemo(() => {
    if (!songDetails?.waveform_json) return []
    try {
      const parsed = JSON.parse(songDetails.waveform_json)
      return Array.isArray(parsed) ? parsed : []
    } catch {
      return []
    }
  }, [songDetails?.waveform_json])

  useEffect(() => {
    if (!clipSummary?.composedVideoUrl) {
      return
    }

    setTimeout(() => {
      setPlayerClipSelectionLocked((locked) => (locked ? false : locked))
      setPlayerActiveClipId((current) => (current !== null ? null : current))
    }, 0)
  }, [clipSummary?.composedVideoUrl])

  useEffect(() => {
    const completedClipEntries =
      clipSummary?.clips?.filter(
        (clip) => normalizeClipStatus(clip.status) === 'completed' && !!clip.videoUrl,
      ) ?? []

    if (!completedClipEntries.length) {
      setTimeout(() => {
        setPlayerActiveClipId(null)
        setPlayerClipSelectionLocked(false)
      }, 0)
      return
    }

    setTimeout(() => {
      setPlayerActiveClipId((current) => {
        if (
          playerClipSelectionLocked &&
          current &&
          completedClipEntries.some((clip) => clip.id === current)
        ) {
          return current
        }
        const latest = completedClipEntries[completedClipEntries.length - 1]
        return latest?.id ?? null
      })
    }, 0)
  }, [clipSummary, playerClipSelectionLocked])

  const handleSectionSelect = useCallback((sectionId: string) => {
    if (!sectionId) return
    if (highlightTimeoutRef.current) {
      window.clearTimeout(highlightTimeoutRef.current)
      highlightTimeoutRef.current = null
    }
    setHighlightedSectionId(sectionId)

    const element = document.getElementById(`section-${sectionId}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' })
    }

    highlightTimeoutRef.current = window.setTimeout(() => {
      setHighlightedSectionId(null)
      highlightTimeoutRef.current = null
    }, 2000)
  }, [])

  const handleFileUpload = useCallback(
    async (file: File) => {
      // Check if user is authenticated
      if (!isAuthenticated) {
        setLoginPromptModalOpen(true)
        return
      }

      resetState()

      if (
        !ACCEPTED_MIME_TYPES.includes(file.type as (typeof ACCEPTED_MIME_TYPES)[number])
      ) {
        setStage('error')
        setError('Unsupported audio format. Try MP3, WAV, M4A, FLAC, or OGG.')
        return
      }

      // Check file size before uploading
      if (file.size > MAX_AUDIO_FILE_SIZE_BYTES) {
        const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1)
        setStage('error')
        setError(
          `Audio file size (${fileSizeMB}MB) exceeds maximum (${MAX_AUDIO_FILE_SIZE_MB}MB).`,
        )
        return
      }

      setStage('uploading')
      setMetadata({
        fileName: file.name,
        fileSize: file.size,
        durationSeconds: null,
      })

      const [durationSeconds] = await Promise.all([
        computeDuration(file).catch(() => null),
        new Promise((resolve) => setTimeout(resolve, 200)),
      ])

      if (durationSeconds && durationSeconds > MAX_DURATION_SECONDS) {
        setStage('error')
        setError('This track is longer than 7 minutes. Please trim it and try again.')
        return
      }

      setMetadata({
        fileName: file.name,
        fileSize: file.size,
        durationSeconds: durationSeconds ?? null,
      })

      const formData = new FormData()
      formData.append('file', file)

      // Create AbortController for this upload
      const abortController = new AbortController()
      uploadAbortControllerRef.current = abortController

      try {
        const response = await apiClient.post<SongUploadResponse>('/songs/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          signal: abortController.signal,
          timeout: 120000, // 2 minute timeout for large files
          onUploadProgress: (event) => {
            if (!event.total) return
            const percentage = Math.min(
              100,
              Math.round((event.loaded / event.total) * 100),
            )
            setProgress(percentage)
          },
        })

        // Clear abort controller on success
        uploadAbortControllerRef.current = null

        setResult(response.data)
        setProgress(100)
        setStage('uploaded')
        // Don't start analysis automatically - wait for user to select video type first
        await fetchSongDetails(response.data.songId)
        // Initialize clip summary (will be empty for new songs)
        await clipPolling.fetchClipSummary(response.data.songId)
      } catch (err) {
        // Clear abort controller on error
        uploadAbortControllerRef.current = null

        // Check if upload was cancelled
        if (
          axios.isCancel(err) ||
          (err as { name?: string })?.name === 'AbortError' ||
          (err as { code?: string })?.code === 'ERR_CANCELED'
        ) {
          console.log('Upload cancelled by user')
          setStage('idle')
          setProgress(0)
          setError(null)
          return
        }

        console.error('Upload failed', err)
        const axiosError = err as {
          response?: { data?: { detail?: string } }
          message?: string
          code?: string
        }
        let message =
          axiosError.response?.data?.detail ??
          axiosError.message ??
          'Upload failed. Please try again.'

        // Handle timeout errors
        if (axiosError.code === 'ECONNABORTED' || message.includes('timeout')) {
          message =
            'Upload timed out. The file may be too large or the connection is slow. Please try again.'
        }

        setError(message)
        setStage('error')
        setProgress(0)
      }
    },
    [isAuthenticated, resetState, fetchSongDetails, clipPolling],
  )

  const handleFilesSelected = useCallback(
    async (files: FileList | null) => {
      if (!files || !files.length) return
      const [file] = files
      await handleFileUpload(file)
    },
    [handleFileUpload],
  )

  const onDrop = useCallback(
    async (event: React.DragEvent<HTMLElement>) => {
      event.preventDefault()
      event.stopPropagation()
      setStage((current) => (current === 'dragging' ? 'idle' : current))
      const files = event.dataTransfer?.files
      if (files?.length) {
        await handleFilesSelected(files)
      }
    },
    [handleFilesSelected],
  )

  const onDragOver = useCallback(
    (event: React.DragEvent<HTMLElement>) => {
      event.preventDefault()
      event.stopPropagation()
      event.dataTransfer.dropEffect = 'copy'
      if (stage !== 'uploading') {
        setStage('dragging')
      }
    },
    [stage],
  )

  const onDragLeave = useCallback(
    (event: React.DragEvent<HTMLElement>) => {
      event.preventDefault()
      event.stopPropagation()
      if (stage === 'dragging') {
        setStage('idle')
      }
    },
    [stage],
  )

  const renderErrorCard = () => (
    <div className="rounded-3xl border border-vc-state-error/40 bg-[rgba(38,12,18,0.85)] p-7 shadow-vc2">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <ErrorIcon className="h-6 w-6 text-vc-state-error" />
          <h3 className="text-lg font-semibold text-white">Upload failed</h3>
        </div>
        <p className="text-sm text-vc-text-secondary">{error}</p>
        <div className="flex gap-2">
          <VCButton variant="ghost" onClick={resetState}>
            Try again
          </VCButton>
        </div>
      </div>
    </div>
  )

  // Determine if video type selector should be shown
  const showVideoTypeSelector =
    stage === 'uploaded' &&
    !analysisPolling.data &&
    analysisState === 'idle' &&
    !videoType

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-gradient-to-b from-[#0C0C12] via-[#121224] to-[#0B0B16] px-4 py-16 text-white">
      <BackgroundOrbs />

      {/* Profile Button - Top Right */}
      <div className="fixed top-6 right-6 z-50">
        {/* Pointing Animation - One Time */}
        {showProfileHint && (
          <div
            className="absolute -left-12 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{
              animation: 'pointAndFade 3s ease-in-out forwards',
            }}
          >
            <div className="text-3xl filter drop-shadow-lg">👉</div>
          </div>
        )}

        <button
          onClick={() => {
            if (isAuthenticated) {
              setProjectsModalOpen(true)
            } else {
              setAuthModalOpen(true)
            }
            setShowProfileHint(false)
          }}
          className="relative flex h-16 w-16 items-center justify-center rounded-full bg-vc-accent-primary shadow-vc2 hover:shadow-vc3 hover:bg-[#7A76FF] transition-all active:scale-[0.98] overflow-hidden disabled:opacity-50 disabled:cursor-not-allowed"
          aria-label={isAuthenticated ? 'Open projects' : 'Login'}
          disabled={isAuthLoading}
        >
          <img
            src="/img/vibe_lightning_simple.png"
            alt="Profile"
            className="w-full h-full object-cover"
          />
        </button>
      </div>

      {analysisState !== 'completed' && (
        <div className="relative z-10 mx-auto flex w-full max-w-3xl flex-col items-center gap-4 text-center">
          <div className="space-y-3">
            {/* <div className="mx-auto w-fit rounded-full border border-vc-border/40 bg-[rgba(255,255,255,0.03)] px-4 py-1 text-xs uppercase tracking-[0.22em] text-vc-text-muted">
              Upload
            </div> */}
            <h1 className="font-display text-4xl md:text-5xl">
              Turn your sound into visuals.
            </h1>
            <p className="max-w-xl text-sm text-vc-text-secondary md:text-base">
              Drop your track below and VibeCraft will start listening for tempo, mood,
              and structure — setting the stage for a cinematic video.
            </p>
          </div>

          {/* Video Type Selection OR Audio Selection - shown between heading and upload card */}
          {/* For short-form: Replace video type selector with audio selection once selected */}
          {(() => {
            // Show audio selection when short_form is selected
            // IMPORTANT: Even if analysis already exists, we should show audio selection
            // Show the UI if short_form is selected, regardless of existing analysis or selection state
            // This allows users to make or change their selection even if analysis exists
            const shouldShowAudioSelection =
              stage === 'uploaded' &&
              videoType === 'short_form' &&
              // Show even if analysis is completed - user might want to re-select
              (analysisState === 'idle' ||
                analysisState === 'queued' ||
                analysisState === 'processing' ||
                analysisState === 'failed' ||
                analysisState === 'completed')

            // Don't reset selection here - let the user make their selection
            // The reset logic was causing the button to disappear immediately
            // Only reset if we're switching songs or starting fresh

            return shouldShowAudioSelection ? (
              // Audio Selection UI - replaces video type selector for short-form
              <div className="w-full">
                <div className="rounded-2xl border-2 border-vc-accent-primary/50 bg-gradient-to-br from-vc-accent-primary/10 via-vc-surface-primary to-vc-surface-primary p-4 shadow-xl">
                  <div className="mb-4">
                    <div className="vc-label">Select Audio Segment (Up to 30s)</div>
                    <p className="text-sm text-vc-text-secondary mt-1">
                      Choose up to 30 seconds from your track. Analysis will start after
                      you make your selection.
                    </p>
                  </div>
                  {(() => {
                    // Try to get audioUrl from result first, fallback to fetching from songDetails if needed
                    const audioUrl = result?.audioUrl
                    const duration =
                      metadata?.durationSeconds ?? songDetails?.duration_sec ?? null

                    // If no audioUrl but we have songId, we might need to fetch it
                    // For now, show a message if audioUrl is missing
                    if (!audioUrl) {
                      return (
                        <div className="rounded-lg border border-vc-border/40 bg-[rgba(255,255,255,0.03)] p-4 text-sm text-vc-text-secondary">
                          <p>Loading audio URL...</p>
                          <p className="text-xs mt-2 opacity-70">
                            If this persists, the audio file may not be accessible. Please
                            try uploading again.
                          </p>
                        </div>
                      )
                    }
                    if (!duration || duration === 0) {
                      return (
                        <div className="rounded-lg border border-vc-border/40 bg-[rgba(255,255,255,0.03)] p-4 text-sm text-vc-text-secondary">
                          <p>Loading audio duration...</p>
                          <p className="text-xs mt-2 opacity-70">
                            Calculating track length...
                          </p>
                        </div>
                      )
                    }
                    return (
                      <AudioSelectionTimeline
                        audioUrl={audioUrl}
                        waveform={waveformValues}
                        durationSec={duration}
                        beatTimes={[]} // No beatTimes yet - analysis hasn't run
                        onSelectionChange={handleSelectionChange}
                        onConfirm={
                          audioSelectionValue
                            ? async () => {
                                if (!result?.songId || !audioSelectionValue) return

                                try {
                                  // Save the selection to backend
                                  await audioSelection.saveSelection(
                                    audioSelectionValue.startSec,
                                    audioSelectionValue.endSec,
                                  )

                                  // Then start analysis
                                  const response = await apiClient.post<{
                                    jobId: string
                                    status: string
                                  }>(`/songs/${result.songId}/analyze`)
                                  if (response.data.jobId) {
                                    analysisPolling.setJobId?.(response.data.jobId)
                                  }
                                } catch (err) {
                                  console.error(
                                    'Failed to save selection or start analysis:',
                                    err,
                                  )
                                  setError(
                                    extractErrorMessage(
                                      err,
                                      'Failed to confirm selection or start analysis',
                                    ),
                                  )
                                }
                              }
                            : undefined
                        }
                        confirmButtonDisabled={
                          !audioSelectionValue ||
                          analysisState === 'queued' ||
                          analysisState === 'processing'
                        }
                        confirmButtonText="Confirm & Start Analysis"
                      />
                    )
                  })()}
                </div>
              </div>
            ) : // Debug: Show why audio selection isn't showing
            // <div className="w-full rounded-lg border border-vc-border/40 bg-[rgba(255,255,255,0.03)] p-4 text-xs">
            //   <p className="font-semibold text-vc-accent-primary mb-2">
            //     Debug: Audio selection not showing
            //   </p>
            //   <div className="space-y-1 text-vc-text-secondary">
            //     <p>Conditions check:</p>
            //     <ul className="list-disc list-inside ml-2 space-y-0.5">
            //       <li
            //         className={stage === 'uploaded' ? 'text-green-400' : 'text-red-400'}
            //       >
            //         stage === 'uploaded': {String(stage === 'uploaded')} (current:{' '}
            //         {stage})
            //       </li>
            //       <li
            //         className={
            //           videoType === 'short_form' ? 'text-green-400' : 'text-red-400'
            //         }
            //       >
            //         videoType === 'short_form': {String(videoType === 'short_form')}{' '}
            //         (current: {videoType ?? 'null'})
            //       </li>
            //       <li
            //         className={!audioSelectionValue ? 'text-green-400' : 'text-red-400'}
            //       >
            //         !audioSelectionValue: {String(!audioSelectionValue)} (current:{' '}
            //         {audioSelectionValue ? 'exists' : 'null'})
            //       </li>
            //       <li
            //         className={
            //           !hasExistingSelection ? 'text-green-400' : 'text-red-400'
            //         }
            //       >
            //         !hasExistingSelection: {String(!hasExistingSelection)} (selected:{' '}
            //         {songDetails?.selected_start_sec ?? 'null'}-
            //         {songDetails?.selected_end_sec ?? 'null'})
            //       </li>
            //       <li
            //         className={
            //           analysisState === 'idle' ||
            //           analysisState === 'queued' ||
            //           analysisState === 'processing' ||
            //           analysisState === 'failed' ||
            //           analysisState === 'completed'
            //             ? 'text-green-400'
            //             : 'text-red-400'
            //         }
            //       >
            //         analysisState allowed:{' '}
            //         {String(
            //           analysisState === 'idle' ||
            //             analysisState === 'queued' ||
            //             analysisState === 'processing' ||
            //             analysisState === 'failed' ||
            //             analysisState === 'completed',
            //         )}{' '}
            //         (current: {analysisState})
            //       </li>
            //     </ul>
            //     <p className="mt-2 text-vc-text-muted">
            //       Check browser console for detailed logs with prefix [AudioSelection]
            //     </p>
            //   </div>
            // </div>
            null
          })()}

          {/* Video Type Selection - shown when no video type selected or for full-length */}
          {(() => {
            const shouldShowVideoTypeSelector =
              showVideoTypeSelector ||
              (videoType && videoTypeSelectorVisible && videoType === 'full_length')

            return shouldShowVideoTypeSelector ? (
              <div
                className={clsx(
                  'w-full transition-opacity duration-500',
                  videoType &&
                    (analysisState === 'queued' || analysisState === 'processing') &&
                    !videoTypeSelectorVisible
                    ? 'opacity-0'
                    : 'opacity-100',
                )}
              >
                <div className="rounded-2xl border-2 border-vc-accent-primary/50 bg-gradient-to-br from-vc-accent-primary/10 via-vc-surface-primary to-vc-surface-primary p-4 shadow-xl">
                  <VideoTypeSelector
                    onSelect={videoTypeSelection.setVideoType}
                    selectedType={videoType}
                  />
                </div>
              </div>
            ) : null
          })()}

          <input
            id={fileInputId}
            ref={inputRef}
            type="file"
            accept={ACCEPTED_MIME_TYPES.join(',')}
            className="hidden"
            onChange={(event) => handleFilesSelected(event.target.files)}
          />

          {(() => {
            const isInteractive = stage === 'idle' || stage === 'dragging'
            const Container: React.ElementType = isInteractive ? 'label' : 'div'
            return (
              <Container
                {...(isInteractive ? { htmlFor: fileInputId } : {})}
                className={clsx(
                  'group block w-full',
                  isInteractive ? 'cursor-pointer' : 'cursor-default',
                  stage === 'uploading' && 'pointer-events-none',
                )}
                onDragOver={onDragOver}
                onDragLeave={onDragLeave}
                onDrop={onDrop}
              >
                {stage === 'error' ? (
                  renderErrorCard()
                ) : (
                  <UploadCard
                    stage={stage}
                    metadata={metadata}
                    progress={progress}
                    result={result}
                    analysisState={videoType ? analysisState : 'idle'}
                    analysisProgress={analysisProgress}
                    analysisError={analysisError}
                    analysisData={analysisData}
                    isFetchingAnalysis={isFetchingAnalysis}
                    summaryMoodKind={summaryMoodKind}
                    // NOTE: Sections are NOT implemented in the backend right now - commenting out section-related props
                    // lyricsBySection={lyricsBySection}
                    onFileSelect={() => inputRef.current?.click()}
                    onReset={resetState}
                    onGenerateClips={handleGenerateClips}
                  />
                )}
              </Container>
            )
          })()}

          <div className="flex flex-wrap items-center justify-center gap-0 text-xs text-vc-text-muted -mt-2">
            <RequirementPill
              icon={<WaveformIcon />}
              label={`Accepted: ${requirementsCopy.formats}`}
            />
            <RequirementPill icon={<TimerIcon />} label={requirementsCopy.duration} />
            <RequirementPill icon={<HardDriveIcon />} label={requirementsCopy.size} />
          </div>
        </div>
      )}

      {/* Removed: "Start Analysis" button moved inside AudioSelectionTimeline component */}
      {/* For short_form videos, the button is now part of the timeline */}
      {/* For full_length videos, analysis starts automatically after video type selection */}

      {analysisState === 'completed' && analysisData && songDetails && (
        <div className="vc-app-main mx-auto w-full max-w-6xl px-4 py-12">
          {/* Fallback: If videoType is not set, show a message */}
          {!videoType && (
            <div className="mb-8 rounded-3xl border border-vc-border/40 bg-[rgba(255,255,255,0.03)] p-7">
              <div className="text-center space-y-4">
                <h3 className="text-lg font-semibold text-white">Video type not set</h3>
                <p className="text-sm text-vc-text-secondary">
                  This song was analyzed before video type selection was implemented.
                  Please upload a new song to select a video type.
                </p>
              </div>
            </div>
          )}
          {/* Character Image Upload Step - only for short-form videos */}
          {videoType === 'short_form' && result?.songId && !hideCharacterConsistency && (
            <section className="mb-2 space-y-4 -mt-8">
              <div className="vc-label text-center">Character Consistency (Optional)</div>
              {songDetails?.character_consistency_enabled &&
              (songDetails.character_reference_image_s3_key ||
                songDetails.character_pose_b_s3_key) ? (
                // Show selected template poses
                <>
                  {/* Debug overlay - uncomment for UI testing */}
                  {/* {process.env.NODE_ENV === 'development' && (
                    <div className="mb-2 rounded-lg border border-blue-500/30 bg-blue-500/10 p-2 text-xs text-blue-400">
                      <div>
                        character_consistency_enabled:{' '}
                        {String(songDetails.character_consistency_enabled)}
                      </div>
                      <div>
                        character_reference_image_s3_key:{' '}
                        {songDetails.character_reference_image_s3_key || 'null'}
                      </div>
                      <div>
                        character_pose_b_s3_key:{' '}
                        {songDetails.character_pose_b_s3_key || 'null'}
                      </div>
                    </div>
                  )} */}
                  <SelectedTemplateDisplay songId={result.songId} />
                </>
              ) : (
                // Show upload/template selection UI
                <>
                  <p className="text-sm text-vc-text-secondary text-center">
                    Upload a character reference image to maintain consistent character
                    appearance across all clips.
                  </p>
                  <CharacterImageUpload
                    songId={result.songId}
                    onUploadSuccess={(imageUrl) => {
                      console.log('Character image uploaded:', imageUrl)
                      // Optionally refresh song details to show character consistency is enabled
                      if (result?.songId) {
                        apiClient
                          .get(`/songs/${result.songId}`)
                          .then((response) => {
                            setSongDetails(response.data)
                          })
                          .catch(console.error)
                      }
                    }}
                    onUploadError={(error) => {
                      console.error('Character image upload failed:', error)
                      setError(error)
                    }}
                    onTemplateSelect={() => setTemplateModalOpen(true)}
                  />
                  <TemplateCharacterModal
                    isOpen={templateModalOpen}
                    onClose={() => setTemplateModalOpen(false)}
                    onSelect={async () => {
                      // Refresh song details to show character consistency is enabled
                      // Note: characterId parameter is provided by TemplateCharacterModal but not used here
                      if (result?.songId) {
                        try {
                          const response = await apiClient.get(`/songs/${result.songId}`)
                          setSongDetails(response.data)
                        } catch (err) {
                          console.error(
                            '[UploadPage] Failed to refresh song details:',
                            err,
                          )
                        }
                      }
                    }}
                    songId={result.songId}
                  />
                </>
              )}
            </section>
          )}

          {/* Audio Selection Step - only shown if analysis completed but selection not made yet (fallback) */}
          {videoType === 'short_form' &&
            !audioSelectionValue &&
            analysisState === 'completed' &&
            analysisData &&
            songDetails && (
              <section className="mb-8 space-y-4">
                <div className="vc-label">Select Audio Segment (Up to 30s)</div>
                <p className="text-sm text-vc-text-secondary">
                  Choose up to 30 seconds from your track to generate video clips.
                </p>
                {result?.audioUrl && songDetails.duration_sec && (
                  <AudioSelectionTimeline
                    audioUrl={result.audioUrl}
                    waveform={waveformValues}
                    durationSec={songDetails.duration_sec}
                    beatTimes={analysisData.beatTimes}
                    onSelectionChange={handleSelectionChange}
                  />
                )}
                {audioSelectionValue && (
                  <div className="flex justify-end">
                    <VCButton
                      onClick={() => {
                        // Selection is saved automatically, proceed
                        audioSelection.setAudioSelection(audioSelectionValue)
                      }}
                      disabled={isSavingSelection}
                    >
                      {isSavingSelection ? 'Saving...' : 'Continue with Selection'}
                    </VCButton>
                  </div>
                )}
              </section>
            )}

          {/* Song Profile View - shown after selection is made (for short-form) or directly (for full-length) */}
          {(videoType === 'full_length' ||
            (videoType === 'short_form' && audioSelectionValue)) &&
            analysisData &&
            songDetails && (
              <SongProfileView
                analysisData={analysisData}
                songDetails={songDetails}
                clipSummary={clipSummary}
                clipJobId={clipJobId}
                clipJobStatus={clipJobStatus}
                clipJobProgress={clipJobProgress}
                clipJobError={clipJobError}
                isComposing={isComposing}
                composeJobProgress={composeJobProgress}
                playerActiveClipId={playerActiveClipId}
                highlightedSectionId={highlightedSectionId}
                metadata={metadata}
                lyricsBySection={lyricsBySection}
                audioUrl={result?.audioUrl ?? null}
                onGenerateClips={handleGenerateClips}
                onCancelClipJob={handleCancelClipJob}
                onCompose={handleComposeClips}
                onPreviewClip={handlePreviewClip}
                onRegenerateClip={handleRegenerateClip}
                onRetryClip={handleRetryClip}
                onPlayerClipSelect={handlePlayerClipSelect}
                onSectionSelect={handleSectionSelect}
              />
            )}
        </div>
      )}
      {/* Confirmation dialog for generating clips without character image */}
      {showNoCharacterConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="relative w-full max-w-md rounded-2xl bg-[rgba(20,20,32,0.95)] backdrop-blur-xl border border-vc-border/50 shadow-2xl p-6">
            <h2 className="text-xl font-bold text-white mb-4">
              Generate Clips Without Character Reference?
            </h2>
            <p className="text-sm text-vc-text-secondary mb-6">
              You haven't selected a character image or template. We'll generate clips
              without a character reference, which means characters may vary between
              clips. This is fine and will still produce a video.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowNoCharacterConfirm(false)}
                className="px-4 py-2 bg-vc-border/30 text-vc-text-secondary rounded-lg hover:bg-vc-border/50 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={async () => {
                  setShowNoCharacterConfirm(false)
                  setHideCharacterConsistency(true)
                  // Now proceed with clip generation
                  if (!result?.songId) return
                  try {
                    console.log(
                      '[generate-clips] Starting clip generation for song:',
                      result.songId,
                    )
                    clipPolling.setError(null)
                    // Use selected duration if available, otherwise fall back to full duration
                    const selectedDuration =
                      songDetails?.selected_start_sec != null &&
                      songDetails?.selected_end_sec != null
                        ? songDetails.selected_end_sec - songDetails.selected_start_sec
                        : null
                    const durationEstimate =
                      selectedDuration ??
                      analysisData?.durationSec ??
                      songDetails?.duration_sec ??
                      clipSummary?.songDurationSec ??
                      clipSummary?.clips.reduce(
                        (total, clip) => total + clip.durationSec,
                        0,
                      ) ??
                      null

                    const maxClipSeconds = 6
                    const minClips = 3
                    const maxClips = 64
                    const computedClipCount =
                      durationEstimate && durationEstimate > 0
                        ? Math.min(
                            maxClips,
                            Math.max(
                              minClips,
                              Math.ceil(durationEstimate / maxClipSeconds),
                            ),
                          )
                        : minClips

                    const needsReplan =
                      !clipSummary ||
                      clipSummary.totalClips === 0 ||
                      clipSummary.completedClips === clipSummary.totalClips ||
                      clipSummary.clips.some(
                        (clip) => clip.durationSec > maxClipSeconds + 0.1,
                      )

                    if (needsReplan) {
                      await apiClient.post(`/songs/${result.songId}/clips/plan`, null, {
                        params: {
                          clip_count: computedClipCount,
                          max_clip_sec: maxClipSeconds,
                        },
                      })
                      await clipPolling.fetchClipSummary(result.songId)
                    }

                    const { data } = await apiClient.post<{
                      jobId: string
                      songId: string
                      status: string
                    }>(`/songs/${result.songId}/clips/generate`)

                    clipPolling.setJobId(data.jobId)
                    clipPolling.setStatus(
                      data.status === 'processing' ? 'processing' : 'queued',
                    )
                  } catch (err) {
                    console.error('[generate-clips] Error:', err)
                    clipPolling.setError(
                      extractErrorMessage(
                        err,
                        'Unable to start clip generation for this track.',
                      ),
                    )
                  }
                }}
                className="px-4 py-2 bg-vc-accent-primary text-white rounded-lg hover:bg-vc-accent-primary/90 transition-colors"
              >
                OK, Generate Clips
              </button>
            </div>
          </div>
        </div>
      )}
      {analysisState === 'completed' && (!analysisData || !songDetails) && (
        <div className="relative z-10 mx-auto flex w-full max-w-3xl flex-col items-center gap-10 text-center">
          <div className="rounded-3xl border border-vc-state-error/40 bg-[rgba(38,12,18,0.85)] p-7 shadow-vc2">
            <div className="flex flex-col gap-4">
              <h3 className="text-lg font-semibold text-white">
                Loading song details...
              </h3>
              <p className="text-sm text-vc-text-secondary">
                Analysis complete but missing data. State: analysisData=
                {String(!!analysisData)}, songDetails={String(!!songDetails)}
              </p>
            </div>
          </div>
        </div>
      )}

      <ProjectsModal
        isOpen={projectsModalOpen}
        onClose={() => setProjectsModalOpen(false)}
        onOpenProject={(songId) => {
          // Load the project by setting the songId in URL
          window.history.pushState({}, '', `/?songId=${songId}`)
          // Trigger a reload of the song details
          if (songId) {
            fetchSongDetails(songId)
            setResult({ songId } as SongUploadResponse)
          }
        }}
        onOpenAuth={() => setAuthModalOpen(true)}
      />

      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={() => {
          // After successful login/register, close the modal
          // The auth state will update automatically via React Query
          setAuthModalOpen(false)
        }}
      />

      {/* Login Prompt Modal */}
      {loginPromptModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => {
            setLoginPromptModalOpen(false)
            // Re-animate the pointing hand after closing - reset to false first to force re-render
            setShowProfileHint(false)
            setTimeout(() => setShowProfileHint(true), 100)
          }}
        >
          <div
            className="relative w-full max-w-md rounded-2xl bg-[rgba(20,20,32,0.95)] backdrop-blur-xl border border-vc-border/50 shadow-2xl p-6"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => {
                setLoginPromptModalOpen(false)
                // Re-animate the pointing hand after closing
                setShowProfileHint(false)
                setTimeout(() => setShowProfileHint(true), 100)
              }}
              className="absolute top-4 right-4 text-vc-text-secondary hover:text-white transition-colors p-2 hover:bg-vc-border/30 rounded-lg"
              aria-label="Close"
            >
              <svg
                className="w-6 h-6"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>

            <div className="text-center">
              <h2 className="text-2xl font-bold text-white mb-4">Login Required</h2>
              <p className="text-white/70 mb-6">
                Please log in or sign up to upload and create videos.
              </p>
              <div className="flex gap-3 justify-center">
                <VCButton
                  onClick={() => {
                    setLoginPromptModalOpen(false)
                    setAuthModalOpen(true)
                  }}
                >
                  Login / Sign Up
                </VCButton>
                <VCButton
                  variant="secondary"
                  onClick={() => {
                    setLoginPromptModalOpen(false)
                    // Re-animate the pointing hand after closing
                    setShowProfileHint(false)
                    setTimeout(() => setShowProfileHint(true), 100)
                  }}
                >
                  Cancel
                </VCButton>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
