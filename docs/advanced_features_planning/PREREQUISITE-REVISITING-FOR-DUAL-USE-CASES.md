# Prerequisite Revisiting: Dual Use Cases (Full-Length vs 30-Second)

## Overview

This document outlines the plan to alter the business logic of Prerequisites 1 and 2 to support two distinct use cases:

1. **Full-Length Video** - Uses section-based generation (sections enabled, but user doesn't see section terminology)
2. **30-Second Short-Form Video** - Disables sections, uses direct clip generation, and presents audio selection UI

**Key Change**: Instead of a global feature flag, the user selects their use case **before analysis**, and this choice controls:
- Whether sections are enabled/disabled for that song
- Whether audio selection UI is shown
- The overall generation workflow

**Goal**: Provide a clear, user-friendly choice that optimizes the workflow for each use case without exposing technical details (like "sections") to the user.

---

## Current State

### Prerequisite 1 (Feature Flag)
- Global `ENABLE_SECTIONS` environment variable
- Controls section-based vs clip-based generation system-wide
- Default: `True` (sections enabled)

### Prerequisite 2 (Audio Selection)
- Audio selection UI appears **after** analysis completes
- User can select up to 30 seconds from their track
- Selection stored in `selected_start_sec` and `selected_end_sec` fields

### Current Flow
```
1. User uploads audio
2. Backend processes audio
3. Analysis runs (sections detected)
4. Audio selection UI appears (if implemented)
5. User triggers clip generation
```

---

## Target State

### New Flow
```
1. User uploads audio
2. **NEW: User selects video type (Full-Length OR 30-Second)**
3. Backend stores choice and sets per-song sections flag
4. Backend processes audio
5. Analysis runs (sections only if full-length selected)
6. **IF 30-Second selected: Audio selection UI appears**
7. User triggers clip generation
8. Generation uses appropriate workflow (sections vs clips)
```

---

## High-Level Architecture Changes

### 1. Per-Song Sections Control

**Current**: Global `ENABLE_SECTIONS` flag affects all songs
**Target**: Each song has its own `use_sections` field that controls behavior

**Rationale**: 
- User choice is per-song, not global
- Allows different songs to use different workflows
- More flexible for future features

### 2. Video Type Selection UI

**Location**: Before analysis, after upload
**Options**:
- "Full-Length Video" (sections enabled)
- "30-Second Video (Optimized for Short-Form Platforms)" (sections disabled)

**Design**: Must follow `docs/more/DESIGN_SYSTEM.md`

### 3. Conditional Audio Selection

**Current**: Audio selection always available after analysis
**Target**: Audio selection only shown when 30-second video type is selected

**Rationale**: Full-length videos use the entire track, so selection isn't needed

---

## Database Schema Changes

### Song Model Updates

#### File: `backend/app/models/song.py`

Add new field:
```python
video_type: Optional[str] = Field(default=None, max_length=32)
```

**Possible Values**:
- `"full_length"` - Full-length video with sections
- `"short_form"` - 30-second video without sections

**Alternative Approach** (Boolean):
```python
use_sections: Optional[bool] = Field(default=None)
```

**Recommendation**: Use `video_type` string for clarity and future extensibility (could add "medium_length" later)

#### Migration

Create migration file: `backend/migrations/003_add_video_type_field.py`

```python
"""Migration 003: Add video_type field to songs table.

This migration adds a video_type field that stores the user's choice
between full-length and short-form video generation.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import inspect, text
from app.core.database import engine

def migrate() -> None:
    """Add video_type field to songs table if it doesn't exist."""
    inspector = inspect(engine)
    
    if "songs" not in inspector.get_table_names():
        raise RuntimeError("songs table does not exist")
    
    existing_columns = {col["name"] for col in inspector.get_columns("songs")}
    
    if "video_type" not in existing_columns:
        database_url = str(engine.url)
        is_postgres = database_url.startswith("postgresql")
        
        with engine.begin() as conn:
            if is_postgres:
                alter_sql = 'ALTER TABLE songs ADD COLUMN IF NOT EXISTS video_type VARCHAR(32)'
            else:
                alter_sql = 'ALTER TABLE songs ADD COLUMN video_type VARCHAR(32)'
            
            try:
                conn.execute(text(alter_sql))
                print(f"  ✓ Added column: video_type")
            except Exception as e:
                error_msg = str(e).lower()
                if "already exists" in error_msg or "duplicate" in error_msg:
                    print(f"  ⚠ Column video_type already exists (skipping)")
                else:
                    raise RuntimeError(f"Failed to add column video_type: {e}") from e
    else:
        print("  Column video_type already exists")
```

---

## Backend API Changes

### 1. Update Song Schema

#### File: `backend/app/schemas/song.py`

Add field to `SongRead`:
```python
video_type: Optional[str] = None
```

### 2. New Endpoint: Set Video Type

#### File: `backend/app/api/v1/routes_songs.py`

Add new endpoint:
```python
@router.patch(
    "/{song_id}/video-type",
    response_model=SongRead,
    summary="Set video type for song",
)
def set_video_type(
    song_id: UUID,
    video_type: VideoTypeUpdate,
    db: Session = Depends(get_db),
) -> Song:
    """Set the video type (full-length or short-form) for a song.
    
    This must be set before analysis runs, as it affects the analysis
    and generation workflow.
    """
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    
    # Validate video type
    if video_type.video_type not in ["full_length", "short_form"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="video_type must be 'full_length' or 'short_form'",
        )
    
    # Prevent changing after analysis has started
    # (Check if analysis exists - this is a business rule)
    from app.services.song_analysis import get_latest_analysis
    existing_analysis = get_latest_analysis(song_id)
    if existing_analysis:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change video type after analysis has been completed. Please upload a new song.",
        )
    
    song.video_type = video_type.video_type
    db.add(song)
    db.commit()
    db.refresh(song)
    
    return song
```

### 3. New Schema: VideoTypeUpdate

#### File: `backend/app/schemas/song.py`

Add new schema:
```python
class VideoTypeUpdate(BaseModel):
    video_type: str = Field(description="Video type: 'full_length' or 'short_form'")
    
    @model_validator(mode='after')
    def validate_video_type(self) -> 'VideoTypeUpdate':
        if self.video_type not in ["full_length", "short_form"]:
            raise ValueError("video_type must be 'full_length' or 'short_form'")
        return self
```

### 4. Update Feature Flag Logic

#### File: `backend/app/core/config.py`

Add helper function to check per-song sections:
```python
def should_use_sections_for_song(song: Song) -> bool:
    """Determine if sections should be used for a specific song.
    
    Args:
        song: Song model instance
        
    Returns:
        True if sections should be used, False otherwise
    """
    # If video_type is set, use it
    if song.video_type == "full_length":
        return True
    elif song.video_type == "short_form":
        return False
    
    # Fallback to global flag for backward compatibility
    return is_sections_enabled()
```

### 5. Update Analysis Service

#### File: `backend/app/services/song_analysis.py`

Modify analysis to respect video type:
```python
def _execute_analysis_pipeline(song_id: UUID, job_id: str | None) -> dict[str, Any]:
    # ... existing code ...
    
    # Check if sections should be analyzed
    from app.core.database import session_scope
    from app.models.song import Song
    from app.core.config import should_use_sections_for_song
    
    with session_scope() as session:
        song = session.get(Song, song_id)
        if not song:
            raise ValueError(f"Song {song_id} not found")
        
        use_sections = should_use_sections_for_song(song)
        
        # Only run section inference if use_sections is True
        if use_sections:
            # Run section inference
            sections = infer_section_types(...)
        else:
            # Skip section inference for short-form videos
            sections = []
    
    # ... rest of analysis ...
```

### 6. Update Composition Services

#### Files: `backend/app/services/composition_execution.py`, `backend/app/services/composition_job.py`

Update to use per-song sections check:
```python
from app.core.config import should_use_sections_for_song

def execute_composition_pipeline(...):
    # Get song to check video type
    song = SongRepository.get_by_id(song_id)
    use_sections = should_use_sections_for_song(song)
    
    if use_sections:
        # Use SectionVideo model
        ...
    else:
        # Use SongClip model directly
        ...
```

---

## Frontend Implementation

### 1. New Component: VideoTypeSelector

#### File: `frontend/src/components/upload/VideoTypeSelector.tsx`

Create a new component following the design system:

```typescript
import React from 'react'
import clsx from 'clsx'

export interface VideoTypeSelectorProps {
  onSelect: (videoType: 'full_length' | 'short_form') => void
  selectedType?: 'full_length' | 'short_form' | null
  className?: string
}

export const VideoTypeSelector: React.FC<VideoTypeSelectorProps> = ({
  onSelect,
  selectedType,
  className,
}) => {
  return (
    <div className={clsx('space-y-4', className)}>
      <div className="vc-label">Choose Your Video Format</div>
      <p className="text-sm text-vc-text-secondary">
        Select the format that best fits your needs.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Full-Length Option */}
        <button
          onClick={() => onSelect('full_length')}
          className={clsx(
            'group relative rounded-2xl border-2 p-6 text-left transition-all',
            'hover:border-vc-accent-primary/50 hover:bg-vc-surface-primary/50',
            selectedType === 'full_length'
              ? 'border-vc-accent-primary bg-vc-accent-primary/10'
              : 'border-vc-border bg-vc-surface-primary',
          )}
        >
          <div className="flex items-start gap-4">
            <div className={clsx(
              'flex h-12 w-12 shrink-0 items-center justify-center rounded-full',
              'border-2 transition-colors',
              selectedType === 'full_length'
                ? 'border-vc-accent-primary bg-vc-accent-primary/20'
                : 'border-vc-border bg-vc-surface-primary',
            )}>
              {selectedType === 'full_length' && (
                <svg className="h-6 w-6 text-vc-accent-primary" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                </svg>
              )}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-vc-text-primary mb-1">
                Full-Length Video
              </h3>
              <p className="text-sm text-vc-text-secondary">
                Complete video covering your entire track. Perfect for music videos, 
                full releases, and comprehensive visual experiences.
              </p>
            </div>
          </div>
        </button>

        {/* Short-Form Option */}
        <button
          onClick={() => onSelect('short_form')}
          className={clsx(
            'group relative rounded-2xl border-2 p-6 text-left transition-all',
            'hover:border-vc-accent-primary/50 hover:bg-vc-surface-primary/50',
            selectedType === 'short_form'
              ? 'border-vc-accent-primary bg-vc-accent-primary/10'
              : 'border-vc-border bg-vc-surface-primary',
          )}
        >
          <div className="flex items-start gap-4">
            <div className={clsx(
              'flex h-12 w-12 shrink-0 items-center justify-center rounded-full',
              'border-2 transition-colors',
              selectedType === 'short_form'
                ? 'border-vc-accent-primary bg-vc-accent-primary/20'
                : 'border-vc-border bg-vc-surface-primary',
            )}>
              {selectedType === 'short_form' && (
                <svg className="h-6 w-6 text-vc-accent-primary" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                </svg>
              )}
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-vc-text-primary mb-1">
                30-Second Video
              </h3>
              <p className="text-sm text-vc-text-secondary">
                Optimized for short-form platforms. Select up to 30 seconds 
                from your track for TikTok, Instagram Reels, and YouTube Shorts.
              </p>
            </div>
          </div>
        </button>
      </div>
    </div>
  )
}
```

**Design System Compliance**:
- Uses `vc-*` color tokens
- Uses spacing scale (`space-4`, `space-6`, etc.)
- Uses border radius (`rounded-2xl`, `rounded-full`)
- Uses typography scale (`text-lg`, `text-sm`)
- Follows card component pattern
- Includes hover states and transitions
- Uses accent colors for selection state

### 2. Update UploadPage Flow

#### File: `frontend/src/pages/UploadPage.tsx`

Add video type selection step:

```typescript
// Add to state
const [videoType, setVideoType] = useState<'full_length' | 'short_form' | null>(null)
const [isSettingVideoType, setIsSettingVideoType] = useState(false)

// Add handler
const handleVideoTypeSelect = useCallback(
  async (type: 'full_length' | 'short_form') => {
    if (!result?.songId) return
    
    setVideoType(type)
    setIsSettingVideoType(true)
    
    try {
      await apiClient.patch(`/songs/${result.songId}/video-type`, {
        video_type: type,
      })
    } catch (err) {
      console.error('Failed to set video type:', err)
      setVideoType(null)
    } finally {
      setIsSettingVideoType(false)
    }
  },
  [result?.songId],
)

// Load existing video type when song loads
useEffect(() => {
  if (songDetails?.video_type) {
    setVideoType(songDetails.video_type as 'full_length' | 'short_form')
  }
}, [songDetails])

// In render, add video type selection step BEFORE analysis
{stage === 'uploaded' && !videoType && (
  <div className="vc-app-main mx-auto w-full max-w-4xl px-4 py-12">
    <VideoTypeSelector
      onSelect={handleVideoTypeSelect}
      selectedType={videoType}
    />
    {isSettingVideoType && (
      <div className="mt-4 text-sm text-vc-text-secondary text-center">
        Setting video type...
      </div>
    )}
  </div>
)}

// Only start analysis after video type is selected
{stage === 'uploaded' && videoType && !analysisState && (
  // Trigger analysis automatically or show button
)}
```

### 3. Conditional Audio Selection

#### File: `frontend/src/pages/UploadPage.tsx`

Update audio selection to only show for short-form:
```typescript
// Only show audio selection if short-form is selected
{analysisState === 'completed' && 
 analysisData && 
 songDetails && 
 videoType === 'short_form' && (
  // Audio selection UI
)}
```

### 4. Update TypeScript Types

#### File: `frontend/src/types/song.ts`

Add field to `SongRead`:
```typescript
export interface SongRead {
  // ... existing fields ...
  video_type?: 'full_length' | 'short_form' | null
}
```

---

## Integration Points

### 1. Upload Flow Integration

**Current Flow**:
1. Upload → Analysis → Selection → Generation

**New Flow**:
1. Upload → **Video Type Selection** → Analysis → **(Selection if short-form)** → Generation

### 2. Analysis Integration

The analysis service should:
- Check `song.video_type` before running section inference
- Skip section inference if `video_type === "short_form"`
- Still run beat detection, mood analysis, etc. (needed for both types)

### 3. Composition Integration

The composition service should:
- Check `should_use_sections_for_song(song)` to determine workflow
- Use `SectionVideo` model if sections enabled
- Use `SongClip` model if sections disabled

### 4. Backward Compatibility

**Existing Songs**:
- Songs without `video_type` set should use global `ENABLE_SECTIONS` flag
- This maintains backward compatibility

**Migration Strategy**:
- New songs: Require video type selection before analysis
- Old songs: Continue using global flag until user re-uploads

---

## UI/UX Considerations

### Design System Adherence

The `VideoTypeSelector` component must follow:
- **Color System**: Use `vc-accent-primary` for selection, `vc-border` for unselected
- **Typography**: Use display font for headings, UI font for body
- **Spacing**: Use spacing scale (16px, 24px, 32px)
- **Motion**: Smooth transitions on selection (250ms)
- **Elevation**: Cards use `--elev-1` shadow
- **Accessibility**: Clear labels, keyboard navigation, focus states

### User Experience Flow

1. **Upload Step**: User uploads audio file
2. **Video Type Selection**: 
   - Clear, prominent choice between two options
   - Visual distinction between selected/unselected
   - Descriptive text for each option
   - No technical jargon (don't mention "sections")
3. **Analysis Step**: 
   - Show progress as before
   - User understands analysis is running
4. **Audio Selection** (if short-form):
   - Only appears for short-form videos
   - Same UI as before
5. **Generation Step**: 
   - Proceeds as normal
   - User doesn't need to know about sections vs clips

### Error Handling

- If user tries to change video type after analysis: Show clear error
- If video type not set before analysis: Prevent analysis from starting
- If API call fails: Show error, allow retry

---

## Testing Considerations

### Unit Tests

#### Backend
- `test_video_type_validation.py`
  - Test valid video types
  - Test invalid video types
  - Test changing after analysis (should fail)
  
- `test_per_song_sections.py`
  - Test `should_use_sections_for_song()` with different video types
  - Test fallback to global flag
  - Test analysis respects video type

#### Frontend
- `test_VideoTypeSelector.tsx`
  - Test selection interaction
  - Test visual states
  - Test accessibility

### Integration Tests

- Test full flow: upload → select type → analyze → (select audio if short-form) → generate
- Test backward compatibility (songs without video_type)
- Test error cases (changing type after analysis)

### Manual Testing Checklist

- [ ] Upload audio file
- [ ] Video type selector appears
- [ ] Can select full-length
- [ ] Can select short-form
- [ ] Selection persists after page refresh
- [ ] Analysis only runs after type selected
- [ ] Audio selection appears only for short-form
- [ ] Full-length videos don't show audio selection
- [ ] Cannot change type after analysis
- [ ] Error messages are clear
- [ ] Design system colors/spacing are correct
- [ ] Keyboard navigation works
- [ ] Mobile responsive

---

## Implementation Checklist

### Phase 1: Database & Backend API
- [ ] Add `video_type` field to Song model
- [ ] Create migration file
- [ ] Run migration
- [ ] Add field to `SongRead` schema
- [ ] Create `VideoTypeUpdate` schema
- [ ] Add PATCH `/songs/{song_id}/video-type` endpoint
- [ ] Add `should_use_sections_for_song()` helper function
- [ ] Update analysis service to respect video type
- [ ] Update composition services to use per-song check
- [ ] Add unit tests

### Phase 2: Frontend Component
- [ ] Create `VideoTypeSelector` component
- [ ] Follow design system guidelines
- [ ] Add selection states and animations
- [ ] Add accessibility features
- [ ] Add unit tests

### Phase 3: Upload Flow Integration
- [ ] Update `UploadPage` to show video type selector
- [ ] Add video type state management
- [ ] Add API call to set video type
- [ ] Prevent analysis until type is selected
- [ ] Load existing video type on page load
- [ ] Update TypeScript types

### Phase 4: Conditional Audio Selection
- [ ] Update audio selection to only show for short-form
- [ ] Hide audio selection for full-length videos
- [ ] Test conditional rendering

### Phase 5: Testing & Polish
- [ ] Write integration tests
- [ ] Manual testing checklist
- [ ] Fix edge cases
- [ ] Performance optimization
- [ ] Accessibility review
- [ ] Mobile responsiveness

---

## Edge Cases & Considerations

### 1. Existing Songs Without Video Type

**Scenario**: Songs uploaded before this feature
**Solution**: Use global `ENABLE_SECTIONS` flag as fallback

### 2. User Changes Mind After Analysis

**Scenario**: User wants to change video type after analysis
**Solution**: Prevent change, show clear error message. User must re-upload.

### 3. Analysis Already Running

**Scenario**: User selects video type while analysis is in progress
**Solution**: Prevent type change, show error message

### 4. Backend Restart

**Scenario**: Backend restarts, loses in-memory state
**Solution**: Video type is stored in database, persists across restarts

### 5. Frontend Refresh

**Scenario**: User refreshes page after selecting type
**Solution**: Load video type from `songDetails` on page load

---

## Migration Strategy

### Backward Compatibility

1. **Database**: `video_type` field is nullable
2. **Backend**: Falls back to global flag if `video_type` is null
3. **Frontend**: Shows selector for new uploads, works with existing songs

### Rollout Plan

1. **Phase 1**: Deploy backend changes (backward compatible)
2. **Phase 2**: Deploy frontend changes
3. **Phase 3**: Monitor usage, gather feedback
4. **Phase 4**: Consider making video type required for new uploads

---

## Success Criteria

1. ✅ User can select video type before analysis
2. ✅ Selection persists across page refreshes
3. ✅ Full-length videos use sections (user doesn't see this)
4. ✅ Short-form videos disable sections and show audio selection
5. ✅ Cannot change type after analysis
6. ✅ Backward compatibility maintained
7. ✅ Design system guidelines followed
8. ✅ Clear, user-friendly language (no technical jargon)
9. ✅ All tests pass
10. ✅ Mobile responsive

---

## Related Files Reference

### Backend Files
- `backend/app/models/song.py` - Song model (add video_type)
- `backend/app/schemas/song.py` - Song schemas (add VideoTypeUpdate)
- `backend/app/api/v1/routes_songs.py` - Song API routes (add endpoint)
- `backend/app/core/config.py` - Config (add should_use_sections_for_song)
- `backend/app/services/song_analysis.py` - Analysis service (respect video_type)
- `backend/app/services/composition_execution.py` - Composition (use per-song check)
- `backend/migrations/003_add_video_type_field.py` - Migration (new)

### Frontend Files
- `frontend/src/components/upload/VideoTypeSelector.tsx` - Selector component (new)
- `frontend/src/pages/UploadPage.tsx` - Upload page (add selection step)
- `frontend/src/types/song.ts` - TypeScript types (add video_type)

---

## Notes

- This change makes the feature flag per-song rather than global
- The user-facing language avoids technical terms like "sections"
- Full-length videos still use sections internally, but user doesn't need to know
- Short-form videos are optimized for 30-second clips on social platforms
- The audio selection UI is only relevant for short-form videos
- This aligns with the Friday Plan's focus on 30-second use case while maintaining full-length capability

