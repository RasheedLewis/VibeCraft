import React from 'react'
import clsx from 'clsx'

import { VCCard } from './VCCard'
import { VCButton } from './VCButton'
import { SectionMoodTag } from './SectionMoodTag'
import type { MoodKind } from './SectionMoodTag'

export interface SectionCardProps {
  name: string
  startSec: number
  endSec: number
  mood: MoodKind
  lyricSnippet?: string
  hasVideo?: boolean
  onGenerate?: () => void
  onRegenerate?: () => void
  onUseInFull?: () => void
  className?: string
}

const formatTime = (sec: number) => {
  const minutes = Math.floor(sec / 60)
  const seconds = Math.floor(sec % 60)
    .toString()
    .padStart(2, '0')
  return `${minutes}:${seconds}`
}

export const SectionCard: React.FC<SectionCardProps> = ({
  name,
  startSec,
  endSec,
  mood,
  lyricSnippet,
  hasVideo,
  onGenerate,
  onRegenerate,
  onUseInFull,
  className,
}) => (
  <VCCard className={clsx('vc-section-card', className)}>
    <div className="vc-card-header">
      <div>
        <h3 className="vc-card-title">{name}</h3>
        <p className="vc-card-subtitle">
          {formatTime(startSec)} – {formatTime(endSec)}
        </p>
      </div>
      <SectionMoodTag mood={mood} />
    </div>

    {lyricSnippet && (
      <p className="border-l border-vc-border pl-3 text-xs italic text-vc-text-secondary">
        “{lyricSnippet}”
      </p>
    )}

    <div className="mt-4 flex flex-wrap items-center gap-2">
      {!hasVideo && (
        <VCButton size="sm" onClick={onGenerate}>
          Generate section video
        </VCButton>
      )}

      {hasVideo && (
        <>
          <VCButton variant="secondary" size="sm" onClick={onRegenerate}>
            Regenerate
          </VCButton>
          <VCButton size="sm" onClick={onUseInFull}>
            Use in full video
          </VCButton>
        </>
      )}
    </div>
  </VCCard>
)
