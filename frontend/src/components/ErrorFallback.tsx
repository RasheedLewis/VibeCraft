import { VCButton } from './vibecraft'

interface ErrorFallbackProps {
  error: Error
  resetErrorBoundary: () => void
}

export function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  const isDev = import.meta.env.DEV

  return (
    <div className="min-h-screen flex items-center justify-center bg-vc-surface-primary p-4">
      <div className="max-w-md w-full bg-vc-surface-secondary rounded-lg p-6 text-center">
        <h1 className="text-2xl font-bold text-vc-text-primary mb-4">
          Something went wrong
        </h1>
        <p className="text-vc-text-secondary mb-6">
          We encountered an unexpected error. Please try reloading the page.
        </p>
        {isDev && (
          <details className="mb-4 text-left">
            <summary className="cursor-pointer text-vc-text-muted">
              Error details (dev only)
            </summary>
            <pre className="mt-2 text-xs text-vc-text-muted overflow-auto">
              {error.message}
              {error.stack}
            </pre>
          </details>
        )}
        <div className="flex gap-3 justify-center">
          <VCButton onClick={resetErrorBoundary}>Reload Page</VCButton>
          <VCButton variant="ghost" onClick={() => (window.location.href = '/')}>
            Go Home
          </VCButton>
        </div>
      </div>
    </div>
  )
}
