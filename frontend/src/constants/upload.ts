export const ACCEPTED_MIME_TYPES = [
  'audio/mpeg',
  'audio/mp3',
  'audio/wav',
  'audio/wave',
  'audio/vnd.wave',
  'audio/x-wav',
  'audio/ogg',
  'audio/webm',
  'audio/flac',
  'audio/x-flac',
  'audio/aac',
  'audio/mp4',
  'audio/m4a',
  'audio/x-m4a',
] as const

export const MAX_DURATION_SECONDS = 7 * 60

export const SECTION_TYPE_LABELS: Record<string, string> = {
  intro: 'Intro',
  verse: 'Verse',
  pre_chorus: 'Pre-chorus',
  chorus: 'Chorus',
  bridge: 'Bridge',
  drop: 'Drop',
  solo: 'Solo',
  outro: 'Outro',
  other: 'Section',
}

export const SECTION_COLORS: Record<string, string> = {
  intro: 'rgba(110, 107, 255, 0.32)',
  verse: 'rgba(130, 89, 255, 0.42)',
  pre_chorus: 'rgba(112, 84, 255, 0.48)',
  chorus: 'rgba(255, 111, 245, 0.55)',
  bridge: 'rgba(0, 198, 192, 0.45)',
  drop: 'rgba(255, 189, 89, 0.5)',
  solo: 'rgba(89, 255, 214, 0.4)',
  outro: 'rgba(90, 105, 255, 0.28)',
  other: 'rgba(120, 120, 180, 0.35)',
}

export const WAVEFORM_BASE_PATTERN = [
  0.25, 0.6, 0.85, 0.4, 0.75, 0.35, 0.9, 0.5, 0.65, 0.3,
]
export const WAVEFORM_BARS = Array.from({ length: 72 }, (_, index) => {
  const patternValue = WAVEFORM_BASE_PATTERN[index % WAVEFORM_BASE_PATTERN.length]
  const pulseBoost =
    ((index + 3) % 11 === 0 ? 0.15 : 0) + ((index + 7) % 17 === 0 ? 0.1 : 0)
  return Math.min(1, patternValue + pulseBoost)
})
