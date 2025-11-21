import type { SongSection } from '../types/song'
import type { MoodKind } from '../components/vibecraft/SectionMoodTag'
import { SECTION_TYPE_LABELS } from '../constants/upload'

export const getSectionTitle = (section: SongSection, index: number) => {
  const label = SECTION_TYPE_LABELS[section.type] ?? `Section`
  return `${label} ${index + 1}`
}

export const buildSectionsWithDisplayNames = (
  sections: SongSection[],
): Array<
  SongSection & {
    displayName: string
    typeSoft: string | null
    rawLabel: number | null
  }
> => {
  const counts: Record<string, number> = {}
  return sections.map((section) => {
    const baseType = section.typeSoft ?? section.type

    const label =
      (section.displayName && section.displayName.split(' ')[0]) ??
      SECTION_TYPE_LABELS[section.type] ??
      'Section'

    const key = baseType ?? section.type
    const nextCount = (counts[key] ?? 0) + 1
    counts[key] = nextCount

    const displayName =
      section.displayName ??
      (key === 'intro_like' || key === 'intro'
        ? 'Intro'
        : key === 'outro_like' || key === 'outro'
          ? 'Outro'
          : key === 'bridge_like' || key === 'bridge'
            ? 'Bridge'
            : `${label} ${nextCount}`)

    return {
      ...section,
      typeSoft: section.typeSoft ?? null,
      rawLabel: section.rawLabel ?? null,
      displayName,
    }
  })
}

export const mapMoodToMoodKind = (mood: string): MoodKind => {
  const normalized = mood?.toLowerCase() ?? ''
  if (normalized.includes('energy') || normalized.includes('energetic'))
    return 'energetic'
  if (
    normalized.includes('dark') ||
    normalized.includes('moody') ||
    normalized.includes('intense')
  )
    return 'dark'
  if (
    normalized.includes('uplift') ||
    normalized.includes('happy') ||
    normalized.includes('bright') ||
    normalized.includes('positive')
  )
    return 'uplifting'
  return 'chill'
}
