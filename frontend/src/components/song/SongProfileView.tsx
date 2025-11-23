import React, { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { ErrorBoundary } from 'react-error-boundary'
import { SectionCard, VCCard, VCButton } from '../vibecraft'
import type {
  ClipGenerationSummary,
  SongAnalysis,
  SongClipStatus,
  SongRead,
} from '../../types/song'
import { MainVideoPlayer } from '../MainVideoPlayer'
import { formatSeconds, formatBpm, formatMoodTags } from '../../utils/formatting'
import { buildSectionsWithDisplayNames, mapMoodToMoodKind } from '../../utils/sections'
import { parseWaveformJson } from '../../utils/waveform'
import { normalizeClipStatus } from '../../utils/status'
import { SongTimeline } from './SongTimeline'
import { WaveformDisplay } from './WaveformDisplay'
import { MoodVectorMeter } from './MoodVectorMeter'
import { ClipGenerationPanel } from './ClipGenerationPanel'
import { useFeatureFlags } from '../../hooks/useFeatureFlags'
import { SectionErrorFallback } from '../SectionErrorFallback'
import { VideoPlayerErrorFallback } from '../VideoPlayerErrorFallback'

interface SongProfileViewProps {
  analysisData: SongAnalysis
  songDetails: SongRead
  clipSummary: ClipGenerationSummary | null
  clipJobId: string | null
  clipJobStatus: 'idle' | 'queued' | 'processing' | 'completed' | 'failed'
  clipJobProgress: number
  clipJobError: string | null
  isComposing: boolean
  composeJobProgress: number
  playerActiveClipId: string | null
  metadata: { fileName: string } | null
  audioUrl: string | null
  onGenerateClips: () => void
  onCancelClipJob: () => void
  onCompose: () => void
  onPreviewClip: (clip: SongClipStatus) => void
  onRegenerateClip: (clip: SongClipStatus) => void
  onRetryClip: (clip: SongClipStatus) => void
  onPlayerClipSelect: (clipId: string | null) => void
  highlightedSectionId: string | null
  lyricsBySection: Map<string, string>
  onSectionSelect: (sectionId: string) => void
  onTitleUpdate?: (title: string) => Promise<void>
}

export const SongProfileView: React.FC<SongProfileViewProps> = ({
  analysisData,
  songDetails,
  clipSummary,
  clipJobId,
  clipJobStatus,
  clipJobProgress,
  clipJobError,
  isComposing,
  composeJobProgress,
  playerActiveClipId,
  highlightedSectionId,
  metadata,
  lyricsBySection,
  onGenerateClips,
  onCancelClipJob,
  onCompose,
  onPreviewClip,
  onRegenerateClip,
  onRetryClip,
  onPlayerClipSelect,
  onSectionSelect,
  audioUrl,
  onTitleUpdate,
}) => {
  const navigate = useNavigate()
  const { data: featureFlags } = useFeatureFlags()
  const sectionsEnabled = featureFlags?.sections ?? true // Default to true for backward compatibility
  const sectionsWithDisplay = buildSectionsWithDisplayNames(analysisData.sections)
  const waveformValues = parseWaveformJson(songDetails.waveform_json)
  const durationValue = analysisData.durationSec ?? songDetails.duration_sec ?? 0
  const bpmLabel = formatBpm(analysisData.bpm)
  const durationLabel = durationValue ? formatSeconds(durationValue) : '—'
  const primaryGenre = analysisData.primaryGenre ?? 'Unknown genre'
  const moodLabel = analysisData.moodPrimary ?? formatMoodTags(analysisData.moodTags)
  const defaultTitle = metadata?.fileName ?? songDetails.original_filename
  const displayTitle = songDetails.title?.trim() ? songDetails.title : defaultTitle
  const sectionMood = mapMoodToMoodKind(analysisData.moodPrimary ?? '')

  // Title editing state
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [titleValue, setTitleValue] = useState(displayTitle)
  const titleInputRef = useRef<HTMLInputElement>(null)
  const [isSavingTitle, setIsSavingTitle] = useState(false)
  const [showTitleHint, setShowTitleHint] = useState(false)
  const [showCelebration, setShowCelebration] = useState(false)
  const [celebrationFading, setCelebrationFading] = useState(false)
  const celebrationShownRef = useRef(false)

  // Update title value when songDetails changes
  useEffect(() => {
    const newDisplayTitle = songDetails.title?.trim() ? songDetails.title : defaultTitle
    setTitleValue(newDisplayTitle)
  }, [songDetails.title, defaultTitle])

  // Show title hint on mount (one-time per page load, if title is editable)
  useEffect(() => {
    if (!onTitleUpdate) return

    // Temporarily show every time for testing - remove sessionStorage check
    // const hasShownHint = sessionStorage.getItem('vibecraft_title_hint_shown')
    // if (!hasShownHint) {
      // Use setTimeout to avoid setState in effect
      const timer = setTimeout(() => {
        setShowTitleHint(true)
        // Set sessionStorage after animation completes (2.5s animation + buffer)
        // setTimeout(() => {
        //   sessionStorage.setItem('vibecraft_title_hint_shown', 'true')
        // }, 3000)
      }, 1000) // Delay slightly to let page settle
      return () => clearTimeout(timer)
    // }
  }, [onTitleUpdate])

  // Focus input when entering edit mode
  useEffect(() => {
    if (isEditingTitle && titleInputRef.current) {
      titleInputRef.current.focus()
      titleInputRef.current.select()
    }
  }, [isEditingTitle])

  const handleTitleClick = () => {
    if (onTitleUpdate) {
      setIsEditingTitle(true)
      setShowTitleHint(false) // Hide hint when user starts editing
    }
  }

  const handleTitleBlur = async () => {
    if (!onTitleUpdate) return

    const trimmedValue = titleValue.trim()
    const finalValue = trimmedValue || defaultTitle

    if (trimmedValue !== songDetails.title) {
      setIsSavingTitle(true)
      try {
        await onTitleUpdate(finalValue)
      } catch (error) {
        console.error('Failed to update title:', error)
        // Revert to original value on error
        setTitleValue(songDetails.title?.trim() ? songDetails.title : defaultTitle)
      } finally {
        setIsSavingTitle(false)
      }
    }

    setIsEditingTitle(false)
  }

  const handleTitleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      titleInputRef.current?.blur()
    } else if (e.key === 'Escape') {
      e.preventDefault()
      setTitleValue(songDetails.title?.trim() ? songDetails.title : defaultTitle)
      setIsEditingTitle(false)
    }
  }

  const completedClipEntries =
    clipSummary?.clips?.filter(
      (clip) => normalizeClipStatus(clip.status) === 'completed' && !!clip.videoUrl,
    ) ?? []
  const composedVideoUrl = clipSummary?.composedVideoUrl ?? null

  // Show celebration animation once when composition completes
  useEffect(() => {
    if (composedVideoUrl && !celebrationShownRef.current) {
      celebrationShownRef.current = true
      setShowCelebration(true)
      setCelebrationFading(false)
      // Start fade-out right after pulse completes (2s pulse + 0.3s buffer = 2.3s)
      const fadeTimer = setTimeout(() => {
        setCelebrationFading(true)
      }, 2300)
      // Fully hide after fade-out completes (1.2 seconds for fade)
      const hideTimer = setTimeout(() => {
        setShowCelebration(false)
        setCelebrationFading(false)
      }, 3500) // 2.3s display + 1.2s fade
      return () => {
        clearTimeout(fadeTimer)
        clearTimeout(hideTimer)
      }
    } else if (!composedVideoUrl) {
      // Reset when composed video is removed (e.g., new project)
      celebrationShownRef.current = false
      setShowCelebration(false)
      setCelebrationFading(false)
    }
  }, [composedVideoUrl])
  const composedPosterUrl = clipSummary?.composedVideoPosterUrl ?? null
  const activePlayerClip =
    completedClipEntries.find((clip) => clip.id === playerActiveClipId) ??
    completedClipEntries[completedClipEntries.length - 1] ??
    null
  const playerVideoUrl = composedVideoUrl ?? activePlayerClip?.videoUrl ?? null
  const playerPosterUrl = composedPosterUrl ?? activePlayerClip?.videoUrl ?? undefined
  // Only use audio URL if we don't have a composed video (composed video includes audio)
  const playerAudioUrl = composedVideoUrl ? null : audioUrl

  // Calculate duration: use selected range if available, otherwise use composed video duration or sum of clips
  const selectedDuration =
    songDetails.selected_start_sec != null && songDetails.selected_end_sec != null
      ? songDetails.selected_end_sec - songDetails.selected_start_sec
      : null
  const composedDuration =
    composedVideoUrl && clipSummary?.songDurationSec ? clipSummary.songDurationSec : null
  const clipsDuration =
    clipSummary?.clips && clipSummary.clips.length > 0
      ? Math.max(...clipSummary.clips.map((c) => c.endSec)) -
        Math.min(...clipSummary.clips.map((c) => c.startSec))
      : null
  // When previewing individual clips (not composed video), use the active clip's duration
  const individualClipDuration =
    !composedVideoUrl && activePlayerClip
      ? activePlayerClip.endSec - activePlayerClip.startSec
      : null

  const playerDurationSec =
    selectedDuration ??
    composedDuration ??
    individualClipDuration ?? // Use individual clip duration when previewing clips
    clipsDuration ??
    durationValue ??
    activePlayerClip?.endSec ??
    null
  // Calculate timeline offset: if there's a selected range, clips should be relative to that start
  const timelineOffset =
    songDetails.selected_start_sec != null ? songDetails.selected_start_sec : 0

  // Normalize clips relative to timeline start and filter/sort them
  const playerClips =
    clipSummary?.clips
      ?.filter((clip) => {
        // Filter out clips that are completely outside the visible range
        if (
          songDetails.selected_start_sec != null &&
          songDetails.selected_end_sec != null
        ) {
          return (
            clip.endSec > songDetails.selected_start_sec &&
            clip.startSec < songDetails.selected_end_sec
          )
        }
        return true
      })
      .sort((a, b) => a.startSec - b.startSec) // Sort by start time
      .map((clip) => ({
        id: clip.id,
        index: clip.clipIndex,
        // Normalize clip times relative to timeline start
        startSec: clip.startSec - timelineOffset,
        endSec: clip.endSec - timelineOffset,
        videoUrl: composedVideoUrl ?? clip.videoUrl ?? undefined,
        thumbUrl: clip.videoUrl ?? composedPosterUrl ?? undefined,
      })) ?? []
  // Normalize beat grid and lyrics relative to timeline offset
  const playerBeatGrid =
    analysisData.beatTimes
      ?.filter((time) => {
        // Filter beats within visible range if there's a selected range
        if (
          songDetails.selected_start_sec != null &&
          songDetails.selected_end_sec != null
        ) {
          return (
            time >= songDetails.selected_start_sec && time <= songDetails.selected_end_sec
          )
        }
        return true
      })
      .map((time) => ({ t: time - timelineOffset })) ?? []
  const playerLyrics =
    analysisData.sectionLyrics
      ?.filter((line) => {
        // Filter lyrics within visible range if there's a selected range
        if (
          songDetails.selected_start_sec != null &&
          songDetails.selected_end_sec != null
        ) {
          return (
            line.endSec > songDetails.selected_start_sec &&
            line.startSec < songDetails.selected_end_sec
          )
        }
        return true
      })
      .map((line) => ({
        t: line.startSec - timelineOffset,
        text: line.text,
        dur: line.endSec - line.startSec,
      })) ?? []

  return (
    <>
      <section className="mt-4 w-full space-y-8 pb-0">
        <header className="flex flex-col gap-6 md:flex-row md:justify-between md:items-start">
          <div className="space-y-2 relative md:flex-shrink-0 overflow-visible">
            <div className="vc-label">Song profile</div>
            <div className="relative flex items-baseline gap-4 flex-wrap overflow-visible">
              <div className="relative max-w-2xl overflow-visible">
                {/* Subtle pointing animation for editable title */}
                {showTitleHint && onTitleUpdate && !isEditingTitle && (
                  <div
                    className="absolute left-full top-1/2 -translate-y-1/2 ml-2 pointer-events-none z-10 whitespace-nowrap"
                    style={{
                      animation: 'pointAndFadeSubtle 2.5s ease-in-out forwards',
                    }}
                  >
                    <div className="text-base filter drop-shadow-md flex items-center gap-1" style={{ opacity: 0.7 }}>
                      <span>👈</span>
                      <span className="text-sm text-vc-text-secondary">edit</span>
                    </div>
                  </div>
                )}
                {isEditingTitle ? (
                  <input
                    ref={titleInputRef}
                    type="text"
                    value={titleValue}
                    onChange={(e) => setTitleValue(e.target.value)}
                    onBlur={handleTitleBlur}
                    onKeyDown={handleTitleKeyDown}
                    disabled={isSavingTitle}
                    className="font-display text-3xl text-white md:text-4xl bg-transparent border-b-2 border-vc-accent-primary/50 focus:border-vc-accent-primary focus:outline-none disabled:opacity-50"
                    style={{ margin: 0, padding: 0, marginRight: '8px' }}
                    maxLength={256}
                  />
                ) : (
                  <h1
                    onClick={handleTitleClick}
                    className={`font-display text-3xl text-white md:text-4xl ${
                      onTitleUpdate
                        ? 'cursor-text hover:text-vc-accent-primary/80 transition-colors'
                        : ''
                    }`}
                    style={{
                      margin: 0,
                      padding: 0,
                      borderBottom: '2px solid transparent',
                      marginRight: '8px',
                    }}
                  >
                    {displayTitle ?? 'Untitled track'}
                  </h1>
                )}
              </div>
            </div>
            <p className="text-xs uppercase tracking-[0.16em] text-vc-text-muted mb-1">
              Source file: {songDetails.original_filename}
            </p>
            <div className="flex items-center gap-3 flex-wrap">
              <span className="text-xs text-vc-text-muted">Visual Style:</span>
              {songDetails.template ? (
                <span className="text-xs font-medium text-vc-text-primary capitalize">
                  {songDetails.template}
                </span>
              ) : (
                <span className="text-xs text-vc-text-secondary">
                  Not set (abstract by default)
                </span>
              )}
              {/* Cost indicator - only show after video is composed */}
              {composedVideoUrl && (
                <>
                  <span className="text-xs text-vc-text-muted">•</span>
                  <div className="text-xs text-vc-text-muted whitespace-nowrap">
                    {songDetails.total_generation_cost_usd != null &&
                    songDetails.total_generation_cost_usd > 0 ? (
                      <>
                        <span>~${songDetails.total_generation_cost_usd.toFixed(2)}</span>
                        <span className="ml-1.5">but free for you!</span>
                        <span
                          className={`ml-1 ${
                            songDetails.template
                              ? 'text-vc-text-primary'
                              : 'text-vc-text-muted'
                          }`}
                        >
                          ♡
                        </span>
                      </>
                    ) : (
                      <>
                        <span>free for you!</span>
                        <span
                          className={`ml-1 ${
                            songDetails.template
                              ? 'text-vc-text-primary'
                              : 'text-vc-text-muted'
                          }`}
                        >
                          ♡
                        </span>
                      </>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
          <VCCard className="w-full space-y-2 border-vc-border/40 bg-[rgba(12,12,18,0.75)] p-4 md:w-72 md:flex-shrink-0">
            <div className="vc-label">Genre & mood</div>
            <div className="text-sm font-medium text-white">{primaryGenre}</div>
            <div className="text-xs text-vc-text-secondary">{moodLabel}</div>
            <div className="text-xs text-vc-text-muted">
              {[bpmLabel, durationLabel].filter(Boolean).join(' • ')}
            </div>
            <div className="pt-2">
              <MoodVectorMeter moodVector={analysisData.moodVector} />
            </div>
          </VCCard>
        </header>

        {playerVideoUrl && playerDurationSec ? (
          <section className="space-y-3">
            <div className="vc-label">
              {composedVideoUrl
                ? 'Your Final Video'
                : `Preview${
                    clipSummary?.completedClips && clipSummary.totalClips
                      ? ` (${clipSummary.completedClips}/${clipSummary.totalClips} clips)`
                      : ''
                  }`}
            </div>
            <ErrorBoundary
              FallbackComponent={VideoPlayerErrorFallback}
              onReset={() => {
                // Reset video player state if needed
              }}
            >
              <MainVideoPlayer
                videoUrl={playerVideoUrl}
                audioUrl={playerAudioUrl ?? undefined}
                posterUrl={playerPosterUrl}
                durationSec={playerDurationSec}
                clips={playerClips}
                activeClipId={activePlayerClip?.id ?? undefined}
                onClipSelect={onPlayerClipSelect}
                beatGrid={playerBeatGrid}
                lyrics={playerLyrics}
                waveform={waveformValues}
                onDownload={
                  playerVideoUrl
                    ? () => window.open(playerVideoUrl, '_blank', 'noopener,noreferrer')
                    : undefined
                }
              />
            </ErrorBoundary>
          </section>
        ) : null}

        {/* Celebration animation - fires once when composition completes */}
        {showCelebration && (
          <div
            className="relative w-full flex flex-col items-center overflow-hidden"
            style={{
              opacity: celebrationFading ? 0 : 1,
              transform: celebrationFading ? 'scaleY(0)' : 'scaleY(1)',
              transformOrigin: 'top',
              maxHeight: celebrationFading ? '0' : '400px',
              paddingTop: celebrationFading ? '0' : '24px',
              paddingBottom: celebrationFading ? '0' : '24px',
              transition: 'opacity 1200ms ease-in-out, transform 1200ms ease-in-out, max-height 1200ms ease-in-out, padding 1200ms ease-in-out',
              willChange: celebrationFading ? 'opacity, transform, max-height' : 'auto',
            }}
          >
            {/* Pulsing success message */}
            <div className="relative z-10 text-center space-y-3">
              <div className="animate-celebration-pulse-once">
                <div
                  className="text-4xl mb-2 inline-block"
                  style={{
                    filter: 'hue-rotate(240deg) saturate(0.7) brightness(0.9)',
                  }}
                >
                  🎉
                </div>
                <h2 className="text-2xl md:text-3xl font-display text-white font-bold">
                  Your video is ready!
                </h2>
                <p className="text-sm text-vc-text-secondary">
                  Composition complete • Ready to share
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Action buttons - between video player and clip generation */}
        {composedVideoUrl && (
          <div className="w-full flex justify-center items-center gap-4 py-4">
            <VCButton
              onClick={() => {
                const shareUrl = `${window.location.origin}/?songId=${songDetails.id}`
                // Try to copy to clipboard (gracefully fail if it doesn't work)
                if (navigator.clipboard && navigator.clipboard.writeText) {
                  navigator.clipboard.writeText(shareUrl).catch(() => {
                    // Gracefully fail - do nothing
                  })
                }
                // Open in new tab
                window.open(shareUrl, '_blank', 'noopener,noreferrer')
              }}
              className="bg-vc-accent-primary/60 hover:bg-vc-accent-primary/70 border border-vc-accent-primary/40 text-white px-6 py-3 text-base font-medium"
            >
              Share project
            </VCButton>
            <VCButton
              onClick={() => {
                // Clear localStorage to prevent reloading the song
                localStorage.removeItem('vibecraft_current_song_id')
                // Force a full page reload to reset all state and show upload area
                window.location.href = '/'
              }}
              className="bg-vc-accent-primary/60 hover:bg-vc-accent-primary/70 border border-vc-accent-primary/40 text-white px-6 py-3 text-base font-medium"
            >
              Start new project
            </VCButton>
          </div>
        )}

        {/* Show ClipGenerationPanel if we have clips OR if there's an active job */}
        <ErrorBoundary FallbackComponent={SectionErrorFallback}>
          {(clipSummary ||
            (clipJobId &&
              (clipJobStatus === 'queued' || clipJobStatus === 'processing'))) && (
            <ClipGenerationPanel
              clipSummary={clipSummary}
              clipJobId={clipJobId}
              clipJobStatus={clipJobStatus}
              clipJobProgress={clipJobProgress}
              clipJobError={clipJobError}
              isComposing={isComposing}
              composeJobProgress={composeJobProgress}
              onCancel={onCancelClipJob}
              onCompose={onCompose}
              onPreviewClip={onPreviewClip}
              onRegenerateClip={onRegenerateClip}
              onRetryClip={onRetryClip}
              onRegenerateClips={onGenerateClips}
            />
          )}
        </ErrorBoundary>

        {/* Generate Clips Button - shown when no clips exist and no active job */}
        {(!clipSummary || clipSummary.totalClips === 0) &&
          !clipJobId &&
          clipJobStatus !== 'queued' &&
          clipJobStatus !== 'processing' && (
            <section className="flex flex-col items-center gap-3 py-2">
              <p className="text-sm text-vc-text-muted text-center">
                Kick off clip generation below!
              </p>
              <VCButton
                variant="primary"
                size="lg"
                onClick={onGenerateClips}
                className="bg-vc-accent-primary/60 hover:bg-vc-accent-primary/70 border border-vc-accent-primary/40"
              >
                Generate clips
              </VCButton>
            </section>
          )}

        <section className="space-y-2 pb-0">
          <div className="vc-label">Waveform</div>
          <WaveformDisplay
            waveform={waveformValues}
            beatTimes={analysisData.beatTimes}
            duration={songDetails.duration_sec || durationValue || 1}
            selectedStartSec={songDetails.selected_start_sec}
            selectedEndSec={songDetails.selected_end_sec}
          />
        </section>

        {sectionsEnabled && analysisData.sections.length > 0 && (
          <>
            <section className="space-y-2">
              <div className="vc-label">Song structure</div>
              <SongTimeline
                sections={sectionsWithDisplay}
                duration={durationValue || 1}
                onSelect={onSectionSelect}
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
                        audioUrl={audioUrl ?? undefined}
                        className="h-full bg-[rgba(12,12,18,0.78)]"
                      />
                    </div>
                  )
                })}
              </div>
            </section>
          </>
        )}
      </section>
    </>
  )
}
