import React from 'react'
import clsx from 'clsx'

import { VCCard } from './VCCard'
import { VCButton } from './VCButton'

interface VideoPreviewCardProps {
  thumbnailUrl?: string
  videoUrl?: string
  label: string
  onUseInFull?: () => void
  className?: string
}

export const VideoPreviewCard: React.FC<VideoPreviewCardProps> = ({
  thumbnailUrl,
  videoUrl,
  label,
  onUseInFull,
  className,
}) => (
  <VCCard className={clsx('flex flex-col gap-4', className)}>
    <div className="text-xs uppercase tracking-[0.16em] text-vc-text-muted">
      Section Video
    </div>
    <div className="relative aspect-video overflow-hidden rounded-md border border-vc-border bg-black/60">
      {videoUrl ? (
        <video src={videoUrl} className="h-full w-full object-cover" controls />
      ) : thumbnailUrl ? (
        <img src={thumbnailUrl} alt={label} className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full w-full items-center justify-center text-xs text-vc-text-muted">
          No video yet
        </div>
      )}
      <div className="pointer-events-none absolute inset-x-0 top-0 flex items-start justify-between px-3 py-3">
        <span className="rounded-md bg-black/60 px-2 py-1 text-xs font-medium text-white backdrop-blur-sm">
          {label}
        </span>
      </div>
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/60 via-transparent" />
    </div>
    {videoUrl && onUseInFull && (
      <VCButton variant="secondary" onClick={onUseInFull}>
        Use in full music video
      </VCButton>
    )}
  </VCCard>
)
