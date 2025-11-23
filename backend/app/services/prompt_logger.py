"""Utility for logging prompts to video-api-testing/prompts.log for rapid iteration."""

import json
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Path to prompts.log file (relative to project root)
PROMPTS_LOG_PATH = Path(__file__).parent.parent.parent.parent / "video-api-testing" / "prompts.log"


def log_prompt_to_file(
    prompt: str,
    song_id: Optional[UUID] = None,
    clip_id: Optional[UUID] = None,
    optimized: bool = True,
) -> None:
    """
    Log a prompt to video-api-testing/prompts.log for rapid iteration.
    
    Format: JSON line with prompt, songId, clipId, and optimized flag.
    
    Args:
        prompt: The full prompt text
        song_id: Optional song ID
        clip_id: Optional clip ID
        optimized: Whether this is the optimized prompt (True) or original (False)
    """
    # Skip logging test prompts
    if prompt and prompt.strip().lower() == "test prompt":
        logger.debug("Skipping log for test prompt")
        return
    
    try:
        # Ensure directory exists
        PROMPTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Create log entry
        log_entry = {
            "prompt": prompt,
            "songId": str(song_id) if song_id else None,
            "clipId": str(clip_id) if clip_id else None,
            "optimized": optimized,
        }
        
        # Write as JSON line (one JSON object per line)
        with open(PROMPTS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        logger.debug(f"Logged prompt to {PROMPTS_LOG_PATH}")
    except Exception as e:
        # Don't fail clip generation if logging fails
        logger.warning(f"Failed to log prompt to file: {e}")

