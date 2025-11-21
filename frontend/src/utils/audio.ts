export const computeDuration = async (file: File): Promise<number | null> => {
  try {
    const audio = document.createElement('audio')
    audio.preload = 'metadata'
    const src = URL.createObjectURL(file)
    audio.src = src
    return await new Promise<number | null>((resolve, reject) => {
      const timeoutId = window.setTimeout(() => {
        URL.revokeObjectURL(src)
        reject(new Error('Timed out while analyzing audio metadata.'))
      }, 8000)

      audio.onloadedmetadata = () => {
        const duration = Number.isFinite(audio.duration) ? audio.duration : null
        URL.revokeObjectURL(src)
        window.clearTimeout(timeoutId)
        resolve(duration)
      }
      audio.onerror = () => {
        URL.revokeObjectURL(src)
        window.clearTimeout(timeoutId)
        resolve(null)
      }
    })
  } catch {
    return null
  }
}
