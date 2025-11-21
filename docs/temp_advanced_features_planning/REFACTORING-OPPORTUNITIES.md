# Refactoring Opportunities Assessment

**Date**: After implementing Prerequisites 1 & 2 (Dual Use Case)

This document identifies refactoring opportunities in the newly written code to improve maintainability, reduce duplication, and enhance type safety.

---

## 🔴 High Priority Refactorings

### 1. Extract Clip Model Selection Logic (Code Duplication)

**Problem**: The same if/else pattern for selecting `SectionVideo` vs `SongClip` is duplicated in:
- `backend/app/services/composition_execution.py` (lines 98-118)
- `backend/app/services/composition_job.py` (lines 57-76)

**Current Code Pattern** (repeated twice):
```python
use_sections = should_use_sections_for_song(song)
if use_sections:
    clip = session.get(SectionVideo, clip_id)
    if not clip:
        raise ClipNotFoundError(f"SectionVideo {clip_id} not found")
    # ... validation ...
else:
    clip = session.get(SongClip, clip_id)
    if not clip:
        raise ClipNotFoundError(f"SongClip {clip_id} not found")
    # ... validation ...
```

**Refactoring Solution**:
Create a helper function in a new module or existing service:

```python
# backend/app/services/clip_model_selector.py (new file)
from typing import TypeVar, Protocol
from uuid import UUID
from sqlmodel import Session

from app.models.clip import SongClip
from app.models.section_video import SectionVideo
from app.exceptions import ClipNotFoundError, CompositionError
from app.core.config import should_use_sections_for_song
from app.models.song import Song

T = TypeVar('T', SongClip, SectionVideo)

class ClipModel(Protocol):
    """Protocol for clip models."""
    id: UUID
    song_id: UUID
    status: str
    video_url: str | None

def get_clip_model_class(use_sections: bool) -> type[SongClip] | type[SectionVideo]:
    """Get the appropriate clip model class based on sections flag."""
    return SectionVideo if use_sections else SongClip

def get_and_validate_clip(
    session: Session,
    clip_id: UUID,
    song_id: UUID,
    use_sections: bool,
) -> SongClip | SectionVideo:
    """
    Get and validate a clip based on video_type.
    
    Args:
        session: Database session
        clip_id: Clip ID to retrieve
        song_id: Expected song ID
        use_sections: Whether to use SectionVideo or SongClip
        
    Returns:
        Validated clip instance
        
    Raises:
        ClipNotFoundError: If clip not found
        CompositionError: If clip doesn't belong to song or isn't ready
    """
    model_class = get_clip_model_class(use_sections)
    clip = session.get(model_class, clip_id)
    
    if not clip:
        model_name = model_class.__name__
        raise ClipNotFoundError(f"{model_name} {clip_id} not found")
    
    if clip.song_id != song_id:
        model_name = model_class.__name__
        raise CompositionError(f"{model_name} {clip_id} does not belong to song {song_id}")
    
    if clip.status != "completed" or not clip.video_url:
        model_name = model_class.__name__
        raise CompositionError(f"{model_name} {clip_id} is not ready (status: {clip.status})")
    
    return clip

def get_clips_for_composition(
    session: Session,
    clip_ids: list[UUID],
    song: Song,
) -> tuple[list[SongClip | SectionVideo], list[str]]:
    """
    Get and validate all clips for composition.
    
    Returns:
        Tuple of (clips, clip_urls)
    """
    use_sections = should_use_sections_for_song(song)
    clips = []
    clip_urls = []
    
    for clip_id in clip_ids:
        clip = get_and_validate_clip(session, clip_id, song.id, use_sections)
        clips.append(clip)
        clip_urls.append(clip.video_url)
    
    return clips, clip_urls
```

**Benefits**:
- Eliminates ~40 lines of duplicated code
- Single source of truth for clip validation logic
- Easier to test
- Easier to extend (e.g., add new clip types)

**Effort**: 2-3 hours

---

### 2. Replace Magic Strings with Constants/Enum

**Problem**: `"full_length"` and `"short_form"` are repeated as string literals throughout:
- `backend/app/core/config.py` (line 103)
- `backend/app/api/v1/routes_songs.py` (lines 289, 303)
- `backend/app/schemas/song.py` (lines 67, 68)
- `frontend/src/pages/UploadPage.tsx` (multiple places)
- `frontend/src/types/song.ts` (line 523)
- `frontend/src/components/upload/VideoTypeSelector.tsx` (multiple places)

**Refactoring Solution**:

**Backend**:
```python
# backend/app/core/constants.py (or add to existing constants.py)
from enum import Enum

class VideoType(str, Enum):
    """Video type enumeration."""
    FULL_LENGTH = "full_length"
    SHORT_FORM = "short_form"
    
    @classmethod
    def values(cls) -> list[str]:
        """Get all valid values."""
        return [item.value for item in cls]
```

**Frontend**:
```typescript
// frontend/src/constants/videoType.ts
export const VIDEO_TYPE = {
  FULL_LENGTH: 'full_length',
  SHORT_FORM: 'short_form',
} as const

export type VideoType = typeof VIDEO_TYPE[keyof typeof VIDEO_TYPE]
```

**Benefits**:
- Type safety (prevents typos)
- IDE autocomplete
- Single source of truth
- Easier refactoring

**Effort**: 1-2 hours

---

### 3. Improve Type Safety in `should_use_sections_for_song()`

**Problem**: Uses `Any` type and `hasattr()` checks:

```python
def should_use_sections_for_song(song: Any) -> bool:
    if hasattr(song, 'video_type') and song.video_type:
        return song.video_type == "full_length"
    return False
```

**Refactoring Solution**:

```python
from typing import Protocol
from app.models.song import Song

class HasVideoType(Protocol):
    """Protocol for objects with video_type attribute."""
    video_type: str | None

def should_use_sections_for_song(song: Song | HasVideoType) -> bool:
    """Determine if sections should be used for a specific song.
    
    Args:
        song: Song model instance (or any object with video_type attribute)
        
    Returns:
        True if sections should be used, False otherwise
    """
    if song.video_type:
        return song.video_type == VideoType.FULL_LENGTH.value
    return False
```

**Benefits**:
- Better type hints
- IDE support
- Removes runtime `hasattr()` check

**Effort**: 30 minutes

---

### 4. Extract Audio Selection Validation Logic

**Problem**: Audio selection validation is duplicated:
- `backend/app/schemas/song.py` (AudioSelectionUpdate validator)
- `backend/app/api/v1/routes_songs.py` (update_audio_selection endpoint)

**Current**: Validation happens in both schema and endpoint.

**Refactoring Solution**:

```python
# backend/app/services/audio_selection.py (new file)
from app.models.song import Song
from app.exceptions import ValidationError

MAX_SELECTION_DURATION_SEC = 30.0
MIN_SELECTION_DURATION_SEC = 1.0

def validate_audio_selection(
    start_sec: float,
    end_sec: float,
    song_duration_sec: float | None,
) -> None:
    """
    Validate audio selection parameters.
    
    Raises:
        ValueError: If validation fails
    """
    if song_duration_sec is None:
        raise ValueError("Song duration not available")
    
    if start_sec < 0:
        raise ValueError("Start time must be >= 0")
    
    if end_sec > song_duration_sec:
        raise ValueError(f"End time ({end_sec}s) exceeds song duration ({song_duration_sec}s)")
    
    if end_sec <= start_sec:
        raise ValueError("End time must be greater than start time")
    
    duration = end_sec - start_sec
    if duration > MAX_SELECTION_DURATION_SEC:
        raise ValueError(f"Selection duration ({duration:.1f}s) exceeds maximum ({MAX_SELECTION_DURATION_SEC}s)")
    
    if duration < MIN_SELECTION_DURATION_SEC:
        raise ValueError(f"Selection duration ({duration:.1f}s) is below minimum ({MIN_SELECTION_DURATION_SEC}s)")
```

Then use in both schema and endpoint.

**Benefits**:
- Single source of truth for validation
- Reusable across schema and endpoint
- Easier to test
- Constants extracted

**Effort**: 1 hour

---

## 🟡 Medium Priority Refactorings

### 5. Consolidate Frontend State Management

**Problem**: `UploadPage.tsx` has many individual state variables:
- `videoType`, `isSettingVideoType`
- `audioSelection`, `isSavingSelection`
- `stage`, `error`, `progress`, `metadata`, `result`
- `songDetails`, `highlightedSectionId`
- `isComposing`, `composeJobId`
- `playerActiveClipId`, `playerClipSelectionLocked`

**Refactoring Solution**:

Option A: Use `useReducer` for related state:
```typescript
type UploadState = {
  stage: UploadStage
  error: string | null
  progress: number
  metadata: UploadMetadata | null
  result: SongUploadResponse | null
  songDetails: SongRead | null
  videoType: 'full_length' | 'short_form' | null
  audioSelection: { startSec: number; endSec: number } | null
  // ... etc
}

const [state, dispatch] = useReducer(uploadReducer, initialState)
```

Option B: Extract custom hooks:
```typescript
// useVideoTypeSelection.ts
export function useVideoTypeSelection(songId: string | null) {
  const [videoType, setVideoType] = useState<...>(null)
  const [isSetting, setIsSetting] = useState(false)
  
  const setVideoType = useCallback(async (type) => {
    // ... logic
  }, [songId])
  
  return { videoType, setVideoType, isSetting }
}

// useAudioSelection.ts
export function useAudioSelection(songId: string | null) {
  // ... similar pattern
}
```

**Benefits**:
- Better organization
- Easier to test
- Reduced prop drilling
- Clearer data flow

**Effort**: 3-4 hours

---

### 6. Extract Common API Endpoint Patterns

**Problem**: `set_video_type()` and `update_audio_selection()` have similar patterns:
- Song lookup
- Validation
- Update
- Save
- Return

**Refactoring Solution**:

```python
# backend/app/api/v1/utils.py (new file)
from typing import Callable, TypeVar
from uuid import UUID
from fastapi import HTTPException, status
from sqlmodel import Session

from app.models.song import Song
from app.services.song_analysis import get_latest_analysis

T = TypeVar('T')

def get_song_or_404(song_id: UUID, db: Session) -> Song:
    """Get song or raise 404."""
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Song not found"
        )
    return song

def ensure_no_analysis(song_id: UUID) -> None:
    """Ensure song has no analysis, or raise 409."""
    existing_analysis = get_latest_analysis(song_id)
    if existing_analysis:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot change after analysis has been completed. Please upload a new song.",
        )

def update_song_field(
    song: Song,
    field_name: str,
    value: T,
    db: Session,
) -> Song:
    """Update a song field and commit."""
    setattr(song, field_name, value)
    db.add(song)
    db.commit()
    db.refresh(song)
    return song
```

**Benefits**:
- DRY principle
- Consistent error handling
- Easier to maintain

**Effort**: 1-2 hours

---

### 7. Extract Constants to Centralized Location

**Problem**: Constants are scattered:
- `MAX_SELECTION_DURATION = 30.0` in multiple places
- `MIN_SELECTION_DURATION = 1.0` in multiple places
- Video type strings repeated

**Refactoring Solution**:

```python
# backend/app/core/constants.py (enhance existing)
# Audio selection constants
MAX_AUDIO_SELECTION_DURATION_SEC = 30.0
MIN_AUDIO_SELECTION_DURATION_SEC = 1.0

# Video type constants (or use enum)
VIDEO_TYPE_FULL_LENGTH = "full_length"
VIDEO_TYPE_SHORT_FORM = "short_form"
VALID_VIDEO_TYPES = [VIDEO_TYPE_FULL_LENGTH, VIDEO_TYPE_SHORT_FORM]
```

**Benefits**:
- Single source of truth
- Easier to change
- Better documentation

**Effort**: 30 minutes

---

## 🟢 Low Priority Refactorings

### 8. Improve Error Messages Consistency

**Problem**: Error messages for SectionVideo vs SongClip are nearly identical but hardcoded:

```python
raise ClipNotFoundError(f"SectionVideo {clip_id} not found")
raise ClipNotFoundError(f"SongClip {clip_id} not found")
```

**Refactoring Solution**: Use model class name dynamically (already addressed in #1).

**Effort**: Already covered by #1

---

### 9. Type Safety for Video Type

**Problem**: `video_type` is `Optional[str]` - could be any string.

**Refactoring Solution**: Use Literal type or enum:

```python
from typing import Literal

VideoTypeLiteral = Literal["full_length", "short_form", None]

# In Song model:
video_type: VideoTypeLiteral = Field(default=None, max_length=32)
```

**Benefits**: Type checking at compile time

**Effort**: 30 minutes

---

### 10. Extract Video Type Validation

**Problem**: Video type validation happens in:
- Schema validator (`VideoTypeUpdate`)
- API endpoint (`set_video_type`)

**Refactoring Solution**: Schema validation should be sufficient, remove redundant check in endpoint.

**Effort**: 15 minutes

---

## 📊 Refactoring Priority Matrix

| Refactoring | Priority | Effort | Impact | ROI |
|------------|----------|--------|--------|-----|
| 1. Extract Clip Model Selection | 🔴 High | 2-3h | High | ⭐⭐⭐⭐⭐ |
| 2. Replace Magic Strings | 🔴 High | 1-2h | Medium | ⭐⭐⭐⭐ |
| 3. Improve Type Safety | 🔴 High | 30m | Medium | ⭐⭐⭐⭐ |
| 4. Extract Audio Validation | 🔴 High | 1h | Medium | ⭐⭐⭐⭐ |
| 5. Consolidate Frontend State | 🟡 Medium | 3-4h | High | ⭐⭐⭐ |
| 6. Extract API Patterns | 🟡 Medium | 1-2h | Low | ⭐⭐⭐ |
| 7. Extract Constants | 🟡 Medium | 30m | Low | ⭐⭐ |
| 8. Error Messages | 🟢 Low | 0h* | Low | ⭐ |
| 9. Type Safety Video Type | 🟢 Low | 30m | Low | ⭐⭐ |
| 10. Remove Redundant Validation | 🟢 Low | 15m | Low | ⭐ |

*Already covered by #1

---

## Recommended Refactoring Order

### Phase 1: Quick Wins (2-3 hours)
1. Extract Constants (#7)
2. Improve Type Safety (#3)
3. Remove Redundant Validation (#10)

### Phase 2: High Impact (4-6 hours)
4. Replace Magic Strings (#2)
5. Extract Clip Model Selection (#1) - Biggest impact
6. Extract Audio Validation (#4)

### Phase 3: Polish (4-6 hours)
7. Extract API Patterns (#6)
8. Consolidate Frontend State (#5) - If time permits

---

## Estimated Total Effort

- **Quick Wins**: 2-3 hours
- **High Impact**: 4-6 hours
- **Polish**: 4-6 hours
- **Total**: 10-15 hours (~2 days)

---

## Benefits Summary

After refactoring:
- ✅ ~100 lines of duplicated code eliminated
- ✅ Type safety improved throughout
- ✅ Single source of truth for constants
- ✅ Easier to test (isolated functions)
- ✅ Easier to extend (new clip types, video types)
- ✅ Better IDE support (autocomplete, type checking)
- ✅ More maintainable codebase

---

## Notes

- These refactorings are **non-breaking** - they improve code quality without changing behavior
- Can be done incrementally
- Should be done before adding more features to avoid accumulating more debt
- All refactorings have tests that should continue passing

