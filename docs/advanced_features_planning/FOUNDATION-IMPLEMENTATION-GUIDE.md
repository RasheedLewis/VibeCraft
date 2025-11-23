# Foundation Implementation Guide

**Purpose**: Detailed implementation guide for foundation work required before
implementing Character Consistency and Beat Sync features. Designed for parallel
development by two different developers/AI agents.

**Date**: After Prerequisites 1 & 2 (Dual Use Case) completion

---

## Table of Contents

1. [Overview](#overview)
2. [Parallel Work Streams](#parallel-work-streams)
3. [Character Consistency Foundation](#character-consistency-foundation)
4. [Beat Sync Foundation](#beat-sync-foundation)
5. [Integration Points](#integration-points)
6. [Testing Requirements](#testing-requirements)
7. [Timeline & Dependencies](#timeline--dependencies)

---

## Overview

### Goal

Implement the minimal foundation infrastructure (Option A from
FOUNDATION-ASSESSMENT.md) to enable both Character Consistency and Beat Sync features.
This foundation work can be done in parallel by two different developers/agents.

### Foundation Work Summary

| Stream | Tasks | Estimated Time | Developer |
| ------ | ----- | -------------- | --------- |
| **Character Consistency Foundation** | Image upload, image-to-video support | 4-6 days | Agent 1 |
| **Beat Sync Foundation** | Prompt enhancement, beat-reactive filters | 3-5 days | Agent 2 |

### Success Criteria

- ✅ Users can upload character reference images
- ✅ Video generation accepts image input for image-to-video models
- ✅ Prompts are enhanced with BPM-based rhythmic descriptors
- ✅ FFmpeg filters can be applied at beat timestamps
- ✅ Both features can be developed independently without conflicts

### Quick Start: Git Worktree Setup

**For parallel development with simultaneous commits, use Git worktrees:**

```bash
# From main repo directory
cd /Users/adamisom/Desktop/VibeCraft
git checkout advancedFeatures
git pull origin advancedFeatures

# Create branches
git branch feature/character-consistency-foundation
git branch feature/beat-sync-foundation

# Create worktrees
git worktree add ../VibeCraft-character-consistency feature/character-consistency-foundation
git worktree add ../VibeCraft-beat-sync feature/beat-sync-foundation

# Agent 1 works in: ../VibeCraft-character-consistency
# Agent 2 works in: ../VibeCraft-beat-sync
```

See [Git Workflow: Worktrees vs. Standard Branches](#git-workflow-worktrees-vs-standard-branches)
section for full details.

---

## Parallel Work Streams

### Work Stream Separation

The foundation work is intentionally separated to minimize conflicts:

**Character Consistency Foundation** (Agent 1):

- Image upload infrastructure
- Image-to-video support in video generation
- Database schema changes (character fields)

**Beat Sync Foundation** (Agent 2):

- Prompt enhancement service
- Beat-reactive FFmpeg filters
- BPM integration in scene planning

**Shared/Coordination Points**:

- Database migrations (coordinate to avoid conflicts)
- Video generation service modifications (coordinate carefully)
- Testing infrastructure

---

## Character Consistency Foundation

### Overview

Implement image upload infrastructure and image-to-video support in the video generation pipeline.

### Task 1: Image Upload Infrastructure

**Goal**: Enable users to upload character reference images with songs.

**Estimated Time**: 1-2 days

#### Step 1.1: Database Schema Changes

**File**: `backend/app/models/song.py`

Add character-related fields to the Song model:

```python
# Add these fields to the Song class:
character_reference_image_s3_key: Optional[str] = Field(default=None, max_length=1024)
character_consistency_enabled: bool = Field(default=False)
character_interrogation_prompt: Optional[str] = Field(default=None)
character_generated_image_s3_key: Optional[str] = Field(default=None, max_length=1024)
```

**Migration File**: `backend/migrations/004_add_character_fields.py`

```python
"""Add character consistency fields to songs table."""

def upgrade():
    # Add character fields
    op.add_column('songs', sa.Column('character_reference_image_s3_key', sa.String(1024), nullable=True))
    op.add_column('songs', sa.Column('character_consistency_enabled', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('songs', sa.Column('character_interrogation_prompt', sa.Text(), nullable=True))
    op.add_column('songs', sa.Column('character_generated_image_s3_key', sa.String(1024), nullable=True))

def downgrade():
    op.drop_column('songs', 'character_generated_image_s3_key')
    op.drop_column('songs', 'character_interrogation_prompt')
    op.drop_column('songs', 'character_consistency_enabled')
    op.drop_column('songs', 'character_reference_image_s3_key')
```

**Action Items**:

1. Add fields to `Song` model
2. Create migration file
3. Run migration: `python -m app.core.migrations upgrade`

#### Step 1.2: Image Validation Service

**File**: `backend/app/services/image_validation.py` (NEW)

Create a service for validating uploaded images:

```python
"""Image validation service for character reference images."""

import logging
from io import BytesIO
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger(__name__)

# Allowed image formats
ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}
MAX_IMAGE_SIZE_MB = 10
MAX_IMAGE_DIMENSION = 2048  # Max width or height in pixels
MIN_IMAGE_DIMENSION = 256   # Min width or height in pixels

def validate_image(
    image_bytes: bytes,
    filename: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[dict]]:
    """
    Validate an uploaded image.
    
    Args:
        image_bytes: Raw image bytes
        filename: Optional filename for logging
        
    Returns:
        Tuple of (is_valid, error_message, metadata_dict)
        metadata_dict contains: format, width, height, size_bytes
    """
    try:
        # Check file size
        size_mb = len(image_bytes) / (1024 * 1024)
        if size_mb > MAX_IMAGE_SIZE_MB:
            return False, f"Image size ({size_mb:.1f}MB) exceeds maximum ({MAX_IMAGE_SIZE_MB}MB)", None
        
        # Open and validate image
        try:
            image = Image.open(BytesIO(image_bytes))
        except Exception as e:
            return False, f"Invalid image format: {str(e)}", None
        
        # Check format
        image_format = image.format
        if image_format not in ALLOWED_IMAGE_FORMATS:
            return False, f"Image format {image_format} not allowed. Allowed: {', '.join(ALLOWED_IMAGE_FORMATS)}", None
        
        # Check dimensions
        width, height = image.size
        max_dim = max(width, height)
        min_dim = min(width, height)
        
        if max_dim > MAX_IMAGE_DIMENSION:
            return False, f"Image dimensions ({width}x{height}) exceed maximum ({MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION})", None
        
        if min_dim < MIN_IMAGE_DIMENSION:
            return False, f"Image dimensions ({width}x{height}) below minimum ({MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION})", None
        
        metadata = {
            "format": image_format,
            "width": width,
            "height": height,
            "size_bytes": len(image_bytes),
            "size_mb": size_mb,
        }
        
        logger.info(f"Image validated: {filename or 'unknown'} - {width}x{height} {image_format}")
        return True, None, metadata
        
    except Exception as e:
        logger.error(f"Error validating image: {e}", exc_info=True)
        return False, f"Image validation error: {str(e)}", None

def normalize_image_format(image_bytes: bytes, target_format: str = "JPEG") -> bytes:
    """
    Convert image to target format (e.g., JPEG).
    
    Args:
        image_bytes: Raw image bytes
        target_format: Target format (JPEG, PNG, WEBP)
        
    Returns:
        Normalized image bytes
    """
    image = Image.open(BytesIO(image_bytes))
    
    # Convert RGBA to RGB for JPEG
    if target_format == "JPEG" and image.mode == "RGBA":
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3])
        image = rgb_image
    
    output = BytesIO()
    image.save(output, format=target_format, quality=95)
    return output.getvalue()
```

**Dependencies**: Add `Pillow` to `requirements.txt`:

```text
Pillow>=10.0.0
```

**Action Items**:

1. Create `image_validation.py` service
2. Add Pillow to requirements.txt
3. Install: `pip install Pillow`

#### Step 1.3: Image Upload API Endpoint

**File**: `backend/app/api/v1/routes_songs.py`

Add endpoint for uploading character reference images:

```python
from fastapi import UploadFile, File, HTTPException, status
from app.services.image_validation import validate_image, normalize_image_format
from app.services.storage import upload_bytes_to_s3, generate_presigned_get_url

@router.post(
    "/{song_id}/character-image",
    status_code=status.HTTP_200_OK,
    summary="Upload character reference image",
)
async def upload_character_image(
    song_id: UUID,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """
    Upload a character reference image for a song.
    
    Only available for songs with video_type='short_form'.
    """
    settings = get_settings()
    
    # Get song
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    
    # Only allow for short_form videos
    if song.video_type != "short_form":
        raise HTTPException(
            status_code=400,
            detail="Character consistency only available for short_form videos"
        )
    
    # Read image bytes
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty")
    
    # Validate image
    is_valid, error_msg, metadata = validate_image(image_bytes, image.filename)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Normalize to JPEG
    normalized_bytes = normalize_image_format(image_bytes, "JPEG")
    
    # Generate S3 key
    s3_key = f"songs/{song_id}/character_reference.jpg"
    
    # Upload to S3
    try:
        await asyncio.to_thread(
            upload_bytes_to_s3,
            bucket_name=settings.s3_bucket_name,
            key=s3_key,
            data=normalized_bytes,
            content_type="image/jpeg",
        )
    except Exception as exc:
        logger.exception(f"Failed to upload character image to S3: {exc}")
        raise HTTPException(
            status_code=502,
            detail="Failed to store image. Verify storage configuration."
        ) from exc
    
    # Update song record
    song.character_reference_image_s3_key = s3_key
    song.character_consistency_enabled = True
    db.add(song)
    db.commit()
    db.refresh(song)
    
    # Generate presigned URL
    try:
        image_url = await asyncio.to_thread(
            generate_presigned_get_url,
            bucket_name=settings.s3_bucket_name,
            key=s3_key,
            expires_in=3600,
        )
    except Exception as exc:
        logger.exception(f"Failed to generate presigned URL: {exc}")
        image_url = None
    
    return {
        "song_id": str(song_id),
        "image_s3_key": s3_key,
        "image_url": image_url,
        "metadata": metadata,
        "status": "uploaded",
    }
```

**Action Items**:

1. Add import statements
2. Add `upload_character_image` endpoint
3. Test endpoint with Postman/curl

#### Step 1.4: Frontend Image Upload Component

**File**: `frontend/src/components/upload/CharacterImageUpload.tsx` (NEW)

Create a component for uploading character images:

```typescript
import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';

interface CharacterImageUploadProps {
  songId: string;
  onUploadSuccess?: (imageUrl: string) => void;
  onUploadError?: (error: string) => void;
}

export const CharacterImageUpload: React.FC<CharacterImageUploadProps> = ({
  songId,
  onUploadSuccess,
  onUploadError,
}) => {
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const onDrop = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    const file = acceptedFiles[0];
    setUploading(true);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewUrl(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Upload to backend
    const formData = new FormData();
    formData.append('image', file);

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL}/api/v1/songs/${songId}/character-image`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const data = await response.json();
      onUploadSuccess?.(data.image_url);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Upload failed';
      onUploadError?.(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/webp': ['.webp'],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  return (
    <div className="character-image-upload">
      <div
        {...getRootProps()}
        className={`dropzone ${isDragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
      >
        <input {...getInputProps()} />
        {previewUrl ? (
          <div className="preview-container">
            <img src={previewUrl} alt="Character preview" />
            <p>Click or drag to replace</p>
          </div>
        ) : (
          <div className="upload-prompt">
            <p>Drag & drop character image here, or click to select</p>
            <p className="hint">JPEG, PNG, or WEBP (max 10MB)</p>
          </div>
        )}
      </div>
      {uploading && <p>Uploading...</p>}
    </div>
  );
};
```

**Action Items**:

1. Create `CharacterImageUpload.tsx` component
2. Add to upload flow (after video type selection, before analysis)
3. Style with Tailwind CSS

### Task 2: Image-to-Video Support

**Goal**: Extend video generation service to accept image input for image-to-video models.

**Estimated Time**: 2-3 days

#### Step 2.1: Research Replicate Image-to-Video Models

**Action Items**:

1. Check Replicate documentation for image-to-video models
2. Test models: `minimax/hailuo-2.3`, `google/veo-3.1`, `luma/ray`
3. Document model parameters, costs, quality

**File**: `docs/temp_advanced_features_planning/REPLICATE_IMAGE_TO_VIDEO_MODELS.md` (NEW)

Create documentation of tested models and their parameters.

#### Step 2.2: Extend Video Generation Service

**File**: `backend/app/services/video_generation.py`

Modify `generate_section_video()` to accept optional image input:

```python
def generate_section_video(
    scene_spec: SceneSpec,
    seed: Optional[int] = None,
    num_frames: Optional[int] = None,
    fps: Optional[int] = None,
    reference_image_url: Optional[str] = None,  # NEW PARAMETER
    max_poll_attempts: int = 180,
    poll_interval_sec: float = 5.0,
) -> tuple[bool, Optional[str], Optional[dict]]:
    """
    Generate a video from a scene specification using Replicate.
    
    Args:
        scene_spec: SceneSpec object with prompt and parameters
        seed: Optional seed for reproducibility
        num_frames: Optional frame count override
        fps: Optional FPS override
        reference_image_url: Optional image URL for image-to-video generation
        max_poll_attempts: Maximum number of polling attempts
        poll_interval_sec: Seconds between polling attempts
    
    Returns:
        Tuple of (success, video_url, metadata_dict)
    """
    try:
        settings = get_settings()
        if not settings.replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            return False, None, None

        client = replicate.Client(api_token=settings.replicate_api_token)

        # Determine model based on whether image is provided
        if reference_image_url:
            # Use image-to-video model
            VIDEO_MODEL = "minimax/hailuo-2.3"  # Supports image-to-video
            logger.info(f"Using image-to-video generation with reference image: {reference_image_url}")
        else:
            # Use text-to-video model (existing behavior)
            VIDEO_MODEL = "minimax/hailuo-2.3"
        
        effective_fps = fps or 8
        frame_count = num_frames if num_frames and num_frames > 0 else int(round(scene_spec.duration_sec * effective_fps))
        
        # Prepare input parameters
        input_params = {
            "prompt": scene_spec.prompt,
            "num_frames": max(1, min(frame_count, 120)),
            "width": 576,
            "height": 320,
            "fps": effective_fps,
        }
        
        # Add image input if provided
        if reference_image_url:
            input_params["image"] = reference_image_url
        
        if seed is not None:
            input_params["seed"] = seed

        logger.info(f"Starting video generation for section {scene_spec.section_id}")
        logger.debug(f"Prompt: {scene_spec.prompt[:100]}...")
        if reference_image_url:
            logger.debug(f"Reference image: {reference_image_url}")

        # Get model and version
        model = client.models.get(VIDEO_MODEL)
        version = model.latest_version
        
        prediction = client.predictions.create(
            version=version,
            input=input_params,
        )

        job_id = prediction.id
        logger.info(f"Replicate job started: {job_id}")

        # ... rest of existing polling logic ...
```

**Action Items**:

1. Add `reference_image_url` parameter to `generate_section_video()`
2. Add conditional logic for image-to-video vs text-to-video
3. Update all call sites to pass `reference_image_url=None` (backward compatible)
4. Test with and without image input

#### Step 2.3: Integrate Image Input in Clip Generation

**File**: `backend/app/services/clip_generation.py`

Modify clip generation to pass character image URL when available:

```python
# In run_clip_generation_job() or similar function:

# Get character image URL if character consistency is enabled
character_image_url = None
if song.character_consistency_enabled and song.character_generated_image_s3_key:
    try:
        character_image_url = generate_presigned_get_url(
            bucket_name=settings.s3_bucket_name,
            key=song.character_generated_image_s3_key,
            expires_in=3600,
        )
    except Exception as e:
        logger.warning(f"Failed to generate presigned URL for character image: {e}")

# Pass to video generation
success, video_url, metadata = generate_section_video(
    scene_spec,
    seed=seed,
    num_frames=clip_num_frames,
    fps=clip_fps,
    reference_image_url=character_image_url,  # NEW
)
```

**Action Items**:

1. Locate clip generation function
2. Add logic to retrieve character image URL
3. Pass to `generate_section_video()`
4. Test end-to-end flow

### Task 3: Character Image Storage Paths

**Goal**: Organize character images in S3 with proper paths.

**File**: `backend/app/services/storage.py`

Add helper function for character image paths:

```python
def get_character_image_s3_key(song_id: UUID, image_type: str = "reference") -> str:
    """
    Generate S3 key for character images.
    
    Args:
        song_id: Song UUID
        image_type: "reference" or "generated"
    
    Returns:
        S3 key path
    """
    if image_type == "reference":
        return f"songs/{song_id}/character_reference.jpg"
    elif image_type == "generated":
        return f"songs/{song_id}/character_generated.jpg"
    else:
        raise ValueError(f"Unknown image_type: {image_type}")
```

**Action Items**:

1. Add helper function to storage service
2. Update upload endpoint to use helper
3. Ensure consistent path structure

---

## Beat Sync Foundation

### Overview

Implement prompt enhancement with BPM and beat-reactive FFmpeg filters.

### Task 1: Prompt Enhancement with BPM

**Goal**: Enhance video generation prompts with rhythmic motion descriptors based on song BPM.

**Estimated Time**: 1 day

#### Step 1.1: Create Prompt Enhancement Service

**File**: `backend/app/services/prompt_enhancement.py` (NEW)

Create service for enhancing prompts with rhythm:

```python
"""Prompt enhancement service for beat synchronization."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Motion type descriptors
MOTION_TYPES = {
    "bouncing": {
        "slow": "gentle bouncing motion, slow rhythmic movement",
        "medium": "bouncing motion, rhythmic pulsing",
        "fast": "rapid bouncing, energetic rhythmic motion",
    },
    "pulsing": {
        "slow": "slow pulsing, gentle rhythmic expansion and contraction",
        "medium": "pulsing motion, rhythmic breathing effect",
        "fast": "rapid pulsing, energetic rhythmic beats",
    },
    "rotating": {
        "slow": "slow rotating motion, gentle circular movement",
        "medium": "rotating motion, steady rhythmic spin",
        "fast": "rapid rotation, energetic spinning motion",
    },
    "stepping": {
        "slow": "slow stepping motion, deliberate rhythmic movement",
        "medium": "stepping motion, steady rhythmic pace",
        "fast": "rapid stepping, energetic rhythmic motion",
    },
    "looping": {
        "slow": "slow looping motion, gentle repetitive cycles",
        "medium": "looping motion, steady rhythmic repetition",
        "fast": "rapid looping, energetic repetitive cycles",
    },
}

# BPM ranges for tempo classification
BPM_SLOW = 60
BPM_MEDIUM = 100
BPM_FAST = 140


def get_tempo_classification(bpm: float) -> str:
    """
    Classify tempo based on BPM.
    
    Args:
        bpm: Beats per minute
        
    Returns:
        "slow", "medium", or "fast"
    """
    if bpm < BPM_SLOW:
        return "slow"
    elif bpm < BPM_MEDIUM:
        return "medium"
    elif bpm < BPM_FAST:
        return "fast"
    else:
        return "very_fast"


def get_motion_descriptor(bpm: float, motion_type: str = "bouncing") -> str:
    """
    Get motion descriptor based on BPM and motion type.
    
    Args:
        bpm: Beats per minute
        motion_type: Type of motion (bouncing, pulsing, rotating, etc.)
        
    Returns:
        Motion descriptor string
    """
    tempo = get_tempo_classification(bpm)
    
    if motion_type not in MOTION_TYPES:
        motion_type = "bouncing"  # Default
    
    motion_dict = MOTION_TYPES[motion_type]
    
    # Map very_fast to fast
    if tempo == "very_fast":
        tempo = "fast"
    
    return motion_dict.get(tempo, motion_dict["medium"])


def enhance_prompt_with_rhythm(
    base_prompt: str,
    bpm: float,
    motion_type: str = "bouncing",
    style_context: Optional[dict] = None,
) -> str:
    """
    Enhance base prompt with rhythmic motion cues.
    
    Args:
        base_prompt: Original user prompt or generated prompt
        bpm: Song BPM from song analysis
        motion_type: Type of rhythmic motion (bouncing, pulsing, rotating, stepping, looping)
        style_context: Optional dict with mood, colors, setting
        
    Returns:
        Enhanced prompt string with rhythmic descriptors
    """
    if bpm <= 0:
        logger.warning(f"Invalid BPM ({bpm}), skipping rhythm enhancement")
        return base_prompt
    
    # Get motion descriptor
    motion_descriptor = get_motion_descriptor(bpm, motion_type)
    
    # Build rhythmic phrase
    bpm_int = int(round(bpm))
    rhythmic_phrase = f"{motion_descriptor} synchronized to {bpm_int} BPM tempo, rhythmic motion matching the beat"
    
    # Combine with base prompt
    enhanced_prompt = f"{base_prompt}, {rhythmic_phrase}"
    
    logger.debug(f"Enhanced prompt with rhythm: BPM={bpm}, motion={motion_type}")
    logger.debug(f"Rhythmic phrase: {rhythmic_phrase}")
    
    return enhanced_prompt


def get_motion_type_from_genre(genre: Optional[str] = None) -> str:
    """
    Suggest motion type based on genre.
    
    Args:
        genre: Music genre (e.g., "electronic", "rock", "jazz")
        
    Returns:
        Suggested motion type
    """
    genre_motion_map = {
        "electronic": "pulsing",
        "dance": "bouncing",
        "rock": "stepping",
        "jazz": "looping",
        "hip-hop": "bouncing",
        "pop": "bouncing",
    }
    
    if genre:
        genre_lower = genre.lower()
        for key, motion in genre_motion_map.items():
            if key in genre_lower:
                return motion
    
    return "bouncing"  # Default
```

**Action Items**:

1. Create `prompt_enhancement.py` service
2. Implement functions above
3. Add unit tests

#### Step 1.2: Integrate Prompt Enhancement in Scene Planning

**File**: `backend/app/services/scene_planner.py`

Modify `build_prompt()` to accept BPM and enhance with rhythm:

```python
def build_prompt(
    section: SongSection,
    lyrics: Optional[SectionLyrics] = None,
    analysis: Optional[SongAnalysis] = None,
    bpm: Optional[float] = None,  # NEW PARAMETER
    motion_type: Optional[str] = None,  # NEW PARAMETER
) -> str:
    """
    Build a video generation prompt from section data.
    
    Args:
        section: SongSection with mood, genre, etc.
        lyrics: Optional section lyrics
        analysis: Optional full song analysis (for context)
        bpm: Optional BPM for rhythm enhancement
        motion_type: Optional motion type for rhythm enhancement
        
    Returns:
        Complete prompt string
    """
    # ... existing prompt building logic ...
    
    # Build base prompt (existing code)
    base_prompt = f"{visual_description}, {mood_description}, {genre_description}"
    
    # Enhance with rhythm if BPM provided
    if bpm and bpm > 0:
        from app.services.prompt_enhancement import (
            enhance_prompt_with_rhythm,
            get_motion_type_from_genre,
        )
        
        # Determine motion type
        effective_motion_type = motion_type
        if not effective_motion_type and section.genre:
            effective_motion_type = get_motion_type_from_genre(section.genre)
        if not effective_motion_type:
            effective_motion_type = "bouncing"  # Default
        
        # Enhance prompt
        base_prompt = enhance_prompt_with_rhythm(
            base_prompt,
            bpm=bpm,
            motion_type=effective_motion_type,
        )
    
    return base_prompt
```

**Action Items**:

1. Locate `build_prompt()` function
2. Add `bpm` and `motion_type` parameters
3. Integrate prompt enhancement
4. Update all call sites to pass BPM from analysis

#### Step 1.3: Pass BPM to Scene Planning

**File**: `backend/app/services/clip_planning.py` or wherever scene planning is called

Ensure BPM is extracted from analysis and passed to `build_prompt()`:

```python
# Get BPM from analysis
bpm = None
if analysis and hasattr(analysis, 'bpm'):
    bpm = analysis.bpm

# Build prompt with BPM
prompt = build_prompt(
    section=section,
    lyrics=lyrics,
    analysis=analysis,
    bpm=bpm,  # NEW
    motion_type=None,  # Can be made configurable later
)
```

**Action Items**:

1. Locate scene planning call sites
2. Extract BPM from analysis
3. Pass to `build_prompt()`
4. Test with different BPM values

### Task 2: Beat-Reactive FFmpeg Filters

**Goal**: Create service for generating FFmpeg filters that trigger visual effects on beats.

**Estimated Time**: 2-3 days

#### Step 2.1: Create Beat Filters Service

**File**: `backend/app/services/beat_filters.py` (NEW)

Create service for generating beat-reactive FFmpeg filters:

```python
"""Beat-reactive FFmpeg filter service for visual beat synchronization."""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Filter effect types
FILTER_TYPES = {
    "flash": {
        "description": "White flash on beat",
        "duration_ms": 50,  # Flash duration in milliseconds
    },
    "color_burst": {
        "description": "Color burst effect on beat",
        "duration_ms": 100,
    },
    "zoom_pulse": {
        "description": "Subtle zoom pulse on beat",
        "duration_ms": 200,
    },
    "brightness_pulse": {
        "description": "Brightness increase on beat",
        "duration_ms": 100,
    },
}


def generate_beat_filter_expression(
    beat_times: List[float],
    filter_type: str = "flash",
    frame_rate: float = 24.0,
    tolerance_ms: float = 20.0,
) -> str:
    """
    Generate FFmpeg filter expression for beat-reactive effects.
    
    Args:
        beat_times: List of beat timestamps in seconds
        filter_type: Type of effect (flash, color_burst, zoom_pulse, brightness_pulse)
        frame_rate: Video frame rate
        tolerance_ms: Tolerance window in milliseconds for beat detection
        
    Returns:
        FFmpeg filter expression string
    """
    if not beat_times:
        logger.warning("No beat times provided, returning empty filter")
        return ""
    
    if filter_type not in FILTER_TYPES:
        logger.warning(f"Unknown filter type {filter_type}, using flash")
        filter_type = "flash"
    
    tolerance_sec = tolerance_ms / 1000.0
    frame_duration = 1.0 / frame_rate
    
    # Build condition expression
    conditions = []
    for beat_time in beat_times:
        # Calculate frame number range for this beat
        start_frame = int((beat_time - tolerance_sec) * frame_rate)
        end_frame = int((beat_time + tolerance_sec) * frame_rate)
        
        # Add condition for this beat window
        condition = f"(n >= {start_frame} && n <= {end_frame})"
        conditions.append(condition)
    
    # Combine conditions with OR
    beat_condition = " || ".join(conditions)
    
    # Generate filter based on type
    if filter_type == "flash":
        # White flash: increase brightness and add white overlay
        filter_expr = f"geq=r='if({beat_condition}, r+50, r)':g='if({beat_condition}, g+50, g)':b='if({beat_condition}, b+50, b)'"
    elif filter_type == "color_burst":
        # Color burst: increase saturation and brightness
        filter_expr = f"eq=saturation='if({beat_condition}, 1.5, 1)':brightness='if({beat_condition}, 0.1, 0)'"
    elif filter_type == "zoom_pulse":
        # Zoom pulse: subtle scale increase
        # Note: This requires crop/scale filter, more complex
        filter_expr = f"scale='if({beat_condition}, iw*1.02, iw)':'if({beat_condition}, ih*1.02, ih)'"
    elif filter_type == "brightness_pulse":
        # Brightness pulse
        filter_expr = f"eq=brightness='if({beat_condition}, 0.15, 0)'"
    else:
        filter_expr = ""
    
    logger.debug(f"Generated {filter_type} filter for {len(beat_times)} beats")
    return filter_expr


def generate_beat_filter_complex(
    beat_times: List[float],
    filter_type: str = "flash",
    frame_rate: float = 24.0,
    tolerance_ms: float = 20.0,
) -> List[str]:
    """
    Generate FFmpeg filter_complex expression for beat-reactive effects.
    
    This is a more flexible approach that can combine multiple filters.
    
    Args:
        beat_times: List of beat timestamps in seconds
        filter_type: Type of effect
        frame_rate: Video frame rate
        tolerance_ms: Tolerance window in milliseconds
        
    Returns:
        List of filter strings for filter_complex
    """
    if not beat_times:
        return []
    
    tolerance_sec = tolerance_ms / 1000.0
    filters = []
    
    # For each beat, create a filter that triggers at that time
    for i, beat_time in enumerate(beat_times):
        start_time = max(0, beat_time - tolerance_sec)
        end_time = beat_time + tolerance_sec
        
        if filter_type == "flash":
            # Flash effect: brightness spike
            filter_str = (
                f"[0:v]select='between(t,{start_time},{end_time})',"
                f"geq=r='r+30':g='g+30':b='b+30'[beat{i}];"
            )
        elif filter_type == "color_burst":
            # Color burst: saturation and brightness
            filter_str = (
                f"[0:v]select='between(t,{start_time},{end_time})',"
                f"eq=saturation=1.5:brightness=0.1[beat{i}];"
            )
        else:
            continue
        
        filters.append(filter_str)
    
    # Combine all beat filters
    # Note: This is simplified - full implementation would overlay effects
    return filters


def apply_beat_filters_to_video(
    input_video_path: str,
    output_video_path: str,
    beat_times: List[float],
    filter_type: str = "flash",
    frame_rate: float = 24.0,
) -> bool:
    """
    Apply beat-reactive filters to a video file using FFmpeg.
    
    This is a helper function that constructs the full FFmpeg command.
    Actual execution should be done in video_composition.py.
    
    Args:
        input_video_path: Path to input video
        output_video_path: Path to output video
        beat_times: List of beat timestamps
        filter_type: Type of effect
        frame_rate: Video frame rate
        
    Returns:
        True if successful
    """
    # This function provides the interface
    # Actual FFmpeg execution should be in video_composition.py
    logger.info(f"Preparing beat filter application: {filter_type} for {len(beat_times)} beats")
    return True
```

**Action Items**:

1. Create `beat_filters.py` service
2. Implement filter generation functions
3. Test filter expressions with sample beat times
4. Document FFmpeg filter syntax

#### Step 2.2: Integrate Beat Filters in Video Composition

**File**: `backend/app/services/video_composition.py`

Add beat filter application to composition pipeline:

```python
from app.services.beat_filters import generate_beat_filter_complex

def compose_final_video(
    clip_paths: List[str],
    audio_path: str,
    output_path: str,
    beat_times: Optional[List[float]] = None,  # NEW PARAMETER
    filter_type: str = "flash",  # NEW PARAMETER
    frame_rate: float = 24.0,  # NEW PARAMETER
) -> bool:
    """
    Compose final video from clips with optional beat-reactive filters.
    
    Args:
        clip_paths: List of paths to video clips
        audio_path: Path to audio file
        output_path: Path to output video
        beat_times: Optional list of beat timestamps for filters
        filter_type: Type of beat filter to apply
        frame_rate: Video frame rate
        
    Returns:
        True if successful
    """
    # ... existing clip concatenation logic ...
    
    # If beat_times provided, apply beat filters
    if beat_times:
        logger.info(f"Applying {filter_type} beat filters for {len(beat_times)} beats")
        
        # Generate filter complex
        beat_filters = generate_beat_filter_complex(
            beat_times=beat_times,
            filter_type=filter_type,
            frame_rate=frame_rate,
        )
        
        # Apply filters using FFmpeg
        # Note: This requires careful FFmpeg command construction
        # See FFmpeg documentation for filter_complex usage
        
    # ... rest of composition logic ...
```

**Action Items**:

1. Locate `compose_final_video()` or similar function
2. Add `beat_times` and `filter_type` parameters
3. Integrate beat filter generation
4. Construct FFmpeg command with filters
5. Test with sample videos

#### Step 2.3: Pass Beat Times to Composition

**File**: `backend/app/services/composition_execution.py` or similar

Ensure beat times are extracted from analysis and passed to composition:

```python
# Get beat times from analysis
beat_times = None
if analysis and hasattr(analysis, 'beat_times'):
    beat_times = analysis.beat_times

# Compose with beat filters
success = compose_final_video(
    clip_paths=clip_paths,
    audio_path=audio_path,
    output_path=output_path,
    beat_times=beat_times,  # NEW
    filter_type="flash",  # Can be made configurable
    frame_rate=24.0,
)
```

**Action Items**:

1. Locate composition execution
2. Extract beat_times from analysis
3. Pass to composition function
4. Test end-to-end

---

## Integration Points

### Shared Components

These components may be modified by both agents - coordinate carefully:

1. **Database Migrations**
   - Character Consistency: Adds character fields
   - Beat Sync: No schema changes needed
   - **Coordination**: Run migrations sequentially, test together

2. **Video Generation Service** (`video_generation.py`)
   - Character Consistency: Adds `reference_image_url` parameter
   - Beat Sync: No changes needed (uses prompt enhancement)
   - **Coordination**: Character Consistency changes are backward compatible

3. **Scene Planning** (`scene_planner.py`)
   - Character Consistency: No changes
   - Beat Sync: Adds BPM parameter to `build_prompt()`
   - **Coordination**: Beat Sync changes are additive (optional parameter)

4. **Composition Pipeline** (`video_composition.py`)
   - Character Consistency: No changes
   - Beat Sync: Adds beat filter support
   - **Coordination**: Beat Sync changes are additive (optional parameters)

### Testing Integration

After both foundations are complete, test integration:

1. **Character Consistency + Beat Sync**
   - Upload song with character image
   - Verify image-to-video generation works
   - Verify prompts include rhythm enhancement
   - Verify beat filters are applied

2. **Backward Compatibility**
   - Test without character image (text-to-video)
   - Test without beat filters (existing behavior)
   - Test with both features enabled

---

## Testing Requirements

### Character Consistency Foundation Tests

**File**: `backend/tests/test_character_foundation.py` (NEW)

```python
"""Tests for character consistency foundation."""

def test_image_validation():
    """Test image validation service."""
    # Test valid images
    # Test invalid formats
    # Test size limits
    # Test dimension limits

def test_image_upload_endpoint():
    """Test image upload API endpoint."""
    # Test successful upload
    # Test validation errors
    # Test S3 integration
    # Test presigned URL generation

def test_image_to_video_generation():
    """Test image-to-video generation."""
    # Test with image input
    # Test without image input (backward compatibility)
    # Test Replicate API integration
```

### Beat Sync Foundation Tests

**File**: `backend/tests/test_beat_sync_foundation.py` (NEW)

```python
"""Tests for beat sync foundation."""

def test_prompt_enhancement():
    """Test prompt enhancement with BPM."""
    # Test different BPM ranges
    # Test different motion types
    # Test genre-based motion selection

def test_beat_filter_generation():
    """Test beat filter generation."""
    # Test filter expression generation
    # Test different filter types
    # Test edge cases (no beats, single beat)

def test_beat_filter_integration():
    """Test beat filter integration in composition."""
    # Test FFmpeg command construction
    # Test filter application
    # Test with real video files
```

---

## Timeline & Dependencies

### Character Consistency Foundation Timeline

| Task | Duration | Dependencies |
| ---- | -------- | ----------- |
| Image Upload Infrastructure | 1-2 days | None |
| Image-to-Video Support | 2-3 days | Image Upload |
| **Total** | **4-6 days** | |

### Beat Sync Foundation Timeline

| Task | Duration | Dependencies |
| ---- | -------- | ----------- |
| Prompt Enhancement | 1 day | None |
| Beat-Reactive Filters | 2-3 days | None |
| **Total** | **3-5 days** | |

### Parallel Execution Plan

**Week 1**:

- **Agent 1**: Image upload infrastructure (Days 1-2)
- **Agent 2**: Prompt enhancement service (Day 1)

**Week 2**:

- **Agent 1**: Image-to-video support (Days 3-5)
- **Agent 2**: Beat-reactive filters (Days 2-4)

**Week 3**:

- **Both**: Integration testing (Day 1)
- **Both**: Bug fixes and polish (Days 2-3)

### Critical Path

1. Image upload must be complete before image-to-video testing
2. Prompt enhancement can be developed independently
3. Beat filters can be developed independently
4. Integration testing requires both foundations

---

## Next Steps After Foundation

Once foundation work is complete:

1. **Character Consistency Implementation**
   - Image interrogation service
   - Character image generation
   - Full workflow integration

2. **Beat Sync Phase 3.3**
   - Beat-aligned transition verification
   - Structural sync improvements

3. **Combined Feature Testing**
   - Test character consistency + beat sync together
   - Performance optimization
   - User experience polish

---

## Notes for Parallel Development

### Git Workflow: Worktrees vs. Standard Branches

#### File Overlap Analysis

**Character Consistency Foundation touches:**

- `backend/app/models/song.py` (adds fields)
- `backend/app/api/v1/routes_songs.py` (adds endpoint)
- `backend/app/services/video_generation.py` (adds optional parameter)
- `backend/app/services/clip_generation.py` (passes image URL)
- `backend/app/services/storage.py` (adds helper)
- **New files**: `image_validation.py`, `CharacterImageUpload.tsx`

**Beat Sync Foundation touches:**

- `backend/app/services/scene_planner.py` (adds optional parameter)
- `backend/app/services/clip_planning.py` (passes BPM)
- `backend/app/services/video_composition.py` (adds optional parameters)
- `backend/app/services/composition_execution.py` (passes beat_times)
- **New files**: `prompt_enhancement.py`, `beat_filters.py`

**Overlap**: Minimal - mostly different files. When files overlap, changes are
**additive and backward compatible** (optional parameters).

#### Recommendation: **Use Git Worktrees for Parallel Development**

Since both agents need to commit simultaneously, **Git worktrees are the right
solution**. This allows each agent to have their own working directory with their
branch checked out, enabling true parallel development.

**Why worktrees ARE needed:**

1. ✅ **Simultaneous commits**: Both agents can commit to their branches at the same time
2. ✅ **No branch switching**: Each agent works in their own directory
3. ✅ **Independent testing**: Each can test their branch without affecting the other
4. ✅ **Clean separation**: Clear physical separation of work
5. ✅ **No stashing needed**: Never need to stash/commit just to switch branches

#### Git Worktree Setup Instructions

**Step 1: Create branches from `advancedFeatures`** (do this once, from main repo):

```bash
# From main repo directory
cd /Users/adamisom/Desktop/VibeCraft

# Ensure we're on advancedFeatures and up to date
git checkout advancedFeatures
git pull origin advancedFeatures

# Create branches (if they don't exist)
git branch feature/character-consistency-foundation
git branch feature/beat-sync-foundation
```

**Step 2: Create worktrees for each agent**:

```bash
# From main repo directory
cd /Users/adamisom/Desktop/VibeCraft

# Create worktree for Character Consistency (Agent 1)
git worktree add ../VibeCraft-character-consistency feature/character-consistency-foundation

# Create worktree for Beat Sync (Agent 2)
git worktree add ../VibeCraft-beat-sync feature/beat-sync-foundation
```

**Step 3: Each agent works in their own directory**:

```bash
# Agent 1 (Character Consistency)
cd /Users/adamisom/Desktop/VibeCraft-character-consistency
# Work normally - commits go to feature/character-consistency-foundation
git status  # Shows branch: feature/character-consistency-foundation
git add .
git commit -m "Add image upload infrastructure"
git push origin feature/character-consistency-foundation

# Agent 2 (Beat Sync)
cd /Users/adamisom/Desktop/VibeCraft-beat-sync
# Work normally - commits go to feature/beat-sync-foundation
git status  # Shows branch: feature/beat-sync-foundation
git add .
git commit -m "Add prompt enhancement service"
git push origin feature/beat-sync-foundation
```

**Step 4: Keep branches in sync** (periodically):

```bash
# Agent 1: Pull latest from advancedFeatures
cd /Users/adamisom/Desktop/VibeCraft-character-consistency
git fetch origin
git merge origin/advancedFeatures  # Merge any updates from main branch

# Agent 2: Same
cd /Users/adamisom/Desktop/VibeCraft-beat-sync
git fetch origin
git merge origin/advancedFeatures
```

**Step 5: Clean up when done**:

```bash
# From main repo directory
cd /Users/adamisom/Desktop/VibeCraft

# Remove worktrees
git worktree remove ../VibeCraft-character-consistency
git worktree remove ../VibeCraft-beat-sync

# Optionally delete branches (after merging)
git branch -d feature/character-consistency-foundation
git branch -d feature/beat-sync-foundation
```

#### Worktree Benefits for This Project

1. **True Parallel Development**: Both agents commit simultaneously without conflicts
2. **Independent Testing**: Each can run tests, start servers, etc. in their own directory
3. **Clear Separation**: Physical directory separation makes it obvious which work is which
4. **No Coordination Needed**: Agents don't need to coordinate branch switching
5. **Easy Integration Testing**: Can test both branches side-by-side if needed

#### Important Notes

- **Shared `.git` directory**: All worktrees share the same `.git` directory, so
  commits are immediately visible to both
- **Separate working directories**: Each worktree has its own working directory, so
  file changes don't conflict
- **Branch protection**: Git prevents checking out the same branch in multiple
  worktrees (which is what we want)
- **Database/venv**: Each worktree can have its own virtual environment and database connections
- **IDE/Editor**: Each agent can open their worktree directory in their IDE independently

#### Troubleshooting

**If worktree creation fails:**

```bash
# Check if branch exists
git branch -a | grep feature/

# If branch doesn't exist, create it first
git checkout -b feature/character-consistency-foundation
git push -u origin feature/character-consistency-foundation
```

**To list all worktrees:**

```bash
git worktree list
```

**To see which files are modified in each worktree:**

```bash
# From main repo
git status  # Shows main worktree status

# From each worktree
cd ../VibeCraft-character-consistency && git status
cd ../VibeCraft-beat-sync && git status
```

### Communication Protocol

1. **Document shared file changes**:
   - If modifying a shared file, document the change in commit message
   - Update this guide if approach changes

2. **Coordinate database migrations**:
   - Character Consistency adds migration (004_add_character_fields.py)
   - Beat Sync: No migrations needed
   - Run migrations sequentially

3. **Test integration points frequently**:
   - After each merge, test that both features work
   - Verify backward compatibility

### Code Review Checklist

Before merging foundation work:

- [ ] All tests pass
- [ ] Backward compatibility maintained
- [ ] Documentation updated
- [ ] No breaking changes to existing APIs
- [ ] Integration points tested
- [ ] Error handling implemented
- [ ] Logging added

---

## Summary

This guide provides detailed implementation steps for foundation work required for
Character Consistency and Beat Sync features. The work is designed to be done in
parallel by two developers/agents with minimal conflicts.

**Key Deliverables**:

1. Image upload infrastructure (Character Consistency)
2. Image-to-video support (Character Consistency)
3. Prompt enhancement with BPM (Beat Sync)
4. Beat-reactive FFmpeg filters (Beat Sync)

**Estimated Total Time**: 4-6 days (Character Consistency) + 3-5 days (Beat Sync) =
7-11 days parallel work

**Next**: After foundation is complete, proceed with full feature implementation as
described in `CHARACTER_CONSISTENCY_IMPLEMENTATION.md` and
`BEAT-SYNC-IMPLEMENTATION-PLAN.md`.
