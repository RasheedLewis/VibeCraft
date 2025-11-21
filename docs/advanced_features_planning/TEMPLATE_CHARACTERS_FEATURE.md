# Template Characters Feature - Planning Document

## Overview

Add a feature that allows users to select from pre-generated template character images instead
of (or in addition to) uploading their own. This will:
- Make manual testing easier (no need to find/create character images)
- Provide users with quick options for character consistency
- Improve UX by offering curated, tested character designs
- Reduce friction for users who don't have character images ready

---

## Goals

1. **User Experience**: Provide 4-6 high-quality template character options
2. **Testing**: Make manual testing easier by providing ready-to-use characters
3. **Integration**: Seamlessly integrate with existing character upload flow
4. **Flexibility**: Allow users to choose template OR upload their own

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
   a. Click "Choose Template" button → Modal opens with 4-6 template options
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
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  [Choose Template]  [Upload Your Own]         │  │
│  └─────────────────────────────────────────────────┘  │
│                                                         │
│  OR (if template/custom already selected):             │
│                                                         │
│  ┌─────────────────────────────────────────────────┐  │
│  │  [Selected Character Preview]                   │  │
│  │  [Change Character] button                      │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Modal Design (Template Selection)

```text
┌─────────────────────────────────────────────────────────┐
│  Choose Template Character                    [×]       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Select a character template to use for your video:     │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ [Image]  │  │ [Image]  │  │ [Image]  │            │
│  │ Template │  │ Template │  │ Template │            │
│  │   1      │  │   2      │  │   3      │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐            │
│  │ [Image]  │  │ [Image]  │  │ [Image]  │            │
│  │ Template │  │ Template │  │ Template │            │
│  │   4      │  │   5      │  │   6      │            │
│  └──────────┘  └──────────┘  └──────────┘            │
│                                                         │
│  [Cancel]                                    [Select]   │
└─────────────────────────────────────────────────────────┘
```

### Design Considerations

1. **Button Placement**:
   - Place "Choose Template" button next to or above upload area
   - Use secondary button style to differentiate from primary upload action
   - Make both options equally prominent

2. **Modal Behavior**:
   - Click outside modal to close
   - ESC key to close
   - Show loading state when template is being "uploaded"
   - Show success state after selection

3. **Template Display**:
   - Show character preview images (thumbnail size, ~200x200px)
   - Show template name/description (optional)
   - Highlight selected template
   - Hover effects for better UX

4. **State Management**:
   - If template selected, show preview (same as custom upload)
   - Allow changing between template and custom upload
   - Clear indication of which type is selected

---

## Technical Architecture

### Template Storage Options

#### Option 1: S3 Storage (Recommended)

**Pros**:
- Consistent with existing image storage
- Can update templates without frontend deployment
- Supports CDN for fast loading
- Easy to add/remove templates

**Cons**:
- Requires S3 bucket setup
- Slightly more complex backend logic

**Implementation**:
- Store templates in S3: `s3://bucket/template-characters/template-1.jpg`, etc.
- Backend endpoint to list available templates
- Backend endpoint to "apply" template (copy to song's character image)

#### Option 2: Static Assets (Frontend)

**Pros**:
- Simple implementation
- No backend changes needed
- Fast loading (bundled with frontend)

**Cons**:
- Requires frontend deployment to update templates
- Larger bundle size
- Less flexible

**Implementation**:
- Store in `frontend/public/template-characters/`
- Frontend component handles template selection
- Frontend uploads template image to backend (same as custom upload)

#### Option 3: Hybrid Approach

- Templates stored in S3
- Frontend fetches template list from backend
- Frontend displays templates
- When selected, backend copies template to song's character image

**Recommendation**: **Option 3 (Hybrid)** - Best balance of flexibility and simplicity

---

## Backend Implementation

### New Endpoints

#### 1. GET `/api/v1/template-characters`

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
      "image_url": "https://...",
      "preview_url": "https://..."
    },
    ...
  ]
}
```

**Implementation**:

```python
# backend/app/api/v1/routes_template_characters.py (NEW)

@router.get(
    "/template-characters",
    response_model=TemplateCharacterListResponse,
    summary="List available template characters",
)
async def list_template_characters(
    db: Session = Depends(get_db),
) -> TemplateCharacterListResponse:
    """List all available template character images."""
    templates = get_template_characters()
    return TemplateCharacterListResponse(templates=templates)
```

#### 2. POST `/api/v1/songs/{song_id}/character-image/template`

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
@router.post(
    "/{song_id}/character-image/template",
    response_model=CharacterImageResponse,
    summary="Apply template character to song",
)
async def apply_template_character(
    song_id: UUID,
    template: TemplateCharacterApply,
    db: Session = Depends(get_db),
) -> CharacterImageResponse:
    """Apply a template character image to a song."""
    # Validate song exists and is short_form
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    if song.video_type != "short_form":
        raise HTTPException(
            status_code=400,
            detail="Template characters only available for short-form videos"
        )
    
    # Get template image from S3
    template_image = get_template_character_image(template.template_id)
    if not template_image:
        raise HTTPException(
            status_code=404,
            detail=f"Template character '{template.template_id}' not found"
        )
    
    # Copy template to song's character image location
    song_s3_key = f"songs/{song_id}/character_reference.jpg"
    copy_template_to_song(template_image, song_s3_key)
    
    # Update song record
    song.character_reference_image_s3_key = song_s3_key
    song.character_consistency_enabled = True
    db.add(song)
    db.commit()
    db.refresh(song)
    
    # Generate presigned URL
    image_url = generate_presigned_get_url(
        bucket_name=settings.s3_bucket_name,
        key=song_s3_key,
        expires_in=3600,
    )
    
    return CharacterImageResponse(
        image_url=image_url,
        s3_key=song_s3_key,
        character_consistency_enabled=True,
    )
```

### Template Character Service

**File**: `backend/app/services/template_characters.py` (NEW)

```python
"""Template character management service."""

import logging
from typing import Optional
from pathlib import Path

from app.core.config import get_settings
from app.services.storage import (
    download_bytes_from_s3,
    upload_bytes_to_s3,
    generate_presigned_get_url,
)

logger = logging.getLogger(__name__)

# Template character definitions
TEMPLATE_CHARACTERS = [
    {
        "id": "template-1",
        "name": "Geometric Character",
        "description": "Clean, minimalist geometric design",
        "s3_key": "template-characters/template-1.jpg",
    },
    {
        "id": "template-2",
        "name": "Organic Character",
        "description": "Smooth, flowing organic shapes",
        "s3_key": "template-characters/template-2.jpg",
    },
    {
        "id": "template-3",
        "name": "Abstract Character",
        "description": "Bold, abstract artistic design",
        "s3_key": "template-characters/template-3.jpg",
    },
    {
        "id": "template-4",
        "name": "Minimalist Character",
        "description": "Simple, elegant minimalist style",
        "s3_key": "template-characters/template-4.jpg",
    },
    {
        "id": "template-5",
        "name": "Vibrant Character",
        "description": "Colorful, energetic design",
        "s3_key": "template-characters/template-5.jpg",
    },
    {
        "id": "template-6",
        "name": "Classic Character",
        "description": "Timeless, classic character design",
        "s3_key": "template-characters/template-6.jpg",
    },
]


def get_template_characters() -> list[dict]:
    """Get list of available template characters."""
    settings = get_settings()
    
    templates = []
    for template in TEMPLATE_CHARACTERS:
        # Generate presigned URLs for thumbnails and full images
        try:
            thumbnail_url = generate_presigned_get_url(
                bucket_name=settings.s3_bucket_name,
                key=template["s3_key"],
                expires_in=3600,
            )
            image_url = generate_presigned_get_url(
                bucket_name=settings.s3_bucket_name,
                key=template["s3_key"],
                expires_in=3600,
            )
            
            templates.append({
                "id": template["id"],
                "name": template["name"],
                "description": template["description"],
                "thumbnail_url": thumbnail_url,
                "image_url": image_url,
                "preview_url": thumbnail_url,  # Same as thumbnail for now
            })
        except Exception as e:
            logger.error(f"Failed to generate URL for template {template['id']}: {e}")
            continue
    
    return templates


def get_template_character_image(template_id: str) -> Optional[bytes]:
    """Get template character image bytes from S3."""
    settings = get_settings()
    
    template = next(
        (t for t in TEMPLATE_CHARACTERS if t["id"] == template_id),
        None
    )
    if not template:
        return None
    
    try:
        image_bytes = download_bytes_from_s3(
            bucket_name=settings.s3_bucket_name,
            key=template["s3_key"],
        )
        return image_bytes
    except Exception as e:
        logger.error(f"Failed to download template {template_id}: {e}")
        return None


def copy_template_to_song(
    template_image_bytes: bytes,
    song_s3_key: str,
    content_type: str = "image/jpeg",
) -> str:
    """Copy template image to song's character image location."""
    settings = get_settings()
    
    s3_key = upload_bytes_to_s3(
        bucket_name=settings.s3_bucket_name,
        key=song_s3_key,
        data=template_image_bytes,
        content_type=content_type,
    )
    
    return s3_key
```

### Schemas

**File**: `backend/app/schemas/template_character.py` (NEW)

```python
"""Template character schemas."""

from pydantic import BaseModel, Field
from typing import Optional


class TemplateCharacter(BaseModel):
    """Template character information."""
    
    id: str = Field(..., description="Template character ID")
    name: str = Field(..., description="Template character name")
    description: Optional[str] = Field(None, description="Template character description")
    thumbnail_url: str = Field(..., description="Thumbnail image URL")
    image_url: str = Field(..., description="Full image URL")
    preview_url: Optional[str] = Field(None, description="Preview image URL")


class TemplateCharacterListResponse(BaseModel):
    """Response for listing template characters."""
    
    templates: list[TemplateCharacter] = Field(..., description="List of template characters")


class TemplateCharacterApply(BaseModel):
    """Request to apply a template character."""
    
    template_id: str = Field(..., description="Template character ID to apply")
```

---

## Frontend Implementation

### New Components

#### 1. TemplateCharacterModal Component

**File**: `frontend/src/components/upload/TemplateCharacterModal.tsx` (NEW)

```typescript
import React, { useState, useEffect } from 'react'
import clsx from 'clsx'
import { apiClient } from '../../lib/apiClient'

interface TemplateCharacter {
  id: string
  name: string
  description?: string
  thumbnail_url: string
  image_url: string
  preview_url?: string
}

interface TemplateCharacterModalProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (template: TemplateCharacter) => void
  songId: string
}

export const TemplateCharacterModal: React.FC<TemplateCharacterModalProps> = ({
  isOpen,
  onClose,
  onSelect,
  songId,
}) => {
  const [templates, setTemplates] = useState<TemplateCharacter[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null)
  const [applying, setApplying] = useState(false)

  useEffect(() => {
    if (isOpen) {
      loadTemplates()
    }
  }, [isOpen])

  const loadTemplates = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get('/template-characters')
      setTemplates(response.data.templates)
    } catch (err) {
      console.error('Failed to load templates:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = async (template: TemplateCharacter) => {
    setSelectedTemplate(template.id)
    setApplying(true)
    
    try {
      // Apply template to song
      const response = await apiClient.post(
        `/songs/${songId}/character-image/template`,
        { template_id: template.id }
      )
      
      onSelect(template)
      onClose()
    } catch (err) {
      console.error('Failed to apply template:', err)
      // Show error message
    } finally {
      setApplying(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="relative w-full max-w-4xl rounded-2xl border border-vc-border/40 bg-[rgba(12,12,18,0.95)] p-6 shadow-vc3">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-semibold text-white">Choose Template Character</h2>
          <button
            onClick={onClose}
            className="text-vc-text-secondary hover:text-white transition-colors"
            aria-label="Close"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Description */}
        <p className="mb-6 text-sm text-vc-text-secondary">
          Select a character template to use for your video. All clips will maintain consistent character appearance.
        </p>

        {/* Templates Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-vc-accent-primary border-r-transparent"></div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
            {templates.map((template) => (
              <button
                key={template.id}
                onClick={() => handleSelect(template)}
                disabled={applying}
                className={clsx(
                  'group relative rounded-xl border-2 transition-all',
                  selectedTemplate === template.id
                    ? 'border-vc-accent-primary ring-2 ring-vc-accent-primary/50'
                    : 'border-vc-border/40 hover:border-vc-accent-primary/60',
                  applying && 'opacity-50 cursor-not-allowed'
                )}
              >
                <div className="aspect-square overflow-hidden rounded-t-xl">
                  <img
                    src={template.thumbnail_url}
                    alt={template.name}
                    className="h-full w-full object-cover transition-transform group-hover:scale-105"
                  />
                </div>
                <div className="p-3">
                  <h3 className="text-sm font-semibold text-white">{template.name}</h3>
                  {template.description && (
                    <p className="mt-1 text-xs text-vc-text-secondary">{template.description}</p>
                  )}
                </div>
                {applying && selectedTemplate === template.id && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/40 rounded-xl">
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-white border-r-transparent"></div>
                  </div>
                )}
              </button>
            ))}
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 flex justify-end gap-3">
          <button
            onClick={onClose}
            disabled={applying}
            className="px-4 py-2 text-sm text-vc-text-secondary hover:text-white transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  )
}
```

#### 2. Updated CharacterImageUpload Component

**Modify**: `frontend/src/components/upload/CharacterImageUpload.tsx`

Add support for template selection alongside custom upload:

```typescript
// Add new props
export interface CharacterImageUploadProps {
  songId: string
  onUploadSuccess?: (imageUrl: string) => void
  onUploadError?: (error: string) => void
  className?: string
  currentImageUrl?: string | null  // Show preview if already selected
  onTemplateSelect?: () => void    // Callback for template selection
}

// Add template button in component
<div className="flex gap-3 mb-4">
  <VCButton
    variant="secondary"
    onClick={() => onTemplateSelect?.()}
    disabled={uploading || !!currentImageUrl}
  >
    Choose Template
  </VCButton>
  <span className="text-sm text-vc-text-secondary self-center">or</span>
  <VCButton
    variant="secondary"
    onClick={handleClick}
    disabled={uploading || !!currentImageUrl}
  >
    Upload Your Own
  </VCButton>
</div>
```

#### 3. Updated UploadPage

**Modify**: `frontend/src/pages/UploadPage.tsx`

Add template modal integration:

```typescript
const [templateModalOpen, setTemplateModalOpen] = useState(false)
const [characterImageUrl, setCharacterImageUrl] = useState<string | null>(null)

// In character upload section:
{stage === 'uploaded' && videoType === 'short_form' && result?.songId && (
  <section className="mb-8 space-y-4">
    <div className="vc-label">Character Consistency (Optional)</div>
    <p className="text-sm text-vc-text-secondary">
      Upload a character reference image to maintain consistent character
      appearance across all clips.
    </p>
    
    <CharacterImageUpload
      songId={result.songId}
      currentImageUrl={characterImageUrl}
      onUploadSuccess={(imageUrl) => {
        setCharacterImageUrl(imageUrl)
        // Refresh song details
        apiClient.get(`/songs/${result.songId}`).then(...)
      }}
      onTemplateSelect={() => setTemplateModalOpen(true)}
    />
    
    <TemplateCharacterModal
      isOpen={templateModalOpen}
      onClose={() => setTemplateModalOpen(false)}
      onSelect={(template) => {
        setCharacterImageUrl(template.image_url)
        // Refresh song details
        apiClient.get(`/songs/${result.songId}`).then(...)
      }}
      songId={result.songId}
    />
  </section>
)}
```

---

## Template Character Images

### Design Requirements

1. **Style Variety**:
   - Geometric/abstract
   - Organic/flowing
   - Minimalist
   - Vibrant/colorful
   - Classic/traditional
   - Modern/contemporary

2. **Technical Requirements**:
   - Format: JPEG (optimized)
   - Size: 1024x1024px (square, 1:1 aspect ratio)
   - File size: < 500KB per image
   - Background: Transparent or solid color
   - Character: Centered, clear, recognizable

3. **Content Requirements**:
   - Single character (not multiple)
   - Clear, distinct design
   - Works well for video generation
   - Consistent style within template set

### Template Creation Process

1. **Design**: Create 6 distinct character designs
2. **Export**: Export as 1024x1024px JPEG
3. **Optimize**: Compress images (< 500KB each)
4. **Upload**: Upload to S3 `template-characters/` bucket
5. **Test**: Verify templates work with video generation

### Template Naming Convention

- `template-1.jpg` - Geometric Character
- `template-2.jpg` - Organic Character
- `template-3.jpg` - Abstract Character
- `template-4.jpg` - Minimalist Character
- `template-5.jpg` - Vibrant Character
- `template-6.jpg` - Classic Character

---

## Implementation Checklist

### Phase 1: Backend Setup

- [ ] Create `template_characters.py` service
- [ ] Create template character schemas
- [ ] Create `GET /api/v1/template-characters` endpoint
- [ ] Create `POST /api/v1/songs/{song_id}/character-image/template` endpoint
- [ ] Upload 6 template character images to S3
- [ ] Test endpoints with Postman/curl

### Phase 2: Frontend Components

- [ ] Create `TemplateCharacterModal` component
- [ ] Update `CharacterImageUpload` component to support templates
- [ ] Add template selection button
- [ ] Integrate modal into `UploadPage`
- [ ] Add loading states and error handling

### Phase 3: Testing

- [ ] Test template listing endpoint
- [ ] Test template application endpoint
- [ ] Test modal UI/UX
- [ ] Test template selection flow
- [ ] Test switching between template and custom upload
- [ ] Test with video generation (verify templates work)

### Phase 4: Documentation

- [ ] Update API documentation
- [ ] Update user documentation (if needed)
- [ ] Update manual testing guide

---

## Testing Considerations

### Manual Testing

1. **Template Selection Flow**:
   - Open modal
   - View all 6 templates
   - Select a template
   - Verify template is applied to song
   - Verify character consistency is enabled

2. **Template vs Custom Upload**:
   - Select template, then switch to custom upload
   - Upload custom image, then switch to template
   - Verify only one character image is active at a time

3. **Error Handling**:
   - Test with invalid template ID
   - Test with network errors
   - Test with S3 access errors

### Integration Testing

1. **End-to-End Flow**:
   - Select template character
   - Complete audio selection
   - Generate clips
   - Verify clips use template character

2. **Backend Verification**:
   - Verify template is copied to song's S3 location
   - Verify `character_reference_image_s3_key` is set
   - Verify `character_consistency_enabled` is true

---

## Future Enhancements

1. **Template Categories**: Group templates by style/genre
2. **Template Preview**: Show how template looks in video (preview clips)
3. **Custom Templates**: Allow users to save their own characters as templates
4. **Template Recommendations**: Suggest templates based on song genre/mood
5. **Template Marketplace**: Allow community-submitted templates (future)

---

## Open Questions

1. **Template Source**:
   - Who creates the initial 6 templates? (Designer, AI-generated, etc.)
   - Where do we source template images?

2. **Template Updates**:
   - How do we update/add templates without breaking existing songs?
   - Should we version templates?

3. **Template Licensing**:
   - What license do templates use?
   - Can users use templates commercially?

4. **Template Storage**:
   - Should templates be in a separate S3 bucket?
   - Should we use CDN for faster loading?

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
- S3 bucket: `template-characters/` directory
- Template images: `template-1.jpg` through `template-6.jpg`

---

## Notes

- This feature makes manual testing significantly easier by providing ready-to-use character images
- Templates should be high-quality and tested with video generation
- Consider creating a simple admin interface for managing templates in the future
- Template selection should feel as seamless as custom upload
