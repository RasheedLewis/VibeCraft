# Prerequisite Step 1: Feature-Flag Section Logic

## Overview

This document outlines the plan and implementation details for adding a feature
flag to control section-based video generation. When the flag is disabled, the
system will operate with a simplified 1-level hierarchy (vid→clips) instead of
the current 2-level hierarchy (vid→sections→clips).

**Goal**: Enable/disable all section-related functionality at the flip of a switch, allowing the system to work directly with clips when sections are disabled.

---

## Current Architecture

### 2-Level Hierarchy (Current State)

```text
Song
  └── Sections (SongSection from analysis)
      └── SectionVideos (SectionVideo model)
          └── Composition (uses SectionVideo IDs)
```

### 1-Level Hierarchy (Target State When Flag Disabled)

```text
Song
  └── Clips (SongClip model)
      └── Composition (uses SongClip IDs)
```

---

## Feature Flag Configuration

### Environment Variable

- **Name**: `ENABLE_SECTIONS`
- **Type**: Boolean
- **Default**: `True` (maintains backward compatibility)
- **Location**: `backend/app/core/config.py`

### Implementation

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # ... existing settings ...
    
    enable_sections: bool = Field(default=True, alias="ENABLE_SECTIONS")
```

---

## Components Requiring Changes

### 1. Backend Configuration

#### File: `backend/app/core/config.py`

- Add `enable_sections` field to `Settings` class
- Export helper function: `is_sections_enabled() -> bool`

**Changes**:

```python
enable_sections: bool = Field(default=True, alias="ENABLE_SECTIONS")

@lru_cache
def is_sections_enabled() -> bool:
    """Check if section-based generation is enabled."""
    return get_settings().enable_sections
```

---

### 2. API Routes

#### File: `backend/app/api/v1/routes_videos.py`

- **Current**: `/sections/{section_id}/generate` endpoint
- **Action**: Add feature flag check at route level
- **Behavior**:
  - When `ENABLE_SECTIONS=False`: Return `404 Not Found` or `503 Service Unavailable` with clear message
  - When `ENABLE_SECTIONS=True`: Normal operation

**Implementation**:

```python
from app.core.config import is_sections_enabled

@router.post("/{section_id}/generate", ...)
async def generate_section_video_endpoint(...):
    if not is_sections_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Section-based video generation is disabled. Use direct clip generation instead."
        )
    # ... existing logic ...
```

#### File: `backend/app/api/v1/routes_scenes.py` (if exists)

- Similar feature flag checks for any section-related endpoints

---

### 3. Composition Service

#### File: `backend/app/services/composition_execution.py`

- **Current**: Uses `SectionVideo` model to fetch clips
- **Action**: Support both `SectionVideo` and `SongClip` models based on flag
- **Behavior**:
  - When `ENABLE_SECTIONS=True`: Use `SectionVideo` (current behavior)
  - When `ENABLE_SECTIONS=False`: Use `SongClip` directly

**Key Changes**:

- Lines 94-104: Conditional model selection
- Update type hints and validation logic

**Implementation**:

```python
from app.core.config import is_sections_enabled
from app.models.clip import SongClip

# In execute_composition_pipeline():
if is_sections_enabled():
    # Use SectionVideo (existing logic)
    for clip_id in clip_ids:
        clip = session.get(SectionVideo, clip_id)
        # ... existing validation ...
else:
    # Use SongClip directly
    for clip_id in clip_ids:
        clip = session.get(SongClip, clip_id)
        if not clip:
            raise ValueError(f"SongClip {clip_id} not found")
        if not clip.video_url:
            raise ValueError(f"SongClip {clip_id} has no video_url")
        clips.append(clip)
        clip_urls.append(clip.video_url)
```

#### File: `backend/app/services/composition_job.py`

- **Current**: Validates `SectionVideo` records
- **Action**: Support both models based on flag
- **Key Functions**:
  - `enqueue_composition()`: Update validation logic
  - `run_composition_job()`: Conditional model handling

**Implementation**:

```python
from app.core.config import is_sections_enabled
from app.models.clip import SongClip

# In enqueue_composition():
if is_sections_enabled():
    # Validate SectionVideo records
    for clip_id in clip_ids:
        clip = session.get(SectionVideo, clip_id)
        # ... existing validation ...
else:
    # Validate SongClip records
    for clip_id in clip_ids:
        clip = session.get(SongClip, clip_id)
        if not clip:
            raise ClipNotFoundError(f"SongClip {clip_id} not found")
        if clip.song_id != song_id:
            raise CompositionError(f"SongClip {clip_id} does not belong to song {song_id}")
        if clip.status != "completed":
            raise CompositionError(f"SongClip {clip_id} is not ready (status: {clip.status})")
```

---

### 4. Clip Generation Service

#### File: `backend/app/services/clip_generation.py`

- **Current**: May reference section-based generation
- **Action**: Ensure all clip generation works independently of sections
- **Note**: `SongClip` model already exists and is section-agnostic

**Review Points**:

- `run_clip_generation_job()`: Should work with `SongClip` directly
- No changes needed if already using `SongClip` model

---

### 5. Scene Planner Service

#### File: `backend/app/services/scene_planner.py`

- **Current**: `build_scene_spec()` requires `section_id` and `SongSection`
- **Action**: Make section-based logic optional
- **Behavior**:
  - When `ENABLE_SECTIONS=True`: Use section-based prompt building (current)
  - When `ENABLE_SECTIONS=False`: Build prompts from song-level analysis only

**Key Changes**:

- Create alternative `build_clip_scene_spec()` function for non-section mode
- Accept `start_sec`, `end_sec` instead of `section_id`
- Use song-level mood/genre/lyrics instead of section-specific

**Implementation**:

```python
from app.core.config import is_sections_enabled

def build_clip_scene_spec(
    start_sec: float,
    end_sec: float,
    analysis: SongAnalysis,
    template: TemplateType = DEFAULT_TEMPLATE,
) -> SceneSpec:
    """
    Build scene specification for a clip (non-section mode).
    
    Uses song-level analysis instead of section-specific data.
    """
    duration_sec = end_sec - start_sec
    
    # Use song-level mood/genre
    color_palette = map_mood_to_color_palette(analysis.mood_primary, analysis.mood_vector)
    camera_motion = map_genre_to_camera_motion(analysis.primary_genre, analysis.bpm)
    
    # Default shot pattern (no section type)
    shot_pattern = ShotPattern(
        pattern="medium",
        pacing="medium",
        transitions=["cut"],
    )
    
    # Build prompt from song-level data
    prompt = build_prompt(
        section=None,  # No section context
        mood_primary=analysis.mood_primary,
        mood_tags=analysis.mood_tags,
        genre=analysis.primary_genre,
        color_palette=color_palette,
        camera_motion=camera_motion,
        shot_pattern=shot_pattern,
        lyrics=None,  # Could extract lyrics for time range if needed
    )
    
    intensity = (analysis.mood_vector.energy + analysis.mood_vector.tension) / 2.0
    
    return SceneSpec(
        section_id=None,  # No section ID in clip mode
        template=template,
        prompt=prompt,
        color_palette=color_palette,
        camera_motion=camera_motion,
        shot_pattern=shot_pattern,
        intensity=intensity,
        duration_sec=duration_sec,
    )
```

**Update `build_prompt()`**:

- Make `section` parameter optional
- Handle None case gracefully

---

### 6. Video Generation Service

#### File: `backend/app/services/video_generation.py`

- **Current**: `generate_section_video()` function name suggests section dependency
- **Action**: Function is already generic (uses `SceneSpec`), but rename for clarity or add wrapper
- **Behavior**: No functional changes needed, but consider renaming to `generate_video_clip()` for clarity

**Optional Refactoring**:

```python
# Keep generate_section_video() as alias for backward compatibility
def generate_section_video(...) -> tuple[bool, Optional[str], Optional[dict]]:
    """Generate video from scene spec (section-based or clip-based)."""
    return generate_video_clip(...)

def generate_video_clip(...) -> tuple[bool, Optional[str], Optional[dict]]:
    """Generate video clip from scene specification."""
    # ... existing implementation ...
```

---

### 7. Frontend Components

#### File: `frontend/src/components/vibecraft/SectionCard.tsx`

- **Current**: Displays section-specific UI
- **Action**: Conditionally render based on feature flag
- **Behavior**:
  - When sections disabled: Hide or show alternative UI
  - Check flag via API endpoint or environment variable

**Implementation Options**:

1. **API Endpoint**: Add `/api/v1/config/features` endpoint returning enabled features
2. **Environment Variable**: Pass via build-time env (less flexible)
3. **Conditional Rendering**: Hide section cards when flag is off

**Recommended**: API endpoint for runtime flexibility

#### New Endpoint: `backend/app/api/v1/routes_config.py`

```python
from fastapi import APIRouter
from app.core.config import is_sections_enabled

router = APIRouter(prefix="/config", tags=["config"])

@router.get("/features")
async def get_feature_flags():
    """Get enabled feature flags."""
    return {
        "sections": is_sections_enabled(),
    }
```

#### Frontend Usage

```typescript
// In component or hook
const { data: features } = useQuery(['features'], () =>
  fetch('/api/v1/config/features').then(r => r.json())
)

if (features?.sections) {
  // Show SectionCard components
} else {
  // Show alternative clip-based UI
}
```

#### Files to Update

- `frontend/src/components/song/SongProfileView.tsx`: Conditionally render section cards
- `frontend/src/pages/UploadPage.tsx`: Check feature flag before showing section UI
- Any other components that reference sections

---

### 8. Database Models

#### No Schema Changes Required

- `SectionVideo` model: Keep as-is (will be unused when flag is off)
- `SongClip` model: Already exists and is section-agnostic
- No migrations needed

**Note**: Existing `SectionVideo` records will remain in database but won't be used when flag is disabled.

---

### 9. API Schema Updates

#### File: `backend/app/schemas/composition.py`

- **Current**: `ComposeVideoRequest` may reference section concepts
- **Action**: Ensure it works with both `SectionVideo` and `SongClip` IDs
- **Behavior**: No changes needed if using generic UUIDs

**Review**: Ensure `clip_ids` field accepts both model types.

---

### 10. Testing Considerations

#### Unit Tests

- Test feature flag configuration loading
- Test conditional logic in composition services
- Test scene planner with and without sections
- Test API route behavior when flag is disabled

#### Integration Tests

- Test full composition pipeline with `ENABLE_SECTIONS=False`
- Test full composition pipeline with `ENABLE_SECTIONS=True`
- Verify no regressions in existing section-based flow

#### Test Files to Update/Create

- `backend/tests/unit/test_feature_flags.py` (new)
- `backend/tests/unit/test_composition_execution.py` (update)
- `backend/tests/unit/test_scene_planner.py` (update)
- `backend/tests/integration/test_composition_without_sections.py` (new)

---

## Implementation Checklist

### Phase 1: Configuration & Core Logic

- [ ] Add `enable_sections` to `Settings` class
- [ ] Add `is_sections_enabled()` helper function
- [ ] Update `composition_execution.py` to support both models
- [ ] Update `composition_job.py` to support both models
- [ ] Create `build_clip_scene_spec()` in `scene_planner.py`
- [ ] Make `build_prompt()` section parameter optional

### Phase 2: API Routes

- [ ] Add feature flag check to `/sections/{section_id}/generate`
- [ ] Create `/api/v1/config/features` endpoint
- [ ] Update API route registration if needed

### Phase 3: Frontend

- [ ] Create feature flags API hook/utility
- [ ] Update `SongProfileView` to conditionally render sections
- [ ] Update `UploadPage` to check feature flag
- [ ] Hide/disable section-related UI when flag is off

### Phase 4: Testing

- [ ] Write unit tests for feature flag logic
- [ ] Write integration tests for both modes
- [ ] Test backward compatibility (flag default True)
- [ ] Test composition with `SongClip` directly

### Phase 5: Documentation

- [ ] Update API documentation
- [ ] Add environment variable documentation
- [ ] Update deployment guide with flag usage

---

## Migration Strategy

### Backward Compatibility

- **Default**: `ENABLE_SECTIONS=True` ensures existing deployments continue working
- **Gradual Rollout**: Can enable/disable per environment
- **Data Safety**: No data migration needed (both models coexist)

### Rollout Plan

1. **Development**: Test with `ENABLE_SECTIONS=False` locally
2. **Staging**: Deploy with flag configurable, test both modes
3. **Production**: Deploy with `ENABLE_SECTIONS=True` (default), then switch when ready

---

## Edge Cases & Considerations

### 1. Mixed State (Flag Changed Mid-Operation)

- **Scenario**: Flag toggled while jobs are in progress
- **Solution**: Jobs use flag value at job creation time (stored in job metadata if needed)

### 2. Existing SectionVideo Records

- **Scenario**: Database has `SectionVideo` records when flag is disabled
- **Solution**: Records remain but are ignored. Consider cleanup job if needed.

### 3. API Client Compatibility

- **Scenario**: Frontend calls section endpoints when disabled
- **Solution**: Return clear error message directing to clip-based endpoints

### 4. Composition Job History

- **Scenario**: Old jobs reference `SectionVideo` IDs
- **Solution**: Job history remains valid; new jobs use appropriate model based on flag

---

## Performance Considerations

### No Performance Impact Expected

- Feature flag check is a simple boolean read (cached via `@lru_cache`)
- Conditional logic is minimal overhead
- Database queries remain the same (just different model)

---

## Rollback Plan

### If Issues Arise

1. Set `ENABLE_SECTIONS=True` in environment
2. Restart services
3. System returns to section-based mode immediately
4. No data changes required

---

## Success Criteria

1. ✅ Feature flag can be toggled via environment variable
2. ✅ When `ENABLE_SECTIONS=False`, no section-related code paths execute
3. ✅ Composition works with `SongClip` directly when flag is off
4. ✅ Frontend hides section UI when flag is disabled
5. ✅ Backward compatibility maintained (default True)
6. ✅ All tests pass in both modes
7. ✅ No regressions in existing section-based flow

---

## Future Enhancements

### Potential Improvements

1. **Admin UI**: Toggle feature flag via admin panel (requires auth)
2. **Per-User Flags**: Allow users to opt-in/out (advanced)
3. **A/B Testing**: Gradually roll out to percentage of users
4. **Metrics**: Track usage of section vs. clip mode

---

## Related Files Reference

### Backend Files

- `backend/app/core/config.py` - Configuration
- `backend/app/api/v1/routes_videos.py` - Section video endpoints
- `backend/app/services/composition_execution.py` - Composition pipeline
- `backend/app/services/composition_job.py` - Job management
- `backend/app/services/scene_planner.py` - Scene specification
- `backend/app/services/video_generation.py` - Video generation
- `backend/app/models/section_video.py` - SectionVideo model
- `backend/app/models/clip.py` - SongClip model

### Frontend Files

- `frontend/src/components/vibecraft/SectionCard.tsx` - Section UI
- `frontend/src/components/song/SongProfileView.tsx` - Main song view
- `frontend/src/pages/UploadPage.tsx` - Upload/analysis page
- `frontend/src/types/sectionVideo.ts` - Section video types

---

## Notes

- This is a **prerequisite** for the sync + consistency features outlined in the Friday Plan
- The 1-level hierarchy (vid→clips) simplifies the architecture for beat-sync and character consistency work
- All section-related code remains in the codebase but is conditionally executed
- This allows for easy re-enabling of sections if needed in the future
