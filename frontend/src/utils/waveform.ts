import { clamp } from './formatting'

export const parseWaveformJson = (waveformJson?: string | null): number[] => {
  if (!waveformJson) return []
  try {
    const parsed = JSON.parse(waveformJson)
    if (Array.isArray(parsed)) {
      return parsed.map((value) => {
        const num = Number(value)
        if (Number.isNaN(num)) {
          return 0
        }
        return clamp(num, 0, 1)
      })
    }
    return []
  } catch {
    return []
  }
}
