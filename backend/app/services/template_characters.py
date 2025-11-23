"""Template character management service."""

import logging
from typing import Optional

from app.core.config import get_settings
from app.services.storage import (
    download_bytes_from_s3,
    generate_presigned_get_url,
    upload_bytes_to_s3,
)

logger = logging.getLogger(__name__)

# Template character definitions
# Images are stored in img/characters/ directory
# Naming: character{N}-pose{1|2}.png
TEMPLATE_CHARACTERS = [
    {
        "id": "character-1",
        "name": "Geometric Character",
        "description": "Clean, minimalist geometric design",
        "poses": {
            "pose-a": "template-characters/character1-pose1.png",
            "pose-b": "template-characters/character1-pose2.png",
        },
        "default_pose": "pose-a",
    },
    {
        "id": "character-2",
        "name": "Organic Character",
        "description": "Flowing, natural organic design",
        "poses": {
            "pose-a": "template-characters/character2-pose1.png",
            "pose-b": "template-characters/character2-pose2.png",
        },
        "default_pose": "pose-a",
    },
    {
        "id": "character-3",
        "name": "Abstract Character",
        "description": "Bold, abstract artistic design",
        "poses": {
            "pose-a": "template-characters/character3-pose1.png",
            "pose-b": "template-characters/character3-pose2.png",
        },
        "default_pose": "pose-a",
    },
    {
        "id": "character-4",
        "name": "Minimalist Character",
        "description": "Simple, elegant minimalist design",
        "poses": {
            "pose-a": "template-characters/character4-pose1.png",
            "pose-b": "template-characters/character4-pose2.png",
        },
        "default_pose": "pose-a",
    },
]


def get_template_characters() -> list[dict]:
    """
    Get list of available template characters with presigned URLs for both poses.
    
    Returns:
        List of character dicts with thumbnail_url and image_url for each pose
    """
    settings = get_settings()
    characters = []
    
    for char_def in TEMPLATE_CHARACTERS:
        poses = []
        
        for pose_id, s3_key in char_def["poses"].items():
            try:
                # Generate presigned URL for thumbnail and full image
                thumbnail_url = generate_presigned_get_url(
                    bucket_name=settings.s3_bucket_name,
                    key=s3_key,
                    expires_in=3600,  # 1 hour
                )
                image_url = thumbnail_url  # Same URL for both
                
                poses.append({
                    "id": pose_id,
                    "thumbnail_url": thumbnail_url,
                    "image_url": image_url,
                })
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL for {s3_key}: {e}")
                # Continue with other poses even if one fails
        
        if poses:  # Only add character if we got at least one pose URL
            characters.append({
                "id": char_def["id"],
                "name": char_def["name"],
                "description": char_def.get("description"),
                "poses": poses,
                "default_pose": char_def["default_pose"],
            })
    
    return characters


def get_template_character(character_id: str) -> Optional[dict]:
    """
    Get a specific template character definition by ID.
    
    Args:
        character_id: Character ID (e.g., "character-1")
    
    Returns:
        Character definition dict or None if not found
    """
    for char_def in TEMPLATE_CHARACTERS:
        if char_def["id"] == character_id:
            return char_def
    return None


def get_template_character_image(character_id: str, pose: str = "pose-a") -> Optional[bytes]:
    """
    Get template character image bytes from S3 for specified character and pose.
    
    Args:
        character_id: Character ID (e.g., "character-1")
        pose: Pose ID (e.g., "pose-a" or "pose-b")
    
    Returns:
        Image bytes or None if not found
    """
    char_def = get_template_character(character_id)
    if not char_def:
        logger.error(f"Template character {character_id} not found")
        return None
    
    s3_key = char_def["poses"].get(pose)
    if not s3_key:
        logger.error(f"Pose {pose} not found for character {character_id}")
        return None
    
    settings = get_settings()
    try:
        image_bytes = download_bytes_from_s3(
            bucket_name=settings.s3_bucket_name,
            key=s3_key,
        )
        return image_bytes
    except Exception as e:
        logger.error(f"Failed to download template image {s3_key}: {e}")
        return None


def copy_template_pose_to_song(
    character_id: str,
    pose: str,
    song_s3_key: str,
) -> bool:
    """
    Copy a template character pose image to song's S3 location.
    
    Args:
        character_id: Character ID (e.g., "character-1")
        pose: Pose ID (e.g., "pose-a" or "pose-b")
        song_s3_key: Target S3 key for song (e.g., "songs/{song_id}/character_pose_a.jpg")
    
    Returns:
        True if successful, False otherwise
    """
    image_bytes = get_template_character_image(character_id, pose)
    if not image_bytes:
        return False
    
    settings = get_settings()
    try:
        # Determine content type based on source file extension
        # Template images are PNG, but we'll normalize to JPEG for consistency
        content_type = "image/jpeg"  # Will be normalized in API endpoint
        upload_bytes_to_s3(
            bucket_name=settings.s3_bucket_name,
            key=song_s3_key,
            data=image_bytes,
            content_type=content_type,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to upload template image to {song_s3_key}: {e}")
        return False

