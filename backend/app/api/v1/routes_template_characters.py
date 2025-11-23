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


async def _upload_template_pose_to_song(
    character_id: str,
    pose: str,
    s3_key: str,
    settings,
    require_success: bool = True,
) -> bool:
    """
    Upload a template character pose to song's S3 location.
    
    Args:
        character_id: Template character ID
        pose: Pose ID ("pose-a" or "pose-b")
        s3_key: Target S3 key for the song
        settings: Application settings
        require_success: If True, raise exception on failure; if False, return False
    
    Returns:
        True if successful, False if failed and require_success=False
    
    Raises:
        HTTPException: If require_success=True and upload fails
    """
    # Get pose image bytes
    pose_bytes = get_template_character_image(character_id, pose)
    if not pose_bytes:
        if require_success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Failed to retrieve {pose} image for character {character_id}"
            )
        logger.warning(f"Failed to retrieve {pose} image for character {character_id}")
        return False
    
    # Normalize to JPEG
    try:
        normalized_bytes = normalize_image_format(pose_bytes, "JPEG")
    except ValueError as exc:
        if require_success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid image format for {pose}: {str(exc)}"
            ) from exc
        logger.warning(f"Invalid image format for {pose}: {exc}")
        return False
    
    # Upload to S3
    try:
        await asyncio.to_thread(
            upload_bytes_to_s3,
            bucket_name=settings.s3_bucket_name,
            key=s3_key,
            data=normalized_bytes,
            content_type="image/jpeg",
        )
        return True
    except Exception as exc:
        if require_success:
            logger.exception(f"Failed to upload {pose} to S3: {exc}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Failed to store character image. Verify storage configuration."
            ) from exc
        logger.warning(f"Failed to upload {pose} to S3: {exc}")
        return False


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
    await _upload_template_pose_to_song(
        character_id=template.character_id,
        pose="pose-a",
        s3_key=pose_a_s3_key,
        settings=settings,
        require_success=True,  # Pose-a is required
    )
    
    # Copy pose-b (secondary) to song's character pose-b location
    pose_b_s3_key = f"songs/{song_id}/character_pose_b.jpg"
    pose_b_success = await _upload_template_pose_to_song(
        character_id=template.character_id,
        pose="pose-b",
        s3_key=pose_b_s3_key,
        settings=settings,
        require_success=False,  # Pose-b is optional, don't fail request if it fails
    )
    if not pose_b_success:
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

