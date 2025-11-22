"""Video generation service using Replicate API."""

import logging
import time
from typing import Optional

import replicate

from app.core.config import get_settings
from app.schemas.scene import SceneSpec

logger = logging.getLogger(__name__)

# Replicate video generation model
# Using Minimax Hailuo 2.3 for text-to-video generation
# Model: minimax/hailuo-2.3
# Note: Using model owner/name format - Replicate will use latest version
VIDEO_MODEL = "minimax/hailuo-2.3"


def generate_section_video(
    scene_spec: SceneSpec,
    seed: Optional[int] = None,
    num_frames: Optional[int] = None,
    fps: Optional[int] = None,
    reference_image_url: Optional[str] = None,
    reference_image_urls: Optional[list[str]] = None,
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
        reference_image_url: Optional single image URL for image-to-video generation
        reference_image_urls: Optional list of image URLs (tries multiple, falls back to single)
        max_poll_attempts: Maximum number of polling attempts
        poll_interval_sec: Seconds between polling attempts

    Returns:
        Tuple of (success, video_url, metadata_dict)
        metadata_dict contains: fps, resolution_width, resolution_height, seed, job_id
    """
    try:
        settings = get_settings()
        if not settings.replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            return False, None, None

        # Create Replicate client
        client = replicate.Client(api_token=settings.replicate_api_token)

        # Determine if using image-to-video or text-to-video
        # Prioritize reference_image_urls (multiple images) over single reference_image_url
        image_urls = None
        if reference_image_urls and len(reference_image_urls) > 0:
            image_urls = reference_image_urls
        elif reference_image_url:
            image_urls = [reference_image_url]
        
        is_image_to_video = image_urls is not None and len(image_urls) > 0
        
        # Optimize prompt for the specific API/model
        from app.services.prompt_enhancement import optimize_prompt_for_api
        
        optimized_prompt = optimize_prompt_for_api(
            prompt=scene_spec.prompt,
            api_name=VIDEO_MODEL,
            bpm=None,  # Will extract from prompt if available
        )
        
        # Prepare input parameters for Minimax Hailuo 2.3
        # Supports both text-to-video and image-to-video
        # Parameters: prompt, num_frames, width, height, fps, seed, image (optional)
        effective_fps = fps or 8
        frame_count = num_frames if num_frames and num_frames > 0 else int(round(scene_spec.duration_sec * effective_fps))
        input_params = {
            "prompt": optimized_prompt,
            "num_frames": max(1, min(frame_count, 120)),
            "width": 576,  # Smaller resolution = faster/cheaper (XL supports up to 1024)
            "height": 320,  # 16:9 aspect ratio (576x320)
            "fps": effective_fps,
        }

        # Add image input if provided (for image-to-video)
        # Try multiple images first, fallback to single image
        if image_urls:
            if len(image_urls) > 1:
                # Try to pass multiple images
                # Attempt different parameter formats that might support multiple images
                # Note: minimax/hailuo-2.3 may not support multiple images, so we'll try and fallback
                try:
                    # Try "images" parameter (array)
                    input_params["images"] = image_urls
                    logger.info(f"Attempting image-to-video with {len(image_urls)} reference images")
                except (TypeError, ValueError):
                    # Fallback: try "image" parameter with array
                    try:
                        input_params["image"] = image_urls
                        logger.info(f"Attempting image-to-video with {len(image_urls)} reference images (array format)")
                    except (TypeError, ValueError):
                        # Final fallback: use first image only
                        logger.warning(
                            f"Model doesn't support multiple images, using first image only "
                            f"(fallback from {len(image_urls)} images)"
                        )
                        input_params["image"] = image_urls[0]
            else:
                # Single image
                input_params["image"] = image_urls[0]
                logger.info(f"Using image-to-video generation with reference image: {image_urls[0]}")

        if seed is not None:
            input_params["seed"] = seed

        generation_type = "image-to-video" if is_image_to_video else "text-to-video"
        logger.info(f"Starting {generation_type} generation for section {scene_spec.section_id}")
        logger.debug(f"Prompt: {scene_spec.prompt[:100]}...")

        # Start the prediction (async - use predictions.create for long-running jobs)
        # Get the model version first
        model = client.models.get(VIDEO_MODEL)
        version = model.latest_version
        
        prediction = client.predictions.create(
            version=version,
            input=input_params,
        )

        job_id = prediction.id
        logger.info(f"Replicate job started: {job_id}")

        # Poll for completion
        video_url = None
        metadata = {
            "fps": input_params["fps"],
            "num_frames": input_params["num_frames"],
            "resolution_width": input_params["width"],
            "resolution_height": input_params["height"],
            "seed": seed,
            "job_id": job_id,
            "generation_type": generation_type,
        }
        if reference_image_url:
            metadata["reference_image_url"] = reference_image_url

        for attempt in range(max_poll_attempts):
            prediction = client.predictions.get(job_id)

            if prediction.status == "succeeded":
                # Get video URL from output
                if prediction.output:
                    if isinstance(prediction.output, str):
                        video_url = prediction.output
                    elif isinstance(prediction.output, list) and len(prediction.output) > 0:
                        video_url = prediction.output[0]
                    elif isinstance(prediction.output, dict) and "video" in prediction.output:
                        video_url = prediction.output["video"]

                if video_url:
                    logger.info(f"Video generation completed: {video_url}")
                    return True, video_url, metadata
                else:
                    logger.error(f"Video generation succeeded but no URL in output: {prediction.output}")
                    return False, None, metadata

            elif prediction.status == "failed":
                error_msg = getattr(prediction, "error", "Unknown error")
                logger.error(f"Video generation failed: {error_msg}")
                metadata["error"] = str(error_msg)
                return False, None, metadata

            elif prediction.status in ["starting", "processing"]:
                elapsed_sec = (attempt + 1) * poll_interval_sec
                logger.info(f"Video generation in progress (attempt {attempt + 1}/{max_poll_attempts}, ~{elapsed_sec:.0f}s elapsed)...")
                time.sleep(poll_interval_sec)
            else:
                logger.warning(f"Unknown prediction status: {prediction.status}")
                time.sleep(poll_interval_sec)

        # Timeout - check final status before giving up
        try:
            final_prediction = client.predictions.get(job_id)
            if final_prediction.status == "failed":
                error_msg = getattr(final_prediction, "error", "Unknown error")
                logger.error(f"Video generation failed on Replicate: {error_msg}")
                metadata["error"] = f"Replicate error: {error_msg}"
            else:
                logger.error(f"Video generation timed out after {max_poll_attempts} attempts (~{max_poll_attempts * poll_interval_sec / 60:.1f} minutes). Final status: {final_prediction.status}")
                metadata["error"] = f"Timeout after {max_poll_attempts * poll_interval_sec / 60:.1f} minutes (status: {final_prediction.status})"
        except Exception as e:
            logger.error(f"Video generation timed out and error checking final status: {e}")
            metadata["error"] = f"Timeout after {max_poll_attempts * poll_interval_sec / 60:.1f} minutes"
        
        return False, None, metadata

    except Exception as e:
        logger.error(f"Error generating video: {e}", exc_info=True)
        return False, None, {"error": str(e)}


def poll_video_generation_status(job_id: str) -> tuple[str, Optional[str], Optional[dict]]:
    """
    Poll the status of a video generation job.

    Args:
        job_id: Replicate prediction ID

    Returns:
        Tuple of (status, video_url, metadata_dict)
        status: "pending", "processing", "completed", "failed"
    """
    try:
        settings = get_settings()
        if not settings.replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            return "failed", None, {"error": "API token not configured"}

        client = replicate.Client(api_token=settings.replicate_api_token)
        prediction = client.predictions.get(job_id)

        status_map = {
            "starting": "processing",
            "processing": "processing",
            "succeeded": "completed",
            "failed": "failed",
            "canceled": "failed",
        }

        status = status_map.get(prediction.status, "pending")
        video_url = None
        metadata = {}

        if status == "completed":
            if prediction.output:
                if isinstance(prediction.output, str):
                    video_url = prediction.output
                elif isinstance(prediction.output, list) and len(prediction.output) > 0:
                    video_url = prediction.output[0]
                elif isinstance(prediction.output, dict) and "video" in prediction.output:
                    video_url = prediction.output["video"]

        if prediction.status == "failed":
            metadata["error"] = getattr(prediction, "error", "Unknown error")

        return status, video_url, metadata

    except Exception as e:
        logger.error(f"Error polling video generation status: {e}", exc_info=True)
        return "failed", None, {"error": str(e)}

