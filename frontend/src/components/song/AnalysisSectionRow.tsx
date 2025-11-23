import React from 'react'
import { VCCard } from '../vibecraft'
import { SectionMoodTag } from '../vibecraft'
import type { SongSection } from '../../types/song'
import type { MoodKind } from '../vibecraft/SectionMoodTag'
import { formatSeconds } from '../../utils/formatting'
import { clamp } from '../../utils/formatting'

interface AnalysisSectionRowProps {
  section: SongSection
  title: string
  mood: MoodKind
  lyric?: string
}

export const AnalysisSectionRow: React.FC<AnalysisSectionRowProps> = ({
  section,
  title,
  mood,
  lyric,
}) => (
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
        "{lyric}"
      </p>
    )}
  </VCCard>
)
