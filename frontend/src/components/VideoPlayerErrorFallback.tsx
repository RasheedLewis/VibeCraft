import React from 'react'
import { VCButton } from './vibecraft'

interface ErrorFallbackProps {
  error: Error
  resetErrorBoundary: () => void
}

export function VideoPlayerErrorFallback({
  error,
  resetErrorBoundary,
}: ErrorFallbackProps) {
  return (
    <div className="w-full aspect-video bg-black flex items-center justify-center rounded-lg border border-vc-state-error/50">
      <div className="text-center p-6">
        <p className="text-vc-state-error mb-2 font-medium">Video failed to load</p>
        <p className="text-vc-text-secondary text-sm mb-4">
          {error.message || 'Unable to play video'}
        </p>
        <VCButton size="sm" variant="ghost" onClick={resetErrorBoundary}>
          Retry
        </VCButton>
      </div>
    </div>
  )
}
