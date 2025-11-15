export interface SectionVideoRead {
  id: string
  songId: string
  sectionId: string
  template: string
  prompt: string
  durationSec: number
  videoUrl?: string
  s3Key?: string
  fps?: number
  resolutionWidth?: number
  resolutionHeight?: number
  seed?: number
  status: string
  errorMessage?: string
  createdAt: string
  updatedAt: string
}

export interface SectionVideoGenerateRequest {
  sectionId: string
  template?: string
}

export interface SectionVideoGenerateResponse {
  sectionVideoId: string
  status: string
  message: string
}
