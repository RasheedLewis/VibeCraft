"""Character consistency orchestration service."""

import json
import logging
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.repositories import SongRepository
from app.services.character_image_generation import generate_consistent_character_image
from app.services.image_interrogation import interrogate_reference_image
from app.services.storage import (
    download_bytes_from_s3,
    generate_presigned_get_url,
    upload_consistent_character_image,
)

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
    
    Args:
        song_id: UUID of the song
    
    Returns:
        Dictionary with status and optional error/result data
    """
    try:
        song = SongRepository.get_by_id(song_id)
        
        if not song.character_reference_image_s3_key:
            logger.warning(f"No character reference image for song {song_id}")
            return {"status": "skipped", "reason": "No reference image"}
        
        settings = get_settings()
        
        # Step 1: Download reference image
        logger.info(f"Downloading reference image for song {song_id}")
        image_bytes = download_bytes_from_s3(
            bucket_name=settings.s3_bucket_name,
            key=song.character_reference_image_s3_key,
        )
        
        # Step 2: Generate presigned URL for interrogation
        reference_url = generate_presigned_get_url(
            bucket_name=settings.s3_bucket_name,
            key=song.character_reference_image_s3_key,
            expires_in=3600,
        )
        
        # Step 3: Interrogate image
        logger.info(f"Interrogating reference image for song {song_id}")
        interrogation_result = interrogate_reference_image(
            image_url=reference_url,
            image_bytes=image_bytes,
        )
        
        # Store interrogation result
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
            song_id=str(song_id),
            image_bytes=generated_image_bytes,
        )
        
        # Step 6: Update song record
        song.character_generated_image_s3_key = consistent_s3_key
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

