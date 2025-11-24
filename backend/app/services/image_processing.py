"""Image processing utilities for video generation.

Handles image transformations needed for video generation, such as aspect ratio padding.
"""

import logging
from io import BytesIO
from typing import Tuple
from uuid import uuid4

import httpx
from PIL import Image

from app.core.config import get_settings
from app.services.storage import generate_presigned_get_url, upload_bytes_to_s3

logger = logging.getLogger(__name__)

# Target 9:16 aspect ratio dimensions
TARGET_9_16_WIDTH = 1080
TARGET_9_16_HEIGHT = 1920  # 1080 * 16 / 9 = 1920


def pad_image_to_9_16(
    image_bytes: bytes,
    target_width: int = TARGET_9_16_WIDTH,
    background_color: Tuple[int, int, int] = (255, 255, 255),  # White
) -> bytes:
    """
    Pad an image to 9:16 aspect ratio by adding equal white space above and below.
    
    The original image is centered vertically. If the image is already 9:16 or wider
    (taller aspect ratio), it will be scaled to fit the width while maintaining
    aspect ratio, then padded to 9:16 height.
    
    Args:
        image_bytes: Raw image bytes (JPEG, PNG, or WEBP)
        target_width: Target width for 9:16 output (default: 1080)
        background_color: RGB color for padding (default: white)
    
    Returns:
        Padded image bytes in JPEG format
    
    Raises:
        ValueError: If image_bytes is not a valid image format
    """
    try:
        # Open image
        image = Image.open(BytesIO(image_bytes))
    except Exception as e:
        raise ValueError(f"Invalid image format: {str(e)}") from e
    
    # Convert RGBA to RGB if needed
    if image.mode == "RGBA":
        rgb_image = Image.new("RGB", image.size, background_color)
        rgb_image.paste(image, mask=image.split()[3])
        image = rgb_image
    elif image.mode != "RGB":
        image = image.convert("RGB")
    
    original_width, original_height = image.size
    target_height = int(target_width * 16 / 9)  # 9:16 aspect ratio
    
    logger.info(
        f"Padding image from {original_width}x{original_height} to {target_width}x{target_height} (9:16)"
    )
    
    # Calculate scaling to fit width (maintain aspect ratio)
    scale_factor = target_width / original_width
    scaled_height = int(original_height * scale_factor)
    
    # Scale image to target width
    if scale_factor != 1.0:
        image = image.resize((target_width, scaled_height), Image.Resampling.LANCZOS)
        logger.debug(f"Scaled image to {target_width}x{scaled_height}")
    
    # Create new image with target dimensions and background color
    padded_image = Image.new("RGB", (target_width, target_height), background_color)
    
    # Calculate vertical centering position
    y_offset = (target_height - scaled_height) // 2
    
    # Paste scaled image centered vertically
    padded_image.paste(image, (0, y_offset))
    
    logger.info(
        f"Padded image: added {y_offset}px above and {target_height - scaled_height - y_offset}px below"
    )
    
    # Convert to JPEG bytes
    output = BytesIO()
    padded_image.save(output, format="JPEG", quality=95)
    return output.getvalue()


def pad_and_upload_image_to_9_16(
    image_url: str,
    song_id: str,
    expires_in: int = 3600,
) -> str:
    """
    Download an image from URL, pad it to 9:16 aspect ratio, upload to S3, and return presigned URL.
    
    This is used when generating Short Form videos (9:16) with character images.
    The padded image ensures the video output matches 9:16 aspect ratio.
    
    Args:
        image_url: URL to the source image (presigned S3 URL or public URL)
        song_id: Song ID for organizing the padded image in S3
        expires_in: Expiration time for the presigned URL (seconds)
    
    Returns:
        Presigned S3 URL to the padded image
    
    Raises:
        ValueError: If image download or processing fails
        RuntimeError: If S3 upload fails
    """
    settings = get_settings()
    
    # Download image from URL
    try:
        logger.info(f"Downloading image from {image_url[:50]}... for 9:16 padding")
        with httpx.Client(timeout=30.0) as client:
            response = client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content
    except Exception as e:
        raise ValueError(f"Failed to download image from URL: {str(e)}") from e
    
    # Pad image to 9:16
    try:
        padded_image_bytes = pad_image_to_9_16(image_bytes)
        logger.info(f"Padded image to 9:16, new size: {len(padded_image_bytes)} bytes")
    except Exception as e:
        raise ValueError(f"Failed to pad image to 9:16: {str(e)}") from e
    
    # Upload padded image to S3
    padded_image_key = f"songs/{song_id}/character_padded_9_16_{uuid4()}.jpg"
    try:
        upload_bytes_to_s3(
            bucket_name=settings.s3_bucket_name,
            key=padded_image_key,
            data=padded_image_bytes,
            content_type="image/jpeg",
        )
        logger.info(f"Uploaded padded image to S3: {padded_image_key}")
    except Exception as e:
        raise RuntimeError(f"Failed to upload padded image to S3: {str(e)}") from e
    
    # Generate presigned URL
    try:
        presigned_url = generate_presigned_get_url(
            bucket_name=settings.s3_bucket_name,
            key=padded_image_key,
            expires_in=expires_in,
        )
        logger.info(f"Generated presigned URL for padded image (expires in {expires_in}s)")
        return presigned_url
    except Exception as e:
        raise RuntimeError(f"Failed to generate presigned URL for padded image: {str(e)}") from e


def create_9_16_placeholder_image(
    target_width: int = TARGET_9_16_WIDTH,
    background_color: Tuple[int, int, int] = (255, 255, 255),  # White
) -> bytes:
    """
    Create a 9:16 placeholder image (solid color background).
    
    This is used for text-to-video generation when no character image is provided
    but we want to generate a 9:16 video (Short Form format).
    
    Args:
        target_width: Target width for 9:16 output (default: 1080)
        background_color: RGB color for background (default: white)
    
    Returns:
        Placeholder image bytes in JPEG format
    """
    target_height = int(target_width * 16 / 9)  # 9:16 aspect ratio
    
    logger.info(
        f"Creating 9:16 placeholder image: {target_width}x{target_height}"
    )
    
    # Create solid color image
    placeholder_image = Image.new("RGB", (target_width, target_height), background_color)
    
    # Convert to JPEG bytes
    output = BytesIO()
    placeholder_image.save(output, format="JPEG", quality=95)
    return output.getvalue()


def create_and_upload_9_16_placeholder(
    song_id: str,
    expires_in: int = 3600,
    target_width: int = TARGET_9_16_WIDTH,
    background_color: Tuple[int, int, int] = (255, 255, 255),
) -> str:
    """
    Create a 9:16 placeholder image, upload to S3, and return presigned URL.
    
    This is used for text-to-video generation when no character image is provided
    but we want to generate a 9:16 video (Short Form format).
    
    Args:
        song_id: Song ID for organizing the placeholder in S3
        expires_in: Expiration time for the presigned URL (seconds)
        target_width: Target width for 9:16 output (default: 1080)
        background_color: RGB color for background (default: white)
    
    Returns:
        Presigned S3 URL to the placeholder image
    
    Raises:
        RuntimeError: If S3 upload fails
    """
    settings = get_settings()
    
    # Create placeholder image
    try:
        placeholder_bytes = create_9_16_placeholder_image(
            target_width=target_width,
            background_color=background_color,
        )
        logger.info(f"Created 9:16 placeholder image, size: {len(placeholder_bytes)} bytes")
    except Exception as e:
        raise RuntimeError(f"Failed to create 9:16 placeholder image: {str(e)}") from e
    
    # Upload placeholder image to S3
    placeholder_key = f"songs/{song_id}/placeholder_9_16_{uuid4()}.jpg"
    try:
        upload_bytes_to_s3(
            bucket_name=settings.s3_bucket_name,
            key=placeholder_key,
            data=placeholder_bytes,
            content_type="image/jpeg",
        )
        logger.info(f"Uploaded 9:16 placeholder to S3: {placeholder_key}")
    except Exception as e:
        raise RuntimeError(f"Failed to upload 9:16 placeholder to S3: {str(e)}") from e
    
    # Generate presigned URL
    try:
        presigned_url = generate_presigned_get_url(
            bucket_name=settings.s3_bucket_name,
            key=placeholder_key,
            expires_in=expires_in,
        )
        logger.info(f"Generated presigned URL for 9:16 placeholder (expires in {expires_in}s)")
        return presigned_url
    except Exception as e:
        raise RuntimeError(f"Failed to generate presigned URL for 9:16 placeholder: {str(e)}") from e

