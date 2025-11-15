import React from 'react'
import clsx from 'clsx'

type GenerationStage =
  | 'idle'
  | 'uploading'
  | 'analyzing'
  | 'generatingSections'
  | 'compositing'
  | 'done'

const stageLabel: Record<GenerationStage, string> = {
  idle: 'Ready when you are.',
  uploading: 'Uploading your track…',
  analyzing: 'Listening for structure, mood, and lyrics…',
  generatingSections: 'Generating section videos…',
  compositing: 'Compositing your full music video…',
  done: 'Your video is ready!',
}

interface GenerationProgressProps {
  stage: GenerationStage
}

export const GenerationProgress: React.FC<GenerationProgressProps> = ({ stage }) => {
  const active = stage !== 'idle' && stage !== 'done'

  return (
    <div className="vc-status-panel">
      <div>
        <p className="mb-1 text-xs uppercase tracking-[0.16em] text-vc-text-muted">
          Status
        </p>
        <p className="text-sm text-white">{stageLabel[stage]}</p>
      </div>
      <div className="vc-pulse-bars">
        {[0, 1, 2].map((index) => (
          <span
            key={index}
            className={clsx(
              'vc-pulse-bar',
              active
                ? [
                    'vc-pulse-animate',
                    'vc-pulse-animate-delay-1',
                    'vc-pulse-animate-delay-2',
                  ][index]
                : 'opacity-60',
            )}
            style={{
              height: active ? '100%' : '40%',
            }}
          />
        ))}
      </div>
    </div>
  )
}
