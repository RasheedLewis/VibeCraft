import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

export interface MseSourceClip {
  id: string
  url: string
  startSec: number
  endSec: number
}

export interface UseMsePlaybackOptions {
  enabled: boolean
  videoRef: React.RefObject<HTMLVideoElement | null>
  clips: MseSourceClip[]
  codecHints?: string[]
  currentTime?: number
  trimLeadSeconds?: number
}

export interface UseMsePlaybackState {
  objectUrl: string | null
  isSupported: boolean
  isReady: boolean
  isBuffering: boolean
  error: string | null
}

const DEFAULT_CODECS = [
  'video/mp4; codecs="avc1.640028"',
  'video/mp4; codecs="avc1.4d4028"',
  'video/mp4; codecs="avc1.4d401f"',
  'video/mp4; codecs="avc1.42E01E"',
]

const DEFAULT_TRIM_SECONDS = 45

export const useMseVideoPlayback = ({
  enabled,
  videoRef,
  clips,
  codecHints,
  currentTime,
  trimLeadSeconds = DEFAULT_TRIM_SECONDS,
}: UseMsePlaybackOptions): UseMsePlaybackState => {
  const [objectUrl, setObjectUrl] = useState<string | null>(null)
  const [isSupported, setIsSupported] = useState<boolean>(() => 'MediaSource' in window)
  const [isReady, setIsReady] = useState(false)
  const [isBuffering, setIsBuffering] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mediaSourceRef = useRef<MediaSource | null>(null)
  const sourceOpenHandlerRef = useRef<((this: MediaSource, ev: Event) => void) | null>(
    null,
  )
  const objectUrlRef = useRef<string | null>(null)
  const sourceBufferRef = useRef<SourceBuffer | null>(null)
  const abortControllersRef = useRef<AbortController[]>([])
  const isEndingRef = useRef(false)
  const pendingRemovalRef = useRef<number | null>(null)

  const sortedClips = useMemo(
    () => [...clips].sort((a, b) => a.startSec - b.startSec),
    [clips],
  )

  const releaseResources = useCallback(() => {
    abortControllersRef.current.forEach((controller) => controller.abort())
    abortControllersRef.current = []

    const videoEl = videoRef.current
    const mediaSource = mediaSourceRef.current
    const sourceOpenHandler = sourceOpenHandlerRef.current
    const sourceBuffer = sourceBufferRef.current

    if (sourceBuffer) {
      try {
        if (mediaSource && mediaSource.readyState === 'open' && !sourceBuffer.updating) {
          mediaSource.removeSourceBuffer(sourceBuffer)
        }
      } catch {
        // ignore
      }
    }

    if (mediaSource) {
      try {
        if (sourceOpenHandler) {
          mediaSource.removeEventListener('sourceopen', sourceOpenHandler)
        }
      } catch {
        // ignore
      }
      if (mediaSource.readyState === 'open') {
        try {
          mediaSource.endOfStream()
        } catch {
          // ignore
        }
      }
    }

    sourceBufferRef.current = null
    mediaSourceRef.current = null
    sourceOpenHandlerRef.current = null
    pendingRemovalRef.current = null
    isEndingRef.current = false

    if (videoEl) {
      try {
        videoEl.removeAttribute('src')
        videoEl.load()
      } catch {
        // ignore
      }
    }
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current)
    }
    objectUrlRef.current = null
    setObjectUrl(null)
  }, [videoRef])

  useEffect(() => {
    if (!enabled) {
      releaseResources()
      setIsReady(false)
      setIsBuffering(false)
      setError(null)
      return
    }

    if (!('MediaSource' in window)) {
      setIsSupported(false)
      setError('MediaSource extensions are not supported in this browser.')
      return
    }

    setIsSupported(true)

    const videoEl = videoRef.current
    if (!videoEl || sortedClips.length === 0) {
      releaseResources()
      return
    }

    setIsReady(false)
    setIsBuffering(true)
    setError(null)

    const mediaSource = new MediaSource()
    mediaSourceRef.current = mediaSource

    const handleSourceOpen = async () => {
      const candidateCodecs = codecHints?.length ? codecHints : DEFAULT_CODECS
      const mimeType = candidateCodecs.find((codec) => MediaSource.isTypeSupported(codec))
      if (!mimeType) {
        setError('No supported codecs found for MediaSource playback.')
        releaseResources()
        return
      }

      let sourceBuffer: SourceBuffer
      try {
        sourceBuffer = mediaSource.addSourceBuffer(mimeType)
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to create MediaSource buffer for playback.',
        )
        releaseResources()
        return
      }

      sourceBuffer.mode = 'segments'
      sourceBufferRef.current = sourceBuffer

      const appendClip = async (clipIndex: number): Promise<void> => {
        if (!mediaSourceRef.current || !sourceBufferRef.current) {
          return
        }
        if (clipIndex >= sortedClips.length) {
          if (!isEndingRef.current && mediaSource.readyState === 'open') {
            isEndingRef.current = true
            try {
              mediaSource.endOfStream()
            } catch {
              // ignore
            }
          }
          return
        }

        const clip = sortedClips[clipIndex]
        const controller = new AbortController()
        abortControllersRef.current.push(controller)

        try {
          const response = await fetch(clip.url, { signal: controller.signal })
          if (!response.ok) {
            throw new Error(`Clip fetch failed (${response.status})`)
          }
          const buffer = await response.arrayBuffer()
          await appendBuffer(clip, buffer)
          setIsReady(true)
          setIsBuffering(false)
          await appendClip(clipIndex + 1)
        } catch (err) {
          if ((err as { name?: string }).name === 'AbortError') {
            return
          }
          setError(
            err instanceof Error
              ? err.message
              : 'Unexpected error while buffering video clips.',
          )
        }
      }

      const appendBuffer = (clip: MseSourceClip, buffer: ArrayBuffer) =>
        new Promise<void>((resolve, reject) => {
          const sb = sourceBufferRef.current
          if (!sb) {
            reject(new Error('SourceBuffer not available'))
            return
          }

          const performAppend = () => {
            try {
              sb.timestampOffset = clip.startSec
              sb.appendBuffer(buffer)
            } catch (appendError) {
              reject(
                appendError instanceof Error
                  ? appendError
                  : new Error('Failed to append clip data.'),
              )
            }
          }

          const handleError = (event: Event) => {
            sb.removeEventListener('updateend', handleUpdateEnd)
            reject(
              event instanceof ErrorEvent
                ? event.error
                : new Error('MediaSource buffer error.'),
            )
          }

          const handleUpdateEnd = () => {
            sb.removeEventListener('error', handleError)
            resolve()
          }

          if (sb.updating) {
            const waitForReady = () => {
              sb.removeEventListener('updateend', waitForReady)
              performAppend()
            }
            sb.addEventListener('updateend', waitForReady, { once: true })
          } else {
            performAppend()
          }

          sb.addEventListener('error', handleError, { once: true })
          sb.addEventListener('updateend', handleUpdateEnd, { once: true })
        })

      await appendClip(0)
    }

    sourceOpenHandlerRef.current = handleSourceOpen
    mediaSource.addEventListener('sourceopen', handleSourceOpen)

    const url = URL.createObjectURL(mediaSource)
    objectUrlRef.current = url
    setObjectUrl(url)
    videoEl.src = url
    videoEl.muted = true

    return () => {
      mediaSource.removeEventListener('sourceopen', handleSourceOpen)
      releaseResources()
    }
  }, [enabled, videoRef, sortedClips, codecHints, releaseResources])

  useEffect(() => {
    if (!enabled) {
      return
    }
    const sourceBuffer = sourceBufferRef.current
    const mediaSource = mediaSourceRef.current
    if (!sourceBuffer || !mediaSource || mediaSource.readyState !== 'open') {
      return
    }
    if (currentTime == null || Number.isNaN(currentTime)) {
      return
    }
    if (trimLeadSeconds <= 0) {
      return
    }

    const targetTrim = Math.max(0, currentTime - trimLeadSeconds)
    if (pendingRemovalRef.current != null && targetTrim <= pendingRemovalRef.current) {
      return
    }

    pendingRemovalRef.current = targetTrim

    const tryTrim = () => {
      const sb = sourceBufferRef.current
      const ms = mediaSourceRef.current
      if (!sb || !ms || ms.readyState !== 'open') {
        pendingRemovalRef.current = null
        return
      }
      if (sb.updating) {
        sb.addEventListener('updateend', tryTrim, { once: true })
        return
      }

      const buffered = sb.buffered
      if (!buffered || buffered.length === 0) {
        pendingRemovalRef.current = null
        return
      }

      const start = buffered.start(0)
      if (targetTrim <= start + 0.25) {
        pendingRemovalRef.current = null
        return
      }

      try {
        sb.remove(start, targetTrim)
      } catch (err) {
        console.warn('[mse] failed to trim buffer', err)
      }
      pendingRemovalRef.current = null
    }

    tryTrim()
  }, [enabled, currentTime, trimLeadSeconds])

  return {
    objectUrl,
    isSupported,
    isReady,
    isBuffering,
    error,
  }
}
