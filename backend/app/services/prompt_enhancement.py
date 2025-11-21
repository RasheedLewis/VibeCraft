"""Prompt enhancement service for beat synchronization."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Motion type descriptors
MOTION_TYPES = {
    "bouncing": {
        "slow": "gentle bouncing motion, slow rhythmic movement",
        "medium": "bouncing motion, rhythmic pulsing",
        "fast": "rapid bouncing, energetic rhythmic motion",
    },
    "pulsing": {
        "slow": "slow pulsing, gentle rhythmic expansion and contraction",
        "medium": "pulsing motion, rhythmic breathing effect",
        "fast": "rapid pulsing, energetic rhythmic beats",
    },
    "rotating": {
        "slow": "slow rotating motion, gentle circular movement",
        "medium": "rotating motion, steady rhythmic spin",
        "fast": "rapid rotation, energetic spinning motion",
    },
    "stepping": {
        "slow": "slow stepping motion, deliberate rhythmic movement",
        "medium": "stepping motion, steady rhythmic pace",
        "fast": "rapid stepping, energetic rhythmic motion",
    },
    "looping": {
        "slow": "slow looping motion, gentle repetitive cycles",
        "medium": "looping motion, steady rhythmic repetition",
        "fast": "rapid looping, energetic repetitive cycles",
    },
}

# BPM ranges for tempo classification
BPM_SLOW = 60
BPM_MEDIUM = 100
BPM_FAST = 140


def get_tempo_classification(bpm: float) -> str:
    """
    Classify tempo based on BPM.
    
    Args:
        bpm: Beats per minute
        
    Returns:
        "slow", "medium", "fast", or "very_fast"
    """
    if bpm < BPM_SLOW:
        return "slow"
    elif bpm < BPM_MEDIUM:
        return "medium"
    elif bpm < BPM_FAST:
        return "fast"
    else:
        return "very_fast"


def get_motion_descriptor(bpm: float, motion_type: str = "bouncing") -> str:
    """
    Get motion descriptor based on BPM and motion type.
    
    Args:
        bpm: Beats per minute
        motion_type: Type of motion (bouncing, pulsing, rotating, etc.)
        
    Returns:
        Motion descriptor string
    """
    tempo = get_tempo_classification(bpm)
    
    if motion_type not in MOTION_TYPES:
        motion_type = "bouncing"  # Default
    
    motion_dict = MOTION_TYPES[motion_type]
    
    # Map very_fast to fast
    if tempo == "very_fast":
        tempo = "fast"
    
    return motion_dict.get(tempo, motion_dict["medium"])


def enhance_prompt_with_rhythm(
    base_prompt: str,
    bpm: float,
    motion_type: str = "bouncing",
    style_context: Optional[dict] = None,
) -> str:
    """
    Enhance base prompt with rhythmic motion cues.
    
    Args:
        base_prompt: Original user prompt or generated prompt
        bpm: Song BPM from song analysis
        motion_type: Type of rhythmic motion (bouncing, pulsing, rotating, stepping, looping)
        style_context: Optional dict with mood, colors, setting
        
    Returns:
        Enhanced prompt string with rhythmic descriptors
    """
    if bpm <= 0:
        logger.warning(f"Invalid BPM ({bpm}), skipping rhythm enhancement")
        return base_prompt
    
    # Get motion descriptor
    motion_descriptor = get_motion_descriptor(bpm, motion_type)
    
    # Build rhythmic phrase
    bpm_int = int(round(bpm))
    rhythmic_phrase = f"{motion_descriptor} synchronized to {bpm_int} BPM tempo, rhythmic motion matching the beat"
    
    # Combine with base prompt
    enhanced_prompt = f"{base_prompt}, {rhythmic_phrase}"
    
    logger.debug(f"Enhanced prompt with rhythm: BPM={bpm}, motion={motion_type}")
    logger.debug(f"Rhythmic phrase: {rhythmic_phrase}")
    
    return enhanced_prompt


def get_motion_type_from_genre(genre: Optional[str] = None) -> str:
    """
    Suggest motion type based on genre.
    
    Args:
        genre: Music genre (e.g., "electronic", "rock", "jazz")
        
    Returns:
        Suggested motion type
    """
    genre_motion_map = {
        "electronic": "pulsing",
        "dance": "bouncing",
        "rock": "stepping",
        "jazz": "looping",
        "hip-hop": "bouncing",
        "pop": "bouncing",
    }
    
    if genre:
        genre_lower = genre.lower()
        for key, motion in genre_motion_map.items():
            if key in genre_lower:
                return motion
    
    return "bouncing"  # Default

