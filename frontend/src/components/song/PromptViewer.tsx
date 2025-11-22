import React, { useState } from 'react'
import { VCCard } from '../vibecraft'

interface PromptViewerProps {
  prompt: string | null | undefined
  model?: string
  trigger: (onClick: () => void) => React.ReactNode
}

const DEFAULT_MODEL = 'minimax/hailuo-2.3'

export const PromptViewer: React.FC<PromptViewerProps> = ({
  prompt,
  model = DEFAULT_MODEL,
  trigger,
}) => {
  const [isOpen, setIsOpen] = useState(false)

  if (!prompt) {
    return null
  }

  const promptData = {
    prompt,
    model,
    timestamp: new Date().toISOString(),
  }

  const formattedJson = JSON.stringify(promptData, null, 2)

  return (
    <>
      {trigger(() => setIsOpen(true))}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4"
          onClick={() => setIsOpen(false)}
        >
          <VCCard
            className="max-h-[90vh] w-full max-w-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-vc-border p-4">
              <div>
                <h3 className="text-lg font-semibold text-white">Prompt Details</h3>
                <p className="text-sm text-vc-text-muted mt-1">Model: {model}</p>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                className="text-vc-text-muted hover:text-white transition-colors"
                aria-label="Close"
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
            <div className="overflow-auto p-4 bg-[rgba(0,0,0,0.3)]">
              <pre className="text-xs text-vc-text-secondary font-mono whitespace-pre-wrap break-words">
                {formattedJson}
              </pre>
            </div>
            <div className="border-t border-vc-border p-4 flex justify-end gap-2">
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(formattedJson)
                }}
                className="px-4 py-2 text-sm bg-vc-accent-primary/20 text-vc-accent-primary rounded hover:bg-vc-accent-primary/30 transition-colors"
              >
                Copy JSON
              </button>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(prompt)
                }}
                className="px-4 py-2 text-sm bg-vc-accent-primary/20 text-vc-accent-primary rounded hover:bg-vc-accent-primary/30 transition-colors"
              >
                Copy Prompt
              </button>
            </div>
          </VCCard>
        </div>
      )}
    </>
  )
}
