import React from 'react'
import type { SongSection } from '../../types/song'
import { SECTION_COLORS } from '../../constants/upload'
import { formatSeconds } from '../../utils/formatting'
import { clamp } from '../../utils/formatting'

interface SongTimelineProps {
  sections: Array<SongSection & { displayName: string }>
  duration: number
  onSelect?: (sectionId: string) => void
}

export const SongTimeline: React.FC<SongTimelineProps> = ({
  sections,
  duration,
  onSelect,
}) => {
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
