import React from 'react'
import clsx from 'clsx'

export interface VideoTypeSelectorProps {
  onSelect: (videoType: 'full_length' | 'short_form') => void
  selectedType?: 'full_length' | 'short_form' | null
  className?: string
}

export const VideoTypeSelector: React.FC<VideoTypeSelectorProps> = ({
  onSelect,
  selectedType,
  className,
}) => {
  return (
    <div className={clsx('space-y-4', className)}>
      <div className="vc-label">Choose Your Video Format</div>
      <p className="text-sm text-vc-text-secondary">
        Select the format that best fits your needs.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Full-Length Option */}
        <button
          onClick={() => onSelect('full_length')}
          className={clsx(
            'group relative rounded-2xl border-2 p-6 text-left transition-all',
            'hover:border-vc-accent-primary/50 hover:bg-vc-surface-primary/50',
            selectedType === 'full_length'
              ? 'border-vc-accent-primary bg-vc-accent-primary/10'
              : 'border-vc-border bg-vc-surface-primary',
          )}
        >
          <div className="flex items-start gap-4">
            <div
              className={clsx(
                'flex h-12 w-12 shrink-0 items-center justify-center rounded-full',
                'border-2 transition-colors',
                selectedType === 'full_length'
                  ? 'border-vc-accent-primary bg-vc-accent-primary/20'
                  : 'border-vc-border bg-vc-surface-primary',
              )}
            >
              {selectedType === 'full_length' && (
                <svg
                  className="h-6 w-6 text-vc-accent-primary"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                </svg>
              )}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-vc-text-primary mb-1">
                Full-Length Video
              </h3>
              <p className="text-sm text-vc-text-secondary">
                Complete video covering your entire track. Perfect for music videos, full
                releases, and comprehensive visual experiences.
              </p>
            </div>
          </div>
        </button>

        {/* Short-Form Option */}
        <button
          onClick={() => onSelect('short_form')}
          className={clsx(
            'group relative rounded-2xl border-2 p-6 text-left transition-all',
            'hover:border-vc-accent-primary/50 hover:bg-vc-surface-primary/50',
            selectedType === 'short_form'
              ? 'border-vc-accent-primary bg-vc-accent-primary/10'
              : 'border-vc-border bg-vc-surface-primary',
          )}
        >
          <div className="flex items-start gap-4">
            <div
              className={clsx(
                'flex h-12 w-12 shrink-0 items-center justify-center rounded-full',
                'border-2 transition-colors',
                selectedType === 'short_form'
                  ? 'border-vc-accent-primary bg-vc-accent-primary/20'
                  : 'border-vc-border bg-vc-surface-primary',
              )}
            >
              {selectedType === 'short_form' && (
                <svg
                  className="h-6 w-6 text-vc-accent-primary"
                  fill="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                </svg>
              )}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-vc-text-primary mb-1">
                30-Second Video
              </h3>
              <p className="text-sm text-vc-text-secondary">
                Optimized for short-form platforms. Select up to 30 seconds from your
                track for TikTok, Instagram Reels, and YouTube Shorts.
              </p>
            </div>
          </div>
        </button>
      </div>
    </div>
  )
}
