# Prerequisite Step 2: User Audio Selection (Up to 30s)

## Overview

This document outlines the plan and implementation details for adding a new UI step that allows users to select up to 30 seconds from their uploaded audio track. The selection interface will include draggable start and end markers on a waveform visualization, with audio preview starting from the playhead (start marker position).

**Goal**: Enable users to select a specific 30-second segment from their uploaded audio before proceeding with clip generation, improving control over which portion of their track gets processed into video.

---

## Current Architecture

### Upload Flow (Current State)

```text
1. User uploads audio file
2. Backend processes audio (preprocessing, analysis)
3. Frontend displays analysis results
4. User triggers clip generation (uses entire track)
5. Clips generated for full duration
```

### Target Flow (With Selection Step)

```text
1. User uploads audio file
2. Backend processes audio (preprocessing, analysis)
3. Frontend displays analysis results
4. **NEW: User selects 30s segment via interactive waveform**
5. **NEW: Backend stores selected range (start_sec, end_sec)**
6. User triggers clip generation (uses selected segment only)
7. Clips generated for selected 30s segment
```

---

## Feature Requirements

### Functional Requirements

1. **Selection Interface**
   - Display full audio waveform with beat markers
   - Draggable start marker (left handle)
   - Draggable end marker (right handle)
   - Visual highlight of selected region
   - Maximum selection: 30 seconds
   - Minimum selection: 1 second (or configurable)

2. **Audio Preview**
   - Play button that starts playback from start marker
   - Playback stops at end marker
   - Real-time playhead indicator showing current position
   - Playhead syncs with audio playback
   - Ability to pause/resume preview

3. **Validation**
   - Ensure end marker > start marker
   - Ensure selection duration ≤ 30 seconds
   - Ensure selection is within audio duration bounds
   - Show error messages for invalid selections

4. **Persistence**
   - Store selected range in database (Song model)
   - Persist selection across page refreshes
   - Allow user to modify selection before clip generation

5. **Integration**
   - Selection step appears after analysis completes
   - Selection must be completed before clip generation
   - Clip generation uses selected range instead of full duration

---

## Database Schema Changes

### Song Model Updates

#### File: `backend/app/models/song.py`

Add new fields to `Song` model:

```python
selected_start_sec: Optional[float] = Field(default=None, ge=0)
selected_end_sec: Optional[float] = Field(default=None, ge=0)
```

**Constraints**:

- Both fields are optional (backward compatible)
- `selected_start_sec` must be >= 0
- `selected_end_sec` must be > `selected_start_sec` (enforced in validation)
- `selected_end_sec - selected_start_sec` must be <= 30.0 (enforced in validation)

#### Migration

Create migration file: `backend/migrations/002_add_audio_selection_fields.py`

```python
"""Add audio selection fields to songs table.

Revision ID: 002
Revises: 001
Create Date: 2024-XX-XX
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('songs', sa.Column('selected_start_sec', sa.Float(), nullable=True))
    op.add_column('songs', sa.Column('selected_end_sec', sa.Float(), nullable=True))

def downgrade():
    op.drop_column('songs', 'selected_end_sec')
    op.drop_column('songs', 'selected_start_sec')
```

---

## Backend API Changes

### 1. Update Song Schema

#### File: `backend/app/schemas/song.py`

Add fields to `SongRead`:

```python
selected_start_sec: Optional[float] = None
selected_end_sec: Optional[float] = None
```

### 2. New Endpoint: Update Audio Selection

#### File: `backend/app/api/v1/routes_songs.py`

Add new endpoint:

```python
@router.patch(
    "/{song_id}/selection",
    response_model=SongRead,
    summary="Update audio selection range",
)
async def update_audio_selection(
    song_id: UUID,
    selection: AudioSelectionUpdate,
    db: Session = Depends(get_db),
) -> Song:
    """Update the selected audio segment for a song."""
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    if song.duration_sec is None:
        raise HTTPException(
            status_code=400,
            detail="Song duration not available. Please wait for analysis to complete."
        )
    
    # Validate selection
    start_sec = selection.start_sec
    end_sec = selection.end_sec
    
    if start_sec < 0:
        raise HTTPException(status_code=400, detail="Start time must be >= 0")
    
    if end_sec > song.duration_sec:
        raise HTTPException(
            status_code=400,
            detail=f"End time ({end_sec}s) exceeds song duration ({song.duration_sec}s)"
        )
    
    if end_sec <= start_sec:
        raise HTTPException(
            status_code=400,
            detail="End time must be greater than start time"
        )
    
    duration = end_sec - start_sec
    MAX_SELECTION_DURATION = 30.0
    if duration > MAX_SELECTION_DURATION:
        raise HTTPException(
            status_code=400,
            detail=f"Selection duration ({duration:.1f}s) exceeds maximum ({MAX_SELECTION_DURATION}s)"
        )
    
    MIN_SELECTION_DURATION = 1.0
    if duration < MIN_SELECTION_DURATION:
        raise HTTPException(
            status_code=400,
            detail=f"Selection duration ({duration:.1f}s) is below minimum ({MIN_SELECTION_DURATION}s)"
        )
    
    # Update song
    song.selected_start_sec = start_sec
    song.selected_end_sec = end_sec
    db.add(song)
    db.commit()
    db.refresh(song)
    
    return song
```

### 3. New Schema: AudioSelectionUpdate

#### File: `backend/app/schemas/song.py`

Add new schema:

```python
class AudioSelectionUpdate(BaseModel):
    start_sec: float = Field(ge=0, description="Start time in seconds")
    end_sec: float = Field(gt=0, description="End time in seconds")
    
    @model_validator(mode='after')
    def validate_range(self) -> 'AudioSelectionUpdate':
        if self.end_sec <= self.start_sec:
            raise ValueError("end_sec must be greater than start_sec")
        duration = self.end_sec - self.start_sec
        if duration > 30.0:
            raise ValueError(f"Selection duration ({duration}s) exceeds maximum (30s)")
        if duration < 1.0:
            raise ValueError(f"Selection duration ({duration}s) is below minimum (1s)")
        return self
```

### 4. Update Clip Generation to Use Selection

#### File: `backend/app/services/clip_planning.py`

Modify clip planning to respect selected range:

```python
def plan_clips(
    song: Song,
    clip_count: int,
    max_clip_sec: float = 6.0,
) -> List[SongClip]:
    """
    Plan clips for a song, respecting audio selection if present.
    
    If song has selected_start_sec and selected_end_sec, clips will be
    planned only for that range. Otherwise, uses full duration.
    """
    # Determine effective duration and offset
    if song.selected_start_sec is not None and song.selected_end_sec is not None:
        effective_duration = song.selected_end_sec - song.selected_start_sec
        time_offset = song.selected_start_sec
    else:
        effective_duration = song.duration_sec or 0.0
        time_offset = 0.0
    
    # ... rest of planning logic using effective_duration ...
    # When creating clips, add time_offset to clip start times
```

#### File: `backend/app/services/clip_generation.py`

Update clip generation to use selected range:

```python
def run_clip_generation_job(
    song_id: UUID,
    job_id: str | None = None,
) -> dict[str, Any]:
    # ... existing code ...
    
    # Get song with selection
    song = session.get(Song, song_id)
    if not song:
        raise ValueError(f"Song {song_id} not found")
    
    # Determine audio range to use
    if song.selected_start_sec is not None and song.selected_end_sec is not None:
        audio_start_sec = song.selected_start_sec
        audio_end_sec = song.selected_end_sec
        logger.info(
            f"Using selected audio range: {audio_start_sec}s - {audio_end_sec}s "
            f"(duration: {audio_end_sec - audio_start_sec}s)"
        )
    else:
        audio_start_sec = 0.0
        audio_end_sec = song.duration_sec or 0.0
        logger.info(f"Using full audio duration: {audio_end_sec}s")
    
    # When processing audio for clips, extract segment:
    # - Use ffmpeg to extract audio segment: [audio_start_sec:audio_end_sec]
    # - Pass extracted segment to video generation
```

---

## Frontend Implementation

### 1. New Component: AudioSelectionTimeline

#### File: `frontend/src/components/upload/AudioSelectionTimeline.tsx`

Create new component for audio selection:

```typescript
import React, { useRef, useState, useEffect, useCallback } from 'react'
import clsx from 'clsx'

export interface AudioSelectionTimelineProps {
  audioUrl: string
  waveform: number[]
  durationSec: number
  beatTimes?: number[]
  initialStartSec?: number
  initialEndSec?: number
  onSelectionChange: (startSec: number, endSec: number) => void
  className?: string
}

const MAX_SELECTION_DURATION = 30.0
const MIN_SELECTION_DURATION = 1.0
const MARKER_WIDTH = 12
const MARKER_HANDLE_WIDTH = 20

export const AudioSelectionTimeline: React.FC<AudioSelectionTimelineProps> = ({
  audioUrl,
  waveform,
  durationSec,
  beatTimes = [],
  initialStartSec,
  initialEndSec,
  onSelectionChange,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const audioRef = useRef<HTMLAudioElement>(null)
  const [startSec, setStartSec] = useState<number>(
    initialStartSec ?? Math.max(0, durationSec - MAX_SELECTION_DURATION)
  )
  const [endSec, setEndSec] = useState<number>(
    initialEndSec ?? Math.min(durationSec, startSec + MAX_SELECTION_DURATION)
  )
  const [isDragging, setIsDragging] = useState<'start' | 'end' | null>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [playheadSec, setPlayheadSec] = useState<number>(startSec)
  const [hoverSec, setHoverSec] = useState<number | null>(null)
  const playheadIntervalRef = useRef<number | null>(null)

  // Validate and constrain selection
  useEffect(() => {
    let newStart = Math.max(0, startSec)
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
    
    if (newStart !== startSec || newEnd !== endSec) {
      setStartSec(newStart)
      setEndSec(newEnd)
    } else {
      onSelectionChange(newStart, newEnd)
    }
  }, [startSec, endSec, durationSec, onSelectionChange])

  // Handle mouse drag for markers
  const handleMouseDown = useCallback((marker: 'start' | 'end', e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(marker)
  }, [])

  useEffect(() => {
    if (!isDragging || !containerRef.current) return

    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return
      
      const rect = containerRef.current.getBoundingClientRect()
      const x = e.clientX - rect.left
      const percent = Math.max(0, Math.min(1, x / rect.width))
      const time = percent * durationSec

      if (isDragging === 'start') {
        const newStart = Math.max(0, Math.min(time, endSec - MIN_SELECTION_DURATION))
        setStartSec(newStart)
      } else if (isDragging === 'end') {
        const newEnd = Math.max(time, startSec + MIN_SELECTION_DURATION)
        const constrainedEnd = Math.min(durationSec, newEnd)
        // Ensure duration doesn't exceed max
        if (constrainedEnd - startSec <= MAX_SELECTION_DURATION) {
          setEndSec(constrainedEnd)
        } else {
          setEndSec(startSec + MAX_SELECTION_DURATION)
        }
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
  const handleTimelineClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
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
  }, [durationSec, startSec, endSec, isDragging])

  // Handle hover for time display
  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return
    const rect = containerRef.current.getBoundingClientRect()
    const x = e.clientX - rect.left
    const percent = Math.max(0, Math.min(1, x / rect.width))
    setHoverSec(percent * durationSec)
  }, [durationSec])

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
            <svg className="h-5 w-5 text-vc-accent-primary" fill="currentColor" viewBox="0 0 24 24">
              <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
            </svg>
          ) : (
            <svg className="h-5 w-5 text-vc-accent-primary" fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          )}
        </button>
        
        <div className="flex-1 text-sm text-vc-text-secondary">
          <span className="tabular-nums">
            {formatTime(playheadSec)} / {formatTime(selectionDuration)}
          </span>
          <span className="ml-2 text-vc-text-muted">
            ({formatTime(startSec)} - {formatTime(endSec)})
          </span>
        </div>
      </div>

      {/* Timeline */}
      <div
        ref={containerRef}
        className="relative h-24 w-full cursor-pointer rounded-lg border border-vc-border/40 bg-[rgba(12,12,18,0.55)] overflow-hidden"
        onClick={handleTimelineClick}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoverSec(null)}
      >
        {/* Waveform background */}
        <div className="absolute inset-0 flex items-center gap-[2px] px-2">
          {waveform.slice(0, 512).map((value, idx) => {
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
          })}
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
          className="absolute top-0 bottom-0 bg-vc-accent-primary/10 border-y border-vc-accent-primary/30"
          style={{
            left: `${startPercent}%`,
            width: `${endPercent - startPercent}%`,
          }}
        />

        {/* Start marker */}
        <div
          className="absolute top-0 bottom-0 cursor-ew-resize group"
          style={{ left: `${startPercent}%`, width: `${MARKER_HANDLE_WIDTH}px`, marginLeft: `-${MARKER_HANDLE_WIDTH / 2}px` }}
          onMouseDown={(e) => handleMouseDown('start', e)}
        >
          <div className="absolute left-1/2 top-0 bottom-0 w-1 -translate-x-1/2 bg-vc-accent-primary" />
          <div className="absolute left-1/2 top-0 h-3 w-3 -translate-x-1/2 rounded-full border-2 border-vc-accent-primary bg-vc-surface-primary" />
          <div className="absolute left-1/2 bottom-0 h-3 w-3 -translate-x-1/2 rounded-full border-2 border-vc-accent-primary bg-vc-surface-primary" />
        </div>

        {/* End marker */}
        <div
          className="absolute top-0 bottom-0 cursor-ew-resize group"
          style={{ left: `${endPercent}%`, width: `${MARKER_HANDLE_WIDTH}px`, marginLeft: `-${MARKER_HANDLE_WIDTH / 2}px` }}
          onMouseDown={(e) => handleMouseDown('end', e)}
        >
          <div className="absolute left-1/2 top-0 bottom-0 w-1 -translate-x-1/2 bg-vc-accent-primary" />
          <div className="absolute left-1/2 top-0 h-3 w-3 -translate-x-1/2 rounded-full border-2 border-vc-accent-primary bg-vc-surface-primary" />
          <div className="absolute left-1/2 bottom-0 h-3 w-3 -translate-x-1/2 rounded-full border-2 border-vc-accent-primary bg-vc-surface-primary" />
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

      {/* Selection info */}
      <div className="flex items-center justify-between text-xs text-vc-text-secondary">
        <div>
          Selected: <span className="tabular-nums font-medium text-vc-text-primary">
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
    </div>
  )
}
```

### 2. Update UploadPage to Include Selection Step

#### File: `frontend/src/pages/UploadPage.tsx`

Add selection state and UI:

```typescript
// Add to state
const [audioSelection, setAudioSelection] = useState<{
  startSec: number
  endSec: number
} | null>(null)
const [isSavingSelection, setIsSavingSelection] = useState(false)

// Add handler for selection changes
const handleSelectionChange = useCallback(
  async (startSec: number, endSec: number) => {
    if (!result?.songId) return
    
    setAudioSelection({ startSec, endSec })
    setIsSavingSelection(true)
    
    try {
      await apiClient.patch(`/songs/${result.songId}/selection`, {
        start_sec: startSec,
        end_sec: endSec,
      })
    } catch (err) {
      console.error('Failed to save audio selection:', err)
      // Don't show error to user - selection is saved locally
    } finally {
      setIsSavingSelection(false)
    }
  },
  [result?.songId]
)

// Load existing selection when song loads
useEffect(() => {
  if (songDetails?.selected_start_sec !== undefined && 
      songDetails?.selected_end_sec !== undefined) {
    setAudioSelection({
      startSec: songDetails.selected_start_sec,
      endSec: songDetails.selected_end_sec,
    })
  }
}, [songDetails])

// In render, add selection step after analysis completes
{analysisState === 'completed' && analysisData && songDetails && (
  <div className="vc-app-main mx-auto w-full max-w-6xl px-4 py-12">
    {/* Audio Selection Step */}
    {!audioSelection && (
      <section className="mb-8 space-y-4">
        <div className="vc-label">Select Audio Segment (Up to 30s)</div>
        <p className="text-sm text-vc-text-secondary">
          Choose up to 30 seconds from your track to generate video clips.
        </p>
        <AudioSelectionTimeline
          audioUrl={result?.audioUrl ?? ''}
          waveform={waveformValues}
          durationSec={songDetails.duration_sec ?? 0}
          beatTimes={analysisData.beatTimes}
          onSelectionChange={handleSelectionChange}
        />
        {audioSelection && (
          <div className="flex justify-end">
            <VCButton
              onClick={() => {
                // Selection is saved automatically, proceed
                setAudioSelection(audioSelection)
              }}
            >
              Continue with Selection
            </VCButton>
          </div>
        )}
      </section>
    )}

    {/* Rest of SongProfileView */}
    {audioSelection && (
      <SongProfileView
        // ... existing props ...
      />
    )}
  </div>
)}
```

### 3. Update Types

#### File: `frontend/src/types/song.ts`

Add fields to `SongRead`:

```typescript
export interface SongRead {
  // ... existing fields ...
  selected_start_sec?: number
  selected_end_sec?: number
}
```

---

## Integration Points

### 1. Clip Planning Service

When planning clips, use selected range if available:

```python
# backend/app/services/clip_planning.py
def plan_clips(song: Song, clip_count: int, max_clip_sec: float = 6.0) -> List[SongClip]:
    # Determine effective range
    if song.selected_start_sec is not None and song.selected_end_sec is not None:
        effective_start = song.selected_start_sec
        effective_end = song.selected_end_sec
        effective_duration = effective_end - effective_start
    else:
        effective_start = 0.0
        effective_end = song.duration_sec or 0.0
        effective_duration = effective_end - effective_start
    
    # Plan clips within effective range
    # ... planning logic ...
    
    # When creating clips, add effective_start offset to clip start times
    for i, clip_start in enumerate(clip_starts):
        clip = SongClip(
            song_id=song.id,
            start_sec=effective_start + clip_start,  # Add offset
            end_sec=effective_start + clip_end,
            # ... other fields ...
        )
```

### 2. Audio Processing for Clips

When generating clips, extract audio segment:

```python
# backend/app/services/clip_generation.py
def extract_audio_segment(
    audio_path: Path,
    start_sec: float,
    end_sec: float,
    output_path: Path,
) -> None:
    """Extract audio segment using ffmpeg."""
    cmd = [
        settings.ffmpeg_bin,
        '-i', str(audio_path),
        '-ss', str(start_sec),
        '-t', str(end_sec - start_sec),
        '-acodec', 'copy',  # or re-encode if needed
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
```

---

## UI/UX Considerations

### Visual Design

1. **Waveform Display**
   - Full waveform shown with dimmed non-selected regions
   - Selected region highlighted with accent color
   - Beat markers visible for timing reference

2. **Markers**
   - Start marker: Left handle, vertical line, circular grips
   - End marker: Right handle, vertical line, circular grips
   - Markers should be clearly draggable (cursor: ew-resize)
   - Visual feedback on hover (slight scale/glow)

3. **Playhead**
   - Thin vertical line indicating current playback position
   - Only visible within selected region during playback
   - Smooth animation as audio plays

4. **Feedback**
   - Show selection duration in real-time
   - Warn if selection exceeds 30s (visual + text)
   - Show time range (start → end) below timeline
   - Disable "Continue" button if selection invalid

### Interaction Patterns

1. **Dragging Markers**
   - Click and drag start/end markers
   - Constrain to valid range (0 to duration, max 30s)
   - Snap to beat markers (optional, can be toggle)

2. **Timeline Click**
   - Click within selection to set playhead
   - Click outside selection to move selection (optional)

3. **Keyboard Shortcuts** (optional)
   - Space: Play/pause
   - Left/Right arrows: Move playhead
   - Shift+Left/Right: Adjust selection start/end

---

## Testing Considerations

### Unit Tests

#### Backend

- `test_audio_selection_validation.py`
  - Test valid selections (1s to 30s)
  - Test invalid selections (too long, too short, negative)
  - Test boundary conditions (exactly 30s, exactly 1s)
  - Test selection outside audio duration

- `test_clip_planning_with_selection.py`
  - Test clip planning uses selected range
  - Test clips are generated within selected range
  - Test time offsets are correct

#### Frontend

- `test_AudioSelectionTimeline.tsx`
  - Test marker dragging
  - Test selection constraints
  - Test audio playback
  - Test playhead synchronization

### Integration Tests

- Test full flow: upload → select → generate clips
- Test selection persistence across page refresh
- Test clip generation uses selected range
- Test backward compatibility (songs without selection)

### Manual Testing Checklist

- [ ] Upload audio file
- [ ] Selection UI appears after analysis
- [ ] Can drag start marker
- [ ] Can drag end marker
- [ ] Selection constrained to 30s max
- [ ] Selection constrained to 1s min
- [ ] Play button starts from start marker
- [ ] Playback stops at end marker
- [ ] Playhead updates during playback
- [ ] Selection persists after page refresh
- [ ] Clip generation uses selected range
- [ ] Works with songs of various durations

---

## Implementation Checklist

### Phase 1: Database & Backend API

- [ ] Add `selected_start_sec` and `selected_end_sec` to Song model
- [ ] Create migration file
- [ ] Run migration
- [ ] Add fields to `SongRead` schema
- [ ] Create `AudioSelectionUpdate` schema
- [ ] Add validation logic
- [ ] Create PATCH `/songs/{song_id}/selection` endpoint
- [ ] Add unit tests for validation
- [ ] Add unit tests for endpoint

### Phase 2: Frontend Component

- [ ] Create `AudioSelectionTimeline` component
- [ ] Implement waveform display
- [ ] Implement draggable markers
- [ ] Implement audio playback with playhead
- [ ] Add selection constraints (30s max, 1s min)
- [ ] Add visual feedback and styling
- [ ] Add unit tests for component

### Phase 3: Integration

- [ ] Update `UploadPage` to show selection step
- [ ] Add selection state management
- [ ] Add API call to save selection
- [ ] Load existing selection on page load
- [ ] Update `SongRead` TypeScript type
- [ ] Test selection persistence

### Phase 4: Clip Generation Integration

- [ ] Update `clip_planning.py` to use selected range
- [ ] Update `clip_generation.py` to extract audio segment
- [ ] Test clip generation with selection
- [ ] Test backward compatibility (no selection)

### Phase 5: Testing & Polish

- [ ] Write integration tests
- [ ] Manual testing checklist
- [ ] Fix edge cases
- [ ] Performance optimization
- [ ] Accessibility review
- [ ] Mobile responsiveness (if needed)

---

## Edge Cases & Considerations

### 1. Songs Shorter Than 30s

- **Scenario**: User uploads 15s track
- **Solution**: Allow selection of entire track (up to available duration)

### 2. Selection Changed After Clips Generated

- **Scenario**: User generates clips, then changes selection
- **Solution**:
  - Option A: Prevent selection change after clips generated (disable UI)
  - Option B: Allow change, require re-generation of clips
  - **Recommended**: Option A (simpler, prevents confusion)

### 3. Selection Outside Audio Duration

- **Scenario**: User somehow sets end > duration (shouldn't happen with validation)
- **Solution**: Backend validation prevents this, frontend constrains to duration

### 4. Concurrent Selection Updates

- **Scenario**: Multiple tabs open, user changes selection in one
- **Solution**: Last write wins (standard behavior), or implement optimistic locking

### 5. Audio Preview Performance

- **Scenario**: Large audio files, seeking may be slow
- **Solution**:
  - Use `preload="metadata"` (already implemented)
  - Consider preloading selected segment only
  - Show loading state during seek

---

## Performance Considerations

### Frontend

- **Waveform Rendering**: Limit to 512 bars (already done)
- **Marker Dragging**: Use `requestAnimationFrame` for smooth updates
- **Audio Playback**: Use `setInterval` with 50ms (good balance)

### Backend

- **Validation**: Lightweight (just number comparisons)
- **Database**: Two float fields, minimal storage impact
- **Audio Extraction**: Only happens during clip generation (not on selection save)

---

## Rollback Plan

### If Issues Arise

1. **Disable Selection UI**: Hide `AudioSelectionTimeline` component
2. **Use Full Duration**: Clip generation falls back to full duration if selection is null
3. **Database**: Fields are nullable, no data loss
4. **No Breaking Changes**: Existing songs continue to work (selection is optional)

---

## Success Criteria

1. ✅ User can select up to 30s from uploaded audio
2. ✅ Selection interface is intuitive and responsive
3. ✅ Audio preview plays from start marker to end marker
4. ✅ Selection persists across page refreshes
5. ✅ Clip generation uses selected range
6. ✅ Backward compatibility maintained (songs without selection work)
7. ✅ All validation rules enforced (30s max, 1s min, within duration)
8. ✅ UI provides clear feedback and error messages

---

## Future Enhancements

### Potential Improvements

1. **Snap to Beats**: Option to snap markers to beat times
2. **Keyboard Shortcuts**: Arrow keys for fine-tuning selection
3. **Multiple Selections**: Allow multiple 30s segments (advanced)
4. **Selection Templates**: Preset selections (first 30s, last 30s, middle 30s)
5. **Waveform Zoom**: Zoom in/out for precise selection
6. **Selection History**: Undo/redo for selection changes
7. **Visual Waveform Enhancement**: Show frequency spectrum, not just amplitude

---

## Related Files Reference

### Backend Files

- `backend/app/models/song.py` - Song model
- `backend/app/schemas/song.py` - Song schemas
- `backend/app/api/v1/routes_songs.py` - Song API routes
- `backend/app/services/clip_planning.py` - Clip planning service
- `backend/app/services/clip_generation.py` - Clip generation service
- `backend/migrations/002_add_audio_selection_fields.py` - Migration (new)

### Frontend Files

- `frontend/src/components/upload/AudioSelectionTimeline.tsx` - Selection component (new)
- `frontend/src/pages/UploadPage.tsx` - Upload page
- `frontend/src/components/song/SongProfileView.tsx` - Song profile view
- `frontend/src/components/song/WaveformDisplay.tsx` - Waveform display (reference)
- `frontend/src/components/MainVideoPlayer.tsx` - Video player (reference for timeline)
- `frontend/src/types/song.ts` - TypeScript types

---

## Notes

- This is a **prerequisite** for the sync + consistency features outlined in the Friday Plan
- The 30-second selection aligns with the use case mentioned in the Friday Plan
- Selection is optional - if user doesn't select, system uses full duration (backward compatible)
- This feature improves user control and reduces processing time for long tracks
- The selection step appears after analysis to ensure waveform and beat data are available
