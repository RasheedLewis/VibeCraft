export interface SongUploadResponse {
  songId: string
  audioUrl: string
  s3Key: string
  status: 'uploaded' | 'processing' | 'failed' | string
}

export interface SongAnalysisJobResponse {
  jobId: string
  status: 'queued' | 'processing' | 'completed' | 'failed' | string
}

export interface JobStatusResponse {
  jobId: string
  songId: string
  status: 'queued' | 'processing' | 'completed' | 'failed' | string
  progress: number
  analysisId?: string | null
  error?: string | null
  result?: SongAnalysis | null
}

export interface MoodVector {
  energy: number
  valence: number
  danceability: number
  tension: number
}

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
  repetitionGroup?: string | null
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

