"""Scene planner service for generating video scene specifications.

Maps song analysis data (mood, genre, section type) to visual prompts and parameters.
"""

import logging
from typing import Optional

from app.schemas.analysis import SectionLyrics, SongAnalysis, SongSection
from app.schemas.scene import (
    CameraMotion,
    ColorPalette,
    SceneSpec,
    ShotPattern,
    TemplateType,
)

logger = logging.getLogger(__name__)

# Default template (can be extended later)
DEFAULT_TEMPLATE: TemplateType = "abstract"


def get_section_from_analysis(analysis: SongAnalysis, section_id: str) -> SongSection | None:
    """
    Get a section from analysis by section ID.

    Args:
        analysis: SongAnalysis object
        section_id: Section ID to find

    Returns:
        SongSection if found, None otherwise
    """
    for section in analysis.sections:
        if section.id == section_id:
            return section
    return None


def get_section_lyrics_from_analysis(
    analysis: SongAnalysis, section_id: str
) -> SectionLyrics | None:
    """
    Get section lyrics from analysis by section ID.

    Args:
        analysis: SongAnalysis object
        section_id: Section ID to find lyrics for

    Returns:
        SectionLyrics if found, None otherwise
    """
    if not analysis.section_lyrics:
        return None
    for section_lyrics in analysis.section_lyrics:
        if section_lyrics.section_id == section_id:
            return section_lyrics
    return None


def map_mood_to_color_palette(mood_primary: str, mood_vector) -> ColorPalette:
    """
    Map mood to color palette.

    Args:
        mood_primary: Primary mood tag (e.g., "energetic", "calm", "melancholic")
        mood_vector: MoodVector object with energy, valence, danceability, tension

    Returns:
        ColorPalette object
    """
    # High energy + high valence = vibrant, warm colors
    if mood_primary == "energetic" and mood_vector.valence > 0.6:
        return ColorPalette(
            primary="#FF6B9D",  # Vibrant pink
            secondary="#FFD93D",  # Bright yellow
            accent="#6BCF7F",  # Electric green
            mood="vibrant",
        )

    # High energy + low valence = intense, dark colors
    if mood_primary == "energetic" and mood_vector.valence <= 0.6:
        return ColorPalette(
            primary="#8B0000",  # Dark red
            secondary="#FF4500",  # Orange red
            accent="#FFD700",  # Gold
            mood="intense",
        )

    # Calm/relaxed = soft, cool colors
    if mood_primary == "calm" or mood_primary == "relaxed":
        return ColorPalette(
            primary="#4A90E2",  # Soft blue
            secondary="#7B68EE",  # Medium slate blue
            accent="#87CEEB",  # Sky blue
            mood="calm",
        )

    # Melancholic/sad = muted, desaturated colors
    if mood_primary == "melancholic" or mood_primary == "sad":
        return ColorPalette(
            primary="#708090",  # Slate gray
            secondary="#556B2F",  # Dark olive green
            accent="#8B7355",  # Dark khaki
            mood="muted",
        )

    # Intense = high contrast, saturated colors
    if mood_primary == "intense":
        return ColorPalette(
            primary="#DC143C",  # Crimson
            secondary="#000000",  # Black
            accent="#FF1493",  # Deep pink
            mood="intense",
        )

    # Default: neutral palette
    return ColorPalette(
        primary="#9370DB",  # Medium purple
        secondary="#BA55D3",  # Medium orchid
        accent="#DDA0DD",  # Plum
        mood="neutral",
    )


def map_genre_to_camera_motion(genre: Optional[str], bpm: Optional[float] = None) -> CameraMotion:
    """
    Map genre to camera motion preset.

    Args:
        genre: Primary genre (e.g., "Electronic", "Rock", "Hip-Hop")
        bpm: Optional BPM for motion speed adjustment

    Returns:
        CameraMotion object
    """
    # Default speed based on BPM
    if bpm is None:
        speed = "medium"
    elif bpm < 90:
        speed = "slow"
    elif bpm > 130:
        speed = "fast"
    else:
        speed = "medium"

    # Electronic/EDM = fast, dynamic motion
    if genre == "Electronic" or genre == "EDM":
        return CameraMotion(
            type="fast_zoom",
            intensity=0.8,
            speed="fast",
        )

    # Rock/Metal = aggressive, quick cuts
    if genre == "Rock" or genre == "Metal":
        return CameraMotion(
            type="quick_cuts",
            intensity=0.9,
            speed="fast",
        )

    # Hip-Hop = smooth, steady motion
    if genre == "Hip-Hop":
        return CameraMotion(
            type="slow_pan",
            intensity=0.6,
            speed="medium",
        )

    # Pop = balanced, dynamic
    if genre == "Pop":
        return CameraMotion(
            type="medium_pan",
            intensity=0.7,
            speed="medium",
        )

    # Country/Folk = slow, gentle motion
    if genre == "Country" or genre == "Folk":
        return CameraMotion(
            type="slow_pan",
            intensity=0.4,
            speed="slow",
        )

    # Ambient = very slow, minimal motion
    if genre == "Ambient":
        return CameraMotion(
            type="static",
            intensity=0.2,
            speed="slow",
        )

    # Default: medium motion
    return CameraMotion(
        type="medium_pan",
        intensity=0.5,
        speed=speed,
    )


def map_section_type_to_shot_pattern(section_type: str) -> ShotPattern:
    """
    Map section type to shot pattern.

    Args:
        section_type: Section type (e.g., "verse", "chorus", "bridge")

    Returns:
        ShotPattern object
    """
    # Intro = wide, establishing shot
    if section_type == "intro":
        return ShotPattern(
            pattern="wide",
            pacing="slow",
            transitions=["fade_in"],
        )

    # Verse = medium shots, steady pacing
    if section_type == "verse":
        return ShotPattern(
            pattern="medium",
            pacing="medium",
            transitions=["cut"],
        )

    # Chorus = dynamic, close-up to wide, fast pacing
    if section_type == "chorus":
        return ShotPattern(
            pattern="close_up_to_wide",
            pacing="fast",
            transitions=["zoom", "cut", "flash"],
        )

    # Pre-chorus = building tension, medium to close
    if section_type == "pre_chorus":
        return ShotPattern(
            pattern="medium_to_close",
            pacing="medium",
            transitions=["zoom_in", "cut"],
        )

    # Bridge = different angle, wide shots
    if section_type == "bridge":
        return ShotPattern(
            pattern="wide",
            pacing="slow",
            transitions=["fade", "crossfade"],
        )

    # Solo = close-up, fast cuts
    if section_type == "solo":
        return ShotPattern(
            pattern="close_up",
            pacing="fast",
            transitions=["quick_cut", "flash"],
        )

    # Drop = intense, rapid cuts
    if section_type == "drop":
        return ShotPattern(
            pattern="close_up",
            pacing="very_fast",
            transitions=["strobe", "quick_cut", "flash"],
        )

    # Outro = wide, fade out
    if section_type == "outro":
        return ShotPattern(
            pattern="wide",
            pacing="slow",
            transitions=["fade_out"],
        )

    # Default: medium shot
    return ShotPattern(
        pattern="medium",
        pacing="medium",
        transitions=["cut"],
    )


def build_prompt(
    section: Optional[SongSection],
    mood_primary: str,
    mood_tags: list[str],
    genre: Optional[str],
    color_palette: ColorPalette,
    camera_motion: CameraMotion,
    shot_pattern: ShotPattern,
    lyrics: Optional[str] = None,
) -> str:
    """
    Build video generation prompt combining all features.

    Args:
        section: SongSection object (optional, None for clip-based generation)
        mood_primary: Primary mood tag
        mood_tags: List of mood tags
        genre: Primary genre
        color_palette: ColorPalette object
        camera_motion: CameraMotion object
        shot_pattern: ShotPattern object
        lyrics: Optional lyrics text for motif injection

    Returns:
        Complete prompt string for video generation
    """
    # Base prompt components
    components = []

    # Visual style from template
    components.append("Abstract visual style")

    # Color palette
    components.append(f"{color_palette.mood} color palette with {color_palette.primary}, {color_palette.secondary}, and {color_palette.accent}")

    # Mood description
    mood_desc = ", ".join(mood_tags[:3])  # Use top 3 mood tags
    components.append(f"{mood_desc} mood")

    # Genre influence
    if genre:
        components.append(f"{genre} aesthetic")

    # Shot pattern
    components.append(f"{shot_pattern.pattern} with {shot_pattern.pacing} pacing")

    # Camera motion
    components.append(f"{camera_motion.type} camera motion ({camera_motion.speed} speed)")

    # Section type context (only if section is provided)
    if section:
        if section.type == "chorus":
            components.append("dynamic and energetic")
        elif section.type == "verse":
            components.append("steady and narrative")
        elif section.type == "bridge":
            components.append("transitional and atmospheric")

    # Lyrics motif (if available)
    if lyrics:
        # Extract key words from lyrics (first 10 words)
        lyric_words = lyrics.split()[:10]
        key_words = [w for w in lyric_words if len(w) > 3][:3]  # Filter short words, take 3
        if key_words:
            components.append(f"inspired by: {', '.join(key_words)}")

    # Combine into final prompt
    prompt = ", ".join(components)
    return prompt


def build_scene_spec(
    section_id: str,
    analysis: SongAnalysis,
    template: TemplateType = DEFAULT_TEMPLATE,
) -> SceneSpec:
    """
    Build scene specification for a given section.

    Args:
        section_id: Section identifier
        analysis: SongAnalysis object
        template: Template type (default: "abstract")

    Returns:
        SceneSpec object with complete scene parameters

    Raises:
        ValueError: If section not found in analysis
    """

    # Find the section
    section = get_section_from_analysis(analysis, section_id)
    if section is None:
        raise ValueError(f"Section {section_id} not found in analysis")

    # Get section lyrics (if available)
    section_lyrics_obj = get_section_lyrics_from_analysis(analysis, section_id)
    lyrics_text = section_lyrics_obj.text if section_lyrics_obj else None

    # Map mood to color palette
    color_palette = map_mood_to_color_palette(analysis.mood_primary, analysis.mood_vector)

    # Map genre to camera motion
    camera_motion = map_genre_to_camera_motion(analysis.primary_genre, analysis.bpm)

    # Map section type to shot pattern
    shot_pattern = map_section_type_to_shot_pattern(section.type)

    # Calculate intensity from mood vector
    intensity = (analysis.mood_vector.energy + analysis.mood_vector.tension) / 2.0

    # Build prompt
    prompt = build_prompt(
        section=section,
        mood_primary=analysis.mood_primary,
        mood_tags=analysis.mood_tags,
        genre=analysis.primary_genre,
        color_palette=color_palette,
        camera_motion=camera_motion,
        shot_pattern=shot_pattern,
        lyrics=lyrics_text,
    )

    # Calculate duration
    duration_sec = section.end_sec - section.start_sec

    return SceneSpec(
        section_id=section_id,
        template=template,
        prompt=prompt,
        color_palette=color_palette,
        camera_motion=camera_motion,
        shot_pattern=shot_pattern,
        intensity=intensity,
        duration_sec=duration_sec,
    )


def build_clip_scene_spec(
    start_sec: float,
    end_sec: float,
    analysis: SongAnalysis,
    template: TemplateType = DEFAULT_TEMPLATE,
) -> SceneSpec:
    """
    Build scene specification for a clip (non-section mode).

    Uses song-level analysis instead of section-specific data.

    Args:
        start_sec: Clip start time in seconds
        end_sec: Clip end time in seconds
        analysis: SongAnalysis object
        template: Template type (default: "abstract")

    Returns:
        SceneSpec object with complete scene parameters
    """
    duration_sec = end_sec - start_sec

    # Use song-level mood/genre
    color_palette = map_mood_to_color_palette(analysis.mood_primary, analysis.mood_vector)
    camera_motion = map_genre_to_camera_motion(analysis.primary_genre, analysis.bpm)

    # Default shot pattern (no section type)
    shot_pattern = ShotPattern(
        pattern="medium",
        pacing="medium",
        transitions=["cut"],
    )

    # Build prompt from song-level data (no section context)
    prompt = build_prompt(
        section=None,  # No section context
        mood_primary=analysis.mood_primary,
        mood_tags=analysis.mood_tags,
        genre=analysis.primary_genre,
        color_palette=color_palette,
        camera_motion=camera_motion,
        shot_pattern=shot_pattern,
        lyrics=None,  # Could extract lyrics for time range if needed
    )

    intensity = (analysis.mood_vector.energy + analysis.mood_vector.tension) / 2.0

    return SceneSpec(
        section_id=None,  # No section ID in clip mode
        template=template,
        prompt=prompt,
        color_palette=color_palette,
        camera_motion=camera_motion,
        shot_pattern=shot_pattern,
        intensity=intensity,
        duration_sec=duration_sec,
    )

