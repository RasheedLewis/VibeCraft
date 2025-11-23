import React from 'react'
import { VCButton } from './vibecraft'

interface ErrorFallbackProps {
  error: Error
  resetErrorBoundary: () => void
}

export function SectionErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  return (
    <div className="rounded-lg border border-vc-state-error/50 bg-vc-state-error/10 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <p className="text-sm font-medium text-vc-state-error mb-1">
            This section encountered an error
          </p>
          <p className="text-xs text-vc-text-secondary">{error.message}</p>
        </div>
        <VCButton size="sm" variant="ghost" onClick={resetErrorBoundary}>
          Retry
        </VCButton>
      </div>
    </div>
  )
}

