export type SongSectionType =
  | 'intro'
  | 'verse'
  | 'pre_chorus'
  | 'chorus'
  | 'bridge'
  | 'drop'
  | 'solo'
  | 'outro'
  | 'other'

export interface SongSection {
  id: string
  type: SongSectionType
  startSec: number
  endSec: number
  confidence: number
  repetitionGroup?: string
}

export interface MoodVector {
  energy: number
  valence: number
  danceability: number
  tension: number
}

export interface SectionLyrics {
  sectionId: string
  startSec: number
  endSec: number
  text: string
}

export interface SongAnalysis {
  durationSec: number
  bpm?: number
  sections: SongSection[]
  moodPrimary: string
  moodTags: string[]
  moodVector: MoodVector
  primaryGenre?: string
  subGenres?: string[]
  lyricsAvailable: boolean
  sectionLyrics?: SectionLyrics[]
}
