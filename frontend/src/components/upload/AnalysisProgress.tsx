import React from 'react'
import clsx from 'clsx'

interface AnalysisProgressProps {
  status: 'idle' | 'queued' | 'processing' | 'completed' | 'failed'
  progress: number
  error?: string | null
  isFetching?: boolean
}

const formatProgressLabel = (status: string, progress: number) => {
  if (status === 'completed') return 'Analysis complete'
  if (status === 'failed') return 'Analysis failed'
  if (status === 'processing') return `Analyzing… ${Math.round(progress)}%`
  if (status === 'queued') return 'Queued for analysis'
  return 'Analyzing…'
}

export const AnalysisProgress: React.FC<AnalysisProgressProps> = ({
  status,
  progress,
  error,
  isFetching,
}) => {
  if (status === 'idle') return null

  const progressValue = status === 'completed' ? 100 : progress

  return (
    <div className="rounded-xl border border-vc-border/40 bg-[rgba(12,12,18,0.6)] px-5 py-4">
      <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.16em] text-vc-text-muted">
        <span>{formatProgressLabel(status, progressValue)}</span>
        <span>{status === 'completed' ? '100%' : `${Math.round(progressValue)}%`}</span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-[rgba(255,255,255,0.08)]">
        <div
          className={clsx(
            'h-full rounded-full bg-gradient-to-r from-vc-accent-primary via-vc-accent-secondary to-vc-accent-tertiary transition-all duration-500 motion-safe:animate-[gradientShift_2.4s_linear_infinite]',
            status === 'failed' &&
              'from-vc-state-error via-vc-state-error to-vc-state-error motion-safe:animate-none',
            status === 'completed' && 'motion-safe:animate-none',
          )}
          style={{
            width: `${status === 'completed' ? 100 : progressValue}%`,
          }}
        />
      </div>
      {error && <p className="mt-2 text-xs text-vc-state-error">{error}</p>}
      {status === 'completed' && isFetching && (
        <p className="mt-2 text-xs text-vc-text-muted">Loading analysis summary…</p>
      )}
    </div>
  )
}
