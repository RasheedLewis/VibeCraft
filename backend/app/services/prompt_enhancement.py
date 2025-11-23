"""Prompt enhancement service for beat synchronization."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Motion type descriptors with enhanced rhythmic detail
MOTION_TYPES = {
    "bouncing": {
        "slow": "gentle bouncing motion, slow rhythmic up-and-down movement, smooth vertical oscillation",
        "medium": "bouncing motion, rhythmic pulsing, steady vertical rhythm matching the beat",
        "fast": "rapid bouncing, energetic rhythmic motion, quick vertical pulses synchronized to tempo",
    },
    "pulsing": {
        "slow": "slow pulsing, gentle rhythmic expansion and contraction, breathing-like motion",
        "medium": "pulsing motion, rhythmic breathing effect, steady expansion and contraction cycles",
        "fast": "rapid pulsing, energetic rhythmic beats, quick expansion-contraction cycles matching tempo",
    },
    "rotating": {
        "slow": "slow rotating motion, gentle circular movement, smooth continuous spin",
        "medium": "rotating motion, steady rhythmic spin, consistent circular rotation",
        "fast": "rapid rotation, energetic spinning motion, quick circular movement synchronized to beats",
    },
    "stepping": {
        "slow": "slow stepping motion, deliberate rhythmic movement, measured side-to-side steps",
        "medium": "stepping motion, steady rhythmic pace, consistent left-right stepping pattern",
        "fast": "rapid stepping, energetic rhythmic motion, quick side-to-side steps matching the beat",
    },
    "looping": {
        "slow": "slow looping motion, gentle repetitive cycles, smooth seamless repetition",
        "medium": "looping motion, steady rhythmic repetition, consistent repeating pattern",
        "fast": "rapid looping, energetic repetitive cycles, quick seamless loops synchronized to tempo",
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


def select_motion_type(
    genre: Optional[str] = None,
    mood: Optional[str] = None,
    mood_tags: Optional[list[str]] = None,
    bpm: Optional[float] = None,
    scene_context: Optional[dict] = None,
) -> str:
    """
    Select appropriate motion type based on song characteristics and scene context.
    
    This is an advanced selection function that considers multiple factors:
    - Genre (primary factor)
    - Mood and mood tags (secondary factor)
    - BPM (influences tempo-appropriate motion)
    - Scene context (e.g., section type, intensity)
    
    Args:
        genre: Music genre (e.g., "electronic", "rock", "jazz")
        mood: Primary mood tag (e.g., "energetic", "calm", "melancholic")
        mood_tags: List of mood tags for more nuanced selection
        bpm: Song BPM (optional, for tempo-based selection)
        scene_context: Optional dict with scene context (e.g., {"section_type": "chorus", "intensity": 0.8})
        
    Returns:
        Selected motion type: "bouncing", "pulsing", "rotating", "stepping", or "looping"
    """
    # Priority 1: Scene context (if provided)
    if scene_context:
        section_type = scene_context.get("section_type", "").lower()
        intensity = scene_context.get("intensity", 0.5)
        
        # Chorus sections: more energetic motion
        if section_type == "chorus":
            if intensity > 0.7:
                return "bouncing"  # High energy chorus
            else:
                return "pulsing"  # Medium energy chorus
        
        # Bridge sections: more flowing motion
        if section_type == "bridge":
            return "looping"  # Smooth transitions
        
        # Verse sections: steady motion
        if section_type == "verse":
            return "stepping"  # Narrative pacing
    
    # Priority 2: Mood-based selection
    if mood:
        mood_lower = mood.lower()
        
        # Energetic moods: bouncing or pulsing
        if "energetic" in mood_lower or "intense" in mood_lower or "aggressive" in mood_lower:
            if bpm and bpm > 140:
                return "pulsing"  # Very fast = pulsing
            else:
                return "bouncing"  # Fast = bouncing
        
        # Calm/relaxed moods: looping or slow pulsing
        if "calm" in mood_lower or "relaxed" in mood_lower or "peaceful" in mood_lower:
            return "looping"  # Smooth, repetitive
        
        # Melancholic/sad moods: slow rotating or stepping
        if "melancholic" in mood_lower or "sad" in mood_lower or "somber" in mood_lower:
            return "rotating"  # Slow, contemplative
    
    # Check mood tags for additional context
    if mood_tags:
        mood_tags_lower = [tag.lower() for tag in mood_tags]
        
        # Dance-related tags: bouncing
        if any(tag in ["dance", "danceable", "groovy"] for tag in mood_tags_lower):
            return "bouncing"
        
        # Electronic/techno tags: pulsing
        if any(tag in ["electronic", "techno", "synth"] for tag in mood_tags_lower):
            return "pulsing"
        
        # Acoustic/folk tags: stepping
        if any(tag in ["acoustic", "folk", "organic"] for tag in mood_tags_lower):
            return "stepping"
    
    # Priority 3: Genre-based selection (fallback to existing function)
    if genre:
        return get_motion_type_from_genre(genre)
    
    # Priority 4: BPM-based selection (if no other factors)
    if bpm:
        if bpm < 80:
            return "looping"  # Very slow = looping
        elif bpm < 100:
            return "rotating"  # Slow = rotating
        elif bpm < 120:
            return "stepping"  # Medium = stepping
        elif bpm < 140:
            return "bouncing"  # Fast = bouncing
        else:
            return "pulsing"  # Very fast = pulsing
    
    # Default fallback
    return "bouncing"


def _extract_bpm_from_prompt(prompt: str) -> Optional[float]:
    """
    Extract BPM value from an enhanced prompt string.
    
    Looks for patterns like "128 BPM", "128 BPM tempo", "at 128 beats per minute"
    
    Args:
        prompt: Prompt string that may contain BPM references
        
    Returns:
        BPM value if found, None otherwise
    """
    import re
    
    # Pattern 1: "128 BPM" or "128BPM"
    pattern1 = r'(\d+)\s*BPM'
    match = re.search(pattern1, prompt, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    # Pattern 2: "at 128 beats per minute"
    pattern2 = r'at\s+(\d+)\s+beats\s+per\s+minute'
    match = re.search(pattern2, prompt, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    
    return None


def optimize_prompt_for_api(
    prompt: str,
    api_name: str,
    bpm: Optional[float] = None,
) -> str:
    """
    Tailor prompt structure for specific video generation API.
    
    Different APIs have different prompt parsing and response patterns.
    This function optimizes prompts to work better with each API's characteristics.
    
    Args:
        prompt: Base prompt (may already be enhanced with rhythm)
        api_name: API/model identifier (e.g., "minimax/hailuo-2.3", "runway", "pika", "kling")
        bpm: Optional song BPM for tempo-specific optimizations. If not provided, will attempt to extract from prompt.
        
    Returns:
        Optimized prompt string
    """
    # Extract BPM from prompt if not provided
    if bpm is None or bpm <= 0:
        extracted_bpm = _extract_bpm_from_prompt(prompt)
        if extracted_bpm:
            bpm = extracted_bpm
            logger.debug(f"Extracted BPM {bpm} from prompt")
        else:
            # No BPM available, skip API-specific optimization
            logger.debug("No BPM available for API optimization, returning original prompt")
            return prompt
    
    # Normalize API name for matching
    api_lower = api_name.lower()
    bpm_int = int(round(bpm))
    
    # Minimax Hailuo 2.3 (current default model)
    if "hailuo" in api_lower or "minimax" in api_lower:
        # Hailuo responds well to concise, directive prompts with clear motion descriptions
        # It benefits from explicit tempo references, but avoid duplication if already in prompt
        if f"{bpm_int} BPM" not in prompt:
            optimized = f"{prompt}. Camera: static. Motion: synchronized to {bpm_int} BPM."
            logger.debug("Optimized prompt for Minimax Hailuo: added explicit BPM reference")
            return optimized
        else:
            # BPM already in prompt, just add camera/motion directive
            optimized = f"{prompt}. Camera: static."
            logger.debug("Optimized prompt for Minimax Hailuo: added camera directive")
            return optimized
    
    # Runway Gen-3 (future support)
    elif "runway" in api_lower:
        # Runway Gen-3 responds well to concise, directive prompts
        # Prefers action-oriented language
        motion_style = get_motion_descriptor(bpm, "bouncing")
        optimized = f"{prompt}. Camera: static. Motion: {motion_style}."
        logger.debug("Optimized prompt for Runway: added motion style")
        return optimized
    
    # Pika (future support)
    elif "pika" in api_lower:
        # Pika benefits from style references and tempo mentions
        if f"{bpm_int} BPM" not in prompt:
            optimized = f"{prompt}. Style: clean motion graphics. Tempo: {bpm_int} BPM."
        else:
            optimized = f"{prompt}. Style: clean motion graphics."
        logger.debug("Optimized prompt for Pika: added style and tempo")
        return optimized
    
    # Kling (future support)
    elif "kling" in api_lower:
        # Kling prefers detailed motion descriptions with context
        motion_style = get_motion_descriptor(bpm, "bouncing")
        if f"{bpm_int} beats per minute" not in prompt.lower():
            optimized = (
                f"{prompt}. The character moves with consistent "
                f"{motion_style} at {bpm_int} beats per minute, "
                f"creating a rhythmic visual pattern."
            )
        else:
            optimized = f"{prompt}. The character moves with consistent {motion_style}, creating a rhythmic visual pattern."
        logger.debug("Optimized prompt for Kling: added detailed motion description")
        return optimized
    
    # Generic optimization (fallback)
    else:
        # For unknown APIs, add basic tempo reference if not already present
        if f"{bpm_int} BPM" not in prompt:
            optimized = f"{prompt}. Tempo: {bpm_int} BPM."
            logger.debug(f"Applied generic prompt optimization for unknown API: {api_name}")
            return optimized
        else:
            return prompt

