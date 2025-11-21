# Character Consistency Implementation Plan

This document provides a detailed implementation plan for **Character Consistency** feature as outlined in Section 2 of the High-Level Plan. This feature enables users to upload a reference image and generate video clips that maintain consistent character appearance across all 6 clips in a 30-second video.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture & Design](#architecture--design)
3. [Implementation Steps](#implementation-steps)
4. [Database Schema Changes](#database-schema-changes)
5. [API Changes](#api-changes)
6. [Service Layer Implementation](#service-layer-implementation)
7. [Testing Strategy](#testing-strategy)
8. [Error Handling & Edge Cases](#error-handling--edge-cases)
9. [Performance Considerations](#performance-considerations)
10. [Cost Analysis](#cost-analysis)
11. [Future Enhancements](#future-enhancements)

---

## Overview

### Goal

Implement a multi-step workflow that ensures character consistency across all video clips by:
1. **Image Interrogation**: Converting user-uploaded reference images into detailed descriptive prompts
2. **Consistent Image Generation**: Creating a standardized character image using the interrogated prompt
3. **Video Generation**: Using the consistent image as input for image-to-video generation across all 6 clips

### Constraints

- **Replicate API Only**: Must use models available via Replicate API
- **Multi-Step Process**: Cannot use a single API call (compromise for Replicate constraint)
- **Visual Drift Tolerance**: Some visual drift between clips is expected and acceptable

### Success Criteria

- User can upload a reference image during song upload
- All 6 clips maintain recognizable character consistency
- System gracefully handles missing/invalid reference images
- Feature can be toggled on/off via feature flag

---

## Architecture & Design

### High-Level Flow

```
User Uploads Song + Reference Image
    ↓
[Step 1] Image Interrogation (Multimodal LLM)
    ↓
[Step 2] Generate Consistent Character Image (Replicate: SDXL + IP-Adapter)
    ↓
[Step 3] Generate 6 Video Clips (Replicate: Image-to-Video Model)
    ↓
Compose Final Video
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
│  - Upload reference image with song                          │
│  - Display character preview                                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              API Layer (FastAPI)                             │
│  - POST /songs/ (accept image upload)                       │
│  - GET /songs/{id}/character-preview                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│            Service Layer (Python)                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  image_interrogation.py                            │    │
│  │  - interrogate_reference_image()                   │    │
│  │  - Uses OpenAI GPT-4 Vision or similar            │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  character_image_generation.py                      │    │
│  │  - generate_consistent_character_image()           │    │
│  │  - Uses Replicate: stability-ai/stable-diffusion-xl│    │
│  │  - With IP-Adapter or ControlNet                    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  video_generation.py (MODIFIED)                     │    │
│  │  - generate_section_video()                         │    │
│  │  - Now accepts reference_image_url parameter       │    │
│  │  - Uses image-to-video model if image provided     │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  clip_generation.py (MODIFIED)                     │    │
│  │  - run_clip_generation_job()                       │    │
│  │  - Retrieves character image for song              │    │
│  │  - Passes to video generation                      │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              Storage Layer (S3)                              │
│  - songs/{song_id}/character/reference.jpg                   │
│  - songs/{song_id}/character/consistent.jpg                  │
│  - songs/{song_id}/character/interrogation.json             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Phase 1: Database & Storage Setup

#### Step 1.1: Add Character Reference Fields to Song Model ✅ COMPLETE

**File**: `backend/app/models/song.py`

**Status**: All fields have been added to the Song model:

```python
# Character consistency fields (all implemented)
character_reference_image_s3_key: Optional[str] = Field(default=None, max_length=1024)
character_consistency_enabled: bool = Field(default=False)
character_interrogation_prompt: Optional[str] = Field(default=None)  # For future Phase 2
character_generated_image_s3_key: Optional[str] = Field(default=None, max_length=1024)  # For future Phase 3
```

**Migration**: ✅ Created `migrations/004_add_character_fields.py` (all 4 fields)

#### Step 1.2: Update Storage Service ✅ COMPLETE

**File**: `backend/app/services/storage.py`

**Status**: Helper function added for character image S3 key generation:

```python
def get_character_image_s3_key(song_id: UUID, image_type: str = "reference") -> str:
    """
    Generate S3 key for character images.
    
    Args:
        song_id: Song UUID
        image_type: "reference" or "generated"
    
    Returns:
        S3 key path: songs/{song_id}/character_reference.jpg or character_generated.jpg
    """
    if image_type == "reference":
        return f"songs/{song_id}/character_reference.jpg"
    elif image_type == "generated":
        return f"songs/{song_id}/character_generated.jpg"
    else:
        raise ValueError(f"Unknown image_type: {image_type}")
```

**Note**: Direct upload functions are not needed - upload happens in API endpoint using existing `upload_bytes_to_s3()` function.

---

### Phase 2: Image Interrogation Service

#### Step 2.1: Create Image Interrogation Service

**File**: `backend/app/services/image_interrogation.py` (NEW)

```python
"""Image interrogation service for character consistency.

Uses multimodal LLM to convert reference images into detailed prompts.
"""

import logging
import json
from typing import Optional
import httpx
from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def interrogate_reference_image(
    image_url: str,
    image_bytes: Optional[bytes] = None,
) -> dict[str, str]:
    """
    Interrogate a reference image to generate a detailed character description.
    
    Args:
        image_url: URL to the image (S3 presigned URL or public URL)
        image_bytes: Optional image bytes (if already downloaded)
    
    Returns:
        Dictionary with:
        - "prompt": Detailed character description prompt
        - "character_description": Concise character description
        - "style_notes": Style and visual notes
    """
    settings = get_settings()
    
    # Use OpenAI GPT-4 Vision for image interrogation
    # Fallback to other multimodal models if OpenAI not available
    if settings.openai_api_key:
        return _interrogate_with_openai(image_url, image_bytes)
    else:
        # Fallback: Use Replicate's image-to-text model
        return _interrogate_with_replicate(image_url, image_bytes)


def _interrogate_with_openai(
    image_url: str,
    image_bytes: Optional[bytes] = None,
) -> dict[str, str]:
    """Interrogate using OpenAI GPT-4 Vision."""
    client = OpenAI(api_key=get_settings().openai_api_key)
    
    # If we have bytes, convert to base64
    if image_bytes:
        import base64
        image_data = base64.b64encode(image_bytes).decode('utf-8')
        image_content = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_data}"
            }
        }
    else:
        image_content = {
            "type": "image_url",
            "image_url": {"url": image_url}
        }
    
    prompt = """Analyze this character image and provide a detailed description for video generation.

Focus on:
1. Character appearance: body shape, proportions, colors, style (geometric/organic/realistic)
2. Visual style: art style, color palette, lighting
3. Key features: distinctive elements that must be preserved
4. Pose and composition: current pose and framing

Format your response as JSON with these keys:
- "character_description": A concise 2-3 sentence description of the character
- "detailed_prompt": A detailed prompt suitable for image generation (100-150 words)
- "style_notes": Visual style notes (colors, art style, mood)

Be specific about colors, shapes, and proportions. This description will be used to generate consistent character images."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # or "gpt-4-vision-preview" if available
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        image_content
                    ]
                }
            ],
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return {
            "prompt": result.get("detailed_prompt", ""),
            "character_description": result.get("character_description", ""),
            "style_notes": result.get("style_notes", ""),
        }
    except Exception as e:
        logger.error(f"OpenAI image interrogation failed: {e}", exc_info=True)
        raise


def _interrogate_with_replicate(
    image_url: str,
    image_bytes: Optional[bytes] = None,
) -> dict[str, str]:
    """Fallback: Use Replicate's image-to-text or BLIP model."""
    import replicate
    
    client = replicate.Client(api_token=get_settings().replicate_api_token)
    
    # Use BLIP-2 or similar image captioning model
    # Example: "salesforce/blip-2" or "methexis-inc/img2prompt"
    try:
        output = client.run(
            "methexis-inc/img2prompt",
            input={"image": image_url}
        )
        
        # Parse output and create structured description
        prompt_text = output if isinstance(output, str) else str(output)
        
        return {
            "prompt": prompt_text,
            "character_description": prompt_text[:200],  # Truncate for description
            "style_notes": "Generated from image interrogation",
        }
    except Exception as e:
        logger.error(f"Replicate image interrogation failed: {e}", exc_info=True)
        raise
```

---

### Phase 3: Character Image Generation Service

#### Step 3.1: Create Character Image Generation Service

**File**: `backend/app/services/character_image_generation.py` (NEW)

```python
"""Character image generation service using Replicate.

Generates a consistent character image from an interrogated prompt and reference image.
"""

import logging
import time
from typing import Optional
import httpx
import replicate

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Replicate model for consistent character generation
# Using Stable Diffusion XL with IP-Adapter or ControlNet
CHARACTER_IMAGE_MODEL = "stability-ai/sdxl"  # or "stability-ai/stable-diffusion-xl-base-1.0"


def generate_consistent_character_image(
    reference_image_url: str,
    interrogation_prompt: str,
    character_description: str,
    style_notes: Optional[str] = None,
    seed: Optional[int] = None,
    max_poll_attempts: int = 60,
    poll_interval_sec: float = 3.0,
) -> tuple[bool, Optional[str], Optional[dict]]:
    """
    Generate a consistent character image using reference image and prompt.
    
    Args:
        reference_image_url: URL to user's reference image
        interrogation_prompt: Detailed prompt from image interrogation
        character_description: Concise character description
        style_notes: Optional style notes
        seed: Optional seed for reproducibility
        max_poll_attempts: Maximum polling attempts
        poll_interval_sec: Seconds between polling attempts
    
    Returns:
        Tuple of (success, image_url, metadata_dict)
    """
    try:
        settings = get_settings()
        if not settings.replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            return False, None, None
        
        client = replicate.Client(api_token=settings.replicate_api_token)
        
        # Construct enhanced prompt
        enhanced_prompt = f"{interrogation_prompt}. {character_description}"
        if style_notes:
            enhanced_prompt += f" Style: {style_notes}"
        
        # Add consistency keywords
        enhanced_prompt += ". High quality, detailed, consistent character design, clear features, professional illustration"
        
        # Negative prompt to avoid drift
        negative_prompt = "blurry, distorted, inconsistent, multiple characters, low quality, artifacts"
        
        # Prepare input parameters for SDXL
        input_params = {
            "prompt": enhanced_prompt,
            "negative_prompt": negative_prompt,
            "width": 1024,
            "height": 1024,
            "num_outputs": 1,
            "num_inference_steps": 30,
            "guidance_scale": 7.5,
        }
        
        # If model supports IP-Adapter or image input, add reference image
        # Note: Check model schema to see if it supports "image" or "ip_adapter_image" parameter
        # For now, we'll use prompt-only approach and enhance with reference in prompt
        
        if seed is not None:
            input_params["seed"] = seed
        
        logger.info("Starting consistent character image generation")
        logger.debug(f"Prompt: {enhanced_prompt[:200]}...")
        
        # Get model version
        model = client.models.get(CHARACTER_IMAGE_MODEL)
        version = model.latest_version
        
        prediction = client.predictions.create(
            version=version,
            input=input_params,
        )
        
        job_id = prediction.id
        logger.info(f"Character image generation job started: {job_id}")
        
        # Poll for completion
        image_url = None
        metadata = {
            "seed": seed,
            "job_id": job_id,
            "model": CHARACTER_IMAGE_MODEL,
        }
        
        for attempt in range(max_poll_attempts):
            prediction = client.predictions.get(job_id)
            
            if prediction.status == "succeeded":
                # Get image URL from output
                if prediction.output:
                    if isinstance(prediction.output, str):
                        image_url = prediction.output
                    elif isinstance(prediction.output, list) and len(prediction.output) > 0:
                        image_url = prediction.output[0]
                    elif isinstance(prediction.output, dict) and "image" in prediction.output:
                        image_url = prediction.output["image"]
                
                if image_url:
                    logger.info(f"Character image generation completed: {image_url}")
                    return True, image_url, metadata
                else:
                    logger.error(f"Character image generation succeeded but no URL in output: {prediction.output}")
                    return False, None, metadata
            
            elif prediction.status == "failed":
                error_msg = getattr(prediction, "error", "Unknown error")
                logger.error(f"Character image generation failed: {error_msg}")
                metadata["error"] = str(error_msg)
                return False, None, metadata
            
            elif prediction.status in ["starting", "processing"]:
                elapsed_sec = (attempt + 1) * poll_interval_sec
                logger.info(f"Character image generation in progress (attempt {attempt + 1}/{max_poll_attempts}, ~{elapsed_sec:.0f}s elapsed)...")
                time.sleep(poll_interval_sec)
            else:
                logger.warning(f"Unknown prediction status: {prediction.status}")
                time.sleep(poll_interval_sec)
        
        # Timeout
        logger.error(f"Character image generation timed out after {max_poll_attempts} attempts")
        metadata["error"] = f"Timeout after {max_poll_attempts * poll_interval_sec / 60:.1f} minutes"
        return False, None, metadata
    
    except Exception as e:
        logger.error(f"Error generating character image: {e}", exc_info=True)
        return False, None, {"error": str(e)}
```

**Note**: The actual implementation will depend on which Replicate models support IP-Adapter or ControlNet. Research required:
- Check if `stability-ai/sdxl` supports image input
- Look for models like `lucataco/sdxl-ip-adapter` or similar
- Consider using `runwayml/stable-diffusion-v1-5` with ControlNet if available

---

### Phase 4: Modify Video Generation Service

#### Step 4.1: Update Video Generation to Support Image Input ✅ COMPLETE

**File**: `backend/app/services/video_generation.py`

**Status**: Modified `generate_section_video()` to accept optional reference image.

**Implementation**:
- Added `reference_image_url: Optional[str] = None` parameter
- When provided, adds `"image": reference_image_url` to Replicate input params
- Uses same Hailuo 2.3 model (supports both text-to-video and image-to-video)
- Logs whether using image-to-video or text-to-video mode
- Includes `reference_image_url` in metadata when used

**Current Flow**:
```python
# In generate_section_video():
if reference_image_url:
    input_params["image"] = reference_image_url
    logger.info(f"Using image-to-video generation with reference image: {reference_image_url}")
```

**Note**: Separate `_generate_image_to_video()` function was not created - image support is integrated into main function. This can be refactored later if needed.

Add new function for image-to-video:

```python
def _generate_image_to_video(
    scene_spec: SceneSpec,
    reference_image_url: str,
    seed: Optional[int] = None,
    num_frames: Optional[int] = None,
    fps: Optional[int] = None,
    max_poll_attempts: int = 180,
    poll_interval_sec: float = 5.0,
) -> tuple[bool, Optional[str], Optional[dict]]:
    """
    Generate video from image using image-to-video model.
    
    Uses Minimax Hailuo 2.3 or similar image-to-video model.
    """
    try:
        settings = get_settings()
        if not settings.replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            return False, None, None
        
        client = replicate.Client(api_token=settings.replicate_api_token)
        
        # Use image-to-video model (Hailuo 2.3 supports image input)
        IMAGE_TO_VIDEO_MODEL = "minimax/hailuo-2.3"  # or check for image-to-video variant
        
        effective_fps = fps or 8
        frame_count = num_frames if num_frames and num_frames > 0 else int(round(scene_spec.duration_sec * effective_fps))
        
        input_params = {
            "image": reference_image_url,  # Reference character image
            "prompt": scene_spec.prompt,  # Scene prompt
            "num_frames": max(1, min(frame_count, 120)),
            "width": 576,
            "height": 320,
            "fps": effective_fps,
        }
        
        if seed is not None:
            input_params["seed"] = seed
        
        logger.info(f"Starting image-to-video generation for section {scene_spec.section_id}")
        logger.debug(f"Using reference image: {reference_image_url[:100]}...")
        logger.debug(f"Prompt: {scene_spec.prompt[:100]}...")
        
        # Get model version
        model = client.models.get(IMAGE_TO_VIDEO_MODEL)
        version = model.latest_version
        
        prediction = client.predictions.create(
            version=version,
            input=input_params,
        )
        
        job_id = prediction.id
        logger.info(f"Image-to-video job started: {job_id}")
        
        # Poll for completion (same logic as text-to-video)
        # ... (reuse polling logic from existing function)
        
    except Exception as e:
        logger.error(f"Error generating image-to-video: {e}", exc_info=True)
        return False, None, {"error": str(e)}
```

**Important**: Verify that `minimax/hailuo-2.3` supports image input. If not, research alternative image-to-video models on Replicate:
- `luma/ray` (if supports image input)
- `google/veo-3.1` (if available and supports image input)
- Other image-to-video models on Replicate

---

### Phase 5: Integrate into Clip Generation Pipeline

#### Step 5.1: Modify Clip Generation Job ✅ COMPLETE

**File**: `backend/app/services/clip_generation.py`

**Status**: Modified `run_clip_generation_job()` to retrieve and use character image.

**Implementation**:
- Retrieves song to get `character_reference_image_s3_key` (uses reference image directly, not generated image)
- Checks if `character_consistency_enabled` is True
- Generates presigned URL for character image (1 hour expiry)
- Passes `reference_image_url` to `generate_section_video()`
- Graceful degradation: continues without character image if URL generation fails

**Current Flow**:
```python
# In run_clip_generation_job():
song = SongRepository.get_by_id(song_id)
character_image_url = None
if song.character_consistency_enabled and song.character_reference_image_s3_key:
    try:
        character_image_url = generate_presigned_get_url(
            bucket_name=settings.s3_bucket_name,
            key=song.character_reference_image_s3_key,
            expires_in=3600
        )
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        character_image_url = None

success, video_url, metadata = generate_section_video(
    scene_spec,
    seed=seed,
    num_frames=clip_num_frames,
    fps=clip_fps,
    reference_image_url=character_image_url,  # Passes to video generation
)
```

**Note**: Currently uses `character_reference_image_s3_key` directly. Once Phase 3 is complete, should switch to `character_generated_image_s3_key` for better consistency.

#### Step 5.2: Add Character Image Generation to Song Upload Flow

**File**: `backend/app/api/v1/routes_songs.py`

Modify `upload_song()` endpoint to accept optional character reference image:

```python
@router.post(
    "/",
    response_model=SongUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a new song",
)
async def upload_song(
    file: UploadFile = File(...),
    character_image: Optional[UploadFile] = File(None),  # NEW PARAMETER
    db: Session = Depends(get_db),
) -> SongUploadResponse:
    """Upload a new song with optional character reference image."""
    
    # ... existing song upload logic ...
    
    # NEW: Handle character reference image
    if character_image:
        try:
            image_bytes = await character_image.read()
            if image_bytes:
                # Validate image
                from PIL import Image
                import io
                try:
                    img = Image.open(io.BytesIO(image_bytes))
                    img.verify()  # Verify it's a valid image
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid image file: {e}"
                    )
                
                # Upload to S3
                from app.services.storage import upload_character_reference
                character_s3_key = await asyncio.to_thread(
                    upload_character_reference,
                    song_id=song.id,
                    image_bytes=image_bytes,
                    content_type=character_image.content_type or "image/jpeg",
                )
                
                song.character_reference_s3_key = character_s3_key
                song.character_consistency_enabled = True
                
                # Generate consistent character image asynchronously
                # (Don't block upload response)
                from app.core.queue import get_queue
                from app.services.character_consistency import generate_character_image_job
                
                queue = get_queue(queue_name=f"{settings.rq_worker_queue}:character-generation")
                queue.enqueue(
                    generate_character_image_job,
                    song.id,
                    job_timeout=300,  # 5 minutes
                )
                
        except Exception as e:
            logger.exception(f"Failed to process character image: {e}")
            # Don't fail song upload if character image fails
            # Just log and continue
    
    db.add(song)
    db.commit()
    # ... rest of existing code ...
```

#### Step 5.3: Create Character Image Generation Job

**File**: `backend/app/services/character_consistency.py` (NEW)

```python
"""Character consistency orchestration service."""

import logging
from uuid import UUID
import httpx

from app.repositories import SongRepository
from app.services.image_interrogation import interrogate_reference_image
from app.services.character_image_generation import generate_consistent_character_image
from app.services.storage import (
    download_bytes_from_s3,
    upload_consistent_character_image,
    generate_presigned_get_url,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def generate_character_image_job(song_id: UUID) -> dict[str, object]:
    """
    RQ job that generates a consistent character image from user's reference.
    
    This job:
    1. Downloads reference image from S3
    2. Interrogates the image to get detailed prompt
    3. Generates consistent character image
    4. Uploads consistent image to S3
    5. Updates song record
    """
    try:
        song = SongRepository.get_by_id(song_id)
        
        if not song.character_reference_s3_key:
            logger.warning(f"No character reference image for song {song_id}")
            return {"status": "skipped", "reason": "No reference image"}
        
        settings = get_settings()
        
        # Step 1: Download reference image
        logger.info(f"Downloading reference image for song {song_id}")
        image_bytes = download_bytes_from_s3(
            bucket_name=settings.s3_bucket_name,
            key=song.character_reference_s3_key,
        )
        
        # Step 2: Generate presigned URL for interrogation
        reference_url = generate_presigned_get_url(
            bucket_name=settings.s3_bucket_name,
            key=song.character_reference_s3_key,
            expires_in=3600,
        )
        
        # Step 3: Interrogate image
        logger.info(f"Interrogating reference image for song {song_id}")
        interrogation_result = interrogate_reference_image(
            image_url=reference_url,
            image_bytes=image_bytes,
        )
        
        # Store interrogation result
        import json
        song.character_interrogation_prompt = json.dumps(interrogation_result)
        SongRepository.update(song)
        
        # Step 4: Generate consistent character image
        logger.info(f"Generating consistent character image for song {song_id}")
        success, image_url, metadata = generate_consistent_character_image(
            reference_image_url=reference_url,
            interrogation_prompt=interrogation_result["prompt"],
            character_description=interrogation_result["character_description"],
            style_notes=interrogation_result.get("style_notes"),
        )
        
        if not success or not image_url:
            error_msg = metadata.get("error", "Unknown error") if metadata else "Generation failed"
            logger.error(f"Character image generation failed for song {song_id}: {error_msg}")
            song.character_consistency_enabled = False
            SongRepository.update(song)
            return {"status": "failed", "error": error_msg}
        
        # Step 5: Download generated image and upload to S3
        logger.info(f"Downloading generated character image for song {song_id}")
        response = httpx.get(image_url, timeout=60.0)
        response.raise_for_status()
        generated_image_bytes = response.content
        
        consistent_s3_key = upload_consistent_character_image(
            song_id=song_id,
            image_bytes=generated_image_bytes,
        )
        
        # Step 6: Update song record
        song.character_consistent_image_s3_key = consistent_s3_key
        song.character_consistency_enabled = True
        SongRepository.update(song)
        
        logger.info(f"Character image generation completed for song {song_id}: {consistent_s3_key}")
        return {
            "status": "completed",
            "consistent_image_s3_key": consistent_s3_key,
        }
    
    except Exception as e:
        logger.error(f"Character image generation job failed for song {song_id}: {e}", exc_info=True)
        try:
            song = SongRepository.get_by_id(song_id)
            song.character_consistency_enabled = False
            SongRepository.update(song)
        except Exception:
            pass
        return {"status": "failed", "error": str(e)}
```

---

### Phase 6: Frontend Integration

#### Step 6.1: Update Upload Page ✅ COMPLETE

**File**: `frontend/src/pages/UploadPage.tsx`

**Status**: Character image upload integrated into upload flow.

**Implementation**:
- Uses separate `CharacterImageUpload` component (see Step 6.2)
- Only shown for `short_form` videos
- Appears after song upload, before audio selection
- Uploads via separate API endpoint: `POST /songs/{song_id}/character-image`
- Shows loading state and error messages
- Updates song details after successful upload

**Current Flow**:
```typescript
// Character image upload section (conditional on videoType === 'short_form')
{stage === 'uploaded' && videoType === 'short_form' && !audioSelectionValue && (
  <section className="mb-8 space-y-4">
    <div className="vc-label">Character Reference Image (Optional)</div>
    <CharacterImageUpload
      songId={result.songId}
      onUploadSuccess={(imageUrl) => {
        // Refresh song details
        apiClient.get(`/songs/${result.songId}`).then(...)
      }}
    />
  </section>
)}
```

**Note**: Uses separate endpoint rather than form field in song upload, providing better UX and separation of concerns.

#### Step 6.2: Add Character Image Upload Component ✅ COMPLETE

**File**: `frontend/src/components/upload/CharacterImageUpload.tsx` ✅ CREATED

**Status**: Full-featured character image upload component implemented.

**Features**:
- Drag-and-drop file upload area
- File input fallback
- Image preview before upload
- Loading states during upload
- Error message display
- Success callback with image URL
- TypeScript with proper error handling (no `any` types)

**Component API**:
```typescript
interface CharacterImageUploadProps {
  songId: string;
  onUploadSuccess?: (imageUrl: string) => void;
  onUploadError?: (error: string) => void;
  currentImageUrl?: string | null;
}
```

**Note**: Character preview component (for viewing uploaded images) is still TODO - can be added when needed.

---

## Database Schema Changes

### Migration: `migrations/004_add_character_fields.py` ✅ IMPLEMENTED

**Status**: Migration created and tested. Adds all 4 character fields to songs table.

**Fields Added**:
- `character_reference_image_s3_key` (VARCHAR(1024)) - User's uploaded reference image
- `character_consistency_enabled` (BOOLEAN DEFAULT FALSE) - Feature flag
- `character_interrogation_prompt` (TEXT) - For future Phase 2 (image interrogation)
- `character_generated_image_s3_key` (VARCHAR(1024)) - For future Phase 3 (generated character image)

**Implementation Details**:
- Uses SQLAlchemy inspector to check for existing columns (idempotent)
- Supports both PostgreSQL and SQLite
- Handles "column already exists" errors gracefully

---

## API Changes

### New Endpoints

#### GET `/songs/{song_id}/character-preview`

Returns presigned URL for character reference or consistent image.

**Response**:
```json
{
  "reference_image_url": "https://...",
  "consistent_image_url": "https://...",
  "interrogation_prompt": {...},
  "enabled": true
}
```

### Modified Endpoints

#### POST `/songs/{song_id}/character-image` ✅ IMPLEMENTED

**Status**: New endpoint created (separate from song upload)

Uploads a character reference image for a song. Only available for `short_form` videos.

**Request**:
- Method: `POST`
- Path: `/api/v1/songs/{song_id}/character-image`
- Body: Multipart form with `image` file field

**Response**:
```json
{
  "image_url": "https://...presigned-url...",
  "s3_key": "songs/{song_id}/character_reference.jpg",
  "character_consistency_enabled": true
}
```

**Features**:
- Validates image format (JPEG, PNG, WEBP)
- Validates image size (max 10MB) and dimensions (256-2048px)
- Normalizes to JPEG format
- Uploads to S3
- Sets `character_consistency_enabled = true` on song

**Note**: Original plan was to add `character_image` to song upload endpoint, but separate endpoint was implemented for better separation of concerns.

---

## Service Layer Implementation

### New Services

1. **`image_validation.py`** ✅ COMPLETE: Validates and normalizes uploaded images
   - `validate_image()`: Checks format, size, dimensions
   - `normalize_image_format()`: Converts to JPEG
   - Comprehensive unit tests (20+ tests)

2. **`image_interrogation.py`**: ⏳ TODO (Phase 2) - Converts images to prompts
3. **`character_image_generation.py`**: ⏳ TODO (Phase 3) - Generates consistent character images
4. **`character_consistency.py`**: ⏳ TODO (Phase 5) - Orchestrates the character consistency workflow

### Modified Services

1. **`video_generation.py`** ✅ COMPLETE: Added image-to-video support
   - `generate_section_video()` now accepts `reference_image_url` parameter
   - Passes image to Replicate model when provided
   - Logs image-to-video vs text-to-video mode

2. **`clip_generation.py`** ✅ COMPLETE: Retrieves and uses character images
   - Retrieves `character_reference_image_s3_key` from song
   - Generates presigned URL for character image
   - Passes to `generate_section_video()` as `reference_image_url`

3. **`storage.py`** ✅ COMPLETE: Added character image storage helpers
   - `get_character_image_s3_key()` for generating S3 keys

---

## Testing Strategy

### Unit Tests

1. **Image Interrogation Tests**
   - Test with valid images
   - Test with invalid images
   - Test fallback to Replicate if OpenAI unavailable

2. **Character Image Generation Tests**
   - Test successful generation
   - Test timeout handling
   - Test error handling

3. **Video Generation Tests**
   - Test image-to-video with valid image
   - Test text-to-video fallback
   - Test with missing image

### Integration Tests

1. **End-to-End Character Consistency Flow**
   - Upload song with character image
   - Verify character image generation job
   - Verify clips use character image
   - Verify final video has consistent character

2. **Error Scenarios**
   - Invalid image format
   - Image interrogation failure
   - Character image generation failure
   - Missing character image (graceful degradation)

### Manual Testing Checklist

- [ ] Upload song with character image
- [ ] Verify character image appears in S3
- [ ] Verify interrogation prompt is generated
- [ ] Verify consistent character image is generated
- [ ] Verify all 6 clips use character image
- [ ] Verify final composed video shows character consistency
- [ ] Test with invalid image (should fail gracefully)
- [ ] Test without character image (should work normally)

---

## Error Handling & Edge Cases

### Error Scenarios

1. **Invalid Image Format**
   - Validate image on upload
   - Return 400 Bad Request with clear error message

2. **Image Interrogation Failure**
   - Log error
   - Disable character consistency for song
   - Continue with normal video generation

3. **Character Image Generation Failure**
   - Log error
   - Disable character consistency for song
   - Continue with normal video generation

4. **Missing Character Image During Clip Generation**
   - Log warning
   - Fall back to text-to-video
   - Continue clip generation

5. **Image-to-Video Model Not Available**
   - Check model availability
   - Fall back to text-to-video with enhanced prompt
   - Log warning

### Graceful Degradation

The system should always be able to generate videos even if character consistency fails:
- If character image generation fails, disable feature and continue
- If character image is missing during clip generation, use text-to-video
- Never block video generation due to character consistency issues

---

## Performance Considerations

### Optimization Strategies

1. **Async Character Image Generation**
   - Don't block song upload
   - Generate character image in background job
   - Clips can start generating once character image is ready

2. **Caching**
   - Cache interrogation results (same image = same prompt)
   - Cache consistent character images

3. **Parallel Processing**
   - Character image generation can happen in parallel with song analysis
   - Clips can be generated in parallel once character image is ready

### Expected Timings

- **Image Interrogation**: 5-10 seconds
- **Character Image Generation**: 30-60 seconds
- **Total Character Setup**: ~1-2 minutes (async, doesn't block upload)

---

## Cost Analysis

### Cost Breakdown

1. **Image Interrogation**
   - OpenAI GPT-4 Vision: ~$0.01-0.02 per image
   - Replicate BLIP-2 (fallback): ~$0.005 per image

2. **Character Image Generation**
   - Replicate SDXL: ~$0.01-0.02 per image

3. **Image-to-Video Generation**
   - Same cost as text-to-video (no additional cost)
   - Minimax Hailuo 2.3: Check Replicate pricing

### Total Additional Cost per Song

- **With Character Consistency**: +$0.02-0.04 per song
- **Per Clip**: No additional cost (uses same video generation API)

---

## Future Enhancements

### Phase 2 Improvements

1. **Better Model Selection**
   - Research and test IP-Adapter models on Replicate
   - Test ControlNet models for better consistency
   - Compare results across different models

2. **Character Consistency Verification**
   - Add automated consistency checking
   - Score clips for character similarity
   - Regenerate clips that fail consistency check

3. **Multiple Character Support**
   - Support multiple characters in one video
   - Character-specific prompts per clip

4. **Style Transfer**
   - Apply consistent art style across clips
   - Style transfer from reference image

5. **User Feedback Loop**
   - Allow users to regenerate character image
   - Fine-tune character based on user feedback

---

## Implementation Status

### ✅ Foundation Complete (November 2025)

The foundation infrastructure for character consistency has been implemented:

**Completed:**
- ✅ Database schema: Added all 4 character fields to Song model
- ✅ Migration: `004_add_character_fields.py` created and tested
- ✅ Image validation service: `image_validation.py` with format/size/dimension validation
- ✅ Storage helpers: `get_character_image_s3_key()` in `storage.py`
- ✅ API endpoint: `POST /songs/{song_id}/character-image` for uploading reference images
- ✅ Video generation: Modified `generate_section_video()` to accept `reference_image_url` parameter
- ✅ Clip generation: Modified to retrieve character image and pass to video generation
- ✅ Frontend component: `CharacterImageUpload.tsx` with drag-and-drop support
- ✅ Frontend integration: Added to `UploadPage.tsx` for short_form videos
- ✅ Unit tests: Comprehensive test coverage for image validation (20+ tests)

**What's Different from Original Plan:**
- Image upload is via separate endpoint (`POST /songs/{song_id}/character-image`) rather than form field in song upload
- Direct image-to-video: Reference image is passed directly to video generation (no intermediate character image generation yet)
- Simplified flow: No image interrogation or character image generation services yet (Phase 2 & 3)

**Current Capabilities:**
- Users can upload character reference images for short_form videos
- Images are validated (format, size, dimensions) and normalized to JPEG
- Images are stored in S3 and linked to songs
- Video generation can accept reference images for image-to-video mode
- Feature flag (`character_consistency_enabled`) is set when image is uploaded

**Still TODO (Future Phases):**
- Image interrogation service (Phase 2)
- Character image generation service (Phase 3)
- Full orchestration workflow (Phase 5)
- Character preview endpoint (Phase 6)

---

## Implementation Checklist

### Phase 1: Database & Storage ✅ COMPLETE
- [x] Add character fields to Song model
- [x] Create migration (`004_add_character_fields.py`)
- [x] Add storage helper functions (`get_character_image_s3_key()`)
- [x] Test S3 upload/download

### Phase 2: Image Interrogation
- [ ] Create `image_interrogation.py` service
- [ ] Implement OpenAI integration
- [ ] Implement Replicate fallback
- [ ] Add unit tests
- [ ] Test with sample images

### Phase 3: Character Image Generation
- [ ] Research Replicate models (SDXL, IP-Adapter, ControlNet)
- [ ] Create `character_image_generation.py` service
- [ ] Test model availability and parameters
- [ ] Add unit tests
- [ ] Generate test character images

### Phase 4: Video Generation Updates ✅ PARTIALLY COMPLETE
- [x] Modify `generate_section_video()` to accept image (`reference_image_url` parameter)
- [x] Basic image-to-video support (passes image to Replicate model)
- [ ] Implement dedicated `_generate_image_to_video()` function (currently inline)
- [x] Verify image-to-video model support (Hailuo 2.3 supports image input)
- [ ] Test image-to-video generation (needs end-to-end testing)
- [ ] Add fallback logic (graceful degradation if image missing)

### Phase 5: Integration ✅ PARTIALLY COMPLETE
- [ ] Create `character_consistency.py` orchestration service (for full workflow)
- [x] Character image upload endpoint (`POST /songs/{song_id}/character-image`)
- [x] Modify `run_clip_generation_job()` to retrieve and use character images
- [ ] Add background job for character image generation (Phase 3 dependency)
- [ ] Test end-to-end flow (needs Phase 2 & 3 complete)

### Phase 6: Frontend ✅ PARTIALLY COMPLETE
- [x] Add character image upload to UploadPage (for short_form videos)
- [x] Create `CharacterImageUpload` component (with drag-and-drop)
- [x] Update API client (uses separate endpoint)
- [ ] Create CharacterPreview component (for viewing uploaded images)
- [x] Test UI flow (upload works, needs preview component)

### Phase 7: Testing & Documentation
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Manual testing
- [ ] Update API documentation
- [ ] Update user documentation

---

## Notes & Considerations

### Model Research Required

Before implementation, research:
1. Which Replicate models support IP-Adapter or ControlNet?
2. Does `minimax/hailuo-2.3` support image input for image-to-video?
3. What are the best models for character consistency on Replicate?
4. What are the cost implications?

### Feature Flag

This feature should be behind a feature flag:
- `CHARACTER_CONSISTENCY_ENABLED` in config
- Allow enabling/disabling per song or globally
- Graceful degradation if disabled

### User Experience

- Character image upload should be optional
- Show character preview after upload
- Indicate when character consistency is enabled
- Show progress for character image generation

---

## References

- High-Level Plan: `docs/temp_advanced_features_planning/High-Level Plan.md`
- Technical Exploration: `docs/temp_advanced_features_planning/Technical-Exploration.md`
- Replicate Models: `docs/more/REPLICATE_VIDEO_MODELS.md`
- Current Video Generation: `backend/app/services/video_generation.py`
- Current Clip Generation: `backend/app/services/clip_generation.py`

