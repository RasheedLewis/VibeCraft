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
    max_poll_attempts: int = 180,
    poll_interval_sec: float = 5.0,
) -> tuple[bool, Optional[str], Optional[dict]]:
    """
    Generate a video from a scene specification using Replicate.

    Args:
        scene_spec: SceneSpec object with prompt and parameters
        seed: Optional seed for reproducibility
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

        # Prepare input parameters for Minimax Hailuo 2.3 (text-to-video)
        # Parameters: prompt, num_frames, width, height, fps, seed
        effective_fps = fps or 8
        frame_count = num_frames if num_frames and num_frames > 0 else int(round(scene_spec.duration_sec * effective_fps))
        input_params = {
            "prompt": scene_spec.prompt,
            "num_frames": max(1, min(frame_count, 120)),
            "width": 576,  # Smaller resolution = faster/cheaper (XL supports up to 1024)
            "height": 320,  # 16:9 aspect ratio (576x320)
            "fps": effective_fps,
        }

        if seed is not None:
            input_params["seed"] = seed

        logger.info(f"Starting video generation for section {scene_spec.section_id}")
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
        }

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

