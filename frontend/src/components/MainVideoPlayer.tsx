import clsx from 'clsx'
import React, {
  type KeyboardEvent,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'

type IconProps = React.SVGProps<SVGSVGElement>

const iconClass = (className?: string) => clsx('flex-none', className)

const PlayIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <polygon points="8 5 19 12 8 19 8 5" />
  </svg>
)

const PauseIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.8}
    strokeLinecap="round"
    {...props}
  >
    <line x1="9" y1="5" x2="9" y2="19" />
    <line x1="15" y1="5" x2="15" y2="19" />
  </svg>
)

const SkipBackIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <polygon points="19 5 11 12 19 19 19 5" />
    <polygon points="12 5 4 12 12 19 12 5" />
  </svg>
)

const SkipForwardIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <polygon points="5 5 13 12 5 19 5 5" />
    <polygon points="12 5 20 12 12 19 12 5" />
  </svg>
)

const RepeatIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <polyline points="17 1 21 5 17 9" />
    <path d="M3 11v-2a4 4 0 0 1 4-4h14" />
    <polyline points="7 23 3 19 7 15" />
    <path d="M21 13v2a4 4 0 0 1-4 4H3" />
  </svg>
)

const CaptionsIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <line x1="7" y1="9.5" x2="11" y2="9.5" />
    <line x1="7" y1="14.5" x2="11" y2="14.5" />
    <line x1="13" y1="12" x2="17" y2="12" />
  </svg>
)

const VolumeOnIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M11 5 6 9H3v6h3l5 4V5Z" />
    <path d="M16 8a4 4 0 0 1 0 8" />
    <path d="M19 6a7 7 0 0 1 0 12" />
  </svg>
)

const VolumeOffIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M11 5 6 9H3v6h3l5 4V5Z" />
    <line x1="16" y1="9" x2="21" y2="15" />
    <line x1="21" y1="9" x2="16" y2="15" />
  </svg>
)

const PictureInPictureIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <rect x="3" y="3" width="18" height="14" rx="2" />
    <rect x="9.5" y="8.5" width="8.5" height="6.5" rx="1.2" />
  </svg>
)

const DownloadIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M12 3v12" />
    <polyline points="7 11 12 16 17 11" />
    <path d="M5 19h14" />
  </svg>
)

const KeyboardIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <rect x="2" y="6" width="20" height="12" rx="2" />
    <path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M6 14h12" />
  </svg>
)

const ScissorsIcon = ({ className, ...props }: IconProps) => (
  <svg
    viewBox="0 0 24 24"
    className={iconClass(className)}
    fill="none"
    stroke="currentColor"
    strokeWidth={1.5}
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="6" cy="6" r="2.5" />
    <circle cx="6" cy="18" r="2.5" />
    <path d="M20 4 8.5 11.5" />
    <path d="M8.5 12.5 20 20" />
  </svg>
)

export interface PlayerClip {
  id: string
  index: number
  startSec: number
  endSec: number
  videoUrl?: string | null
  thumbUrl?: string | null
}

export interface PlayerBeat {
  t: number
}

export interface PlayerLyricLine {
  t: number
  text: string
  dur?: number
}

interface MainVideoPlayerProps {
  videoUrl: string
  audioUrl?: string | null
  posterUrl?: string | null
  durationSec: number
  clips?: PlayerClip[]
  activeClipId?: string
  onClipSelect?: (clipId: string) => void
  beatGrid?: PlayerBeat[]
  lyrics?: PlayerLyricLine[]
  waveform?: number[]
  onDownload?: () => void
}

const clampValue = (value: number, min: number, max: number) =>
  Math.min(max, Math.max(min, value))

const fmtTime = (seconds: number) => {
  const safe = Math.max(0, seconds)
  const s = Math.floor(safe)
  const mins = Math.floor(s / 60)
  const secs = String(s % 60).padStart(2, '0')
  return `${mins}:${secs}`
}

const getClipDuration = (clip: PlayerClip) => Math.max(clip.endSec - clip.startSec, 0)

const clampRelativeTimeForClip = (clip: PlayerClip, globalTime: number) => {
  const duration = getClipDuration(clip)
  if (duration <= 0) return 0
  const relative = globalTime - clip.startSec
  return clampValue(relative, 0, Math.max(duration - 0.05, 0))
}

const findClipForGlobalTime = (clips: PlayerClip[], time: number) => {
  if (!clips.length) return null
  const match = clips.find((clip) => time >= clip.startSec && time < clip.endSec)
  return match ?? clips[clips.length - 1]
}

export const MainVideoPlayer: React.FC<MainVideoPlayerProps> = ({
  videoUrl,
  audioUrl,
  posterUrl,
  durationSec,
  clips = [],
  activeClipId,
  onClipSelect,
  beatGrid = [],
  lyrics = [],
  waveform,
  onDownload,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const railRef = useRef<HTMLDivElement | null>(null)
  const pendingVideoSeekRef = useRef<number | null>(null)
  const justResetRef = useRef<boolean>(false)

  const [isPlaying, setIsPlaying] = useState(false)
  const [current, setCurrent] = useState(0)
  const [hoverSec, setHoverSec] = useState<number | null>(null)
  const [volume, setVolume] = useState(0.9)
  const [muted, setMuted] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1)
  const [pipSupported, setPipSupported] = useState(false)

  const [aMark, setAMark] = useState<number | null>(null)
  const [bMark, setBMark] = useState<number | null>(null)
  const [loopAB, setLoopAB] = useState(false)

  const [showLyrics, setShowLyrics] = useState(true)
  const [showSettings, setShowSettings] = useState(false)

  const usingExternalAudio = Boolean(audioUrl)

  // Close settings modal on Escape key
  useEffect(() => {
    const handleEscape = (e: globalThis.KeyboardEvent) => {
      if (e.key === 'Escape' && showSettings) {
        setShowSettings(false)
      }
    }
    window.addEventListener('keydown', handleEscape)
    return () => window.removeEventListener('keydown', handleEscape)
  }, [showSettings])

  // Shared function to handle time clamping and stopping at end
  const handleTimeClamp = useCallback(
    (currentTime: number, mediaElement: HTMLAudioElement | HTMLVideoElement) => {
      // If we just reset, ignore the first timeupdate to avoid race condition
      if (justResetRef.current) {
        justResetRef.current = false
        setCurrent(0)
        return
      }

      // Clamp current time to duration for display
      const clampedTime = Math.min(currentTime, durationSec)
      setCurrent(clampedTime)

      // If we've reached or exceeded the duration and media is playing, stop and reset
      if (currentTime >= durationSec && !mediaElement.paused) {
        mediaElement.pause()
        mediaElement.currentTime = 0
        setIsPlaying(false)
        setCurrent(0)
      }
    },
    [durationSec],
  )

  const resolveClipForTime = useCallback(
    (time: number): PlayerClip | null => {
      if (!clips.length) return null
      if (activeClipId) {
        const manual = clips.find((clip) => clip.id === activeClipId)
        if (manual) {
          return manual
        }
      }
      return findClipForGlobalTime(clips, time)
    },
    [clips, activeClipId],
  )

  const setVideoPlaybackTime = useCallback(
    (globalTime: number, clipOverride?: PlayerClip | null) => {
      if (!usingExternalAudio) return
      const videoEl = videoRef.current
      if (!videoEl) return
      const clip = clipOverride ?? resolveClipForTime(globalTime)
      if (!clip) return

      const relative = clampRelativeTimeForClip(clip, globalTime)
      try {
        videoEl.currentTime = relative
        if (videoEl.readyState <= 1) {
          pendingVideoSeekRef.current = relative
        } else {
          pendingVideoSeekRef.current = null
        }
      } catch {
        pendingVideoSeekRef.current = relative
      }
    },
    [resolveClipForTime, usingExternalAudio],
  )

  useEffect(() => {
    if (!usingExternalAudio) return
    const videoEl = videoRef.current
    if (!videoEl) return

    const handleLoadedMetadata = () => {
      if (pendingVideoSeekRef.current == null) return
      try {
        videoEl.currentTime = pendingVideoSeekRef.current
      } catch {
        // Ignore; next event will retry if needed
      } finally {
        pendingVideoSeekRef.current = null
      }
    }

    videoEl.addEventListener('loadedmetadata', handleLoadedMetadata)
    return () => {
      videoEl.removeEventListener('loadedmetadata', handleLoadedMetadata)
    }
  }, [videoUrl, usingExternalAudio])

  useEffect(() => {
    setPipSupported(Boolean(document?.pictureInPictureEnabled))
  }, [])

  useEffect(() => {
    const audioEl = audioRef.current
    const videoEl = videoRef.current

    if (usingExternalAudio && audioEl) {
      const handleTime = () => {
        handleTimeClamp(audioEl.currentTime, audioEl)
        // Also pause video if audio stops
        if (audioEl.paused && videoEl) {
          videoEl.pause()
        }
      }
      const handlePlay = () => setIsPlaying(true)
      const handlePause = () => setIsPlaying(false)
      const handleEnded = () => {
        // When audio ends, reset to beginning
        audioEl.pause()
        audioEl.currentTime = 0
        setIsPlaying(false)
        setCurrent(0)
        if (videoEl) {
          videoEl.pause()
          videoEl.currentTime = 0
        }
      }

      audioEl.volume = muted ? 0 : volume
      audioEl.muted = muted
      audioEl.playbackRate = playbackRate

      audioEl.addEventListener('timeupdate', handleTime)
      audioEl.addEventListener('play', handlePlay)
      audioEl.addEventListener('pause', handlePause)
      audioEl.addEventListener('ended', handleEnded)

      if (videoEl) {
        videoEl.muted = true
        videoEl.playbackRate = playbackRate
      }

      return () => {
        audioEl.removeEventListener('timeupdate', handleTime)
        audioEl.removeEventListener('play', handlePlay)
        audioEl.removeEventListener('pause', handlePause)
        audioEl.removeEventListener('ended', handleEnded)
      }
    }

    if (videoEl) {
      const handleTime = () => {
        handleTimeClamp(videoEl.currentTime, videoEl)
      }
      const handlePlay = () => setIsPlaying(true)
      const handlePause = () => setIsPlaying(false)
      const handleEnded = () => {
        // When video ends, reset to beginning and stop
        videoEl.pause()
        videoEl.currentTime = 0
        setIsPlaying(false)
        setCurrent(0)
      }

      videoEl.volume = muted ? 0 : volume
      videoEl.muted = muted
      videoEl.playbackRate = playbackRate

      videoEl.addEventListener('timeupdate', handleTime)
      videoEl.addEventListener('play', handlePlay)
      videoEl.addEventListener('pause', handlePause)
      videoEl.addEventListener('ended', handleEnded)

      return () => {
        videoEl.removeEventListener('timeupdate', handleTime)
        videoEl.removeEventListener('play', handlePlay)
        videoEl.removeEventListener('pause', handlePause)
        videoEl.removeEventListener('ended', handleEnded)
      }
    }
  }, [
    usingExternalAudio,
    volume,
    muted,
    playbackRate,
    audioUrl,
    videoUrl,
    durationSec,
    handleTimeClamp,
  ])

  useEffect(() => {
    if (!usingExternalAudio) return
    const audioEl = audioRef.current
    const videoEl = videoRef.current
    if (!audioEl || !videoEl) return

    const sync = () => {
      const audioCurrent = audioRef.current
      const videoCurrent = videoRef.current
      if (!audioCurrent || !videoCurrent) return
      const clip = resolveClipForTime(audioCurrent.currentTime)
      if (!clip) return
      const relative = clampRelativeTimeForClip(clip, audioCurrent.currentTime)
      if (Math.abs(videoCurrent.currentTime - relative) > 0.25) {
        setVideoPlaybackTime(audioCurrent.currentTime, clip)
      }
    }

    const id = window.setInterval(sync, 250)
    return () => window.clearInterval(id)
  }, [usingExternalAudio, resolveClipForTime, setVideoPlaybackTime])

  useEffect(() => {
    const media = usingExternalAudio ? audioRef.current : videoRef.current
    if (!media || !loopAB || aMark == null || bMark == null) return
    if (current >= bMark) {
      media.currentTime = aMark
      if (usingExternalAudio) {
        setVideoPlaybackTime(aMark)
      } else if (videoRef.current) {
        videoRef.current.currentTime = aMark
      }
    }
  }, [current, loopAB, aMark, bMark, usingExternalAudio, setVideoPlaybackTime])

  // Reset state only when switching between external audio and embedded audio modes
  // Don't reset on every videoUrl/audioUrl change to avoid infinite loops
  const prevUsingExternalAudioRef = useRef(usingExternalAudio)
  useEffect(() => {
    if (prevUsingExternalAudioRef.current !== usingExternalAudio) {
      prevUsingExternalAudioRef.current = usingExternalAudio
      if (!usingExternalAudio) {
        setIsPlaying(false)
        setCurrent(0)
      }
    }
  }, [usingExternalAudio])

  const togglePlay = () => {
    const audioEl = usingExternalAudio ? audioRef.current : null
    const videoEl = videoRef.current

    if (usingExternalAudio && audioEl) {
      if (isPlaying) {
        audioEl.pause()
        videoEl?.pause()
      } else {
        if (videoEl) {
          videoEl.muted = true
        }
        const clip = resolveClipForTime(audioEl.currentTime)
        setVideoPlaybackTime(audioEl.currentTime, clip)
        const playPromises: Array<Promise<unknown>> = [
          audioEl.play().catch((err) => {
            console.error('[MainVideoPlayer] Audio play failed:', err)
            return undefined
          }),
        ]
        if (videoEl) {
          playPromises.push(
            videoEl.play().catch((err) => {
              console.error('[MainVideoPlayer] Video play failed:', err)
              return undefined
            }),
          )
        }
        void Promise.all(playPromises)
      }
      return
    }

    if (!videoEl) return
    if (isPlaying) {
      videoEl.pause()
    } else {
      // If video is at or past the end, reset to beginning before playing
      if (videoEl.currentTime >= durationSec) {
        videoEl.currentTime = 0
        setCurrent(0)
        justResetRef.current = true // Flag to ignore next timeupdate
      }
      videoEl.play().catch((err) => {
        console.error('[MainVideoPlayer] Video play failed:', err)
        setIsPlaying(false)
        justResetRef.current = false
      })
    }
  }

  const jump = (delta: number) => {
    const target = clampValue(current + delta, 0, durationSec)
    seekTo(target)
  }

  const seekTo = (time: number) => {
    const newTime = clampValue(time, 0, durationSec)
    if (usingExternalAudio && audioRef.current) {
      audioRef.current.currentTime = newTime
      setVideoPlaybackTime(newTime)
    } else if (videoRef.current) {
      videoRef.current.currentTime = newTime
    }
    setCurrent(newTime)
  }

  const setTimeFromRail = (clientX: number) => {
    if (!railRef.current) return
    const rect = railRef.current.getBoundingClientRect()
    const ratio = clampValue((clientX - rect.left) / rect.width, 0, 1)
    const target = ratio * durationSec
    seekTo(target)
  }

  const handleClipSelection = (clip: PlayerClip) => {
    seekTo(clip.startSec)
    if (onClipSelect) {
      onClipSelect(clip.id)
    }
  }

  const onRailMouseMove = (e: React.MouseEvent) => {
    if (!railRef.current) return
    const rect = railRef.current.getBoundingClientRect()
    const ratio = clampValue((e.clientX - rect.left) / rect.width, 0, 1)
    setHoverSec(ratio * durationSec)
  }

  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement | null)?.tagName === 'INPUT') return
    switch (e.key) {
      case ' ':
      case 'k':
        e.preventDefault()
        togglePlay()
        break
      case 'j':
        jump(-5)
        break
      case 'l':
        jump(5)
        break
      case 'ArrowLeft':
        jump(-1)
        break
      case 'ArrowRight':
        jump(1)
        break
      case 'ArrowUp':
        setVolume((v) => clampValue(v + 0.05, 0, 1))
        setMuted(false)
        break
      case 'ArrowDown':
        setVolume((v) => clampValue(v - 0.05, 0, 1))
        break
      case 'm':
        setMuted((m) => !m)
        break
      case '[':
        setPlaybackRate((r) => clampValue(r - 0.25, 0.25, 2))
        break
      case ']':
        setPlaybackRate((r) => clampValue(r + 0.25, 0.25, 2))
        break
      case 'a':
        setAMark(current)
        break
      case 'b':
        setBMark(current)
        break
      case '\\':
        setLoopAB((v) => !v)
        break
      case 'c':
        setShowLyrics((v) => !v)
        break
    }
  }

  const currentLyric = useMemo(() => {
    if (!lyrics.length) return null
    let index = lyrics.findIndex((line) => line.t > current)
    index = index === -1 ? lyrics.length - 1 : Math.max(0, index - 1)
    const line = lyrics[index]
    if (!line) return null
    if (line.dur != null && current > line.t + line.dur) return null
    return line.text
  }, [current, lyrics])

  const timelineActiveClip = useMemo(() => {
    if (!clips.length) return null
    if (activeClipId) {
      const manual = clips.find((clip) => clip.id === activeClipId)
      if (manual) {
        return manual
      }
    }
    return findClipForGlobalTime(clips, current)
  }, [clips, activeClipId, current])

  return (
    <div className="vc-card p-0 overflow-hidden" onKeyDown={onKey} tabIndex={0}>
      <div className="relative bg-black">
        <audio
          ref={audioRef}
          src={audioUrl ?? undefined}
          preload="auto"
          className="hidden"
        />
        <video
          key={(() => {
            if (!videoUrl) return 'video-none'
            try {
              // Use S3 key path as stable identifier (doesn't change when presigned URL regenerates)
              const url = new URL(videoUrl)
              return `video-${url.pathname}`
            } catch {
              // Fallback to full URL if parsing fails
              return `video-${videoUrl}`
            }
          })()}
          ref={videoRef}
          src={videoUrl || undefined}
          poster={posterUrl ?? undefined}
          className="w-full aspect-video"
          onClick={togglePlay}
          muted={usingExternalAudio ? true : muted}
          controls={false}
          playsInline
          onError={() => {
            console.error('[MainVideoPlayer] Video error', {
              error: videoRef.current?.error,
              networkState: videoRef.current?.networkState,
              readyState: videoRef.current?.readyState,
            })
          }}
        />
        <div className="pointer-events-none absolute inset-0 flex items-end justify-between p-3">
          {/* Left side playback controls */}
          <div className="pointer-events-auto flex items-center gap-2">
            {/* Skip Back: Jump backward 5 seconds (J key) */}
            <TransportButton onClick={() => jump(-5)} title="Back 5s (J)">
              <SkipBackIcon className="h-4 w-4" />
            </TransportButton>
            {/* Play/Pause: Toggle playback (Space/K key) */}
            <TransportButton onClick={togglePlay} title="Play/Pause (Space/K)">
              {isPlaying ? (
                <PauseIcon className="h-5 w-5" />
              ) : (
                <PlayIcon className="h-5 w-5" />
              )}
            </TransportButton>
            {/* Skip Forward: Jump forward 5 seconds (L key) */}
            <TransportButton onClick={() => jump(5)} title="Forward 5s (L)">
              <SkipForwardIcon className="h-4 w-4" />
            </TransportButton>
            {/* Time Display: Shows current time / total duration */}
            <span className="ml-2 text-[11px] text-white/90 bg-black/40 rounded px-1 py-0.5">
              {fmtTime(current)} / {fmtTime(durationSec)}
            </span>
          </div>

          {/* Right side utility controls */}
          <div className="pointer-events-auto flex items-center gap-2">
            {/* Repeat/Loop Toggle: Toggle A/B loop mode (\ key) */}
            <TransportButton
              onClick={() => setLoopAB((v) => !v)}
              title="Toggle A/B Loop (\\)"
              selected={loopAB}
            >
              <RepeatIcon className="h-4 w-4" />
            </TransportButton>
            {/* Captions Toggle: Show/hide lyrics/captions overlay (C key) */}
            <TransportButton
              onClick={() => setShowLyrics((v) => !v)}
              title="Toggle Captions (C)"
              selected={showLyrics}
            >
              <CaptionsIcon className="h-4 w-4" />
            </TransportButton>

            {/* Playback Speed Control: Adjust playback rate ([-] slower, []] faster) */}
            <div className="flex items-center gap-1 bg-black/40 rounded px-1.5 py-0.5">
              <button
                className="text-[11px] text-white/90 hover:text-white"
                onClick={() => setPlaybackRate((r) => clampValue(r - 0.25, 0.25, 2))}
                title="Slower ([)"
              >
                –
              </button>
              <span className="text-[11px] text-white/90 w-8 text-center">
                {playbackRate.toFixed(2)}x
              </span>
              <button
                className="text-[11px] text-white/90 hover:text-white"
                onClick={() => setPlaybackRate((r) => clampValue(r + 0.25, 0.25, 2))}
                title="Faster (])"
              >
                +
              </button>
            </div>

            {/* Volume/Mute Toggle: Mute or unmute audio (M key) */}
            <TransportButton
              onClick={() => setMuted((m) => !m)}
              title={muted ? 'Unmute (M)' : 'Mute (M)'}
            >
              {muted || volume === 0 ? (
                <VolumeOffIcon className="h-4 w-4" />
              ) : (
                <VolumeOnIcon className="h-4 w-4" />
              )}
            </TransportButton>

            {/* Picture-in-Picture: Enter/exit PiP mode (only shown if browser supports it) */}
            {pipSupported && Boolean(videoUrl) && (
              <TransportButton
                onClick={async () => {
                  const element = videoRef.current
                  if (!element) return
                  if (document.pictureInPictureElement) {
                    await (
                      document as { exitPictureInPicture?: () => Promise<void> }
                    ).exitPictureInPicture?.()
                  } else {
                    await (element as HTMLVideoElement).requestPictureInPicture?.()
                  }
                }}
                title="Picture-in-picture"
              >
                <PictureInPictureIcon className="h-4 w-4" />
              </TransportButton>
            )}

            {/* Download: Download the video file */}
            <TransportButton onClick={onDownload} title="Download">
              <DownloadIcon className="h-4 w-4" />
            </TransportButton>

            {/* Help: Open keyboard shortcuts help menu */}
            <TransportButton
              onClick={() => setShowSettings(true)}
              title="Keyboard Shortcuts"
            >
              <KeyboardIcon className="h-4 w-4" />
            </TransportButton>
          </div>
        </div>

        {/* A/B Loop Markers: Vertical lines on video showing A and B loop point positions */}
        {(aMark != null || bMark != null) && (
          <div className="pointer-events-none absolute inset-x-0 bottom-20 h-0">
            {aMark != null && (
              <Marker time={aMark} duration={durationSec} color="bg-vc-accent-primary" />
            )}
            {bMark != null && (
              <Marker
                time={bMark}
                duration={durationSec}
                color="bg-vc-accent-secondary"
              />
            )}
          </div>
        )}

        {/* Lyrics Overlay: Displays current lyric line when captions are enabled */}
        {showLyrics && currentLyric && (
          <div className="pointer-events-none absolute inset-x-0 bottom-16 flex justify-center">
            <div className="px-3 py-1.5 rounded-md bg-black/50 text-white text-sm font-medium">
              {currentLyric}
            </div>
          </div>
        )}
      </div>

      {/* Timeline/Waveform Section: Interactive timeline for seeking and viewing clips */}
      <div
        ref={railRef}
        className="relative px-3 py-3 border-t border-vc-border bg-[rgba(255,255,255,0.02)]"
        onMouseMove={onRailMouseMove}
        onMouseLeave={() => setHoverSec(null)}
        onClick={(e) => setTimeFromRail(e.clientX)}
      >
        <div className="h-10 rounded bg-[rgba(255,255,255,0.03)] relative overflow-hidden">
          {/* Waveform Bars: Visual representation of audio waveform */}
          <WaveBars duration={durationSec} waveform={waveform} />
          {/* Beat Ticks: Vertical lines marking beat positions */}
          {beatGrid.map((beat, index) => (
            <BeatTick key={`beat-${index}-${beat.t}`} t={beat.t} duration={durationSec} />
          ))}
          {/* Clip Spans: Visual segments representing individual video clips */}
          {clips.map((clip) => (
            <ClipSpan
              key={clip.id}
              clip={clip}
              duration={durationSec}
              active={clip.id === timelineActiveClip?.id}
              disabled={onClipSelect != null && !clip.videoUrl}
              onSelect={() => handleClipSelection(clip)}
            />
          ))}
          {/* Playhead: White vertical line showing current playback position */}
          <Playhead t={current} duration={durationSec} />
          {/* Hover Time Indicator: Shows time when hovering over timeline */}
          {hoverSec != null && <HoverTime t={hoverSec} duration={durationSec} />}
        </div>

        {/* A/B Loop Controls: Set loop points and toggle looping between A and B markers */}
        <div className="mt-2 flex items-center gap-2">
          <span className="vc-badge">A/B Loop</span>
          {/* Set A: Mark current position as loop start point (A key) */}
          <button
            className="vc-btn-secondary vc-btn-sm"
            onClick={() => setAMark(current)}
            title="Set A (a)"
          >
            <ScissorsIcon className="mr-1 h-3.5 w-3.5" /> Set A
          </button>
          {/* Set B: Mark current position as loop end point (B key) */}
          <button
            className="vc-btn-secondary vc-btn-sm"
            onClick={() => setBMark(current)}
            title="Set B (b)"
          >
            <ScissorsIcon className="mr-1 h-3.5 w-3.5" /> Set B
          </button>
          {/* Loop Toggle: Enable/disable looping between A and B markers (\ key) */}
          <button
            className={clsx('vc-btn-sm', loopAB ? 'vc-btn-primary' : 'vc-btn-secondary')}
            onClick={() => setLoopAB((v) => !v)}
          >
            {loopAB ? 'Loop A↔B On' : 'Loop A↔B Off'}
          </button>
          {/* A/B Time Display: Shows the time positions of A and B markers */}
          {(aMark != null || bMark != null) && (
            <span className="ml-2 text-[11px] text-vc-text-muted">
              A: {aMark != null ? fmtTime(aMark) : '--:--'} • B:{' '}
              {bMark != null ? fmtTime(bMark) : '--:--'}
            </span>
          )}
        </div>
      </div>

      {/* Settings Modal: Shows keyboard shortcuts and player information */}
      {showSettings && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
          onClick={() => setShowSettings(false)}
        >
          <div
            className="relative w-full max-w-2xl rounded-2xl bg-[rgba(20,20,32,0.95)] backdrop-blur-xl border border-vc-border/50 shadow-2xl p-6 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Keyboard Shortcuts</h2>
              <button
                onClick={() => setShowSettings(false)}
                className="text-vc-text-secondary hover:text-white transition-colors p-2 hover:bg-vc-border/30 rounded-lg"
                aria-label="Close"
              >
                <svg
                  className="w-6 h-6"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            {/* Keyboard Shortcuts List */}
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Playback</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Play/Pause</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      Space
                    </kbd>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      K
                    </kbd>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Jump Back 5s</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      J
                    </kbd>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Jump Forward 5s</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      L
                    </kbd>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Seek Back 1s</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      ←
                    </kbd>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Seek Forward 1s</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      →
                    </kbd>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Volume</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Mute/Unmute</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      M
                    </kbd>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Volume Up</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      ↑
                    </kbd>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Volume Down</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      ↓
                    </kbd>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Playback Speed</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Slower</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      [
                    </kbd>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Faster</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      ]
                    </kbd>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">A/B Loop</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Set A Marker</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      A
                    </kbd>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Set B Marker</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      B
                    </kbd>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Toggle Loop</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      \
                    </kbd>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Other</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center py-1 border-b border-vc-border/30">
                    <span className="text-vc-text-secondary">Toggle Captions</span>
                    <kbd className="px-2 py-1 bg-vc-border/30 rounded text-white font-mono text-xs">
                      C
                    </kbd>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const TransportButton: React.FC<{
  onClick?: () => void
  title?: string
  selected?: boolean
  children: React.ReactNode
}> = ({ onClick, title, selected, children }) => (
  <button
    onClick={onClick}
    title={title}
    className={clsx(
      'pointer-events-auto vc-icon-btn',
      selected && 'vc-icon-btn-selected',
    )}
  >
    {children}
  </button>
)

const Playhead: React.FC<{ t: number; duration: number }> = ({ t, duration }) => {
  const left = `${(t / duration) * 100}%`
  return <div className="absolute inset-y-0 w-[2px] bg-white/90" style={{ left }} />
}

const HoverTime: React.FC<{ t: number; duration: number }> = ({ t, duration }) => {
  const left = `${(t / duration) * 100}%`
  return (
    <div className="absolute -top-5" style={{ left }}>
      <div className="translate-x-[-50%] text-[10px] text-white/90 bg-black/60 rounded px-1 py-[1px]">
        {fmtTime(t)}
      </div>
    </div>
  )
}

const BeatTick: React.FC<{ t: number; duration: number }> = ({ t, duration }) => {
  const left = `${(t / duration) * 100}%`
  return <div className="absolute inset-y-0 w-[1px] bg-white/24" style={{ left }} />
}

const Marker: React.FC<{ time: number; duration: number; color: string }> = ({
  time,
  duration,
  color,
}) => {
  const left = `${(time / duration) * 100}%`
  return <div className={clsx('absolute w-[2px] h-6 rounded', color)} style={{ left }} />
}

const ClipSpan: React.FC<{
  clip: PlayerClip
  duration: number
  active: boolean
  onSelect: () => void
  disabled?: boolean
}> = ({ clip, duration, active, onSelect, disabled }) => {
  const left = `${(clip.startSec / duration) * 100}%`
  const width = `${((clip.endSec - clip.startSec) / duration) * 100}%`
  return (
    <button
      type="button"
      onClick={(e) => {
        e.stopPropagation()
        onSelect()
      }}
      disabled={disabled}
      className={clsx(
        'absolute top-0 bottom-0 rounded-sm border border-vc-border/60 bg-gradient-to-r from-vc-accent-primary/15 to-vc-accent-tertiary/20 transition focus:outline-none',
        active && 'border-vc-accent-primary/80 shadow-[0_0_0_2px_rgba(110,107,255,0.35)]',
        disabled
          ? 'cursor-not-allowed opacity-50 saturate-[0.8]'
          : 'hover:border-vc-accent-primary/70 hover:shadow-[0_0_0_2px_rgba(110,107,255,0.25)]',
      )}
      style={{ left, width }}
      title={`Clip #${clip.index + 1}`}
    />
  )
}

const WaveBars: React.FC<{ duration: number; waveform?: number[] }> = ({ waveform }) => {
  const bars =
    waveform && waveform.length
      ? waveform.map((value) => clampValue(value, 0, 1))
      : Array.from({ length: 160 }, (_, i) => 0.3 + 0.35 * Math.sin(i / 6) ** 2)

  return (
    <div className="absolute inset-0 flex items-center gap-[2px] px-2">
      {bars.map((height, index) => (
        <div
          key={`bar-${index}`}
          className="w-[2px] rounded-full bg-gradient-to-t from-vc-accent-primary/70 via-vc-accent-secondary/70 to-vc-accent-tertiary/70"
          style={{ height: `${clampValue(height, 0.08, 1) * 100}%`, opacity: 0.85 }}
        />
      ))}
    </div>
  )
}
