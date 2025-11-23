import React from 'react'

interface AttributionProps {
  text?: string
}

/**
 * Attribution component for displaying music credits
 * Only renders if attribution text is provided
 * Unobtrusive styling - small, muted text
 */
export const Attribution: React.FC<AttributionProps> = ({ text }) => {
  // Don't render if no attribution text
  if (!text) return null

  return (
    <div className="mt-6 border-t border-vc-border pt-4">
      <p className="text-xs text-vc-text-muted">Music: {text}</p>
    </div>
  )
}
