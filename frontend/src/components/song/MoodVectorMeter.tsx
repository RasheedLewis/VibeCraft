import React from 'react'
import type { MoodVector } from '../../types/song'
import { clamp } from '../../utils/formatting'

interface MoodVectorMeterProps {
  moodVector: MoodVector
}

export const MoodVectorMeter: React.FC<MoodVectorMeterProps> = ({ moodVector }) => {
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
