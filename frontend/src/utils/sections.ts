import type { SongSection } from '../types/song'
import type { MoodKind } from '../components/vibecraft/SectionMoodTag'
import { SECTION_TYPE_LABELS } from '../constants/upload'

export const getSectionTitle = (section: SongSection, index: number) => {
  const label = SECTION_TYPE_LABELS[section.type] ?? `Section`
  return `${label} ${index + 1}`
}

export const buildSectionsWithDisplayNames = (
  sections: SongSection[],
): Array<SongSection & { displayName: string }> => {
  const counts: Record<string, number> = {}
  return sections.map((section) => {
    const label = SECTION_TYPE_LABELS[section.type] ?? 'Section'
    const nextCount = (counts[section.type] ?? 0) + 1
    counts[section.type] = nextCount

    const displayName =
      section.type === 'intro' || section.type === 'outro' || section.type === 'bridge'
        ? label
        : `${label} ${nextCount}`

    return { ...section, displayName }
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
