import React from 'react'
import { WAVEFORM_BARS } from '../../constants/upload'

interface WaveformPlaceholderProps {
  /** Whether to show the shimmer animation. Only true when analysis is running. */
  isAnimating?: boolean
}

export const WaveformPlaceholder: React.FC<WaveformPlaceholderProps> = ({
  isAnimating = false,
}) => (
  <div className="relative flex h-20 w-full items-center overflow-hidden rounded-2xl border border-vc-border/50 bg-[rgba(255,255,255,0.03)]">
    {isAnimating && <div className="absolute inset-0 vc-shimmer opacity-70" />}
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
