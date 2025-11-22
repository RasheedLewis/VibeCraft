# Template Characters Feature - Planning Document

## Overview

Add pre-generated template character images (4 characters, each with 2 poses = 8 images total) that
users can select instead of uploading their own. This will make manual testing easier and provide
quick character options.

**Benefits**:

- Easier manual testing (no need to find/create character images)
- Quick character options for users
- Curated, tested character designs
- Reduced friction for users without character images

---

## Character Image Flow to Video Generation API

**Note:** This section was added after implementation to document how character images (template or custom) are passed to the video generation API.

### Overview

When a character is selected (template or custom upload), the system collects presigned S3 URLs for the character images and passes them to the Replicate video generation API. The flow prioritizes generated images, then reference images, with support for multiple poses. This works the same way for both section-based (full-length) and clip-based (short-form) video generation.

### Important Note on Function Names

The function `generate_section_video()` is a general video generation function despite its name. It accepts a `SceneSpec` object which can have `section_id=None` for clip-based generation (short-form videos). The character image passing mechanism is identical regardless of whether sections are used.

### Step-by-Step Flow

1. **Image URL Collection** (`backend/app/services/clip_generation.py`)
   - Function `_get_character_image_urls()` retrieves presigned URLs from S3
   - Priority order: generated image → pose-a (reference) → pose-b
   - Returns tuple: `(urls_list, fallback_url)` where `urls_list` contains all available URLs and `fallback_url` is the primary single image

2. **Passing to Video Generation** (`backend/app/services/clip_generation.py`)
   - In `run_clip_generation_job()`, character URLs are fetched and passed to `generate_section_video()`
   - Both `reference_image_url` (single) and `reference_image_urls` (list) parameters are provided
   - Falls back gracefully if character consistency is not enabled or URLs are unavailable
   - Note: This happens for both section-based and clip-based generation

3. **Video Generation Processing** (`backend/app/services/video_generation.py`)
   - Function `generate_section_video()` handles the image-to-video logic (works for both sections and clips)
   - For single images: uses dedicated `_generate_image_to_video()` function
   - For multiple images: attempts to pass array, with fallback to single image if model doesn't support multiple
   - Falls back to text-to-video if image URLs are invalid or unavailable

4. **API Call to Replicate** (`backend/app/services/video_generation.py`)
   - Image URL(s) are included in `input_params` dictionary with key `"image"` (or `"images"` for multiple)
   - For Minimax Hailuo 2.3 model, single image is passed as `input_params["image"] = image_url`
   - Multiple images are attempted with `input_params["images"]` or `input_params["image"]` as array, with fallback to first image only

### Current Behavior

- Template characters: Both pose-a and pose-b URLs are collected, but the model typically uses only pose-a (first image) since multiple image support may not be available
- Custom uploads: Single reference image URL is used
- Generated images: If a consistent character image was generated from the reference, it takes priority over the original reference image
- Works identically for: Section-based generation (full-length videos) and clip-based generation (short-form videos)

---

## Goals

1. Provide 4 high-quality template character options (each with 2 poses)
2. Make manual testing easier
3. Seamlessly integrate with existing character upload flow
4. Allow users to choose template OR upload their own

---

## User Flow

### Current Flow

```text
1. User sees "Character Consistency (Optional)" section
2. User uploads their own character image
3. Image is saved and used for clip generation
```

### New Flow (With Templates)

```text
1. User sees "Character Consistency (Optional)" section
2. User has two options:
   a. Click "Choose Template" → Modal opens with 4 character options (each showing 2 poses)
   b. Upload their own image (existing flow)
3. If character selected:
   - Both poses (pose-a and pose-b) are stored for the song
   - Character consistency enabled
   - Video generation will attempt to use both poses, with fallback to pose-a if multiple
     images are not supported by the model
   - See "Video Generation Integration" section for implementation details
```

---

## UI/UX Design

### Component Layout

```text
┌─────────────────────────────────────────────────────────┐
│  Character Consistency (Optional)                      │
│  [Choose Template]  [Upload Your Own]                 │
│                                                         │
│  OR (if selected):                                      │
│  [Selected Character Preview]                           │
│  [Change Character]                                    │
└─────────────────────────────────────────────────────────┘
```

### Modal Design

```text
┌─────────────────────────────────────────────────────────┐
│  Choose Template Character                    [×]       │
├─────────────────────────────────────────────────────────┤
│  Select a character (each shows 2 poses):               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│  │  Pose A  │  │  Pose A  │  │  Pose A  │  │  Pose A  │
│  │          │  │          │  │          │  │          │
│  │  Pose B  │  │  Pose B  │  │  Pose B  │  │  Pose B  │
│  │ Character│  │ Character│  │ Character│  │ Character│
│  │    1     │  │    2     │  │    3     │  │    4     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘
│  [Cancel]                                    [Select]   │
└─────────────────────────────────────────────────────────┘
```

### Design Considerations

- **Button Placement**: "Choose Template" next to/above upload area, secondary button style
- **Modal Behavior**: Click outside/ESC to close, loading state during upload, success state
- **Template Display**: Each column shows both poses stacked vertically (~200x200px each),
  character name, highlight selected column, hover effects
- **Selection**: User selects entire character (column), not individual pose
- **State Management**: Show preview if template selected, allow switching between template/custom

---

## Technical Architecture

### Template Storage: Hybrid Approach (Recommended)

- Templates stored in S3: `s3://bucket/template-characters/character-1-pose-a.jpg`,
  `character-1-pose-b.jpg`, `character-2-pose-a.jpg`, `character-2-pose-b.jpg`,
  `character-3-pose-a.jpg`, `character-3-pose-b.jpg`, `character-4-pose-a.jpg`,
  `character-4-pose-b.jpg` (8 images total)
- Frontend fetches template list from backend
- Frontend displays templates in modal
- When selected, backend copies template to song's character image location

**Why Hybrid**: Best balance of flexibility (can update templates without
frontend deployment) and simplicity (consistent with existing storage).

---

## Backend Implementation

### New Endpoints

#### GET `/api/v1/template-characters`

**Purpose**: List available template characters

**Response**:

```json
{
  "templates": [
    {
      "id": "character-1",
      "name": "Geometric Character",
      "description": "Clean, minimalist geometric design",
      "poses": [
        {
          "id": "pose-a",
          "thumbnail_url": "https://...",
          "image_url": "https://..."
        },
        {
          "id": "pose-b",
          "thumbnail_url": "https://...",
          "image_url": "https://..."
        }
      ],
      "default_pose": "pose-a"
    }
  ]
}
```

**Implementation**:

```python
@router.get("/template-characters", response_model=TemplateCharacterListResponse)
async def list_template_characters(db: Session = Depends(get_db)):
    """List all available template character images."""
    templates = get_template_characters()
    return TemplateCharacterListResponse(templates=templates)
```

#### POST `/api/v1/songs/{song_id}/character-image/template`

**Purpose**: Apply a template character to a song

**Request**:

```json
{
  "character_id": "character-1",
  "pose": "pose-a"
}
```

**Note**: `pose` is optional, defaults to `pose-a` if not specified.

**Response**:

```json
{
  "image_url": "https://...",
  "s3_key": "songs/{song_id}/character_reference.jpg",
  "character_consistency_enabled": true
}
```

**Implementation**:

```python
@router.post("/{song_id}/character-image/template", response_model=CharacterImageResponse)
async def apply_template_character(
    song_id: UUID,
    template: TemplateCharacterApply,
    db: Session = Depends(get_db),
):
    """Apply a template character image to a song."""
    song = db.get(Song, song_id)
    if not song or song.video_type != "short_form":
        raise HTTPException(status_code=404 if not song else 400, ...)
    
    # Get character image from S3 (default to pose-a if not specified)
    pose = template.pose or "pose-a"
    template_image = get_template_character_image(template.character_id, pose)
    if not template_image:
        raise HTTPException(status_code=404, ...)
    
    # Copy template to song's character image location
    song_s3_key = f"songs/{song_id}/character_reference.jpg"
    copy_template_to_song(template_image, song_s3_key)
    
    # Update song record
    song.character_reference_image_s3_key = song_s3_key
    song.character_consistency_enabled = True
    db.commit()
    
    # Generate presigned URL and return
    image_url = generate_presigned_get_url(...)
    return CharacterImageResponse(...)
```

### Template Character Service

**File**: `backend/app/services/template_characters.py` (NEW)

```python
"""Template character management service."""

TEMPLATE_CHARACTERS = [
    {
        "id": "character-1",
        "name": "Geometric Character",
        "description": "Clean, minimalist geometric design",
        "poses": {
            "pose-a": "template-characters/character-1-pose-a.jpg",
            "pose-b": "template-characters/character-1-pose-b.jpg",
        },
        "default_pose": "pose-a",
    },
    {
        "id": "character-2",
        "name": "Organic Character",
        "description": "Flowing, natural organic design",
        "poses": {
            "pose-a": "template-characters/character-2-pose-a.jpg",
            "pose-b": "template-characters/character-2-pose-b.jpg",
        },
        "default_pose": "pose-a",
    },
    {
        "id": "character-3",
        "name": "Abstract Character",
        "description": "Bold, abstract artistic design",
        "poses": {
            "pose-a": "template-characters/character-3-pose-a.jpg",
            "pose-b": "template-characters/character-3-pose-b.jpg",
        },
        "default_pose": "pose-a",
    },
    {
        "id": "character-4",
        "name": "Minimalist Character",
        "description": "Simple, elegant minimalist design",
        "poses": {
            "pose-a": "template-characters/character-4-pose-a.jpg",
            "pose-b": "template-characters/character-4-pose-b.jpg",
        },
        "default_pose": "pose-a",
    },
]

def get_template_characters() -> list[dict]:
    """Get list of available template characters with presigned URLs for both poses."""
    # Generate presigned URLs for each character's poses
    # Return list with poses array containing thumbnail_url, image_url for each pose

def get_template_character_image(character_id: str, pose: str = "pose-a") -> Optional[bytes]:
    """Get template character image bytes from S3 for specified character and pose."""

def copy_template_to_song(template_image_bytes: bytes, song_s3_key: str) -> str:
    """Copy template image to song's character image location."""
```

### Schemas

**File**: `backend/app/schemas/template_character.py` (NEW)

```python
class CharacterPose(BaseModel):
    id: str
    thumbnail_url: str
    image_url: str

class TemplateCharacter(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    poses: list[CharacterPose]
    default_pose: str

class TemplateCharacterListResponse(BaseModel):
    templates: list[TemplateCharacter]

class TemplateCharacterApply(BaseModel):
    character_id: str
    pose: Optional[str] = "pose-a"
```

---

## Frontend Implementation

### New Components

#### TemplateCharacterModal Component

**File**: `frontend/src/components/upload/TemplateCharacterModal.tsx` (NEW)

**Key Features**:

- Fetches characters from `GET /api/v1/template-characters`
- Displays 4 characters in grid (4 columns)
- Each column shows both poses stacked vertically
- Shows character name, description
- Highlights selected character (entire column)
- Applies character via `POST /api/v1/songs/{song_id}/character-image/template` (uses default pose)
- Loading states during fetch and apply
- Error handling

**Props**:

```typescript
interface TemplateCharacterModalProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (template: TemplateCharacter) => void
  songId: string
}
```

#### Updated CharacterImageUpload Component

**Modify**: `frontend/src/components/upload/CharacterImageUpload.tsx`

**Changes**:

- Add `onTemplateSelect?: () => void` prop
- Add "Choose Template" button next to upload area
- Show preview if template/custom already selected
- Allow changing between template and custom

#### Updated UploadPage

**Modify**: `frontend/src/pages/UploadPage.tsx`

**Changes**:

- Add `templateModalOpen` state
- Add `TemplateCharacterModal` component
- Pass `onTemplateSelect` callback to `CharacterImageUpload`
- Handle template selection success

---

## Video Generation Integration

### Implementation Strategy: Try Both Poses with Fallback

**Model**: `minimax/hailuo-2.3` (Replicate)

**Approach**: Attempt to use **both poses** (pose-a and pose-b) for video generation when
possible, with automatic fallback to single pose if multiple images are not supported.

### Current Implementation

**Current Behavior**:

- Only **ONE reference image** is passed to video generation
- The model accepts a single `image` parameter
- Currently, only **pose-a** (default pose) is used when a template character is selected

**Code Reference** (`backend/app/services/video_generation.py`):

```python
if reference_image_url:
    input_params["image"] = reference_image_url  # Single image only
```

### New Implementation Plan

#### Step 1: Update Template Character Service

**File**: `backend/app/services/template_characters.py`

When applying a template character, store **both poses** in song metadata:

```python
def apply_template_character_to_song(song_id: UUID, character_id: str) -> dict:
    """Apply template character to song, storing both poses."""
    character = get_template_character(character_id)
    
    # Store both poses in song metadata or S3
    pose_a_s3_key = f"songs/{song_id}/character_pose_a.jpg"
    pose_b_s3_key = f"songs/{song_id}/character_pose_b.jpg"
    
    # Copy both poses to song's S3 location
    copy_template_pose_to_song(character_id, "pose-a", pose_a_s3_key)
    copy_template_pose_to_song(character_id, "pose-b", pose_b_s3_key)
    
    # Update song record
    song.character_reference_image_s3_key = pose_a_s3_key  # Primary (fallback)
    song.character_pose_b_s3_key = pose_b_s3_key  # Secondary
    song.character_consistency_enabled = True
```

**Note**: May need to add `character_pose_b_s3_key` field to Song model, or store in JSON
metadata field.

#### Step 2: Update Video Generation Service

**File**: `backend/app/services/video_generation.py`

Modify `generate_section_video()` to accept multiple reference images:

```python
def generate_section_video(
    scene_spec: SceneSpec,
    seed: Optional[int] = None,
    num_frames: Optional[int] = None,
    fps: Optional[int] = None,
    reference_image_url: Optional[str] = None,
    reference_image_urls: Optional[list[str]] = None,  # NEW: Multiple images
    max_poll_attempts: int = 180,
    poll_interval_sec: float = 5.0,
) -> tuple[bool, Optional[str], Optional[dict]]:
    """Generate video with support for multiple reference images."""
    
    # Try multiple images first (if provided)
    if reference_image_urls and len(reference_image_urls) > 1:
        # Attempt to pass multiple images
        # Check if model supports multiple images (research needed)
        input_params = {
            "prompt": scene_spec.prompt,
            "num_frames": max(1, min(frame_count, 120)),
            "width": 576,
            "height": 320,
            "fps": effective_fps,
        }
        
        # Try different parameter names that might support multiple images
        # Option 1: Array of images
        try:
            input_params["images"] = reference_image_urls
            # Test if model accepts this
        except:
            # Option 2: image parameter with array
            try:
                input_params["image"] = reference_image_urls
            except:
                # Fallback: Use first image only
                logger.warning("Model doesn't support multiple images, using first image only")
                input_params["image"] = reference_image_urls[0]
    elif reference_image_url:
        # Single image (existing behavior)
        input_params["image"] = reference_image_url
    elif reference_image_urls and len(reference_image_urls) == 1:
        # Single image in list
        input_params["image"] = reference_image_urls[0]
```

#### Step 3: Update Clip Generation Service

**File**: `backend/app/services/clip_generation.py`

Modify to pass both poses when available:

```python
# Get character image URLs if character consistency is enabled
character_image_urls = []
if song and song.character_consistency_enabled:
    try:
        # Get primary pose (pose-a)
        if song.character_reference_image_s3_key:
            pose_a_url = generate_presigned_get_url(
                bucket_name=settings.s3_bucket_name,
                key=song.character_reference_image_s3_key,
                expires_in=3600
            )
            character_image_urls.append(pose_a_url)
        
        # Get secondary pose (pose-b) if available
        if hasattr(song, 'character_pose_b_s3_key') and song.character_pose_b_s3_key:
            pose_b_url = generate_presigned_get_url(
                bucket_name=settings.s3_bucket_name,
                key=song.character_pose_b_s3_key,
                expires_in=3600
            )
            character_image_urls.append(pose_b_url)
    except Exception as e:
        logger.warning(f"Failed to generate presigned URLs for character images: {e}")

# Pass to video generation (will try multiple, fallback to single)
success, video_url, metadata = generate_section_video(
    scene_spec,
    seed=seed,
    num_frames=clip_num_frames,
    fps=clip_fps,
    reference_image_urls=character_image_urls if character_image_urls else None,
    reference_image_url=character_image_urls[0] if character_image_urls else None,  # Fallback
)
```

### Model Support Research

**Question**: Does `minimax/hailuo-2.3` support multiple reference images?

**Research Tasks**:

1. Check Replicate model documentation for `minimax/hailuo-2.3`
2. Test API with array of images: `input_params["images"] = [url1, url2]`
3. Test API with single image parameter containing array: `input_params["image"] = [url1, url2]`
4. Check for alternative parameter names (e.g., `reference_images`, `image_list`)
5. If not supported, implement graceful fallback to single image

**Fallback Strategy**:

- If model doesn't support multiple images, automatically use **pose-a** (primary pose)
- Log warning when fallback occurs
- No user-facing error - seamless degradation
- Both poses still shown in UI for user context

### Benefits

- **Better character consistency**: Model sees both poses, better understanding of character
- **Graceful degradation**: Falls back to single pose if not supported
- **Future-proof**: Easy to enable when model support is confirmed
- **No breaking changes**: Existing single-image flow still works

---

## Template Character Images

### Requirements

**Style Variety**: 4 distinct character styles (e.g., geometric, organic, abstract, minimalist)

**Pose Variety**: Each character has 2 different poses (pose-a and pose-b)

**Technical**:

- Format: JPEG (optimized)
- Size: 1024x1024px (square)
- File size: < 500KB per image
- Background: Transparent or solid color
- Character: Single character, centered, clear, recognizable

**Naming**: `character-{1-4}-pose-{a|b}.jpg` in S3 `template-characters/` directory

- `character-1-pose-a.jpg`, `character-1-pose-b.jpg`
- `character-2-pose-a.jpg`, `character-2-pose-b.jpg`
- `character-3-pose-a.jpg`, `character-3-pose-b.jpg`
- `character-4-pose-a.jpg`, `character-4-pose-b.jpg`

### Creation Process

1. Design 4 distinct character designs
2. Create 2 poses for each character (8 images total)
3. Export as 1024x1024px JPEG
4. Optimize (< 500KB each)
5. Upload to S3 `template-characters/` bucket with naming convention
6. Test with video generation

---

## Implementation Checklist

### Phase 1: Backend Setup

- [ ] Create `template_characters.py` service
- [ ] Create template character schemas
- [ ] Create `GET /api/v1/template-characters` endpoint
- [ ] Create `POST /api/v1/songs/{song_id}/character-image/template` endpoint
- [ ] Upload 8 template character images to S3 (4 characters × 2 poses)
- [ ] Test endpoints

### Phase 2: Frontend Components

- [ ] Create `TemplateCharacterModal` component
- [ ] Update `CharacterImageUpload` component
- [ ] Add template selection button
- [ ] Integrate modal into `UploadPage`
- [ ] Add loading states and error handling

### Phase 3: Testing

- [ ] Test template listing endpoint
- [ ] Test template application endpoint
- [ ] Test modal UI/UX
- [ ] Test template selection flow
- [ ] Test switching between template and custom upload
- [ ] Test with video generation

### Phase 4: Documentation

- [ ] Update API documentation
- [ ] Update manual testing guide

---

## Testing Considerations

### Manual Testing

1. **Template Selection Flow**: Open modal → View 4 characters (each with 2 poses) → Select character
   → Verify applied (default pose-a)
2. **Template vs Custom**: Switch between template and custom upload, verify only one active
3. **Error Handling**: Invalid template ID, network errors, S3 access errors

### Integration Testing

1. **End-to-End**: Select template → Complete audio selection → Generate clips
   → Verify clips use template
2. **Backend Verification**: Template copied to song's S3 location,
   `character_reference_image_s3_key` set, `character_consistency_enabled` true

---

## Future Enhancements

1. Template categories (group by style/genre)
2. Template preview (show in video preview clips)
3. Custom templates (users save their own)
4. Template recommendations (based on song genre/mood)
5. Template marketplace (community-submitted)

---

## Open Questions

1. **Template Source**: Who creates initial 4 characters with 2 poses each?
   (Designer, AI-generated, etc.)
2. **Template Updates**: How to update/add templates without breaking existing songs? Version templates?
3. **Template Licensing**: What license? Commercial use allowed?
4. **Template Storage**: Separate S3 bucket? Use CDN?

---

## Success Criteria

1. ✅ Users can select from 4 template characters (each with 2 poses visible)
2. ✅ Template selection works seamlessly with existing upload flow
3. ✅ Templates are applied correctly to songs
4. ✅ Manual testing is easier (no need for custom images)
5. ✅ UI/UX is intuitive and polished
6. ✅ All templates work with video generation

---

## Related Files

### Backend

- `backend/app/services/template_characters.py` (NEW)
- `backend/app/schemas/template_character.py` (NEW)
- `backend/app/api/v1/routes_template_characters.py` (NEW)
- `backend/app/api/v1/routes_songs.py` (MODIFY - add template endpoint)

### Frontend

- `frontend/src/components/upload/TemplateCharacterModal.tsx` (NEW)
- `frontend/src/components/upload/CharacterImageUpload.tsx` (MODIFY)
- `frontend/src/pages/UploadPage.tsx` (MODIFY)

### Storage

- S3: `template-characters/character-{1-4}-pose-{a|b}.jpg` (8 images total)

---

## Notes

- Makes manual testing significantly easier
- Templates should be high-quality and tested with video generation
- Consider admin interface for managing templates in the future
- Template selection should feel as seamless as custom upload
