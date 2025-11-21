import type { SongAnalysis, ClipGenerationSummary } from '../types/song'

export const isSongAnalysis = (payload: unknown): payload is SongAnalysis => {
  if (!payload || typeof payload !== 'object') return false
  const candidate = payload as Partial<SongAnalysis>
  return (
    typeof candidate.durationSec === 'number' &&
    Array.isArray(candidate.sections) &&
    Array.isArray(candidate.moodTags)
  )
}

export const isClipGenerationSummary = (
  payload: unknown,
): payload is ClipGenerationSummary => {
  if (!payload || typeof payload !== 'object') return false
  const candidate = payload as Partial<ClipGenerationSummary>
  return (
    typeof candidate.songId === 'string' &&
    typeof candidate.totalClips === 'number' &&
    typeof candidate.progressCompleted === 'number' &&
    typeof candidate.progressTotal === 'number' &&
    Array.isArray(candidate.clips)
  )
}

export const extractErrorMessage = (error: unknown, fallback: string): string => {
  if (typeof error === 'string') return error
  if (error && typeof error === 'object') {
    const maybeError = error as {
      message?: string
      response?: { data?: unknown }
    }
    const responseData = maybeError.response?.data
    if (typeof responseData === 'string') return responseData
    if (responseData && typeof responseData === 'object') {
      const detail = (responseData as Record<string, unknown>).detail
      if (typeof detail === 'string') return detail
      const message = (responseData as Record<string, unknown>).message
      if (typeof message === 'string') return message
    }
    if (maybeError.message) return maybeError.message
  }
  return fallback
}
