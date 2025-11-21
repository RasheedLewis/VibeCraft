export const formatBytes = (bytes: number) => {
  if (!Number.isFinite(bytes)) return '—'
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  const exponent = Math.min(
    Math.floor(Math.log(bytes) / Math.log(1024)),
    units.length - 1,
  )
  const value = bytes / Math.pow(1024, exponent)
  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[exponent]}`
}

export const formatSeconds = (seconds: number | null) => {
  if (!Number.isFinite(seconds) || seconds === null) return '—'
  const wholeSeconds = Math.round(seconds)
  const mins = Math.floor(wholeSeconds / 60)
  const secs = wholeSeconds % 60
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`
}

export const formatBpm = (bpm?: number) => {
  if (!bpm || Number.isNaN(bpm)) return '—'
  return `${Math.round(bpm)} BPM`
}

export const formatMoodTags = (tags: string[]) =>
  tags.length
    ? tags
        .map((tag) => tag.trim())
        .filter(Boolean)
        .join(', ')
    : '—'

export const formatDurationShort = (seconds: number) => {
  if (!Number.isFinite(seconds)) return '—'
  if (seconds >= 10) return `${Math.round(seconds)}s`
  return `${seconds.toFixed(1)}s`
}

export const formatTimeRange = (startSec: number, endSec: number) =>
  `${formatSeconds(startSec)}–${formatSeconds(endSec)}`

export const clamp = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value))

export const getFileTypeLabel = (fileName?: string | null) => {
  if (!fileName) return 'Audio'
  const parts = fileName.split('.')
  if (parts.length <= 1) return 'Audio'
  return parts.pop()?.toUpperCase() ?? 'Audio'
}
