import React, { useState } from 'react'

import {
  VCAppShell,
  VCButton,
  GenerationProgress,
  SectionCard,
  TemplatePill,
  VideoPreviewCard,
  Attribution,
} from '../components/vibecraft'

const templates = [
  {
    id: 'abstract',
    label: 'Abstract Visualizer',
    description: 'Floating shapes • Violet & neon gradients',
  },
  {
    id: 'cozy',
    label: 'Mood Environment',
    description: 'Foggy forest • Dream pop ambience',
  },
  {
    id: 'city',
    label: 'Neon City Run',
    description: 'Hyperlapse skyline • Vaporwave glow',
  },
] as const

const demoSections = [
  {
    name: 'Intro',
    startSec: 0,
    endSec: 18,
    mood: 'chill' as const,
    lyricSnippet: 'Floating through the city lights…',
    hasVideo: false,
  },
  {
    name: 'Verse 1',
    startSec: 18,
    endSec: 45,
    mood: 'dark' as const,
    lyricSnippet: 'Echoes in the stairwell call your name…',
    hasVideo: true,
  },
  {
    name: 'Chorus',
    startSec: 45,
    endSec: 75,
    mood: 'energetic' as const,
    lyricSnippet: 'Turn the volume up, don’t let go…',
    hasVideo: true,
  },
] as const

export const SongProfilePage: React.FC = () => {
  const [stage, setStage] = useState<'idle' | 'analyzing' | 'generatingSections'>(
    'analyzing',
  )
  const [selectedTemplate, setSelectedTemplate] =
    useState<(typeof templates)[number]['id']>('abstract')

  return (
    <VCAppShell
      sidebar={
        <div className="space-y-4 px-4 py-6 text-sm text-vc-text-secondary">
          <p className="uppercase tracking-[0.16em] text-xs text-vc-text-muted">
            Project
          </p>
          <div className="space-y-2">
            <button className="w-full rounded-md border border-vc-border bg-vc-surface px-3 py-2 text-left text-white">
              Aurora Skies EP
            </button>
            <button className="w-full rounded-md border border-transparent px-3 py-2 text-left hover:border-vc-border">
              Demo Gallery
            </button>
          </div>
        </div>
      }
      header={
        <>
          <div>
            <p className="text-xs uppercase tracking-[0.12em] text-vc-text-muted">
              Song Profile
            </p>
            <h1 className="font-display text-lg text-white">“Aurora Skies”</h1>
          </div>
          <VCButton
            variant="secondary"
            size="sm"
            onClick={() =>
              setStage((prev) =>
                prev === 'analyzing' ? 'generatingSections' : 'analyzing',
              )
            }
          >
            Toggle Stage
          </VCButton>
        </>
      }
    >
      <div className="space-y-6">
        <GenerationProgress
          stage={stage === 'generatingSections' ? 'generatingSections' : 'analyzing'}
        />

        <section className="rounded-lg border border-vc-border bg-vc-surface/60 p-4 shadow-vc1 backdrop-blur">
          <header className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.12em] text-vc-text-muted">
                Visual Template
              </p>
              <h2 className="font-display text-base text-white">
                Choose how this song should feel
              </h2>
            </div>
            <VCButton variant="primary" size="sm">
              Generate full video
            </VCButton>
          </header>
          <div className="mt-4 flex flex-wrap gap-3">
            {templates.map((template) => (
              <TemplatePill
                key={template.id}
                label={template.label}
                description={template.description}
                selected={template.id === selectedTemplate}
                onClick={() => setSelectedTemplate(template.id)}
              />
            ))}
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          {demoSections.map((section) => (
            <SectionCard
              key={section.name}
              {...section}
              onGenerate={() => setStage('generatingSections')}
              onRegenerate={() => setStage('generatingSections')}
              onUseInFull={() => setStage('generatingSections')}
            />
          ))}
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <VideoPreviewCard
            label="Chorus - Take 02"
            videoUrl=""
            thumbnailUrl="https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=800&q=80"
          />
          <VideoPreviewCard
            label="Verse 1 - Approved"
            videoUrl="https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
            onUseInFull={() => {}}
          />
        </section>

        {/* Attribution - only shows if attribution text exists */}
        <Attribution text='"Electrodoodle" by Kevin MacLeod (Incompetech) • CC BY 4.0' />
      </div>
    </VCAppShell>
  )
}
