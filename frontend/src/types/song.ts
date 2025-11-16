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
  beatTimes?: number[]
  sections: SongSection[]
  moodPrimary: string
  moodTags: string[]
  moodVector: MoodVector
  primaryGenre?: string
  subGenres?: string[]
  lyricsAvailable: boolean
  sectionLyrics?: SectionLyrics[]
}

export interface SongRead {
  id: string
  user_id: string
  title: string
  original_filename: string
  original_file_size: number
  original_content_type?: string | null
  original_s3_key: string
  processed_s3_key?: string | null
  processed_sample_rate?: number | null
  waveform_json?: string | null
  duration_sec?: number | null
  description?: string | null
  attribution?: string | null
  created_at: string
  updated_at: string
}
