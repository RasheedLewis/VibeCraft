"""Character image generation service using Replicate.

Generates a consistent character image from an interrogated prompt and reference image.
"""

import logging
import time
from typing import Optional

import replicate

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Replicate model for consistent character generation
# Using Stable Diffusion XL
# Note: We'll use prompt-only approach initially, can be enhanced with IP-Adapter later
CHARACTER_IMAGE_MODEL = "stability-ai/sdxl"


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
        reference_image_url: URL to user's reference image (for future IP-Adapter support)
        interrogation_prompt: Detailed prompt from image interrogation
        character_description: Concise character description
        style_notes: Optional style notes
        seed: Optional seed for reproducibility
        max_poll_attempts: Maximum polling attempts
        poll_interval_sec: Seconds between polling attempts
    
    Returns:
        Tuple of (success, image_url, metadata_dict)
        metadata_dict contains: seed, job_id, model, error (if failed)
    """
    try:
        settings = get_settings()
        if not settings.replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            return False, None, {"error": "REPLICATE_API_TOKEN not configured"}
        
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
        # Future enhancement: Add IP-Adapter support when available
        
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
                    metadata["error"] = "No image URL in output"
                    return False, None, metadata
            
            elif prediction.status == "failed":
                error_msg = getattr(prediction, "error", "Unknown error")
                logger.error(f"Character image generation failed: {error_msg}")
                metadata["error"] = str(error_msg)
                return False, None, metadata
            
            elif prediction.status in ["starting", "processing"]:
                elapsed_sec = (attempt + 1) * poll_interval_sec
                logger.info(
                    f"Character image generation in progress "
                    f"(attempt {attempt + 1}/{max_poll_attempts}, ~{elapsed_sec:.0f}s elapsed)..."
                )
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

