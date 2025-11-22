"""Cost tracking service for video generation."""

import logging
from uuid import UUID

from app.core.database import session_scope
from app.repositories import SongRepository

logger = logging.getLogger(__name__)

# Estimated costs per model (in USD)
# These are rough estimates - actual costs may vary on Replicate
MODEL_COST_ESTIMATES = {
    "minimax/hailuo-2.3": 0.05,  # Estimated $0.05 per generation
    "minimax/hailuo-02": 0.08,  # Estimated $0.08 per generation
    "minimax/hailuo-2.3-fast": 0.03,  # Estimated $0.03 per generation
    "runway/gen-3": 0.20,  # Estimated $0.20 per generation
    "pika/pika": 0.15,  # Estimated $0.15 per generation
    "kling/kling": 0.10,  # Estimated $0.10 per generation
}

# Character consistency costs
CHARACTER_IMAGE_GENERATION_COST = 0.02  # Estimated $0.02 per character image
IMAGE_INTERROGATION_COST_OPENAI = 0.01  # Estimated $0.01 per OpenAI vision call
IMAGE_INTERROGATION_COST_REPLICATE = 0.005  # Estimated $0.005 per Replicate call


def estimate_video_generation_cost(
    model_name: str,
    num_clips: int = 1,
    has_character_consistency: bool = False,
) -> float:
    """
    Estimate cost for video generation.
    
    Args:
        model_name: Replicate model name (e.g., "minimax/hailuo-2.3")
        num_clips: Number of clips to generate
        has_character_consistency: Whether character consistency is enabled
        
    Returns:
        Estimated cost in USD
    """
    # Get base cost per clip
    cost_per_clip = MODEL_COST_ESTIMATES.get(model_name, 0.05)  # Default $0.05
    
    # Calculate total video generation cost
    video_cost = cost_per_clip * num_clips
    
    # Add character consistency costs if enabled
    character_cost = 0.0
    if has_character_consistency:
        # One-time character image generation + interrogation
        character_cost = CHARACTER_IMAGE_GENERATION_COST + IMAGE_INTERROGATION_COST_OPENAI
    
    total_cost = video_cost + character_cost
    
    logger.info(
        f"[COST] Estimated cost for {num_clips} clips using {model_name}: "
        f"${total_cost:.4f} (video: ${video_cost:.4f}, character: ${character_cost:.4f})"
    )
    
    return total_cost


def track_video_generation_cost(
    song_id: UUID,
    model_name: str,
    num_clips: int = 1,
    has_character_consistency: bool = False,
) -> float:
    """
    Calculate and store estimated cost for video generation.
    
    Args:
        song_id: Song UUID to store cost for
        model_name: Replicate model name
        num_clips: Number of clips generated
        has_character_consistency: Whether character consistency is enabled
        
    Returns:
        Estimated cost in USD
    """
    cost = estimate_video_generation_cost(
        model_name=model_name,
        num_clips=num_clips,
        has_character_consistency=has_character_consistency,
    )
    
    # Store cost in database
    try:
        with session_scope() as session:
            song = SongRepository.get_by_id(song_id)
            if song:
                # Add to existing cost (if any)
                current_cost = song.total_generation_cost_usd or 0.0
                song.total_generation_cost_usd = current_cost + cost
                SongRepository.update(song)
                logger.info(
                    f"[COST-TRACKING] Stored cost ${cost:.4f} for song {song_id} "
                    f"(total: ${song.total_generation_cost_usd:.4f})"
                )
    except Exception as e:
        logger.warning(f"Failed to store cost for song {song_id}: {e}")
    
    return cost

