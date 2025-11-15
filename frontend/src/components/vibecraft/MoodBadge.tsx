import React from 'react'

interface MoodBadgeProps {
  mood: string
  size?: 'sm' | 'md'
}

/**
 * Badge component for displaying mood tags
 */
export const MoodBadge: React.FC<MoodBadgeProps> = ({ mood, size = 'sm' }) => {
  const sizeClasses = size === 'sm' ? 'text-xs px-2 py-1' : 'text-sm px-3 py-1.5'

  // Color mapping for different moods
  const moodColors: Record<string, string> = {
    energetic: 'bg-vc-accent/20 border-vc-accent/40 text-vc-accent',
    upbeat: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400',
    happy: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400',
    calm: 'bg-blue-500/20 border-blue-500/40 text-blue-400',
    relaxed: 'bg-green-500/20 border-green-500/40 text-green-400',
    melancholic: 'bg-purple-500/20 border-purple-500/40 text-purple-400',
    sad: 'bg-blue-500/20 border-blue-500/40 text-blue-400',
    intense: 'bg-red-500/20 border-red-500/40 text-red-400',
    danceable: 'bg-pink-500/20 border-pink-500/40 text-pink-400',
    ambient: 'bg-cyan-500/20 border-cyan-500/40 text-cyan-400',
  }

  const colorClass =
    moodColors[mood.toLowerCase()] ||
    'bg-vc-surface/60 border-vc-border text-vc-text-secondary'

  return (
    <span
      className={`inline-flex items-center rounded-md border ${colorClass} ${sizeClasses} font-medium`}
    >
      {mood}
    </span>
  )
}
