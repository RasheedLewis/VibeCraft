export interface SongUploadResponse {
  songId: string
  audioUrl: string
  s3Key: string
  status: 'uploaded' | 'processing' | 'failed' | string
}

export interface SongAnalysisJobResponse {
  jobId: string
  songId: string
  status: 'queued' | 'processing' | 'completed' | 'failed' | string
}

export interface SongClipStatus {
  id: string
  clipIndex: number
  startSec: number
  endSec: number
  durationSec: number
  startBeat?: number | null
  endBeat?: number | null
  status: string
  source: string
  numFrames: number
  fps: number
  videoUrl?: string
  rqJobId?: string
  replicateJobId?: string
  error?: string | null
}

export interface ClipGenerationSummary {
  songId: string
  songDurationSec?: number
  totalClips: number
  completedClips: number
  failedClips: number
  processingClips: number
  queuedClips: number
  progressCompleted: number
  progressTotal: number
  clips: SongClipStatus[]
  analysis?: SongAnalysis
  composedVideoUrl?: string | null
  composedVideoPosterUrl?: string | null
}

export interface JobStatusResponse<T = SongAnalysis | ClipGenerationSummary | null> {
  jobId: string
  songId: string
  status: 'queued' | 'processing' | 'completed' | 'failed' | string
  progress?: number
  analysisId?: string | null
  error?: string | null
  result?: T
}

export interface ComposeVideoResponse {
  jobId: string
  status: string
  songId: string
}

export interface CompositionJobStatusResponse {
  jobId: string
  songId: string
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled' | string
  progress: number
  composedVideoId?: string | null
  error?: string | null
  createdAt: string
  updatedAt: string
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
  typeSoft?: string | null
  displayName?: string | null
  rawLabel?: number | null
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
  composed_video_s3_key?: string | null
  composed_video_poster_s3_key?: string | null
  composed_video_duration_sec?: number | null
  composed_video_fps?: number | null
  selected_start_sec?: number | null
  selected_end_sec?: number | null
  video_type?: 'full_length' | 'short_form' | null
  created_at: string
  updated_at: string
}
