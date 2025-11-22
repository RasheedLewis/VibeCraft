import React from 'react'
import clsx from 'clsx'
import { VCButton } from '../vibecraft'
import { MusicNoteIcon, UploadIcon, CheckIcon, ArrowRightIcon } from './Icons'
import {
  formatBytes,
  formatSeconds,
  getFileTypeLabel,
  clamp,
  formatBpm,
  formatMoodTags,
} from '../../utils/formatting'
import { AnalysisProgress } from './AnalysisProgress'
import { SummaryStat } from './SummaryStat'
import { WaveformPlaceholder } from '../song/WaveformPlaceholder'
import { MoodVectorMeter } from '../song/MoodVectorMeter'
import { AnalysisSectionRow } from '../song/AnalysisSectionRow'
import type { SongAnalysis, SongUploadResponse } from '../../types/song'
import type { MoodKind } from '../vibecraft/SectionMoodTag'
import { getSectionTitle } from '../../utils/sections'

type UploadStage = 'idle' | 'dragging' | 'uploading' | 'uploaded' | 'error'

interface UploadMetadata {
  fileName: string
  fileSize: number
  durationSeconds: number | null
}

interface UploadCardProps {
  stage: UploadStage
  metadata: UploadMetadata | null
  progress: number
  result: SongUploadResponse | null
  analysisState: 'idle' | 'queued' | 'processing' | 'completed' | 'failed'
  analysisProgress: number
  analysisError: string | null
  analysisData: SongAnalysis | null
  isFetchingAnalysis: boolean
  summaryMoodKind: MoodKind
  // NOTE: Sections are NOT implemented in the backend right now - making optional
  lyricsBySection?: Map<string, string>
  onFileSelect: () => void
  onReset: () => void
  onGenerateClips: () => void
}

export const UploadCard: React.FC<UploadCardProps> = ({
  stage,
  metadata,
  progress,
  result,
  analysisState,
  analysisProgress,
  analysisError,
  analysisData,
  isFetchingAnalysis,
  summaryMoodKind,
  lyricsBySection,
  onFileSelect,
  onReset,
  onGenerateClips,
}) => {
  if (stage === 'idle' || stage === 'dragging') {
    return (
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
            onClick={onFileSelect}
          >
            Choose a track
          </VCButton>
        </div>
      </div>
    )
  }

  if (stage === 'uploading') {
    return (
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
            <VCButton variant="ghost" onClick={onReset}>
              Cancel
            </VCButton>
          </div>
        </div>
      </div>
    )
  }

  if (stage === 'uploaded') {
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
                We'll listen for tempo, sections, lyrics, and mood to set up your visual
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

          <WaveformPlaceholder
            isAnimating={analysisState !== 'idle' && analysisState !== 'completed'}
          />

          {analysisState !== 'idle' && (
            <AnalysisProgress
              status={analysisState}
              progress={progressValue}
              error={analysisError}
              isFetching={isFetchingAnalysis && !analysisData}
            />
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
                      lyric={lyricsBySection?.get(section.id) ?? undefined}
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
              <VCButton variant="ghost" onClick={onReset}>
                Upload another track
              </VCButton>
              {analysisData ? (
                <VCButton
                  variant="primary"
                  iconRight={<ArrowRightIcon />}
                  onClick={onGenerateClips}
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

  return null
}
