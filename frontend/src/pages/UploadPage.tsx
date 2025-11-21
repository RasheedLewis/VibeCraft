import React, { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import clsx from 'clsx'
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
import { ACCEPTED_MIME_TYPES, MAX_DURATION_SECONDS } from '../constants/upload'

// Utilities
import { extractErrorMessage } from '../utils/validation'
import { mapMoodToMoodKind } from '../utils/sections'
import { computeDuration } from '../utils/audio'
import { normalizeClipStatus } from '../utils/status'

// Hooks
import { useAnalysisPolling } from '../hooks/useAnalysisPolling'
import { useClipPolling } from '../hooks/useClipPolling'
import { useCompositionPolling } from '../hooks/useCompositionPolling'

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
import { SongProfileView } from '../components/song/SongProfileView'

type UploadStage = 'idle' | 'dragging' | 'uploading' | 'uploaded' | 'error'

interface UploadMetadata {
  fileName: string
  fileSize: number
  durationSeconds: number | null
}

export const UploadPage: React.FC = () => {
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

  // Use polling hooks with bugfixes
  const analysisPolling = useAnalysisPolling(result?.songId ?? null)
  const clipPolling = useClipPolling(result?.songId ?? null)

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
      console.log('[compose] Starting composition for song:', result.songId)
      setIsComposing(true)
      clipPolling.setError(null)
      // Reset the completion handler ref for the new job
      compositionCompleteHandledRef.current = null
      const { data } = await apiClient.post<ComposeVideoResponse>(
        `/songs/${result.songId}/clips/compose/async`,
      )
      console.log('[compose] Composition job started:', data.jobId)
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
    try {
      console.log('[generate-clips] Starting clip generation for song:', result.songId)
      clipPolling.setError(null)
      const durationEstimate =
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

      console.log('[generate-clips] Planning check:', {
        needsReplan,
        hasSummary: !!clipSummary,
        totalClips: clipSummary?.totalClips ?? null,
        completedClips: clipSummary?.completedClips ?? null,
        computedClipCount,
        note: clipSummary
          ? 'Using existing clip summary'
          : 'No clip summary yet (new song or not fetched)',
      })

      if (needsReplan) {
        console.log('[generate-clips] Planning clips...')
        await apiClient.post(`/songs/${result.songId}/clips/plan`, null, {
          params: {
            clip_count: computedClipCount,
            max_clip_sec: maxClipSeconds,
          },
        })
        console.log('[generate-clips] Clips planned, fetching updated summary...')
        await clipPolling.fetchClipSummary(result.songId)
      }

      console.log('[generate-clips] Starting clip generation job...')
      const { data } = await apiClient.post<{
        jobId: string
        songId: string
        status: string
      }>(`/songs/${result.songId}/clips/generate`)

      console.log('[generate-clips] Job started:', data.jobId, 'status:', data.status)
      clipPolling.setJobId(data.jobId)
      clipPolling.setStatus(data.status === 'processing' ? 'processing' : 'queued')
      console.log('[generate-clips] State updated, UI should show progress now')
    } catch (err) {
      console.error('[generate-clips] Error:', err)
      clipPolling.setError(
        extractErrorMessage(err, 'Unable to start clip generation for this track.'),
      )
    }
  }, [result, clipSummary, analysisData, songDetails, clipPolling])

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
      size: 'We recommend files under ~200 MB',
    }),
    [],
  )

  const resetState = useCallback(() => {
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
    // NOTE: Sections are NOT implemented in the backend right now - cleanup code commented out
    // if (highlightTimeoutRef.current) {
    //   window.clearTimeout(highlightTimeoutRef.current)
    //   highlightTimeoutRef.current = null
    // }
    // setHighlightedSectionId(null)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }, [])

  const fetchSongDetails = useCallback(async (songId: string) => {
    try {
      const { data } = await apiClient.get<SongRead>(`/songs/${songId}`)
      setSongDetails(data)
    } catch (err) {
      console.error('Failed to load song details', err)
    }
  }, [])

  // Load song from URL parameter if present
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const songIdParam = urlParams.get('songId')

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

  // Fetch song details when analysis completes (backup in case it wasn't fetched after upload)
  useEffect(() => {
    if (analysisState === 'completed' && result?.songId && !songDetails) {
      setTimeout(() => {
        void fetchSongDetails(result.songId)
      }, 0)
    }
  }, [analysisState, result?.songId, songDetails, fetchSongDetails])

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
      resetState()

      if (
        !ACCEPTED_MIME_TYPES.includes(file.type as (typeof ACCEPTED_MIME_TYPES)[number])
      ) {
        setStage('error')
        setError('Unsupported audio format. Try MP3, WAV, M4A, FLAC, or OGG.')
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

      try {
        const response = await apiClient.post<SongUploadResponse>('/songs/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
          onUploadProgress: (event) => {
            if (!event.total) return
            const percentage = Math.min(
              100,
              Math.round((event.loaded / event.total) * 100),
            )
            setProgress(percentage)
          },
        })

        setResult(response.data)
        setProgress(100)
        setStage('uploaded')
        await analysisPolling.startAnalysis(response.data.songId)
        await fetchSongDetails(response.data.songId)
        // Initialize clip summary (will be empty for new songs)
        await clipPolling.fetchClipSummary(response.data.songId)
      } catch (err) {
        console.error('Upload failed', err)
        const message =
          (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
          'Upload failed. Please try again.'
        setError(message)
        setStage('error')
      }
    },
    [resetState, analysisPolling, fetchSongDetails, clipPolling],
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

  return (
    <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-gradient-to-b from-[#0C0C12] via-[#121224] to-[#0B0B16] px-4 py-16 text-white">
      <BackgroundOrbs />

      {analysisState !== 'completed' && (
        <div className="relative z-10 mx-auto flex w-full max-w-3xl flex-col items-center gap-10 text-center">
          <div className="space-y-3">
            <div className="mx-auto w-fit rounded-full border border-vc-border/40 bg-[rgba(255,255,255,0.03)] px-4 py-1 text-xs uppercase tracking-[0.22em] text-vc-text-muted">
              Upload
            </div>
            <h1 className="font-display text-4xl md:text-5xl">
              Turn your sound into visuals.
            </h1>
            <p className="max-w-xl text-sm text-vc-text-secondary md:text-base">
              Drop your track below and VibeCraft will start listening for tempo, mood,
              and structure — setting the stage for a cinematic video.
            </p>
          </div>

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
                    analysisState={analysisState}
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

          <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-3 text-xs text-vc-text-muted">
            <RequirementPill
              icon={<WaveformIcon />}
              label={`Accepted: ${requirementsCopy.formats}`}
            />
            <RequirementPill icon={<TimerIcon />} label={requirementsCopy.duration} />
            <RequirementPill icon={<HardDriveIcon />} label={requirementsCopy.size} />
          </div>
        </div>
      )}

      {analysisState === 'completed' && analysisData && songDetails && (
        <div className="vc-app-main mx-auto w-full max-w-6xl px-4 py-12">
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
    </div>
  )
}
