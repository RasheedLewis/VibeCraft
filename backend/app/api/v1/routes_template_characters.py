"""API routes for template characters."""

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.api.deps import get_db
from app.api.v1.utils import get_song_or_404
from app.core.config import get_settings
from app.schemas.template_character import (
    TemplateCharacterApply,
    TemplateCharacterListResponse,
)
from app.services.image_validation import normalize_image_format
from app.services.storage import (
    generate_presigned_get_url,
    get_character_image_s3_key,
    upload_bytes_to_s3,
)
from app.services.template_characters import (
    get_template_character,
    get_template_character_image,
    get_template_characters,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/template-characters",
    response_model=TemplateCharacterListResponse,
    summary="List available template characters",
)
async def list_template_characters():
    """
    List all available template character images with both poses.
    
    Returns list of characters, each with pose-a and pose-b images.
    """
    try:
        templates = get_template_characters()
        return TemplateCharacterListResponse(templates=templates)
    except Exception as exc:
        logger.exception(f"Failed to list template characters: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve template characters"
        ) from exc


@router.post(
    "/songs/{song_id}/character-image/template",
    status_code=status.HTTP_200_OK,
    summary="Apply template character to song",
)
async def apply_template_character(
    song_id: UUID,
    template: TemplateCharacterApply,
    db: Session = Depends(get_db),
) -> dict:
    """
    Apply a template character image to a song.
    
    Copies both poses (pose-a and pose-b) to the song's S3 location.
    Only available for songs with video_type='short_form'.
    """
    settings = get_settings()
    
    # Get song
    song = get_song_or_404(song_id, db)
    
    # Only allow for short_form videos
    if song.video_type != "short_form":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character consistency only available for short_form videos"
        )
    
    # Verify character exists
    char_def = get_template_character(template.character_id)
    if not char_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template character {template.character_id} not found"
        )
    
    # Copy pose-a (primary) to song's character reference location
    # Note: We always use pose-a as primary, pose-b as secondary
    pose_a_s3_key = get_character_image_s3_key(str(song_id), "reference")
    
    # Get pose-a image bytes and normalize to JPEG
    pose_a_bytes = get_template_character_image(template.character_id, "pose-a")
    if not pose_a_bytes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to retrieve pose-a image for character {template.character_id}"
        )
    
    # Normalize to JPEG
    normalized_pose_a = normalize_image_format(pose_a_bytes, "JPEG")
    
    # Upload pose-a
    try:
        await asyncio.to_thread(
            upload_bytes_to_s3,
            bucket_name=settings.s3_bucket_name,
            key=pose_a_s3_key,
            data=normalized_pose_a,
            content_type="image/jpeg",
        )
    except Exception as exc:
        logger.exception(f"Failed to upload pose-a to S3: {exc}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store character image. Verify storage configuration."
        ) from exc
    
    # Copy pose-b (secondary) to song's character pose-b location
    pose_b_s3_key = f"songs/{song_id}/character_pose_b.jpg"
    
    pose_b_bytes = get_template_character_image(template.character_id, "pose-b")
    if pose_b_bytes:
        # Normalize to JPEG
        normalized_pose_b = normalize_image_format(pose_b_bytes, "JPEG")
        
        # Upload pose-b
        try:
            await asyncio.to_thread(
                upload_bytes_to_s3,
                bucket_name=settings.s3_bucket_name,
                key=pose_b_s3_key,
                data=normalized_pose_b,
                content_type="image/jpeg",
            )
        except Exception as exc:
            logger.warning(f"Failed to upload pose-b to S3: {exc}")
            # Don't fail the request if pose-b fails, just log it
            pose_b_s3_key = None
    else:
        logger.warning(f"Failed to retrieve pose-b image for character {template.character_id}")
        pose_b_s3_key = None
    
    # Update song record
    song.character_reference_image_s3_key = pose_a_s3_key
    song.character_pose_b_s3_key = pose_b_s3_key
    song.character_consistency_enabled = True
    db.add(song)
    db.commit()
    db.refresh(song)
    
    # Generate presigned URLs
    try:
        image_url = await asyncio.to_thread(
            generate_presigned_get_url,
            bucket_name=settings.s3_bucket_name,
            key=pose_a_s3_key,
            expires_in=3600,
        )
    except Exception as exc:
        logger.exception(f"Failed to generate presigned URL: {exc}")
        image_url = None
    
    return {
        "song_id": str(song_id),
        "character_id": template.character_id,
        "image_s3_key": pose_a_s3_key,
        "pose_b_s3_key": pose_b_s3_key,
        "image_url": image_url,
        "character_consistency_enabled": True,
        "status": "applied",
    }

