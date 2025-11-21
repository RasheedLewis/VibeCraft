import React from 'react'
import clsx from 'clsx'
import { VCCard, VCButton } from '../vibecraft'
import { ArrowRightIcon } from '../upload/Icons'
import { ClipStatusBadge } from './ClipStatusBadge'
import type { ClipGenerationSummary, SongClipStatus } from '../../types/song'
import { normalizeClipStatus } from '../../utils/status'
import {
  formatSeconds,
  formatDurationShort,
  formatTimeRange,
} from '../../utils/formatting'

interface ClipGenerationPanelProps {
  clipSummary: ClipGenerationSummary | null
  clipJobId: string | null
  clipJobStatus: 'idle' | 'queued' | 'processing' | 'completed' | 'failed'
  clipJobProgress: number
  clipJobError: string | null
  isComposing: boolean
  composeJobProgress: number
  onCancel: () => void
  onCompose: () => void
  onPreviewClip: (clip: SongClipStatus) => void
  onRegenerateClip: (clip: SongClipStatus) => void
  onRetryClip: (clip: SongClipStatus) => void
}

export const ClipGenerationPanel: React.FC<ClipGenerationPanelProps> = ({
  clipSummary,
  clipJobId,
  clipJobStatus,
  clipJobProgress,
  clipJobError,
  isComposing,
  composeJobProgress,
  onCancel,
  onCompose,
  onPreviewClip,
  onRegenerateClip,
  onRetryClip,
}) => {
  // Show panel if we have clips OR if there's an active job (even if clips haven't been planned yet)
  const hasActiveJob =
    clipJobId != null && (clipJobStatus === 'queued' || clipJobStatus === 'processing')

  // If we have clips, always show the real UI (even if job is still active)
  const hasClips = clipSummary && clipSummary.totalClips > 0

  if (!hasClips && !hasActiveJob) {
    return null
  }

  // If no clips yet but there's an active job, show a simplified "preparing" version
  // This should only show briefly while clips are being planned
  if (!hasClips && hasActiveJob) {
    return (
      <section className="space-y-3">
        <div className="vc-label">Clip generation</div>
        <VCCard className="space-y-4 bg-[rgba(12,12,18,0.8)] p-5">
          <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
            <div>
              <h3 className="text-sm font-medium text-white">
                {clipJobStatus === 'queued'
                  ? 'Queuing clip generation…'
                  : 'Starting clip generation…'}
              </h3>
              <p className="text-xs text-vc-text-muted">
                {clipJobStatus === 'queued'
                  ? 'Preparing to generate video clips'
                  : 'Enqueuing video generation jobs for each clip'}
              </p>
            </div>
          </div>

          {/* Indeterminate progress indicator - animated gradient */}
          <div className="relative h-2 overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-vc-accent-primary/60 to-transparent animate-pulse" />
            <div
              className="absolute left-0 top-0 h-full w-1/3 rounded-full bg-gradient-to-r from-vc-accent-primary via-vc-accent-secondary to-vc-accent-tertiary"
              style={{
                animation: 'slide-indeterminate 1.5s ease-in-out infinite',
              }}
            />
          </div>
          <style>{`
            @keyframes slide-indeterminate {
              0% {
                transform: translateX(-100%);
              }
              100% {
                transform: translateX(400%);
              }
            }
          `}</style>

          {clipJobError && <p className="text-xs text-vc-state-error">{clipJobError}</p>}
        </VCCard>
      </section>
    )
  }

  // From here on, we have clips - show the full UI with all sections
  if (!clipSummary) {
    // This shouldn't happen if hasClips is true, but guard against it
    return null
  }

  const sortedClips = [...clipSummary.clips].sort((a, b) => a.clipIndex - b.clipIndex)
  const processingClip = sortedClips.find(
    (clip) => normalizeClipStatus(clip.status) === 'processing',
  )
  const queuedClip = sortedClips.find(
    (clip) => normalizeClipStatus(clip.status) === 'queued',
  )
  const completedClip = [...sortedClips]
    .reverse()
    .find((clip) => normalizeClipStatus(clip.status) === 'completed')
  const referenceClip = processingClip ?? queuedClip ?? completedClip ?? sortedClips[0]

  const referenceIndex = referenceClip
    ? sortedClips.findIndex((clip) => clip.id === referenceClip.id)
    : -1
  const total = clipSummary.totalClips
  const completed = Math.min(clipSummary.completedClips, total)
  const countsProgress = total > 0 ? (completed / total) * 100 : 0
  const progressValue =
    clipJobStatus === 'completed' ? 100 : Math.max(countsProgress, clipJobProgress)
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

  const hasComposedVideo = Boolean(clipSummary.composedVideoUrl)
  const composeDisabled =
    total === 0 ||
    completed < total ||
    clipJobStatus === 'failed' ||
    isComposing ||
    hasComposedVideo
  const cancelDisabled =
    !clipJobId || clipJobStatus === 'completed' || clipJobStatus === 'failed'
  const composeButtonLabel = isComposing
    ? 'Composing…'
    : hasComposedVideo
      ? 'Composed'
      : 'Compose when done'

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

        {isComposing && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.16em] text-vc-text-muted">
              <span>Composing video…</span>
              <span>{Math.round(composeJobProgress)}%</span>
            </div>
            <div className="relative h-2 overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
              <div
                className={clsx(
                  'absolute left-0 top-0 h-full rounded-full bg-gradient-to-r from-vc-accent-primary via-vc-accent-secondary to-vc-accent-tertiary transition-all duration-500',
                  'vc-gradient-shift-animate',
                )}
                style={{
                  width: `${Math.min(100, Math.max(2, composeJobProgress))}%`,
                }}
              />
            </div>
          </div>
        )}

        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
          <div className="text-xs text-vc-text-muted">
            {isComposing
              ? 'Composition is running in the background.'
              : clipJobStatus === 'failed' && !clipJobError
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
              onClick={onCancel}
              disabled={cancelDisabled}
            >
              Cancel
            </VCButton>
            <VCButton
              variant="primary"
              size="sm"
              iconRight={<ArrowRightIcon />}
              disabled={composeDisabled}
              onClick={onCompose}
            >
              {composeButtonLabel}
            </VCButton>
          </div>
        </div>
      </VCCard>

      {/* Clip Queue section - always show when we have clips */}
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
                          onClick={() => onPreviewClip(clip)}
                          disabled={!clip.videoUrl}
                        >
                          Preview
                        </VCButton>
                        <VCButton
                          variant="ghost"
                          size="sm"
                          onClick={() => onRegenerateClip(clip)}
                        >
                          Regenerate
                        </VCButton>
                      </>
                    )}
                    {normalizedStatus === 'failed' && (
                      <VCButton
                        variant="secondary"
                        size="sm"
                        onClick={() => onRetryClip(clip)}
                      >
                        Retry
                      </VCButton>
                    )}
                    {normalizedStatus === 'canceled' && (
                      <span className="text-vc-text-muted">Clip canceled</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Completed Clips section - always show */}
      <div className="space-y-2">
        <div className="vc-label">Completed clips</div>
        {clipSummary.completedClips === 0 ? (
          <VCCard className="border-dashed border-vc-border/30 bg-[rgba(12,12,18,0.65)] p-6 text-center text-xs text-vc-text-muted">
            Completed clips will appear here once generation finishes.
          </VCCard>
        ) : (
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {sortedClips
              .filter((clip) => normalizeClipStatus(clip.status) === 'completed')
              .map((clip) => (
                <button
                  key={`thumb-${clip.id}`}
                  type="button"
                  onClick={() => onPreviewClip(clip)}
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
                      {formatDurationShort(clip.durationSec)} • {clip.numFrames} frames •{' '}
                      {clip.fps} fps
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
}
