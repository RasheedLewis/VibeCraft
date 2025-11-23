import React, { useRef, useState, useEffect, useCallback } from 'react'
import clsx from 'clsx'
import { VCButton } from '../vibecraft'
import { ArrowRightIcon } from './Icons'

export interface AudioSelectionTimelineProps {
  audioUrl: string
  waveform: number[]
  durationSec: number
  beatTimes?: number[]
  initialStartSec?: number
  initialEndSec?: number
  onSelectionChange: (startSec: number, endSec: number) => void
  onConfirm?: () => void | Promise<void>
  confirmButtonDisabled?: boolean
  confirmButtonText?: string
  className?: string
}

const MAX_SELECTION_DURATION = 30.0
const MIN_SELECTION_DURATION = 9.0
const MARKER_HANDLE_WIDTH = 24 // Increased from 20 for easier grabbing

export const AudioSelectionTimeline: React.FC<AudioSelectionTimelineProps> = ({
  audioUrl,
  waveform,
  durationSec,
  beatTimes = [],
  initialStartSec,
  initialEndSec,
  onSelectionChange,
  onConfirm,
  confirmButtonDisabled = false,
  confirmButtonText = 'Confirm & Start Analysis',
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const [startSec, setStartSec] = useState<number>(
    initialStartSec ?? Math.max(0, durationSec - MAX_SELECTION_DURATION),
  )
  const [endSec, setEndSec] = useState<number>(
    initialEndSec ??
      Math.min(
        durationSec,
        (initialStartSec ?? Math.max(0, durationSec - MAX_SELECTION_DURATION)) +
          MAX_SELECTION_DURATION,
      ),
  )
  const [isDragging, setIsDragging] = useState<'start' | 'end' | 'range' | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playheadSec, setPlayheadSec] = useState<number>(startSec)
  const [hoverSec, setHoverSec] = useState<number | null>(null)
  const playheadIntervalRef = useRef<number | null>(null)
  const hasShownMinDurationAlertRef = useRef<boolean>(false)
  const [showMinDurationMessage, setShowMinDurationMessage] = useState(false)
  const minDurationMessageTimeoutRef = useRef<number | null>(null)

  // Validate and constrain selection
  useEffect(() => {
    const newStart = Math.max(0, startSec)
    let newEnd = Math.min(durationSec, endSec)

    if (newEnd <= newStart) {
      newEnd = Math.min(durationSec, newStart + MIN_SELECTION_DURATION)
    }

    const duration = newEnd - newStart
    if (duration > MAX_SELECTION_DURATION) {
      newEnd = newStart + MAX_SELECTION_DURATION
    }
    if (duration < MIN_SELECTION_DURATION) {
      newEnd = newStart + MIN_SELECTION_DURATION
    }

    // Only update state if values changed, otherwise notify parent
    if (newStart !== startSec || newEnd !== endSec) {
      // Use requestAnimationFrame to defer state update
      requestAnimationFrame(() => {
        setStartSec(newStart)
        setEndSec(newEnd)
      })
    } else {
      onSelectionChange(newStart, newEnd)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [startSec, endSec, durationSec])

  // Handle mouse drag for markers
  const handleMouseDown = useCallback(
    (marker: 'start' | 'end' | 'range', e: React.MouseEvent) => {
      e.preventDefault()
      e.stopPropagation()
      setIsDragging(marker)
    },
    [],
  )

  useEffect(() => {
    if (!isDragging || !containerRef.current) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return

      const rect = containerRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percent = Math.max(0, Math.min(1, x / rect.width))
      const time = percent * durationSec

      if (isDragging === 'start') {
        const attemptedDuration = endSec - time
        // Check if user is trying to select less than minimum duration
        if (
          attemptedDuration < MIN_SELECTION_DURATION &&
          !hasShownMinDurationAlertRef.current
        ) {
          setShowMinDurationMessage(true)
          hasShownMinDurationAlertRef.current = true
          // Clear any existing timeout
          if (minDurationMessageTimeoutRef.current) {
            clearTimeout(minDurationMessageTimeoutRef.current)
          }
          // Auto-dismiss after 4 seconds
          minDurationMessageTimeoutRef.current = window.setTimeout(() => {
            setShowMinDurationMessage(false)
            minDurationMessageTimeoutRef.current = null
          }, 4000)
        }
        const newStart = Math.max(0, Math.min(time, endSec - MIN_SELECTION_DURATION))
        setStartSec(newStart)
      } else if (isDragging === 'end') {
        const attemptedDuration = time - startSec
        // Check if user is trying to select less than minimum duration
        if (
          attemptedDuration < MIN_SELECTION_DURATION &&
          !hasShownMinDurationAlertRef.current
        ) {
          setShowMinDurationMessage(true)
          hasShownMinDurationAlertRef.current = true
          // Clear any existing timeout
          if (minDurationMessageTimeoutRef.current) {
            clearTimeout(minDurationMessageTimeoutRef.current)
          }
          // Auto-dismiss after 4 seconds
          minDurationMessageTimeoutRef.current = window.setTimeout(() => {
            setShowMinDurationMessage(false)
            minDurationMessageTimeoutRef.current = null
          }, 4000)
        }
        const newEnd = Math.max(time, startSec + MIN_SELECTION_DURATION)
        const constrainedEnd = Math.min(durationSec, newEnd)
        // Ensure duration doesn't exceed max
        if (constrainedEnd - startSec <= MAX_SELECTION_DURATION) {
          setEndSec(constrainedEnd)
        } else {
          setEndSec(startSec + MAX_SELECTION_DURATION)
        }
      } else if (isDragging === 'range') {
        // Move the entire selection while maintaining duration
        const currentDuration = endSec - startSec
        const centerTime = time
        const halfDuration = currentDuration / 2

        // Calculate new start and end positions
        let newStart = centerTime - halfDuration
        let newEnd = centerTime + halfDuration

        // Constrain to timeline bounds
        if (newStart < 0) {
          newStart = 0
          newEnd = currentDuration
        } else if (newEnd > durationSec) {
          newEnd = durationSec
          newStart = durationSec - currentDuration
        }

        setStartSec(newStart)
        setEndSec(newEnd)
      }
    }

    const handleMouseUp = () => {
      setIsDragging(null)
    }

    window.addEventListener('mousemove', handleMouseMove)
    window.addEventListener('mouseup', handleMouseUp)

    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      window.removeEventListener('mouseup', handleMouseUp)
    }
  }, [isDragging, durationSec, startSec, endSec])

  // Handle timeline click to set playhead
  const handleTimelineClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!containerRef.current || isDragging) return

      const rect = containerRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percent = Math.max(0, Math.min(1, x / rect.width))
      const time = percent * durationSec

      // If click is within selection, set playhead
      if (time >= startSec && time <= endSec) {
        if (audioRef.current) {
          audioRef.current.currentTime = time
          setPlayheadSec(time)
        }
      }
    },
    [durationSec, startSec, endSec, isDragging],
  )

  // Handle hover for time display
  const handleMouseMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percent = Math.max(0, Math.min(1, x / rect.width))
      setHoverSec(percent * durationSec)
    },
    [durationSec],
  )

  // Audio playback control
  const handlePlayPause = useCallback(() => {
    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
      setIsPlaying(false)
      if (playheadIntervalRef.current) {
        clearInterval(playheadIntervalRef.current)
        playheadIntervalRef.current = null
      }
    } else {
      // Set to start if playhead is outside selection
      if (playheadSec < startSec || playheadSec >= endSec) {
        audioRef.current.currentTime = startSec
        setPlayheadSec(startSec)
      }

      audioRef.current.play()
      setIsPlaying(true)

      // Update playhead during playback
      playheadIntervalRef.current = window.setInterval(() => {
        if (audioRef.current) {
          const time = audioRef.current.currentTime
          setPlayheadSec(time)

          // Stop at end marker
          if (time >= endSec) {
            audioRef.current.pause()
            audioRef.current.currentTime = startSec
            setIsPlaying(false)
            setPlayheadSec(startSec)
            if (playheadIntervalRef.current) {
              clearInterval(playheadIntervalRef.current)
              playheadIntervalRef.current = null
            }
          }
        }
      }, 50)
    }
  }, [isPlaying, playheadSec, startSec, endSec])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (playheadIntervalRef.current) {
        clearInterval(playheadIntervalRef.current)
      }
      if (minDurationMessageTimeoutRef.current) {
        clearTimeout(minDurationMessageTimeoutRef.current)
      }
    }
  }, [])

  // Format time helper
  const formatTime = (sec: number): string => {
    const minutes = Math.floor(sec / 60)
    const seconds = Math.floor(sec % 60)
    return `${minutes}:${seconds.toString().padStart(2, '0')}`
  }

  // Calculate positions
  const startPercent = (startSec / durationSec) * 100
  const endPercent = (endSec / durationSec) * 100
  const playheadPercent = (playheadSec / durationSec) * 100
  const hoverPercent = hoverSec !== null ? (hoverSec / durationSec) * 100 : null
  const selectionDuration = endSec - startSec
  const rangeCenterPercent = (startPercent + endPercent) / 2

  return (
    <div className={clsx('space-y-4', className)}>
      {/* Audio element (hidden) */}
      <audio
        ref={audioRef}
        src={audioUrl}
        preload="metadata"
        onTimeUpdate={() => {
          if (audioRef.current && isPlaying) {
            setPlayheadSec(audioRef.current.currentTime)
          }
        }}
        onEnded={() => {
          setIsPlaying(false)
          if (audioRef.current) {
            audioRef.current.currentTime = startSec
            setPlayheadSec(startSec)
          }
          if (playheadIntervalRef.current) {
            clearInterval(playheadIntervalRef.current)
            playheadIntervalRef.current = null
          }
        }}
      />

      {/* Playback controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={handlePlayPause}
          className="flex h-10 w-10 items-center justify-center rounded-full bg-vc-accent-primary/20 hover:bg-vc-accent-primary/30 transition-colors"
          aria-label={isPlaying ? 'Pause' : 'Play'}
        >
          {isPlaying ? (
            <svg
              className="h-5 w-5 text-vc-accent-primary"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg
              className="h-5 w-5 text-vc-accent-primary"
              fill="currentColor"
              viewBox="0 0 24 24"
            >
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>

        <div className="flex-1 text-sm text-vc-text-secondary -mt-1">
          <span className="tabular-nums">
            {formatTime(Math.max(0, playheadSec - startSec))} /{' '}
            {formatTime(selectionDuration)}
          </span>
          <span className="ml-2 text-vc-text-muted">
            ({formatTime(startSec)} - {formatTime(endSec)})
          </span>
        </div>
      </div>

      {/* Timeline container with range handle above */}
      <div className="relative">
        {/* Range handle - positioned above timeline */}
        <div
          className="absolute -top-6 left-0 right-0 h-6 z-30"
          style={{ pointerEvents: isDragging === 'range' ? 'auto' : 'auto' }}
        >
          <div
            className="absolute top-0 cursor-move group z-30"
            style={{
              left: `${rangeCenterPercent}%`,
              transform: 'translateX(-50%)',
              pointerEvents: 'auto',
            }}
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
              handleMouseDown('range', e)
            }}
          >
            <div className="flex flex-col items-center">
              {/* Handle icon/indicator */}
              <div className="h-3 w-8 rounded-t-md border-2 border-vc-accent-primary bg-vc-surface-primary shadow-lg hover:scale-110 transition-transform" />
              {/* Connecting line to timeline */}
              <div className="w-0.5 h-3 bg-vc-accent-primary/40" />
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div
          ref={containerRef}
          className="relative h-24 w-full cursor-pointer rounded-lg border border-vc-border/40 bg-[rgba(12,12,18,0.55)] overflow-hidden"
          onClick={handleTimelineClick}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverSec(null)}
          style={{ position: 'relative' }}
        >
          {/* Waveform background */}
          <div className="absolute inset-0 flex items-center gap-[2px] px-2">
            {waveform.length > 0
              ? waveform.slice(0, 512).map((value, idx) => {
                  const barTime = (idx / 512) * durationSec
                  const isInSelection = barTime >= startSec && barTime <= endSec
                  return (
                    <div
                      key={`bar-${idx}`}
                      className="w-[2px] rounded-full transition-opacity"
                      style={{
                        height: `${Math.max(8, value * 100)}%`,
                        opacity: isInSelection ? 0.9 : 0.3,
                        background: isInSelection
                          ? 'linear-gradient(to top, #6E6BFF, #FF6FF5, #00C6C0)'
                          : 'rgba(255, 255, 255, 0.2)',
                      }}
                    />
                  )
                })
              : // Placeholder bars when waveform data not available
                Array.from({ length: 100 }).map((_, idx) => (
                  <div
                    key={`placeholder-bar-${idx}`}
                    className="w-[2px] rounded-full bg-vc-border/20"
                    style={{
                      height: `${20 + (idx % 3) * 10}%`,
                    }}
                  />
                ))}
          </div>

          {/* Beat markers */}
          {beatTimes.map((beat, idx) => {
            const beatPercent = (beat / durationSec) * 100
            return (
              <div
                key={`beat-${idx}`}
                className="absolute top-0 bottom-0 w-px bg-white/20"
                style={{ left: `${beatPercent}%` }}
              />
            )
          })}

          {/* Selected region highlight */}
          <div
            className="absolute top-0 bottom-0 bg-vc-accent-primary/10 border-y border-vc-accent-primary/30 z-0"
            style={{
              left: `${startPercent}%`,
              width: `${endPercent - startPercent}%`,
            }}
          />

          {/* Start marker - higher z-index to ensure it's above other elements */}
          <div
            className="absolute top-0 bottom-0 cursor-ew-resize group z-20"
            style={{
              left: `${startPercent}%`,
              width: `${MARKER_HANDLE_WIDTH}px`,
              marginLeft: `-${MARKER_HANDLE_WIDTH / 2}px`,
              pointerEvents: 'auto', // Ensure it's clickable
            }}
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
              handleMouseDown('start', e)
            }}
          >
            <div className="absolute left-1/2 top-0 bottom-0 w-1 -translate-x-1/2 bg-vc-accent-primary pointer-events-none" />
            <div className="absolute left-1/2 top-0 h-4 w-4 -translate-x-1/2 rounded-full border-2 border-vc-accent-primary bg-vc-surface-primary shadow-lg hover:scale-110 transition-transform pointer-events-none" />
            <div className="absolute left-1/2 bottom-0 h-4 w-4 -translate-x-1/2 rounded-full border-2 border-vc-accent-primary bg-vc-surface-primary shadow-lg hover:scale-110 transition-transform pointer-events-none" />
          </div>

          {/* End marker - higher z-index to ensure it's above other elements */}
          <div
            className="absolute top-0 bottom-0 cursor-ew-resize group z-20"
            style={{
              left: `${endPercent}%`,
              width: `${MARKER_HANDLE_WIDTH}px`,
              marginLeft: `-${MARKER_HANDLE_WIDTH / 2}px`,
              pointerEvents: 'auto', // Ensure it's clickable
            }}
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
              handleMouseDown('end', e)
            }}
          >
            <div className="absolute left-1/2 top-0 bottom-0 w-1 -translate-x-1/2 bg-vc-accent-primary pointer-events-none" />
            <div className="absolute left-1/2 top-0 h-4 w-4 -translate-x-1/2 rounded-full border-2 border-vc-accent-primary bg-vc-surface-primary shadow-lg hover:scale-110 transition-transform pointer-events-none" />
            <div className="absolute left-1/2 bottom-0 h-4 w-4 -translate-x-1/2 rounded-full border-2 border-vc-accent-primary bg-vc-surface-primary shadow-lg hover:scale-110 transition-transform pointer-events-none" />
          </div>

          {/* Playhead */}
          {playheadSec >= startSec && playheadSec <= endSec && (
            <div
              className="absolute top-0 bottom-0 w-0.5 bg-white"
              style={{ left: `${playheadPercent}%` }}
            >
              <div className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 rounded-full bg-white" />
            </div>
          )}

          {/* Hover time indicator */}
          {hoverSec !== null && (
            <div
              className="absolute top-0 bottom-0 w-px bg-white/40"
              style={{ left: `${hoverPercent}%` }}
            />
          )}
        </div>
      </div>

      {/* Selection info */}
      <div className="flex items-center justify-between text-xs text-vc-text-secondary">
        <div>
          Selected:{' '}
          <span className="tabular-nums font-medium text-vc-text-primary">
            {selectionDuration.toFixed(1)}s
          </span>
          {selectionDuration > MAX_SELECTION_DURATION && (
            <span className="ml-2 text-vc-state-error">
              (Max: {MAX_SELECTION_DURATION}s)
            </span>
          )}
        </div>
        <div className="tabular-nums">
          {formatTime(startSec)} → {formatTime(endSec)}
        </div>
      </div>

      {/* Minimum duration message */}
      {showMinDurationMessage && (
        <div className="mt-2 rounded-lg border border-yellow-500/40 bg-[rgba(234,179,8,0.12)] px-3 py-2 text-xs text-yellow-400 transition-opacity duration-300">
          Minimum is 9 seconds
        </div>
      )}

      {/* Confirm button - shown at bottom when onConfirm is provided */}
      {onConfirm && (
        <div className="mt-4 flex justify-end">
          <VCButton
            variant="primary"
            size="md"
            onClick={(e) => {
              // Prevent click if disabled
              if (confirmButtonDisabled) {
                e.preventDefault()
                e.stopPropagation()
                return
              }
              onConfirm()
            }}
            disabled={confirmButtonDisabled}
            iconRight={<ArrowRightIcon />}
          >
            {confirmButtonText}
          </VCButton>
        </div>
      )}
    </div>
  )
}
