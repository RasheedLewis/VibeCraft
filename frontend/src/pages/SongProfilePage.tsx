import React, { useCallback, useEffect, useState } from 'react'

import {
  VCAppShell,
  VCButton,
  GenerationProgress,
  SectionCard,
  TemplatePill,
  VideoPreviewCard,
  Attribution,
  ThemeToggle,
} from '../components/vibecraft'
import { apiClient } from '../lib/apiClient'
import type {
  SectionVideoGenerateRequest,
  SectionVideoGenerateResponse,
  SectionVideoRead,
} from '../types/sectionVideo'

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
    id: 'section-1',
    name: 'Intro',
    startSec: 0,
    endSec: 18,
    mood: 'chill' as const,
    lyricSnippet: 'Floating through the city lights...',
  },
  {
    id: 'section-2',
    name: 'Verse 1',
    startSec: 18,
    endSec: 45,
    mood: 'dark' as const,
    lyricSnippet: 'Echoes in the stairwell call your name...',
  },
  {
    id: 'section-4',
    name: 'Chorus',
    startSec: 45,
    endSec: 75,
    mood: 'energetic' as const,
    lyricSnippet: "Turn the volume up, don't let go...",
  },
] as const

export const SongProfilePage: React.FC = () => {
  const [stage, setStage] = useState<'idle' | 'analyzing' | 'generatingSections'>(
    'analyzing',
  )
  const [selectedTemplate, setSelectedTemplate] =
    useState<(typeof templates)[number]['id']>('abstract')
  const [sectionVideos, setSectionVideos] = useState<Map<string, SectionVideoRead>>(
    new Map(),
  )
  const [, setGeneratingSections] = useState<Set<string>>(new Set())

  const fetchSectionVideo = useCallback(async (sectionId: string) => {
    try {
      const response = await apiClient.get<SectionVideoRead>(
        `/sections/${sectionId}/video`,
      )
      setSectionVideos((prev) => {
        const next = new Map(prev)
        next.set(sectionId, response.data)
        return next
      })
    } catch (error) {
      // Video doesn't exist yet, that's okay
      if ((error as { response?: { status?: number } }).response?.status !== 404) {
        console.error('Error fetching section video:', error)
      }
    }
  }, [])

  const generateSectionVideo = useCallback(
    async (sectionId: string) => {
      setGeneratingSections((prev) => new Set(prev).add(sectionId))
      setStage('generatingSections')

      try {
        const request: SectionVideoGenerateRequest = {
          sectionId,
          template: selectedTemplate,
        }
        const response = await apiClient.post<SectionVideoGenerateResponse>(
          `/sections/${sectionId}/generate`,
          request,
        )

        // Poll for completion (in production, use WebSocket or polling endpoint)
        if (response.data.status === 'completed') {
          await fetchSectionVideo(sectionId)
        } else {
          // Poll until completed
          const pollInterval = setInterval(async () => {
            try {
              await fetchSectionVideo(sectionId)
              const video = sectionVideos.get(sectionId)
              if (video?.status === 'completed' || video?.status === 'failed') {
                clearInterval(pollInterval)
                setGeneratingSections((prev) => {
                  const next = new Set(prev)
                  next.delete(sectionId)
                  return next
                })
              }
            } catch {
              // Keep polling
            }
          }, 3000) // Poll every 3 seconds

          // Stop polling after 5 minutes
          setTimeout(() => clearInterval(pollInterval), 5 * 60 * 1000)
        }
      } catch (error) {
        console.error('Error generating section video:', error)
        setGeneratingSections((prev) => {
          const next = new Set(prev)
          next.delete(sectionId)
          return next
        })
      }
    },
    [selectedTemplate, fetchSectionVideo, sectionVideos],
  )

  // Fetch existing videos on mount
  useEffect(() => {
    demoSections.forEach((section) => {
      fetchSectionVideo(section.id)
    })
  }, [fetchSectionVideo])

  return (
    <VCAppShell
      sidebar={
        <div className="space-y-4 px-4 py-6 text-sm text-vc-text-secondary">
          <p className="uppercase tracking-[0.16em] text-xs text-vc-text-muted">
            Project
          </p>
          <div className="space-y-2">
            <button className="w-full rounded-md border border-vc-border bg-vc-surface px-3 py-2 text-left text-vc-text-primary">
              Aurora Skies EP
            </button>
            <button className="w-full rounded-md border border-transparent px-3 py-2 text-left text-vc-text-primary hover:border-vc-border">
              Demo Gallery
            </button>
          </div>
        </div>
      }
      header={
        <div className="flex w-full items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.12em] text-vc-text-muted">
              Song Profile
            </p>
            <h1 className="font-display text-lg text-vc-text-primary">“Aurora Skies”</h1>
          </div>
          <div className="flex items-center gap-2">
            <ThemeToggle />
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
          </div>
        </div>
      }
    >
      <div className="space-y-6">
        <GenerationProgress
          stage={stage === 'generatingSections' ? 'generatingSections' : 'analyzing'}
        />

        <section className="vc-panel backdrop-blur p-4 space-y-3">
          <header className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.12em] text-vc-text-muted">
                Visual Template
              </p>
              <h2 className="font-display text-base text-vc-text-primary">
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
          {demoSections.map((section) => {
            const video = sectionVideos.get(section.id)
            const hasVideo = video?.status === 'completed' && !!video.videoUrl

            return (
              <SectionCard
                key={section.id}
                name={section.name}
                startSec={section.startSec}
                endSec={section.endSec}
                mood={section.mood}
                lyricSnippet={section.lyricSnippet}
                hasVideo={hasVideo}
                onGenerate={() => generateSectionVideo(section.id)}
                onRegenerate={() => generateSectionVideo(section.id)}
                onUseInFull={() => {}}
              />
            )
          })}
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          {demoSections
            .filter((section) => {
              const video = sectionVideos.get(section.id)
              return video?.status === 'completed' && video.videoUrl
            })
            .map((section) => {
              const video = sectionVideos.get(section.id)!
              return (
                <VideoPreviewCard
                  key={section.id}
                  label={`${section.name} - Generated`}
                  videoUrl={video.videoUrl}
                />
              )
            })}
        </section>

        {/* Attribution - only shows if attribution text exists */}
        <Attribution text='"Electrodoodle" by Kevin MacLeod (Incompetech) • CC BY 4.0' />
      </div>
    </VCAppShell>
  )
}
