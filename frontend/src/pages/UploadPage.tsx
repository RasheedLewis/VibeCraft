import React, { useCallback, useEffect, useId, useMemo, useRef, useState } from 'react'
import clsx from 'clsx'
import { apiClient } from '../lib/apiClient'
import { SectionCard, SectionMoodTag, VCCard, VCButton } from '../components/vibecraft'
import type { MoodKind } from '../components/vibecraft/SectionMoodTag'
import type {
  ClipGenerationSummary,
  JobStatusResponse,
  SongAnalysis,
  SongAnalysisJobResponse,
  SongClipStatus,
  SongRead,
  SongSection,
  MoodVector,
  SongUploadResponse,
} from '../types/song'

const ACCEPTED_MIME_TYPES = [
  'audio/mpeg',
  'audio/mp3',
  'audio/wav',
  'audio/wave',
  'audio/vnd.wave',
  'audio/x-wav',
  'audio/ogg',
  'audio/webm',
  'audio/flac',
  'audio/x-flac',
  'audio/aac',
  'audio/mp4',
  'audio/m4a',
  'audio/x-m4a',
] as const

const MAX_DURATION_SECONDS = 7 * 60

const SECTION_TYPE_LABELS: Record<string, string> = {
  intro: 'Intro',
  verse: 'Verse',
  pre_chorus: 'Pre-chorus',
  chorus: 'Chorus',
  bridge: 'Bridge',
  drop: 'Drop',
  solo: 'Solo',
  outro: 'Outro',
  other: 'Section',
}

const SECTION_COLORS: Record<string, string> = {
  intro: 'rgba(110, 107, 255, 0.32)',
  verse: 'rgba(130, 89, 255, 0.42)',
  pre_chorus: 'rgba(112, 84, 255, 0.48)',
  chorus: 'rgba(255, 111, 245, 0.55)',
  bridge: 'rgba(0, 198, 192, 0.45)',
  drop: 'rgba(255, 189, 89, 0.5)',
  solo: 'rgba(89, 255, 214, 0.4)',
  outro: 'rgba(90, 105, 255, 0.28)',
  other: 'rgba(120, 120, 180, 0.35)',
}

const WAVEFORM_BASE_PATTERN = [0.25, 0.6, 0.85, 0.4, 0.75, 0.35, 0.9, 0.5, 0.65, 0.3]
const WAVEFORM_BARS = Array.from({ length: 72 }, (_, index) => {
  const patternValue = WAVEFORM_BASE_PATTERN[index % WAVEFORM_BASE_PATTERN.length]
  const pulseBoost =
    ((index + 3) % 11 === 0 ? 0.15 : 0) + ((index + 7) % 17 === 0 ? 0.1 : 0)
  return Math.min(1, patternValue + pulseBoost)
})

const getFileTypeLabel = (fileName?: string | null) => {
  if (!fileName) return 'Audio'
  const parts = fileName.split('.')
  if (parts.length <= 1) return 'Audio'
  return parts.pop()?.toUpperCase() ?? 'Audio'
}

const formatBytes = (bytes: number) => {
  if (!Number.isFinite(bytes)) return '—'
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  )
  const value = bytes / Math.pow(1024, exponent)
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[exponent]}`
}

const formatSeconds = (seconds: number | null) => {
  if (!Number.isFinite(seconds) || seconds === null) return '—'
  const wholeSeconds = Math.round(seconds)
  const mins = Math.floor(wholeSeconds / 60)
  const secs = wholeSeconds % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value))

const mapMoodToMoodKind = (mood: string): MoodKind => {
  const normalized = mood?.toLowerCase() ?? ''
  if (normalized.includes('energy') || normalized.includes('energetic'))
    return 'energetic'
  if (
    normalized.includes('dark') ||
    normalized.includes('moody') ||
    normalized.includes('intense')
  )
    return 'dark'
  if (
    normalized.includes('uplift') ||
    normalized.includes('happy') ||
    normalized.includes('bright') ||
    normalized.includes('positive')
  )
    return 'uplifting'
  return 'chill'
}

const formatBpm = (bpm?: number) => {
  if (!bpm || Number.isNaN(bpm)) return '—'
  return `${Math.round(bpm)} BPM`
}

const isSongAnalysis = (payload: unknown): payload is SongAnalysis => {
  if (!payload || typeof payload !== 'object') return false
  const candidate = payload as Partial<SongAnalysis>
  return (
    typeof candidate.durationSec === 'number' &&
    Array.isArray(candidate.sections) &&
    Array.isArray(candidate.moodTags)
  )
}

const isClipGenerationSummary = (payload: unknown): payload is ClipGenerationSummary => {
  if (!payload || typeof payload !== 'object') return false
  const candidate = payload as Partial<ClipGenerationSummary>
  return (
    typeof candidate.songId === 'string' &&
    typeof candidate.totalClips === 'number' &&
    typeof candidate.progressCompleted === 'number' &&
    typeof candidate.progressTotal === 'number' &&
    Array.isArray(candidate.clips)
  )
}

const formatMoodTags = (tags: string[]) =>
  tags.length
    ? tags
        .map((tag) => tag.trim())
        .filter(Boolean)
        .join(', ')
    : '—'

const formatDurationShort = (seconds: number) => {
  if (!Number.isFinite(seconds)) return '—'
  if (seconds >= 10) return `${Math.round(seconds)}s`
  return `${seconds.toFixed(1)}s`
}

const formatTimeRange = (startSec: number, endSec: number) =>
  `${formatSeconds(startSec)}–${formatSeconds(endSec)}`

const getSectionTitle = (section: SongSection, index: number) => {
  const label = SECTION_TYPE_LABELS[section.type] ?? `Section`
  return `${label} ${index + 1}`
}

const formatProgressLabel = (status: string, progress: number) => {
  if (status === 'completed') return 'Analysis complete'
  if (status === 'failed') return 'Analysis failed'
  if (status === 'processing') return `Analyzing… ${Math.round(progress)}%`
  if (status === 'queued') return 'Queued for analysis'
  return 'Analyzing…'
}

const normalizeJobStatus = (
  status?: string,
): 'queued' | 'processing' | 'completed' | 'failed' => {
  const normalized = status?.toLowerCase()
  if (normalized === 'processing') return 'processing'
  if (normalized === 'completed') return 'completed'
  if (normalized === 'failed') return 'failed'
  return 'queued'
}

const normalizeClipStatus = (
  status?: string,
): 'queued' | 'processing' | 'completed' | 'failed' | 'canceled' => {
  const normalized = status?.toLowerCase()
  if (normalized === 'processing' || normalized === 'generating') return 'processing'
  if (normalized === 'completed' || normalized === 'done') return 'completed'
  if (normalized === 'failed' || normalized === 'error') return 'failed'
  if (normalized === 'canceled' || normalized === 'cancelled') return 'canceled'
  return 'queued'
}

const extractErrorMessage = (error: unknown, fallback: string): string => {
  if (typeof error === 'string') return error
  if (error && typeof error === 'object') {
    const maybeError = error as {
      message?: string
      response?: { data?: unknown }
    }
    const responseData = maybeError.response?.data
    if (typeof responseData === 'string') return responseData
    if (responseData && typeof responseData === 'object') {
      const detail = (responseData as Record<string, unknown>).detail
      if (typeof detail === 'string') return detail
      const message = (responseData as Record<string, unknown>).message
      if (typeof message === 'string') return message
    }
    if (maybeError.message) return maybeError.message
  }
  return fallback
}

const buildSectionsWithDisplayNames = (
  sections: SongSection[],
): Array<SongSection & { displayName: string }> => {
  const counts: Record<string, number> = {}
  return sections.map((section) => {
    const label = SECTION_TYPE_LABELS[section.type] ?? 'Section'
    const nextCount = (counts[section.type] ?? 0) + 1
    counts[section.type] = nextCount

    const displayName =
      section.type === 'intro' || section.type === 'outro' || section.type === 'bridge'
        ? label
        : `${label} ${nextCount}`

    return { ...section, displayName }
  })
}

const parseWaveformJson = (waveformJson?: string | null): number[] => {
  if (!waveformJson) return []
  try {
    const parsed = JSON.parse(waveformJson)
    if (Array.isArray(parsed)) {
      return parsed.map((value) => {
        const num = Number(value)
        if (Number.isNaN(num)) {
          return 0
        }
        return clamp(num, 0, 1)
      })
    }
    return []
  } catch {
    return []
  }
}

const SongTimeline: React.FC<{
  sections: Array<SongSection & { displayName: string }>
  duration: number
  onSelect?: (sectionId: string) => void
}> = ({ sections, duration, onSelect }) => {
  if (!sections.length || !Number.isFinite(duration) || duration <= 0) {
    return null
  }

  return (
    <div className="overflow-hidden rounded-full border border-vc-border/40 bg-[rgba(12,12,18,0.65)]">
      <div className="flex h-12">
        {sections.map((section) => {
          const length = Math.max(section.endSec - section.startSec, 0)
          const widthPercent = clamp((length / duration) * 100, 4, 100)
          return (
            <button
              key={section.id}
              type="button"
              onClick={() => onSelect?.(section.id)}
              className="group relative flex items-center justify-center border-r border-white/5 px-2 text-xs text-white transition-colors last:border-r-0 hover:opacity-90 focus:outline-none focus-visible:ring-2 focus-visible:ring-vc-accent-primary focus-visible:ring-offset-2 focus-visible:ring-offset-[rgba(12,12,18,0.85)]"
              style={{
                width: `${widthPercent}%`,
                backgroundColor: SECTION_COLORS[section.type] ?? 'rgba(100,100,150,0.35)',
              }}
            >
              <span className="pointer-events-none px-2 text-[11px] font-medium tracking-wide">
                {section.displayName}
              </span>
              <span className="pointer-events-none absolute bottom-1 text-[10px] uppercase tracking-[0.12em] text-white/70 opacity-0 transition-opacity group-hover:opacity-100">
                {formatSeconds(section.startSec)} – {formatSeconds(section.endSec)}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

const WaveformDisplay: React.FC<{
  waveform: number[]
  beatTimes?: number[]
  duration: number
}> = ({ waveform, beatTimes, duration }) => {
  if (!waveform.length) {
    return (
      <div className="flex h-16 items-center justify-center rounded-2xl border border-dashed border-vc-border/40 bg-[rgba(12,12,18,0.45)] text-xs text-vc-text-muted">
        Waveform preview unavailable
      </div>
    )
  }

  const bars = waveform.slice(0, 512)
  const hasBeats = Array.isArray(beatTimes) && beatTimes.length > 0 && duration > 0

  return (
    <div className="relative h-20 w-full overflow-hidden rounded-2xl border border-vc-border/40 bg-[rgba(12,12,18,0.55)]">
      <div className="absolute inset-0 bg-gradient-to-r from-[#6E6BFF33] via-[#FF6FF533] to-[#00C6C033]" />
      <div className="relative z-10 flex h-full items-center justify-between px-3">
        {bars.map((value, idx) => (
          <span
            key={`wave-bar-${idx}-${value}`}
            className="w-[2px] rounded-full bg-white/85 transition-all duration-300"
            style={{
              height: `${Math.max(16, value * 100)}%`,
              opacity: Math.max(0.25, value),
            }}
          />
        ))}
      </div>
      {hasBeats && (
        <div className="pointer-events-none absolute inset-0">
          {beatTimes!.slice(0, 400).map((time, idx) => {
            const position = clamp((time / duration) * 100, 0, 100)
            return (
              <span
                key={`beat-${idx}-${time}`}
                className="absolute top-0 bottom-0 w-px bg-white/45"
                style={{ left: `${position}%` }}
              />
            )
          })}
        </div>
      )}
    </div>
  )
}

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
  const inputRef = useRef<HTMLInputElement | null>(null)
  const [analysisState, setAnalysisState] = useState<
    'idle' | 'queued' | 'processing' | 'completed' | 'failed'
  >('idle')
  const [analysisJobId, setAnalysisJobId] = useState<string | null>(null)
  const [analysisProgress, setAnalysisProgress] = useState<number>(0)
  const [analysisData, setAnalysisData] = useState<SongAnalysis | null>(null)
  const [analysisError, setAnalysisError] = useState<string | null>(null)
  const [isFetchingAnalysis, setIsFetchingAnalysis] = useState<boolean>(false)
  const [songDetails, setSongDetails] = useState<SongRead | null>(null)
  const [highlightedSectionId, setHighlightedSectionId] = useState<string | null>(null)
  const [clipJobId, setClipJobId] = useState<string | null>(null)
  const [clipJobStatus, setClipJobStatus] = useState<
    'idle' | 'queued' | 'processing' | 'completed' | 'failed'
  >('idle')
  const [clipJobProgress, setClipJobProgress] = useState<number>(0)
  const [clipJobError, setClipJobError] = useState<string | null>(null)
  const [clipSummary, setClipSummary] = useState<ClipGenerationSummary | null>(null)
  const handleCancelClipJob = useCallback(() => {
    if (!clipJobId) return
    setClipJobError('Canceling clip generation is not available yet.')
  }, [clipJobId])

  const handleComposeClips = useCallback(() => {
    if (!clipSummary) return
    if (clipSummary.completedClips !== clipSummary.totalClips) return
    console.info('Compose action not yet implemented.')
  }, [clipSummary])

  const handleGenerateClips = useCallback(async () => {
    if (!result?.songId) return
    try {
      setClipJobError(null)
      setClipSummary(null)
      const durationEstimate =
        analysisData?.durationSec ??
        songDetails?.duration_sec ??
        clipSummary?.songDurationSec ??
        clipSummary?.clips.reduce((total, clip) => total + clip.durationSec, 0) ??
        null

      const maxClipSeconds = 15
      const minClips = 3
      const maxClips = 64
      const computedClipCount =
        durationEstimate && durationEstimate > 0
          ? Math.min(
              maxClips,
              Math.max(minClips, Math.ceil(durationEstimate / maxClipSeconds)),
            )
          : minClips

      if (
        !clipSummary ||
        clipSummary.totalClips === 0 ||
        clipSummary.completedClips === clipSummary.totalClips
      ) {
        await apiClient.post(`/songs/${result.songId}/clips/plan`, null, {
          params: {
            clip_count: computedClipCount,
            max_clip_sec: maxClipSeconds,
          },
        })
      }

      const { data } = await apiClient.post<{
        jobId: string
        songId: string
        status: string
      }>(`/songs/${result.songId}/clips/generate`)

      setClipJobId(data.jobId)
      setClipJobStatus(normalizeJobStatus(data.status))
      setClipJobProgress(0)
    } catch (err) {
      setClipJobError(
        extractErrorMessage(err, 'Unable to start clip generation for this track.'),
      )
    }
  }, [result?.songId, clipSummary, analysisData?.durationSec, songDetails?.duration_sec])

  const handlePreviewClip = useCallback(
    (clip: SongClipStatus) => {
      if (clip.videoUrl) {
        window.open(clip.videoUrl, '_blank', 'noopener,noreferrer')
      } else {
        setClipJobError('Preview not available for this clip yet.')
      }
    },
    [setClipJobError],
  )

  const handleRegenerateClip = useCallback(
    (clip: SongClipStatus) => {
      console.info('Regenerate clip requested', clip.id)
      setClipJobError('Clip regeneration is not available yet.')
    },
    [setClipJobError],
  )

  const handleRetryClip = useCallback(
    (clip: SongClipStatus) => {
      console.info('Retry clip requested', clip.id)
      setClipJobError('Retry is not available yet.')
    },
    [setClipJobError],
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
  }, [analysisData?.sectionLyrics])

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
    setResult(null)
    setAnalysisState('idle')
    setAnalysisJobId(null)
    setAnalysisProgress(0)
    setAnalysisData(null)
    setAnalysisError(null)
    setIsFetchingAnalysis(false)
    setSongDetails(null)
    setClipJobId(null)
    setClipJobStatus('idle')
    setClipJobProgress(0)
    setClipJobError(null)
    setClipSummary(null)
    if (highlightTimeoutRef.current) {
      window.clearTimeout(highlightTimeoutRef.current)
      highlightTimeoutRef.current = null
    }
    setHighlightedSectionId(null)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }, [])

  const fetchAnalysis = useCallback(async (songId: string) => {
    setIsFetchingAnalysis(true)
    try {
      const { data } = await apiClient.get<SongAnalysis>(`/songs/${songId}/analysis`)
      setAnalysisData(data)
      setAnalysisError(null)
    } catch (err) {
      setAnalysisError(extractErrorMessage(err, 'Unable to load analysis results.'))
    } finally {
      setIsFetchingAnalysis(false)
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

  const fetchClipSummary = useCallback(
    async (songId: string) => {
      try {
        const { data } = await apiClient.get<ClipGenerationSummary>(
          `/songs/${songId}/clips/status`,
        )
        setClipSummary(data)
      } catch (err) {
        const message = extractErrorMessage(err, 'Unable to load clip status.')
        if (clipJobId) {
          setClipJobError((prev) => prev ?? message)
        } else {
          console.warn('[clip-summary]', message)
        }
      }
    },
    [clipJobId],
  )

  const startAnalysis = useCallback(async (songId: string) => {
    try {
      setAnalysisState('queued')
      setAnalysisProgress(0)
      setAnalysisError(null)
      setAnalysisData(null)
      setAnalysisJobId(null)
      setSongDetails(null)

      const { data } = await apiClient.post<SongAnalysisJobResponse>(
        `/songs/${songId}/analyze`,
      )
      setAnalysisJobId(data.jobId)
      setAnalysisState(normalizeJobStatus(data.status))
    } catch (err) {
      setAnalysisState('failed')
      setAnalysisError(
        extractErrorMessage(err, 'Unable to start analysis for this track.'),
      )
    }
  }, [])

  useEffect(() => {
    if (!analysisJobId || !result?.songId) return

    let cancelled = false
    let timeoutId: number | undefined

    const pollStatus = async () => {
      try {
        const { data } = await apiClient.get<JobStatusResponse>(`/jobs/${analysisJobId}`)
        if (cancelled) {
          return
        }

        const normalizedStatus = normalizeJobStatus(data.status)
        setAnalysisState(normalizedStatus)
        setAnalysisProgress(
          normalizedStatus === 'completed' ? 100 : clamp(data.progress ?? 0, 0, 99),
        )

        if (normalizedStatus === 'completed') {
          setAnalysisError(null)
          if (data.result && isSongAnalysis(data.result)) {
            setAnalysisData(data.result)
          } else if (result?.songId) {
            await fetchAnalysis(result.songId)
          }
          if (result?.songId) {
            void fetchSongDetails(result.songId)
          }
          return
        }

        if (normalizedStatus === 'failed') {
          setAnalysisError(
            data.error ??
              'Song analysis failed. Please try again or upload a different track.',
          )
          return
        }

        timeoutId = window.setTimeout(pollStatus, 3_000)
      } catch (err) {
        if (!cancelled) {
          setAnalysisError(extractErrorMessage(err, 'Unable to fetch analysis progress.'))
          setAnalysisState('failed')
        }
      }
    }

    pollStatus()

    return () => {
      cancelled = true
      if (timeoutId) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [analysisJobId, result?.songId, fetchAnalysis, fetchSongDetails])

  useEffect(() => {
    if (!analysisData && clipSummary?.analysis) {
      setAnalysisData(clipSummary.analysis)
    }
  }, [clipSummary?.analysis, analysisData])

  useEffect(() => {
    if (!clipJobId || !result?.songId) return

    let cancelled = false
    let timeoutId: number | undefined

    const pollClipJob = async () => {
      try {
        const { data } = await apiClient.get<JobStatusResponse>(`/jobs/${clipJobId}`)
        if (cancelled) return

        const normalizedStatus = normalizeJobStatus(data.status)
        setClipJobStatus(normalizedStatus)
        setClipJobProgress(
          normalizedStatus === 'completed' ? 100 : clamp(data.progress ?? 0, 0, 99),
        )
        setClipJobError(
          normalizedStatus === 'failed'
            ? (data.error ?? 'Clip generation failed. Please retry.')
            : null,
        )

        if (data.result && isClipGenerationSummary(data.result)) {
          setClipSummary(data.result)
        }

        if (normalizedStatus === 'completed' || normalizedStatus === 'failed') {
          if (result?.songId) {
            void fetchClipSummary(result.songId)
          }
          return
        }

        timeoutId = window.setTimeout(pollClipJob, 3_000)
      } catch (err) {
        if (!cancelled) {
          setClipJobError(
            extractErrorMessage(err, 'Unable to fetch clip generation progress.'),
          )
          timeoutId = window.setTimeout(pollClipJob, 5_000)
        }
      }
    }

    pollClipJob()

    return () => {
      cancelled = true
      if (timeoutId) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [clipJobId, result?.songId, fetchClipSummary])

  useEffect(() => {
    if (!result?.songId || clipJobId || clipSummary) {
      return
    }
    void fetchClipSummary(result.songId)
  }, [result?.songId, clipJobId, clipSummary, fetchClipSummary])

  useEffect(() => {
    if (!result?.songId) {
      setClipSummary(null)
      return
    }

    if (
      !clipJobId &&
      clipSummary &&
      clipSummary.completedClips === clipSummary.totalClips
    ) {
      return
    }

    let cancelled = false
    let timeoutId: number | undefined

    const pollClipSummary = async () => {
      try {
        const { data } = await apiClient.get<ClipGenerationSummary>(
          `/songs/${result.songId}/clips/status`,
        )
        if (cancelled) return

        setClipSummary(data)

        const hasActiveJob =
          clipJobId != null &&
          clipJobProgress < 100 &&
          (clipJobStatus === 'queued' || clipJobStatus === 'processing') &&
          data.totalClips > 0 &&
          data.completedClips < data.totalClips

        if (hasActiveJob) {
          timeoutId = window.setTimeout(pollClipSummary, 2_000)
        } else if (clipJobId) {
          timeoutId = window.setTimeout(pollClipSummary, 6_000)
        }
      } catch (err) {
        if (cancelled) return

        if (clipJobId) {
          const message = extractErrorMessage(err, 'Unable to load clip status.')
          setClipJobError((prev) => prev ?? message)
          timeoutId = window.setTimeout(pollClipSummary, 6_000)
        } else {
          setClipSummary(null)
        }
      }
    }

    pollClipSummary()

    return () => {
      cancelled = true
      if (timeoutId) {
        window.clearTimeout(timeoutId)
      }
    }
  }, [result?.songId, clipJobId, clipJobStatus, clipJobProgress, clipSummary])

  useEffect(() => {
    if (clipJobError) {
      console.warn('[clip-generation]', clipJobError)
    }
  }, [clipJobError])

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

  const computeDuration = useCallback(async (file: File): Promise<number | null> => {
    try {
      const audio = document.createElement('audio')
      audio.preload = 'metadata'
      const src = URL.createObjectURL(file)
      audio.src = src
      return await new Promise<number | null>((resolve, reject) => {
        const timeoutId = window.setTimeout(() => {
          URL.revokeObjectURL(src)
          reject(new Error('Timed out while analyzing audio metadata.'))
        }, 8000)

        audio.onloadedmetadata = () => {
          const duration = Number.isFinite(audio.duration) ? audio.duration : null
          URL.revokeObjectURL(src)
          window.clearTimeout(timeoutId)
          resolve(duration)
        }
        audio.onerror = () => {
          URL.revokeObjectURL(src)
          window.clearTimeout(timeoutId)
          resolve(null)
        }
      })
    } catch {
      return null
    }
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
        await startAnalysis(response.data.songId)
      } catch (err) {
        console.error('Upload failed', err)
        const message =
          (err as { response?: { data?: { detail?: string } } }).response?.data?.detail ??
          'Upload failed. Please try again.'
        setError(message)
        setStage('error')
      }
    },
    [computeDuration, resetState, startAnalysis],
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

  const renderIdleCard = () => (
    <div
      className={clsx(
        'relative rounded-3xl border-2 border-dashed transition-all duration-300',
        stage === 'dragging'
          ? 'border-vc-accent-primary/90 shadow-vc3'
          : 'border-vc-border/70 hover:border-vc-accent-primary/60 hover:shadow-vc2',
        'bg-[rgba(20,20,32,0.68)]/60 backdrop-blur-xl',
      )}
    >
      <div className="pointer-events-none absolute inset-0 rounded-3xl bg-gradient-to-br from-vc-accent-primary/10 via-transparent to-vc-accent-tertiary/10 opacity-0 transition-opacity duration-300 group-hover:opacity-70" />
      <div className="flex flex-col items-center justify-center px-10 py-14 text-center">
        <MusicNoteIcon className="h-16 w-16 text-vc-accent-primary/90 drop-shadow-[0_0_22px_rgba(110,107,255,0.4)]" />
        <h2 className="mt-6 text-2xl font-semibold tracking-tight text-white">
          Drop your track
        </h2>
        <p className="mt-2 text-sm text-vc-text-secondary">or click to upload</p>
        <VCButton
          className="mt-6"
          variant="secondary"
          size="lg"
          iconLeft={<UploadIcon />}
          onClick={() => inputRef.current?.click()}
        >
          Choose a track
        </VCButton>
      </div>
    </div>
  )

  const renderUploadingCard = () => (
    <div className="rounded-3xl border border-vc-border/80 bg-[rgba(12,12,18,0.82)] p-8 shadow-vc2">
      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-vc-accent-primary/15">
            <MusicNoteIcon className="h-6 w-6 text-vc-accent-primary" />
          </div>
          <div>
            <p className="font-medium text-white">{metadata?.fileName}</p>
            <p className="text-xs text-vc-text-muted">
              {formatSeconds(metadata?.durationSeconds ?? null)} •{' '}
              {formatBytes(metadata?.fileSize ?? 0)}
            </p>
          </div>
        </div>
        <div className="relative h-2.5 overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
          <div
            className="h-full rounded-full bg-gradient-to-r from-vc-accent-primary via-vc-accent-secondary to-vc-accent-tertiary transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
        <p className="text-xs text-vc-text-muted">
          Uploading your track… This may take a moment.
        </p>
        <div className="flex justify-end">
          <VCButton
            variant="ghost"
            onClick={() => {
              resetState()
            }}
          >
            Cancel
          </VCButton>
        </div>
      </div>
    </div>
  )

  const renderUploadedCard = () => {
    const progressValue =
      analysisState === 'completed' ? 100 : clamp(analysisProgress, 0, 99)

    return (
      <div className="rounded-3xl border border-vc-accent-primary/40 bg-[rgba(12,12,18,0.9)] p-8 shadow-vc3">
        <div className="flex flex-col gap-6">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-vc-accent-primary/15">
              <CheckIcon className="h-5 w-5 text-vc-accent-primary" />
            </div>
            <div className="text-left">
              <p className="text-sm font-semibold text-white">
                Track uploaded successfully
              </p>
              <p className="text-xs text-vc-text-muted">
                We’ll listen for tempo, sections, lyrics, and mood to set up your visual
                journey.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-vc-border/40 bg-[rgba(255,255,255,0.02)] px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[rgba(255,255,255,0.05)]">
                <MusicNoteIcon className="h-5 w-5 text-vc-accent-primary" />
              </div>
              <div className="overflow-hidden text-left">
                <p className="truncate text-sm font-medium text-white">
                  {metadata?.fileName}
                </p>
                <p className="text-[11px] uppercase tracking-[0.14em] text-vc-text-muted">
                  {getFileTypeLabel(metadata?.fileName)} •{' '}
                  {formatSeconds(metadata?.durationSeconds ?? null)} •{' '}
                  {formatBytes(metadata?.fileSize ?? 0)}
                </p>
              </div>
            </div>
            {result?.songId && (
              <span className="rounded-md border border-vc-border/30 bg-[rgba(255,255,255,0.03)] px-3 py-1 font-mono text-[11px] tracking-tight text-vc-text-secondary">
                ID {result.songId.slice(0, 8)}…
              </span>
            )}
          </div>

          <WaveformPlaceholder />

          {analysisState !== 'idle' && (
            <div className="rounded-xl border border-vc-border/40 bg-[rgba(12,12,18,0.6)] px-5 py-4">
              <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.16em] text-vc-text-muted">
                <span>{formatProgressLabel(analysisState, progressValue)}</span>
                <span>
                  {analysisState === 'completed'
                    ? '100%'
                    : `${Math.round(progressValue)}%`}
                </span>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-[rgba(255,255,255,0.08)]">
                <div
                  className={clsx(
                    'h-full rounded-full bg-gradient-to-r from-vc-accent-primary via-vc-accent-secondary to-vc-accent-tertiary transition-all duration-500 motion-safe:animate-[gradientShift_2.4s_linear_infinite]',
                    analysisState === 'failed' &&
                      'from-vc-state-error via-vc-state-error to-vc-state-error motion-safe:animate-none',
                    analysisState === 'completed' && 'motion-safe:animate-none',
                  )}
                  style={{
                    width: `${analysisState === 'completed' ? 100 : progressValue}%`,
                  }}
                />
              </div>
              {analysisError && (
                <p className="mt-2 text-xs text-vc-state-error">{analysisError}</p>
              )}
              {analysisState === 'completed' && isFetchingAnalysis && !analysisData && (
                <p className="mt-2 text-xs text-vc-text-muted">
                  Loading analysis summary…
                </p>
              )}
            </div>
          )}

          {analysisData && (
            <div className="space-y-5 rounded-2xl border border-vc-border/40 bg-[rgba(255,255,255,0.03)] p-5 text-left">
              <div className="grid gap-3 md:grid-cols-2">
                <SummaryStat label="Tempo" value={formatBpm(analysisData.bpm)} />
                <SummaryStat
                  label="Duration"
                  value={formatSeconds(analysisData.durationSec)}
                />
                <SummaryStat label="Primary mood" value={analysisData.moodPrimary} />
                <SummaryStat
                  label="Mood tags"
                  value={formatMoodTags(analysisData.moodTags)}
                />
                <SummaryStat
                  label="Primary genre"
                  value={analysisData.primaryGenre ?? '—'}
                />
                <SummaryStat
                  label="Lyrics detected"
                  value={analysisData.lyricsAvailable ? 'Yes' : 'No'}
                />
              </div>

              <div>
                <h4 className="text-[11px] uppercase tracking-[0.16em] text-vc-text-muted">
                  Mood vector
                </h4>
                <div className="mt-3">
                  <MoodVectorMeter moodVector={analysisData.moodVector} />
                </div>
              </div>

              <div>
                <h4 className="text-[11px] uppercase tracking-[0.16em] text-vc-text-muted">
                  Sections
                </h4>
                <div className="mt-3 space-y-3">
                  {analysisData.sections.map((section, index) => (
                    <AnalysisSectionRow
                      key={section.id}
                      section={section}
                      title={getSectionTitle(section, index)}
                      mood={summaryMoodKind}
                      lyric={lyricsBySection.get(section.id) ?? undefined}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          <div className="flex flex-wrap items-center justify-between gap-3">
            <a
              href={result?.audioUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-vc-accent-primary transition-colors hover:text-vc-accent-secondary"
            >
              Preview uploaded audio
            </a>
            <div className="flex flex-wrap items-center gap-2">
              <VCButton variant="ghost" onClick={resetState}>
                Upload another track
              </VCButton>
              {analysisData ? (
                <VCButton
                  variant="primary"
                  iconRight={<ArrowRightIcon />}
                  onClick={handleGenerateClips}
                >
                  Generate clips
                </VCButton>
              ) : (
                <VCButton variant="primary" iconRight={<ArrowRightIcon />} disabled>
                  Analyzing…
                </VCButton>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  const renderSongProfile = () => {
    if (!analysisData || !songDetails) return null

    const sectionsWithDisplay = buildSectionsWithDisplayNames(analysisData.sections)
    const waveformValues = parseWaveformJson(songDetails.waveform_json)
    const durationValue = analysisData.durationSec ?? songDetails.duration_sec ?? 0
    const bpmLabel = formatBpm(analysisData.bpm)
    const durationLabel = durationValue ? formatSeconds(durationValue) : '—'
    const primaryGenre = analysisData.primaryGenre ?? 'Unknown genre'
    const moodLabel = analysisData.moodPrimary ?? formatMoodTags(analysisData.moodTags)
    const fileName = songDetails.title?.trim()
      ? songDetails.title
      : (metadata?.fileName ?? songDetails.original_filename)
    const sectionMood = mapMoodToMoodKind(analysisData.moodPrimary ?? '')

    const clipPanel =
      clipSummary && clipSummary.totalClips > 0
        ? (() => {
            const sortedClips = [...clipSummary.clips].sort(
              (a, b) => a.clipIndex - b.clipIndex,
            )
            const processingClip = sortedClips.find(
              (clip) => normalizeClipStatus(clip.status) === 'processing',
            )
            const queuedClip = sortedClips.find(
              (clip) => normalizeClipStatus(clip.status) === 'queued',
            )
            const completedClip = [...sortedClips]
              .reverse()
              .find((clip) => normalizeClipStatus(clip.status) === 'completed')
            const referenceClip =
              processingClip ?? queuedClip ?? completedClip ?? sortedClips[0]

            const referenceIndex = referenceClip
              ? sortedClips.findIndex((clip) => clip.id === referenceClip.id)
              : -1
            const total = clipSummary.totalClips
            const completed = Math.min(clipSummary.completedClips, total)
            const countsProgress = total > 0 ? (completed / total) * 100 : 0
            const progressValue =
              clipJobStatus === 'completed'
                ? 100
                : Math.max(countsProgress, clipJobProgress)
            const safeProgress = Math.min(100, Math.max(progressValue, 2))

            const headline =
              total === 0
                ? 'Clip generation queued'
                : completed >= total
                  ? 'All clips generated ✅'
                  : referenceClip && referenceIndex >= 0
                    ? `Generating clip ${referenceIndex + 1} of ${total}…`
                    : `Generating clips…`

            const activeRange =
              referenceClip != null
                ? `${formatSeconds(referenceClip.startSec)}–${formatSeconds(referenceClip.endSec)}`
                : null

            const beatsCount =
              referenceClip?.startBeat != null && referenceClip?.endBeat != null
                ? Math.max(referenceClip.endBeat - referenceClip.startBeat, 0)
                : null

            const detailParts: string[] = []
            if (activeRange) detailParts.push(activeRange)
            if (referenceClip) {
              detailParts.push(formatDurationShort(referenceClip.durationSec))
              detailParts.push(`${referenceClip.numFrames} frames`)
              detailParts.push(`${referenceClip.fps} fps`)
            }
            if (beatsCount && beatsCount > 0) {
              detailParts.push(`${beatsCount} beats`)
            }

            const detailLine =
              referenceClip && detailParts.length > 0 ? detailParts.join(' • ') : null

            const concurrencyLabel =
              clipSummary.processingClips > 1
                ? `(${clipSummary.processingClips} concurrent)`
                : undefined

            const composeDisabled =
              total === 0 || completed < total || clipJobStatus === 'failed'
            const cancelDisabled =
              !clipJobId || clipJobStatus === 'completed' || clipJobStatus === 'failed'

            return (
              <section className="space-y-3">
                <div className="vc-label">Clip generation</div>
                <VCCard className="space-y-4 bg-[rgba(12,12,18,0.8)] p-5">
                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div>
                      <h3 className="text-sm font-medium text-white">{headline}</h3>
                      <p className="text-xs text-vc-text-muted">
                        {completed}/{total} clips completed
                        {concurrencyLabel ? ` ${concurrencyLabel}` : ''}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-vc-text-secondary">
                      {clipJobStatus === 'failed' && clipJobError && (
                        <span className="text-vc-state-error">{clipJobError}</span>
                      )}
                      {clipJobStatus === 'completed' && (
                        <span className="text-vc-text-muted">Ready to compose</span>
                      )}
                    </div>
                  </div>

                  <div className="relative h-2 overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
                    <div
                      className={clsx(
                        'absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-vc-accent-primary via-vc-accent-secondary to-vc-accent-tertiary transition-all duration-500',
                        clipJobStatus !== 'completed' && 'vc-gradient-shift-animate',
                      )}
                      style={{ width: `${safeProgress}%` }}
                    />
                  </div>

                  {detailLine && (
                    <p className="text-xs text-vc-text-secondary">
                      #{referenceIndex + 1} • {detailLine}
                    </p>
                  )}

                  <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                    <div className="text-xs text-vc-text-muted">
                      {clipJobStatus === 'failed' && !clipJobError
                        ? 'Clip generation failed. Retry once available.'
                        : clipJobStatus === 'processing'
                          ? 'Clip generation is running in the background.'
                          : clipJobStatus === 'completed'
                            ? 'All clips are ready for composition.'
                            : clipJobStatus === 'queued'
                              ? 'Clip jobs are queued and will start soon.'
                              : null}
                    </div>
                    <div className="flex items-center gap-2">
                      <VCButton
                        variant="ghost"
                        size="sm"
                        onClick={handleCancelClipJob}
                        disabled={cancelDisabled}
                      >
                        Cancel
                      </VCButton>
                      <VCButton
                        variant="primary"
                        size="sm"
                        iconRight={<ArrowRightIcon />}
                        disabled={composeDisabled}
                        onClick={handleComposeClips}
                      >
                        Compose when done
                      </VCButton>
                    </div>
                  </div>
                </VCCard>

                {sortedClips.length > 0 && (
                  <div className="space-y-2">
                    <div className="vc-label">Clip queue</div>
                    <div className="overflow-hidden rounded-2xl border border-vc-border/40 bg-[rgba(12,12,18,0.65)]">
                      {sortedClips.map((clip, index) => {
                        const normalizedStatus = normalizeClipStatus(clip.status)
                        const rangeLabel = formatTimeRange(clip.startSec, clip.endSec)
                        const beats =
                          clip.startBeat != null && clip.endBeat != null
                            ? Math.max(clip.endBeat - clip.startBeat, 0)
                            : null
                        const infoParts: string[] = [
                          formatDurationShort(clip.durationSec),
                          `${clip.numFrames} frames`,
                          `${clip.fps} fps`,
                        ]
                        if (beats && beats > 0) {
                          infoParts.push(`${beats} beats`)
                        }
                        const infoLine = infoParts.join(' • ')
                        const isLast = index === sortedClips.length - 1

                        return (
                          <div
                            key={clip.id}
                            className={clsx(
                              'flex flex-col gap-2 border-b border-vc-border/20 px-4 py-4',
                              isLast && 'border-b-0',
                            )}
                          >
                            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                              <div className="flex items-center gap-3 text-sm font-medium text-white">
                                <div className="w-8 text-right text-xs text-vc-text-muted">
                                  #{clip.clipIndex + 1}
                                </div>
                                <div>{rangeLabel}</div>
                              </div>
                              <div className="flex items-center gap-2">
                                <ClipStatusBadge status={normalizedStatus} />
                                {normalizedStatus === 'processing' && (
                                  <span className="flex items-center gap-1 text-[11px] text-vc-text-muted">
                                    <span className="inline-block h-2 w-2 rounded-full bg-vc-accent-primary animate-pulse" />
                                    Generating…
                                  </span>
                                )}
                                {normalizedStatus === 'queued' && (
                                  <span className="text-[11px] text-vc-text-muted">
                                    Awaiting generation
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="flex flex-col gap-2 text-xs text-vc-text-secondary md:flex-row md:items-center md:justify-between">
                              <div>{infoLine}</div>
                              <div className="flex flex-wrap items-center gap-2">
                                {normalizedStatus === 'completed' && (
                                  <>
                                    <VCButton
                                      variant="secondary"
                                      size="sm"
                                      onClick={() => handlePreviewClip(clip)}
                                      disabled={!clip.videoUrl}
                                    >
                                      Preview
                                    </VCButton>
                                    <VCButton
                                      variant="ghost"
                                      size="sm"
                                      onClick={() => handleRegenerateClip(clip)}
                                    >
                                      Regenerate
                                    </VCButton>
                                  </>
                                )}
                                {normalizedStatus === 'failed' && (
                                  <VCButton
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => handleRetryClip(clip)}
                                  >
                                    Retry
                                  </VCButton>
                                )}
                                {normalizedStatus === 'canceled' && (
                                  <span className="text-vc-text-muted">
                                    Clip canceled
                                  </span>
                                )}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}

                <div className="space-y-2">
                  <div className="vc-label">Completed clips</div>
                  {clipSummary.completedClips === 0 ? (
                    <VCCard className="border-dashed border-vc-border/30 bg-[rgba(12,12,18,0.65)] p-6 text-center text-xs text-vc-text-muted">
                      Completed clips will appear here once generation finishes.
                    </VCCard>
                  ) : (
                    <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                      {sortedClips
                        .filter(
                          (clip) => normalizeClipStatus(clip.status) === 'completed',
                        )
                        .map((clip) => (
                          <button
                            key={`thumb-${clip.id}`}
                            type="button"
                            onClick={() => handlePreviewClip(clip)}
                            className={clsx(
                              'group relative overflow-hidden rounded-xl border border-vc-border/40 bg-[rgba(12,12,18,0.55)] transition',
                              clip.videoUrl && 'hover:border-vc-accent-primary',
                            )}
                            disabled={!clip.videoUrl}
                          >
                            <div className="absolute inset-0 bg-gradient-to-t from-black/65 via-transparent to-transparent opacity-80 transition-opacity group-hover:opacity-90" />
                            <div className="relative z-10 flex h-24 flex-col justify-end p-3 text-left">
                              <div className="text-xs font-medium text-white">
                                #{clip.clipIndex + 1} •{' '}
                                {formatTimeRange(clip.startSec, clip.endSec)}
                              </div>
                              <div className="text-[11px] text-vc-text-muted">
                                {formatDurationShort(clip.durationSec)} • {clip.numFrames}{' '}
                                frames • {clip.fps} fps
                              </div>
                            </div>
                            {!clip.videoUrl && (
                              <div className="absolute inset-0 flex items-center justify-center text-[11px] text-vc-text-muted">
                                Preview coming soon
                              </div>
                            )}
                          </button>
                        ))}
                    </div>
                  )}
                </div>
              </section>
            )
          })()
        : null

    const clipJobActive =
      clipJobId != null && (clipJobStatus === 'queued' || clipJobStatus === 'processing')
    const clipJobCompleted =
      clipSummary &&
      clipSummary.totalClips > 0 &&
      clipSummary.completedClips === clipSummary.totalClips
    const generateButtonLabel = clipJobActive
      ? 'Generating…'
      : clipJobCompleted
        ? 'Regenerate clips'
        : 'Generate clips'

    return (
      <section className="mt-12 w-full space-y-8">
        <header className="flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
          <div className="space-y-2">
            <div className="vc-label">Song profile</div>
            <h1 className="font-display text-3xl text-white md:text-4xl">
              {fileName ?? 'Untitled track'}
            </h1>
            <p className="text-xs uppercase tracking-[0.16em] text-vc-text-muted">
              Source file: {songDetails.original_filename}
            </p>
          </div>
          <VCCard className="w-full space-y-2 border-vc-border/40 bg-[rgba(12,12,18,0.75)] p-4 md:w-72">
            <div className="vc-label">Genre & mood</div>
            <div className="text-sm font-medium text-white">{primaryGenre}</div>
            <div className="text-xs text-vc-text-secondary">{moodLabel}</div>
            <div className="text-xs text-vc-text-muted">
              {[bpmLabel, durationLabel].filter(Boolean).join(' • ')} • Key: —
            </div>
            <div className="pt-2">
              <MoodVectorMeter moodVector={analysisData.moodVector} />
            </div>
          </VCCard>
        </header>

        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-vc-text-muted">
            Kick off clip generation to visualize this song in multiple scenes.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <VCButton
              variant="primary"
              iconRight={<ArrowRightIcon />}
              onClick={handleGenerateClips}
              disabled={clipJobActive}
            >
              {generateButtonLabel}
            </VCButton>
            {clipJobError && (
              <span className="text-xs text-vc-state-error">{clipJobError}</span>
            )}
          </div>
        </div>

        {clipPanel}

        <section className="space-y-2">
          <div className="vc-label">Waveform</div>
          <WaveformDisplay
            waveform={waveformValues}
            beatTimes={analysisData.beatTimes}
            duration={durationValue || 1}
          />
        </section>

        <section className="space-y-2">
          <div className="vc-label">Song structure</div>
          <SongTimeline
            sections={sectionsWithDisplay}
            duration={durationValue || 1}
            onSelect={handleSectionSelect}
          />
        </section>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="vc-label">Sections</div>
            <div className="text-xs text-vc-text-muted">
              {analysisData.sections.length} section
              {analysisData.sections.length === 1 ? '' : 's'}
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {sectionsWithDisplay.map((section) => {
              const lyric = lyricsBySection.get(section.id) ?? undefined
              const highlightClass =
                highlightedSectionId === section.id
                  ? 'ring-2 ring-vc-accent-primary ring-offset-2 ring-offset-[rgba(12,12,18,0.9)]'
                  : ''

              return (
                <div
                  key={section.id}
                  id={`section-${section.id}`}
                  className={highlightClass}
                >
                  <SectionCard
                    name={section.displayName}
                    startSec={section.startSec}
                    endSec={section.endSec}
                    mood={sectionMood}
                    lyricSnippet={lyric}
                    hasVideo={false}
                    className="h-full bg-[rgba(12,12,18,0.78)]"
                    onGenerate={() => {}}
                    onRegenerate={() => {}}
                    onUseInFull={() => {}}
                  />
                </div>
              )
            })}
          </div>
        </section>
      </section>
    )
  }

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
                {stage === 'idle' || stage === 'dragging'
                  ? renderIdleCard()
                  : stage === 'uploading'
                    ? renderUploadingCard()
                    : stage === 'uploaded'
                      ? renderUploadedCard()
                      : stage === 'error'
                        ? renderErrorCard()
                        : null}
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
          {renderSongProfile()}
        </div>
      )}
    </div>
  )
}

const RequirementPill: React.FC<{ icon: React.ReactNode; label: string }> = ({
  icon,
  label,
}) => (
  <div className="inline-flex items-center gap-2 rounded-full border border-vc-border/40 bg-[rgba(255,255,255,0.02)] px-3 py-1.5 text-xs text-vc-text-secondary shadow-vc1">
    <span className="text-vc-accent-primary">{icon}</span>
    <span>{label}</span>
  </div>
)

const SummaryStat: React.FC<{ label: string; value: React.ReactNode }> = ({
  label,
  value,
}) => (
  <div className="rounded-lg border border-vc-border/40 bg-[rgba(12,12,18,0.5)] p-3">
    <p className="text-[11px] uppercase tracking-[0.16em] text-vc-text-muted">{label}</p>
    <p className="mt-2 text-sm text-white">{value}</p>
  </div>
)

const MoodVectorMeter: React.FC<{ moodVector: MoodVector }> = ({ moodVector }) => {
  const entries: Array<[string, number]> = [
    ['Energy', clamp(moodVector.energy * 100, 0, 100)],
    ['Valence', clamp(moodVector.valence * 100, 0, 100)],
    ['Danceability', clamp(moodVector.danceability * 100, 0, 100)],
    ['Tension', clamp(moodVector.tension * 100, 0, 100)],
  ]

  return (
    <div className="space-y-3">
      {entries.map(([label, value]) => (
        <div key={label}>
          <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.14em] text-vc-text-muted">
            <span>{label}</span>
            <span>{Math.round(value)}%</span>
          </div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
            <div
              className="h-full rounded-full bg-gradient-to-r from-vc-accent-primary via-vc-accent-secondary to-vc-accent-tertiary transition-all duration-500"
              style={{ width: `${value}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

const ClipStatusBadge: React.FC<{
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'canceled'
}> = ({ status }) => {
  const labelMap: Record<typeof status, string> = {
    queued: 'Queued',
    processing: 'Processing',
    completed: 'Completed',
    failed: 'Failed',
    canceled: 'Canceled',
  }

  const variantClass =
    status === 'completed'
      ? 'vc-badge-success'
      : status === 'failed'
        ? 'vc-badge-danger'
        : 'vc-badge'

  return (
    <span className={clsx(variantClass, 'inline-flex items-center gap-1 text-[11px]')}>
      {status === 'processing' && (
        <span className="inline-block h-2 w-2 rounded-full bg-white/80 animate-pulse" />
      )}
      {labelMap[status]}
    </span>
  )
}

const AnalysisSectionRow: React.FC<{
  section: SongSection
  title: string
  mood: MoodKind
  lyric?: string
}> = ({ section, title, mood, lyric }) => (
  <VCCard className="border-vc-border/30 bg-[rgba(12,12,18,0.68)]">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h3 className="font-display text-sm text-white">{title}</h3>
        <p className="text-xs text-vc-text-muted">
          {formatSeconds(section.startSec)} – {formatSeconds(section.endSec)}
        </p>
      </div>
      <SectionMoodTag mood={mood} />
    </div>
    <div className="mt-3 flex flex-wrap items-center gap-3 text-[11px] uppercase tracking-[0.14em] text-vc-text-muted">
      <span>Confidence {Math.round(clamp(section.confidence * 100, 0, 100))}%</span>
      {section.repetitionGroup && (
        <span>Group {section.repetitionGroup.toUpperCase()}</span>
      )}
    </div>
    {lyric && (
      <p className="mt-3 border-l border-vc-border pl-3 text-xs italic text-vc-text-secondary">
        “{lyric}”
      </p>
    )}
  </VCCard>
)

const WaveformPlaceholder: React.FC = () => (
  <div className="relative flex h-20 w-full items-center overflow-hidden rounded-2xl border border-vc-border/50 bg-[rgba(255,255,255,0.03)]">
    <div className="absolute inset-0 vc-shimmer opacity-70" />
    <div className="relative z-10 flex w-full items-center justify-between gap-[3px] px-4">
      {WAVEFORM_BARS.map((height, index) => (
        <span
          key={`placeholder-bar-${index}-${height}`}
          className="w-[3px] rounded-full bg-gradient-to-t from-vc-accent-primary via-vc-accent-secondary to-vc-accent-tertiary"
          style={{ height: `${Math.max(0.16, height) * 100}%`, opacity: 0.85 }}
        />
      ))}
    </div>
  </div>
)

const BackgroundOrbs: React.FC = () => (
  <>
    <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(110,107,255,0.24),_transparent_65%)]" />
    <div className="pointer-events-none absolute -top-40 -left-32 h-80 w-80 rounded-full bg-[radial-gradient(circle,_rgba(110,107,255,0.45),_transparent_60%)] blur-3xl" />
    <div className="pointer-events-none absolute -bottom-32 -right-20 h-72 w-72 rounded-full bg-[radial-gradient(circle,_rgba(0,198,192,0.4),_transparent_60%)] blur-3xl" />
    <div className="pointer-events-none absolute top-1/4 left-1/2 h-52 w-52 -translate-x-1/2 rounded-full bg-[radial-gradient(circle,_rgba(255,111,245,0.35),_transparent_65%)] blur-2xl" />
  </>
)

const MusicNoteIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M9 18.5C9 20.433 7.433 22 5.5 22C3.567 22 2 20.433 2 18.5C2 16.567 3.567 15 5.5 15C6.4157 15 7.24821 15.3425 7.87569 15.9121V5.99997C7.87569 4.34311 9.21883 3 10.8757 3H18.1243C19.7812 3 21.1243 4.34311 21.1243 5.99997V8.99997C21.1243 10.6568 19.7812 12 18.1243 12H12.75V18.5C12.75 20.433 11.183 22 9.25 22C7.317 22 5.75 20.433 5.75 18.5C5.75 16.567 7.317 15 9.25 15C9.66719 15 10.0669 15.0735 10.4375 15.2106V6.74997"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

const UploadIcon: React.FC = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12 3V15M12 3L7 8M12 3L17 8M5 17C5 18.1046 5.89543 19 7 19H17C18.1046 19 19 18.1046 19 17"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

const ArrowRightIcon: React.FC = () => (
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M5 12H19M19 12L13 6M19 12L13 18"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

const CheckIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    width="20"
    height="20"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M5 12.5L9.5 17L19 7"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

const TimerIcon: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12 7V12L15 15M9 3H15M12 21C16.4183 21 20 17.4183 20 13C20 8.58172 16.4183 5 12 5C7.58172 5 4 8.58172 4 13C4 17.4183 7.58172 21 12 21Z"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

const WaveformIcon: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M5 12H7M9 7V17M12 4V20M15 7V17M17 12H19"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

const HardDriveIcon: React.FC = () => (
  <svg
    width="16"
    height="16"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M20 13V16C20 17.1046 19.1046 18 18 18H6C4.89543 18 4 17.1046 4 16V8C4 6.89543 4.89543 6 6 6H14.5858C14.851 6 15.1054 6.10536 15.2929 6.29289L19.7071 10.7071C19.8946 10.8946 20 11.149 20 11.4142V13ZM12 15H12.01M16 15H16.01"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)

const ErrorIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    className={className}
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12 8V12M12 16H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
)
