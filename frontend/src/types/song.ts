export interface SongUploadResponse {
  songId: string
  audioUrl: string
  s3Key: string
  status: 'uploaded' | 'processing' | 'failed' | string
}


