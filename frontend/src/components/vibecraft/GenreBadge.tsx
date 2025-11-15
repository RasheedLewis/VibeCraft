import React from 'react'

interface GenreBadgeProps {
  genre: string
  confidence?: number
  size?: 'sm' | 'md'
}

/**
 * Badge component for displaying genre
 */
export const GenreBadge: React.FC<GenreBadgeProps> = ({
  genre,
  confidence,
  size = 'sm',
}) => {
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-1' : 'text-sm px-3 py-1.5'

  return (
    <span
      className={`inline-flex items-center rounded-md border border-vc-border bg-vc-surface/60 px-2 py-1 text-xs font-medium text-vc-text-secondary ${sizeClasses}`}
    >
      {genre}
      {confidence !== undefined && (
        <span className="ml-1.5 text-vc-text-muted">
          ({Math.round(confidence * 100)}%)
        </span>
      )}
    </span>
  )
}
