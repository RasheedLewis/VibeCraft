import React from 'react'

import { VCBadge } from './VCBadge'

export type MoodKind = 'chill' | 'energetic' | 'dark' | 'uplifting'

interface SectionMoodTagProps {
  mood: MoodKind
}

const moodLabel: Record<MoodKind, string> = {
  chill: 'Chill / Lofi',
  energetic: 'High Energy',
  dark: 'Moody',
  uplifting: 'Uplifting',
}

const moodTone: Record<MoodKind, Parameters<typeof VCBadge>[0]['tone']> = {
  chill: 'default',
  energetic: 'success',
  dark: 'danger',
  uplifting: 'warning',
}

export const SectionMoodTag: React.FC<SectionMoodTagProps> = ({ mood }) => (
  <VCBadge tone={moodTone[mood]}>{moodLabel[mood]}</VCBadge>
)
