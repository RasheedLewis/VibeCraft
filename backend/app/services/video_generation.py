"""Video generation service using Replicate API."""

import logging
import time
from typing import Optional
from uuid import UUID

import replicate

from app.core.config import get_settings
from app.schemas.scene import SceneSpec
from app.services.image_processing import pad_and_upload_image_to_9_16

logger = logging.getLogger(__name__)

# Replicate video generation model
# Using Minimax Hailuo 2.3 for text-to-video generation
# Model: minimax/hailuo-2.3
# Note: Using model owner/name format - Replicate will use latest version
VIDEO_MODEL = "minimax/hailuo-2.3"
IMAGE_TO_VIDEO_MODEL = "minimax/hailuo-2.3"  # Same model supports image input


def _generate_image_to_video(
    scene_spec: SceneSpec,
    reference_image_url: str,
    seed: Optional[int] = None,
    num_frames: Optional[int] = None,
    fps: Optional[int] = None,
    max_poll_attempts: int = 180,
    poll_interval_sec: float = 5.0,
    song_id: Optional[UUID] = None,  # For prompt logging
    clip_id: Optional[UUID] = None,  # For prompt logging
) -> tuple[bool, Optional[str], Optional[dict]]:
    """
    Generate video from image using image-to-video model.
    
    CHARACTER CONSISTENCY IMPLEMENTATION:
    - Uses Minimax Hailuo 2.3's image-to-video capability for character consistency
    - Both reference image (first_frame_image) AND text prompt are used together:
      * Image provides visual character reference (appearance, style, pose)
      * Prompt describes scene, motion, and action
      * They complement each other - image doesn't replace prompt
    - The model generates video starting from the reference image, maintaining character appearance
    - Seed parameter ensures reproducibility when regenerating the same scene
    - Reference image should be a clear character image (uploaded via character-image endpoint)
    
    Args:
        scene_spec: SceneSpec object with prompt and parameters
        reference_image_url: URL to reference character image (S3 presigned URL)
        seed: Optional seed for reproducibility
        num_frames: Optional frame count override
        fps: Optional FPS override
        max_poll_attempts: Maximum polling attempts
        poll_interval_sec: Seconds between polling attempts
    
    Returns:
        Tuple of (success, video_url, metadata_dict)
    """
    try:
        settings = get_settings()
        if not settings.replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            return False, None, {"error": "REPLICATE_API_TOKEN not configured"}

        client = replicate.Client(api_token=settings.replicate_api_token)

        # Optimize prompt for the specific API/model
        from app.services.prompt_enhancement import optimize_prompt_for_api

        optimized_prompt = optimize_prompt_for_api(
            prompt=scene_spec.prompt,
            api_name=IMAGE_TO_VIDEO_MODEL,
            bpm=None,  # Will extract from prompt if available
        )

        effective_fps = fps or 8
        frame_count = num_frames if num_frames and num_frames > 0 else int(round(scene_spec.duration_sec * effective_fps))
        logger.info(
            f"[VIDEO-GEN] Image-to-video frame calculation: "
            f"num_frames param={num_frames}, scene_spec.duration_sec={scene_spec.duration_sec}, "
            f"effective_fps={effective_fps}, calculated frame_count={frame_count}"
        )

        # CHARACTER CONSISTENCY: Both image AND prompt are used together
        # - Image provides visual character reference (appearance, style, pose)
        # - Prompt describes scene, motion, and action
        # - They complement each other - image doesn't replace prompt
        input_params = {
            "first_frame_image": reference_image_url,  # Reference character image for consistency
            "prompt": optimized_prompt,  # Scene prompt (used together with image)
            "num_frames": max(1, min(frame_count, 120)),
            "width": 576,
            "height": 320,
            "fps": effective_fps,
        }
        logger.info(
            f"[VIDEO-GEN] Image-to-video API params: num_frames={input_params['num_frames']}, "
            f"fps={input_params['fps']}, width={input_params['width']}, height={input_params['height']}"
        )

        if seed is not None:
            input_params["seed"] = seed

        logger.info(
            f"[VIDEO-GEN] Starting image-to-video generation for section {scene_spec.section_id}, "
            f"reference_image_url={'set' if reference_image_url else 'none'}"
        )
        logger.info(f"[VIDEO-GEN] Using reference image: {reference_image_url}")
        # Log FULL prompt for rapid iteration and debugging
        logger.info(f"[VIDEO-GEN] FULL PROMPT (optimized): {optimized_prompt}")
        logger.info(f"[VIDEO-GEN] FULL PROMPT (original): {scene_spec.prompt}")
        
        # Log optimized prompt to prompts.log file for collection
        from app.services.prompt_logger import log_prompt_to_file
        log_prompt_to_file(
            prompt=optimized_prompt,
            song_id=song_id,
            clip_id=clip_id,
            optimized=True,
        )

        # Get model version
        model = client.models.get(IMAGE_TO_VIDEO_MODEL)
        version = model.latest_version

        logger.info(f"[VIDEO-GEN] Calling Replicate API: model={IMAGE_TO_VIDEO_MODEL}, has_image={'first_frame_image' in input_params}")
        prediction = client.predictions.create(
            version=version,
            input=input_params,
        )

        job_id = prediction.id
        logger.info(f"[VIDEO-GEN] Replicate job started: {job_id}, type=image-to-video")

        # Poll for completion
        video_url = None
        metadata = {
            "fps": input_params["fps"],
            "num_frames": input_params["num_frames"],
            "resolution_width": input_params["width"],
            "resolution_height": input_params["height"],
            "seed": seed,
            "job_id": job_id,
            "generation_type": "image-to-video",
            "reference_image_url": reference_image_url,
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
                    logger.info(f"Image-to-video generation completed: {video_url}")
                    return True, video_url, metadata
                else:
                    logger.error(f"Image-to-video generation succeeded but no URL in output: {prediction.output}")
                    metadata["error"] = "No video URL in output"
                    return False, None, metadata

            elif prediction.status == "failed":
                error_msg = getattr(prediction, "error", "Unknown error")
                logger.error(f"Image-to-video generation failed: {error_msg}")
                metadata["error"] = str(error_msg)
                return False, None, metadata

            elif prediction.status in ["starting", "processing"]:
                elapsed_sec = (attempt + 1) * poll_interval_sec
                logger.info(
                    f"Image-to-video generation in progress "
                    f"(attempt {attempt + 1}/{max_poll_attempts}, ~{elapsed_sec:.0f}s elapsed)..."
                )
                time.sleep(poll_interval_sec)
            else:
                logger.warning(f"Unknown prediction status: {prediction.status}")
                time.sleep(poll_interval_sec)

        # Timeout
        try:
            final_prediction = client.predictions.get(job_id)
            if final_prediction.status == "failed":
                error_msg = getattr(final_prediction, "error", "Unknown error")
                logger.error(f"Image-to-video generation failed on Replicate: {error_msg}")
                metadata["error"] = f"Replicate error: {error_msg}"
            else:
                logger.error(
                    f"Image-to-video generation timed out after {max_poll_attempts} attempts "
                    f"(~{max_poll_attempts * poll_interval_sec / 60:.1f} minutes). "
                    f"Final status: {final_prediction.status}"
                )
                metadata["error"] = f"Timeout after {max_poll_attempts * poll_interval_sec / 60:.1f} minutes (status: {final_prediction.status})"
        except Exception as e:
            logger.error(f"Image-to-video generation timed out and error checking final status: {e}")
            metadata["error"] = f"Timeout after {max_poll_attempts * poll_interval_sec / 60:.1f} minutes"

        return False, None, metadata

    except Exception as e:
        logger.error(f"Error generating image-to-video: {e}", exc_info=True)
        return False, None, {"error": str(e)}


def generate_section_video(
    scene_spec: SceneSpec,
    seed: Optional[int] = None,
    num_frames: Optional[int] = None,
    fps: Optional[int] = None,
    reference_image_url: Optional[str] = None,
    reference_image_urls: Optional[list[str]] = None,
    pose: Optional[str] = None,  # "A" or "B" - maps to index 0 or 1 in reference_image_urls
    video_type: Optional[str] = None,  # "short_form" or "full_length" - determines if image should be padded to 9:16
    max_poll_attempts: int = 180,
    poll_interval_sec: float = 5.0,
    song_id: Optional[UUID] = None,  # For prompt logging
    clip_id: Optional[UUID] = None,  # For prompt logging
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
        pose: Optional pose selection ("A" -> index 0, "B" -> index 1) for selecting from reference_image_urls
        video_type: Optional video type ("short_form" or "full_length") - if "short_form", character images are padded to 9:16
        max_poll_attempts: Maximum number of polling attempts
        poll_interval_sec: Seconds between polling attempts
        song_id: Optional song ID for prompt logging
        clip_id: Optional clip ID for prompt logging

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
        # Enhanced fallback: validate image URLs and gracefully degrade to text-to-video if invalid
        image_urls = None
        if reference_image_urls and len(reference_image_urls) > 0:
            # Filter out None/empty URLs
            image_urls = [url for url in reference_image_urls if url and url.strip()]
            if not image_urls:
                logger.warning("All reference_image_urls were empty, falling back to text-to-video")
                image_urls = None
        elif reference_image_url:
            if reference_image_url and reference_image_url.strip():
                image_urls = [reference_image_url]
            else:
                logger.warning("reference_image_url is empty, falling back to text-to-video")
                image_urls = None
        
        is_image_to_video = image_urls is not None and len(image_urls) > 0
        
        # If we have a single image URL, use the dedicated image-to-video function
        if is_image_to_video and len(image_urls) == 1:
            try:
                return _generate_image_to_video(
                    scene_spec=scene_spec,
                    reference_image_url=image_urls[0],
                    seed=seed,
                    num_frames=num_frames,
                    fps=fps,
                    max_poll_attempts=max_poll_attempts,
                    poll_interval_sec=poll_interval_sec,
                    song_id=song_id,  # Pass song_id for prompt logging
                    clip_id=clip_id,  # Pass clip_id for prompt logging
                )
            except Exception as e:
                logger.warning(f"Image-to-video generation failed, falling back to text-to-video: {e}")
                # Fall through to text-to-video generation
                is_image_to_video = False
        
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
        logger.info(
            f"[VIDEO-GEN] Text-to-video frame calculation: "
            f"num_frames param={num_frames}, scene_spec.duration_sec={scene_spec.duration_sec}, "
            f"effective_fps={effective_fps}, calculated frame_count={frame_count}"
        )
        input_params = {
            "prompt": optimized_prompt,
            "num_frames": max(1, min(frame_count, 120)),
            "width": 576,  # Smaller resolution = faster/cheaper (XL supports up to 1024)
            "height": 320,  # 16:9 aspect ratio (576x320)
            "fps": effective_fps,
        }
        logger.info(
            f"[VIDEO-GEN] Text-to-video API params: num_frames={input_params['num_frames']}, "
            f"fps={input_params['fps']}, width={input_params['width']}, height={input_params['height']}"
        )

        # CHARACTER CONSISTENCY: Add image input if provided (for image-to-video)
        # - Both image AND prompt are used together (image = character reference, prompt = scene/motion)
        # - They complement each other - image doesn't replace prompt
        # - Note: minimax/hailuo-2.3 only supports single "first_frame_image" parameter
        if image_urls:
            # Select image based on pose parameter
            # The image_urls list from _get_character_image_urls() is ordered by selected_pose:
            # - If selected_pose="A": [pose_a_url, pose_b_url] (selected pose A at index 0)
            # - If selected_pose="B": [pose_b_url, pose_a_url] (selected pose B at index 0)
            # Since selected_pose is passed as the pose parameter, index 0 is always the selected pose.
            # The pose parameter mapping A->0, B->1 is relative to the list order, which depends on selected_pose.
            # For now, we use index 0 (the selected pose, which is first in the list).
            # If pose parameter is provided and differs from selected_pose, we'd need additional logic
            # to find the correct image, but currently we pass selected_pose as pose, so index 0 is correct.
            selected_index = 0  # Default to first image (selected pose, which is always first in list)
            
            if pose and pose.upper() in ("A", "B"):
                # The pose parameter should match selected_pose (which is passed from clip_generation.py)
                # So index 0 is correct. If we wanted to support pose != selected_pose, we'd need to
                # track which image is which pose, but that's not currently implemented.
                logger.debug(f"Using pose '{pose}' (selected pose), selecting index 0 from image_urls list")
            elif pose:
                logger.warning(f"Invalid pose '{pose}', expected 'A' or 'B', using index 0 instead")
            
            selected_image_url = image_urls[selected_index]
            
            # For Short Form videos (9:16), pad character image to 9:16 aspect ratio
            # This ensures the video output matches 9:16 (TikTok/Instagram/YouTube Shorts format)
            if video_type == "short_form" and song_id:
                try:
                    logger.info(
                        f"[VIDEO-GEN] Padding character image to 9:16 for Short Form video "
                        f"(song_id={song_id})"
                    )
                    selected_image_url = pad_and_upload_image_to_9_16(
                        image_url=selected_image_url,
                        song_id=str(song_id),
                        expires_in=3600,
                    )
                    logger.info(f"[VIDEO-GEN] Using padded 9:16 image: {selected_image_url[:50]}...")
                except Exception as e:
                    logger.warning(
                        f"Failed to pad image to 9:16, using original image: {e}. "
                        f"Video may not be 9:16 aspect ratio."
                    )
                    # Continue with original image - video generation will still work
            
            input_params["first_frame_image"] = selected_image_url
            
            if len(image_urls) > 1:
                logger.info(
                    f"Using image at index {selected_index} (pose={pose or 'default'}) for image-to-video generation "
                    f"(model supports single image only, ignoring {len(image_urls) - 1} additional image(s))"
                )
            else:
                logger.info(f"Using image-to-video generation with reference image: {selected_image_url}")
            logger.debug(f"Both image and prompt are being used: image={selected_image_url[:50]}..., prompt={optimized_prompt[:100]}...")

        if seed is not None:
            input_params["seed"] = seed

        generation_type = "image-to-video" if is_image_to_video else "text-to-video"
        logger.info(
            f"[VIDEO-GEN] Starting {generation_type} generation for section {scene_spec.section_id}, "
            f"has_image_urls={is_image_to_video}, image_count={len(image_urls) if image_urls else 0}"
        )
        # Log FULL prompt for rapid iteration and debugging
        logger.info(f"[VIDEO-GEN] FULL PROMPT (optimized): {optimized_prompt}")
        logger.info(f"[VIDEO-GEN] FULL PROMPT (original): {scene_spec.prompt}")
        
        # Log optimized prompt to prompts.log file for collection
        from app.services.prompt_logger import log_prompt_to_file
        log_prompt_to_file(
            prompt=optimized_prompt,
            song_id=song_id,
            clip_id=clip_id,
            optimized=True,
        )

        # Start the prediction (async - use predictions.create for long-running jobs)
        # Get the model version first
        model = client.models.get(VIDEO_MODEL)
        version = model.latest_version
        
        logger.info(
            f"[VIDEO-GEN] Calling Replicate API: model={VIDEO_MODEL}, "
            f"generation_type={generation_type}, has_image={'first_frame_image' in input_params}"
        )
        prediction = client.predictions.create(
            version=version,
            input=input_params,
        )

        job_id = prediction.id
        logger.info(f"[VIDEO-GEN] Replicate job started: {job_id}, type={generation_type}")

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

