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

