import React from 'react'
import { clamp } from '../../utils/formatting'

interface WaveformDisplayProps {
  waveform: number[]
  beatTimes?: number[]
  duration: number
}

export const WaveformDisplay: React.FC<WaveformDisplayProps> = ({
  waveform,
  beatTimes,
  duration,
}) => {
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
