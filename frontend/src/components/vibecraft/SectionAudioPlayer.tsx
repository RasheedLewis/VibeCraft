import React, { useRef, useEffect, useState } from 'react'
import clsx from 'clsx'

export interface SectionAudioPlayerProps {
  audioUrl: string
  startSec: number
  endSec: number
  className?: string
}

export const SectionAudioPlayer: React.FC<SectionAudioPlayerProps> = ({
  audioUrl,
  startSec,
  endSec,
  className,
}) => {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const intervalRef = useRef<number | null>(null)

  const duration = endSec - startSec

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  const handlePlayPause = () => {
    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      setIsPlaying(false)
    } else {
      // Set to start time if not already in range
      if (
        audioRef.current.currentTime < startSec ||
        audioRef.current.currentTime >= endSec
      ) {
        audioRef.current.currentTime = startSec
      }

      audioRef.current.play()
      setIsPlaying(true)

      // Monitor playback and stop at end
      intervalRef.current = window.setInterval(() => {
        if (audioRef.current) {
          const time = audioRef.current.currentTime
          setCurrentTime(time - startSec)

          if (time >= endSec) {
            audioRef.current.pause()
            audioRef.current.currentTime = startSec
            setIsPlaying(false)
            setCurrentTime(0)
            if (intervalRef.current !== null) {
              clearInterval(intervalRef.current)
              intervalRef.current = null
            }
          }
        }
      }, 100)
    }
  }

  const handleTimeUpdate = () => {
    if (!audioRef.current || !isPlaying) return
    const time = audioRef.current.currentTime

    // Stop if we've gone past the end
    if (time >= endSec) {
      audioRef.current.pause()
      audioRef.current.currentTime = startSec
      setIsPlaying(false)
      setCurrentTime(0)
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }

  const handleEnded = () => {
    setIsPlaying(false)
    setCurrentTime(0)
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  const formatTime = (sec: number) => {
    const minutes = Math.floor(sec / 60)
    const seconds = Math.floor(sec % 60)
      .toString()
      .padStart(2, '0')
    return `${minutes}:${seconds}`
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className={clsx('flex items-center gap-3', className)}>
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleEnded}
        preload="metadata"
      />

      <button
        onClick={handlePlayPause}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-vc-accent-primary/20 hover:bg-vc-accent-primary/30 transition-colors"
        aria-label={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? (
          <svg
            className="h-4 w-4 text-vc-accent-primary"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
          </svg>
        ) : (
          <svg
            className="h-4 w-4 text-vc-accent-primary"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </button>

      <div className="flex-1">
        <div className="h-1.5 w-full rounded-full bg-vc-surface-tertiary overflow-hidden">
          <div
            className="h-full bg-vc-accent-primary transition-all duration-100"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <span className="text-xs text-vc-text-secondary tabular-nums">
        {formatTime(currentTime)} / {formatTime(duration)}
      </span>
    </div>
  )
}

