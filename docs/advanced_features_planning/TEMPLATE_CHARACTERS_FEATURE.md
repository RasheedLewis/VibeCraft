# Template Characters Feature - Planning Document

## Overview

Add pre-generated template character images (4-6 options) that users can select instead of
uploading their own. This will make manual testing easier and provide quick character options.

**Benefits**:

- Easier manual testing (no need to find/create character images)
- Quick character options for users
- Curated, tested character designs
- Reduced friction for users without character images

---

## Goals

1. Provide 4-6 high-quality template character options
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
   a. Click "Choose Template" → Modal opens with 4-6 template options
   b. Upload their own image (existing flow)
3. If template selected:
   - Template image is "uploaded" to song (same backend flow)
   - Character consistency enabled
   - Same behavior as custom upload
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
│  Select a character template:                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Template │  │ Template │  │ Template │            │
│  │   1      │  │   2      │  │   3      │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ Template │  │ Template │  │ Template │            │
│  │   4      │  │   5      │  │   6      │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│  [Cancel]                                    [Select]   │
└─────────────────────────────────────────────────────────┘
```

### Design Considerations

- **Button Placement**: "Choose Template" next to/above upload area, secondary button style
- **Modal Behavior**: Click outside/ESC to close, loading state during upload, success state
- **Template Display**: Thumbnail images (~200x200px), name/description, highlight selected, hover effects
- **State Management**: Show preview if template selected, allow switching between template/custom

---

## Technical Architecture

### Template Storage: Hybrid Approach (Recommended)

- Templates stored in S3: `s3://bucket/template-characters/template-1.jpg` through `template-6.jpg`
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
      "id": "template-1",
      "name": "Geometric Character",
      "description": "Clean, minimalist geometric design",
      "thumbnail_url": "https://...",
      "image_url": "https://..."
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
  "template_id": "template-1"
}
```

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
    
    # Get template image from S3
    template_image = get_template_character_image(template.template_id)
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
    {"id": "template-1", "name": "Geometric Character", "s3_key": "template-characters/template-1.jpg"},
    {"id": "template-2", "name": "Organic Character", "s3_key": "template-characters/template-2.jpg"},
    {"id": "template-3", "name": "Abstract Character", "s3_key": "template-characters/template-3.jpg"},
    {"id": "template-4", "name": "Minimalist Character", "s3_key": "template-characters/template-4.jpg"},
    {"id": "template-5", "name": "Vibrant Character", "s3_key": "template-characters/template-5.jpg"},
    {"id": "template-6", "name": "Classic Character", "s3_key": "template-characters/template-6.jpg"},
]

def get_template_characters() -> list[dict]:
    """Get list of available template characters with presigned URLs."""
    # Generate presigned URLs for each template
    # Return list with thumbnail_url, image_url, etc.

def get_template_character_image(template_id: str) -> Optional[bytes]:
    """Get template character image bytes from S3."""

def copy_template_to_song(template_image_bytes: bytes, song_s3_key: str) -> str:
    """Copy template image to song's character image location."""
```

### Schemas

**File**: `backend/app/schemas/template_character.py` (NEW)

```python
class TemplateCharacter(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    thumbnail_url: str
    image_url: str

class TemplateCharacterListResponse(BaseModel):
    templates: list[TemplateCharacter]

class TemplateCharacterApply(BaseModel):
    template_id: str
```

---

## Frontend Implementation

### New Components

#### TemplateCharacterModal Component

**File**: `frontend/src/components/upload/TemplateCharacterModal.tsx` (NEW)

**Key Features**:

- Fetches templates from `GET /api/v1/template-characters`
- Displays 4-6 templates in grid (2-3 columns)
- Shows thumbnail, name, description
- Highlights selected template
- Applies template via `POST /api/v1/songs/{song_id}/character-image/template`
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

## Template Character Images

### Requirements

**Style Variety**: Geometric, organic, abstract, minimalist, vibrant, classic

**Technical**:

- Format: JPEG (optimized)
- Size: 1024x1024px (square)
- File size: < 500KB per image
- Background: Transparent or solid color
- Character: Single character, centered, clear, recognizable

**Naming**: `template-1.jpg` through `template-6.jpg` in S3 `template-characters/` directory

### Creation Process

1. Design 6 distinct character designs
2. Export as 1024x1024px JPEG
3. Optimize (< 500KB each)
4. Upload to S3 `template-characters/` bucket
5. Test with video generation

---

## Implementation Checklist

### Phase 1: Backend Setup

- [ ] Create `template_characters.py` service
- [ ] Create template character schemas
- [ ] Create `GET /api/v1/template-characters` endpoint
- [ ] Create `POST /api/v1/songs/{song_id}/character-image/template` endpoint
- [ ] Upload 6 template character images to S3
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

1. **Template Selection Flow**: Open modal → View templates → Select → Verify applied
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

1. **Template Source**: Who creates initial 6 templates? (Designer, AI-generated, etc.)
2. **Template Updates**: How to update/add templates without breaking existing songs? Version templates?
3. **Template Licensing**: What license? Commercial use allowed?
4. **Template Storage**: Separate S3 bucket? Use CDN?

---

## Success Criteria

1. ✅ Users can select from 4-6 template characters
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

- S3: `template-characters/template-1.jpg` through `template-6.jpg`

---

## Notes

- Makes manual testing significantly easier
- Templates should be high-quality and tested with video generation
- Consider admin interface for managing templates in the future
- Template selection should feel as seamless as custom upload
