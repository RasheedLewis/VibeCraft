"""Image interrogation service for character consistency.

Uses multimodal LLM to convert reference images into detailed prompts.
"""

import base64
import json
import logging
from typing import Optional

import replicate
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
    
    Raises:
        RuntimeError: If interrogation fails with both OpenAI and Replicate
    """
    settings = get_settings()
    
    # Use OpenAI GPT-4 Vision for image interrogation
    # Fallback to other multimodal models if OpenAI not available
    if settings.openai_api_key:
        try:
            return _interrogate_with_openai(image_url, image_bytes)
        except Exception as e:
            logger.warning(f"OpenAI image interrogation failed, trying Replicate fallback: {e}")
            # Fall through to Replicate fallback
    
    # Fallback: Use Replicate's image-to-text model
    if settings.replicate_api_token:
        return _interrogate_with_replicate(image_url, image_bytes)
    else:
        raise RuntimeError(
            "Neither OpenAI API key nor Replicate API token is configured. "
            "Cannot perform image interrogation."
        )


def _interrogate_with_openai(
    image_url: str,
    image_bytes: Optional[bytes] = None,
) -> dict[str, str]:
    """Interrogate using OpenAI GPT-4 Vision."""
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured")
    
    client = OpenAI(api_key=settings.openai_api_key)
    
    # If we have bytes, convert to base64
    if image_bytes:
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
            model="gpt-4o",  # GPT-4o supports vision
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
    settings = get_settings()
    if not settings.replicate_api_token:
        raise ValueError("Replicate API token not configured")
    
    client = replicate.Client(api_token=settings.replicate_api_token)
    
    # Use img2prompt model for image captioning
    # Note: This model converts images to prompts suitable for image generation
    try:
        output = client.run(
            "methexis-inc/img2prompt",
            input={"image": image_url}
        )
        
        # Parse output and create structured description
        # The output is typically a string prompt
        prompt_text = output if isinstance(output, str) else str(output)
        
        # Create structured response from the prompt
        # Since Replicate's img2prompt doesn't return structured JSON,
        # we use the prompt as both the detailed prompt and description
        return {
            "prompt": prompt_text,
            "character_description": prompt_text[:200] if len(prompt_text) > 200 else prompt_text,
            "style_notes": "Generated from image interrogation via Replicate",
        }
    except Exception as e:
        logger.error(f"Replicate image interrogation failed: {e}", exc_info=True)
        raise

