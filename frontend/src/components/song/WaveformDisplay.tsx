import React from 'react'
import { clamp } from '../../utils/formatting'

interface WaveformDisplayProps {
  waveform: number[]
  beatTimes?: number[]
  duration: number
  selectedStartSec?: number | null
  selectedEndSec?: number | null
}

export const WaveformDisplay: React.FC<WaveformDisplayProps> = ({
  waveform,
  beatTimes,
  duration,
  selectedStartSec,
  selectedEndSec,
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
  const hasSelection =
    selectedStartSec != null &&
    selectedEndSec != null &&
    duration > 0 &&
    selectedStartSec >= 0 &&
    selectedEndSec > selectedStartSec &&
    selectedEndSec <= duration &&
    // Only show selection if it's not the full song
    !(selectedStartSec === 0 && Math.abs(selectedEndSec - duration) < 0.1)

  // Calculate which bars are outside the selected range
  const isBarInSelection = (idx: number) => {
    if (!hasSelection) return true // If no selection, show all bars normally
    // Each bar represents a time position - calculate the time position of this bar
    // The waveform array represents the full audio file, so we map index to time
    const barTime = (idx / bars.length) * duration
    // Check if this bar's time is within the selected range
    const inRange = barTime >= selectedStartSec! && barTime <= selectedEndSec!
    return inRange
  }

  return (
    <div className="relative w-full">
      {/* Selection indicator - shown above waveform when there's a selection */}
      {hasSelection && (
        <div className="relative mb-2 h-4 w-full">
          <div
            className="absolute h-full border-y border-vc-accent-primary/30 bg-vc-accent-primary/5"
            style={{
              left: `${(selectedStartSec! / duration) * 100}%`,
              width: `${((selectedEndSec! - selectedStartSec!) / duration) * 100}%`,
            }}
          >
            {/* Left marker */}
            <div
              className="absolute -left-0.5 top-0 h-full w-0.5 bg-vc-accent-primary/40"
              style={{ left: 0 }}
            />
            {/* Right marker */}
            <div
              className="absolute -right-0.5 top-0 h-full w-0.5 bg-vc-accent-primary/40"
              style={{ right: 0 }}
            />
          </div>
        </div>
      )}
      <div className="relative h-20 w-full overflow-hidden rounded-2xl border border-vc-border/40 bg-[rgba(12,12,18,0.55)]">
        <div className="absolute inset-0 bg-gradient-to-r from-[#6E6BFF33] via-[#FF6FF533] to-[#00C6C033]" />
        <div className="relative z-10 flex h-full items-center justify-between px-3">
          {bars.map((value, idx) => {
            const inSelection = isBarInSelection(idx)
            return (
              <span
                key={`wave-bar-${idx}-${value}`}
                className="w-[2px] rounded-full bg-white/85 transition-all duration-300"
                style={{
                  height: `${Math.max(16, value * 100)}%`,
                  opacity: inSelection
                    ? Math.max(0.25, value)
                    : Math.max(0.25, value) * 0.2, // Gray out non-selected bars
                  filter: inSelection ? 'none' : 'grayscale(100%) brightness(0.5)',
                }}
              />
            )
          })}
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
    </div>
  )
}
