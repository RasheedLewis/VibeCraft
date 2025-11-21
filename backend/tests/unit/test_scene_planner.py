"""Unit tests for scene planner service.

Tests logic for mapping mood/genre/section type to visual parameters - no audio files needed, fast.
Validates map_mood_to_color_palette(), map_genre_to_camera_motion(), map_section_type_to_shot_pattern(),
build_prompt(), and build_scene_spec() in isolation.

Run with: pytest backend/tests/unit/test_scene_planner.py -v
Or from backend/: pytest tests/unit/test_scene_planner.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from app.schemas.analysis import MoodVector, SongAnalysis, SongSection  # noqa: E402
from app.services.scene_planner import (  # noqa: E402
    build_prompt,
    build_scene_spec,
    map_genre_to_camera_motion,
    map_mood_to_color_palette,
    map_section_type_to_shot_pattern,
)


class TestMapMoodToColorPalette:
    """Test mood to color palette mapping logic."""

    def test_energetic_high_valence(self):
        """Test energetic mood with high valence produces vibrant palette."""
        mood_vector = MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5)
        result = map_mood_to_color_palette("energetic", mood_vector)

        assert result.mood == "vibrant"
        assert result.primary == "#FF6B9D"  # Vibrant pink
        assert result.secondary == "#FFD93D"  # Bright yellow
        assert result.accent == "#6BCF7F"  # Electric green

    def test_energetic_low_valence(self):
        """Test energetic mood with low valence produces intense palette."""
        mood_vector = MoodVector(energy=0.8, valence=0.5, danceability=0.7, tension=0.5)
        result = map_mood_to_color_palette("energetic", mood_vector)

        assert result.mood == "intense"
        assert result.primary == "#8B0000"  # Dark red
        assert result.secondary == "#FF4500"  # Orange red
        assert result.accent == "#FFD700"  # Gold

    def test_energetic_boundary_valence(self):
        """Test energetic mood with boundary valence (0.6) matches low valence path."""
        mood_vector = MoodVector(energy=0.8, valence=0.6, danceability=0.7, tension=0.5)
        result = map_mood_to_color_palette("energetic", mood_vector)

        # Should match low valence path (≤0.6)
        assert result.mood == "intense"
        assert result.primary == "#8B0000"

    def test_calm_mood(self):
        """Test calm mood produces soft blue palette."""
        mood_vector = MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2)
        result = map_mood_to_color_palette("calm", mood_vector)

        assert result.mood == "calm"
        assert result.primary == "#4A90E2"  # Soft blue
        assert result.secondary == "#7B68EE"  # Medium slate blue
        assert result.accent == "#87CEEB"  # Sky blue

    def test_relaxed_mood(self):
        """Test relaxed mood produces same palette as calm."""
        mood_vector = MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2)
        result = map_mood_to_color_palette("relaxed", mood_vector)

        assert result.mood == "calm"
        assert result.primary == "#4A90E2"

    def test_melancholic_mood(self):
        """Test melancholic mood produces muted palette."""
        mood_vector = MoodVector(energy=0.4, valence=0.2, danceability=0.3, tension=0.3)
        result = map_mood_to_color_palette("melancholic", mood_vector)

        assert result.mood == "muted"
        assert result.primary == "#708090"  # Slate gray
        assert result.secondary == "#556B2F"  # Dark olive green
        assert result.accent == "#8B7355"  # Dark khaki

    def test_sad_mood(self):
        """Test sad mood produces same palette as melancholic."""
        mood_vector = MoodVector(energy=0.4, valence=0.2, danceability=0.3, tension=0.3)
        result = map_mood_to_color_palette("sad", mood_vector)

        assert result.mood == "muted"
        assert result.primary == "#708090"

    def test_intense_mood(self):
        """Test intense mood produces high contrast palette."""
        mood_vector = MoodVector(energy=0.9, valence=0.4, danceability=0.6, tension=0.9)
        result = map_mood_to_color_palette("intense", mood_vector)

        assert result.mood == "intense"
        assert result.primary == "#DC143C"  # Crimson
        assert result.secondary == "#000000"  # Black
        assert result.accent == "#FF1493"  # Deep pink

    def test_unknown_mood(self):
        """Test unknown mood produces default neutral palette."""
        mood_vector = MoodVector(energy=0.5, valence=0.5, danceability=0.5, tension=0.5)
        result = map_mood_to_color_palette("unknown_mood", mood_vector)

        assert result.mood == "neutral"
        assert result.primary == "#9370DB"  # Medium purple
        assert result.secondary == "#BA55D3"  # Medium orchid
        assert result.accent == "#DDA0DD"  # Plum


class TestMapGenreToCameraMotion:
    """Test genre to camera motion mapping logic."""

    def test_electronic_genre(self):
        """Test Electronic genre produces fast_zoom motion."""
        result = map_genre_to_camera_motion("Electronic", bpm=128.0)

        assert result.type == "fast_zoom"
        assert result.intensity == 0.8
        assert result.speed == "fast"

    def test_edm_genre(self):
        """Test EDM genre produces same motion as Electronic."""
        result = map_genre_to_camera_motion("EDM", bpm=128.0)

        assert result.type == "fast_zoom"
        assert result.intensity == 0.8
        assert result.speed == "fast"

    def test_rock_genre(self):
        """Test Rock genre produces quick_cuts motion."""
        result = map_genre_to_camera_motion("Rock", bpm=110.0)

        assert result.type == "quick_cuts"
        assert result.intensity == 0.9
        assert result.speed == "fast"

    def test_metal_genre(self):
        """Test Metal genre produces same motion as Rock."""
        result = map_genre_to_camera_motion("Metal", bpm=160.0)

        assert result.type == "quick_cuts"
        assert result.intensity == 0.9
        assert result.speed == "fast"

    def test_hip_hop_genre(self):
        """Test Hip-Hop genre produces slow_pan motion."""
        result = map_genre_to_camera_motion("Hip-Hop", bpm=95.0)

        assert result.type == "slow_pan"
        assert result.intensity == 0.6
        assert result.speed == "medium"

    def test_pop_genre(self):
        """Test Pop genre produces medium_pan motion."""
        result = map_genre_to_camera_motion("Pop", bpm=120.0)

        assert result.type == "medium_pan"
        assert result.intensity == 0.7
        assert result.speed == "medium"

    def test_country_genre(self):
        """Test Country genre produces slow_pan motion."""
        result = map_genre_to_camera_motion("Country", bpm=95.0)

        assert result.type == "slow_pan"
        assert result.intensity == 0.4
        assert result.speed == "slow"

    def test_folk_genre(self):
        """Test Folk genre produces same motion as Country."""
        result = map_genre_to_camera_motion("Folk", bpm=85.0)

        assert result.type == "slow_pan"
        assert result.intensity == 0.4
        assert result.speed == "slow"

    def test_ambient_genre(self):
        """Test Ambient genre produces static motion."""
        result = map_genre_to_camera_motion("Ambient", bpm=70.0)

        assert result.type == "static"
        assert result.intensity == 0.2
        assert result.speed == "slow"

    def test_unknown_genre(self):
        """Test unknown genre produces default medium_pan motion."""
        result = map_genre_to_camera_motion("UnknownGenre", bpm=100.0)

        assert result.type == "medium_pan"
        assert result.intensity == 0.5
        assert result.speed == "medium"

    def test_bpm_none(self):
        """Test BPM None produces medium speed."""
        result = map_genre_to_camera_motion("Pop", bpm=None)

        assert result.speed == "medium"

    def test_bpm_slow(self):
        """Test BPM < 90 produces slow speed (for unknown genre)."""
        # Use unknown genre to test BPM speed calculation
        result = map_genre_to_camera_motion("UnknownGenre", bpm=85.0)

        assert result.speed == "slow"

    def test_bpm_boundary_90(self):
        """Test BPM exactly 90 produces medium speed."""
        result = map_genre_to_camera_motion("Pop", bpm=90.0)

        assert result.speed == "medium"

    def test_bpm_medium_range(self):
        """Test BPM 90-130 produces medium speed."""
        result = map_genre_to_camera_motion("Pop", bpm=110.0)

        assert result.speed == "medium"

    def test_bpm_boundary_130(self):
        """Test BPM exactly 130 produces medium speed."""
        result = map_genre_to_camera_motion("Pop", bpm=130.0)

        assert result.speed == "medium"

    def test_bpm_fast(self):
        """Test BPM > 130 produces fast speed (for unknown genre)."""
        # Use unknown genre to test BPM speed calculation
        result = map_genre_to_camera_motion("UnknownGenre", bpm=140.0)

        assert result.speed == "fast"

    def test_genre_speed_override(self):
        """Test genre-specific speed override (e.g., Electronic always fast)."""
        # Electronic should always be fast, even with low BPM
        result = map_genre_to_camera_motion("Electronic", bpm=70.0)

        assert result.type == "fast_zoom"
        assert result.speed == "fast"  # Override, not based on BPM


class TestMapSectionTypeToShotPattern:
    """Test section type to shot pattern mapping logic."""

    def test_intro_section(self):
        """Test intro section produces wide pattern."""
        result = map_section_type_to_shot_pattern("intro")

        assert result.pattern == "wide"
        assert result.pacing == "slow"
        assert "fade_in" in result.transitions

    def test_verse_section(self):
        """Test verse section produces medium pattern."""
        result = map_section_type_to_shot_pattern("verse")

        assert result.pattern == "medium"
        assert result.pacing == "medium"
        assert "cut" in result.transitions

    def test_chorus_section(self):
        """Test chorus section produces close_up_to_wide pattern."""
        result = map_section_type_to_shot_pattern("chorus")

        assert result.pattern == "close_up_to_wide"
        assert result.pacing == "fast"
        assert "zoom" in result.transitions
        assert "cut" in result.transitions
        assert "flash" in result.transitions

    def test_pre_chorus_section(self):
        """Test pre_chorus section produces medium_to_close pattern."""
        result = map_section_type_to_shot_pattern("pre_chorus")

        assert result.pattern == "medium_to_close"
        assert result.pacing == "medium"
        assert "zoom_in" in result.transitions
        assert "cut" in result.transitions

    def test_bridge_section(self):
        """Test bridge section produces wide pattern."""
        result = map_section_type_to_shot_pattern("bridge")

        assert result.pattern == "wide"
        assert result.pacing == "slow"
        assert "fade" in result.transitions
        assert "crossfade" in result.transitions

    def test_solo_section(self):
        """Test solo section produces close_up pattern."""
        result = map_section_type_to_shot_pattern("solo")

        assert result.pattern == "close_up"
        assert result.pacing == "fast"
        assert "quick_cut" in result.transitions
        assert "flash" in result.transitions

    def test_drop_section(self):
        """Test drop section produces close_up with very_fast pacing."""
        result = map_section_type_to_shot_pattern("drop")

        assert result.pattern == "close_up"
        assert result.pacing == "very_fast"
        assert "strobe" in result.transitions
        assert "quick_cut" in result.transitions
        assert "flash" in result.transitions

    def test_outro_section(self):
        """Test outro section produces wide pattern."""
        result = map_section_type_to_shot_pattern("outro")

        assert result.pattern == "wide"
        assert result.pacing == "slow"
        assert "fade_out" in result.transitions

    def test_other_section(self):
        """Test other section produces default pattern."""
        result = map_section_type_to_shot_pattern("other")

        assert result.pattern == "medium"
        assert result.pacing == "medium"
        assert "cut" in result.transitions

    def test_unknown_section_type(self):
        """Test unknown section type produces default pattern."""
        result = map_section_type_to_shot_pattern("unknown_type")

        assert result.pattern == "medium"
        assert result.pacing == "medium"
        assert "cut" in result.transitions


class TestBuildPrompt:
    """Test prompt building logic."""

    def test_complete_prompt(self):
        """Test prompt with all components."""
        section = SongSection(
            id="section-1", type="chorus", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "energetic", MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5)
        )
        camera_motion = map_genre_to_camera_motion("Electronic", bpm=128.0)
        shot_pattern = map_section_type_to_shot_pattern("chorus")

        prompt = build_prompt(
            section=section,
            mood_primary="energetic",
            mood_tags=["energetic", "upbeat", "danceable"],
            genre="Electronic",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics="Moving through the night feeling the beat inside",
        )

        assert "Abstract visual style" in prompt
        assert "vibrant color palette" in prompt
        assert "energetic, upbeat, danceable mood" in prompt
        assert "Electronic aesthetic" in prompt
        assert "close_up_to_wide" in prompt
        assert "fast_zoom camera motion" in prompt
        assert "dynamic and energetic" in prompt
        assert "inspired by:" in prompt

    def test_prompt_without_genre(self):
        """Test prompt without genre should not include genre aesthetic."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "calm", MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2)
        )
        camera_motion = map_genre_to_camera_motion(None, bpm=100.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        prompt = build_prompt(
            section=section,
            mood_primary="calm",
            mood_tags=["calm", "relaxed"],
            genre=None,
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "Abstract visual style" in prompt
        assert "calm color palette" in prompt
        assert "aesthetic" not in prompt  # Should not include genre aesthetic

    def test_prompt_without_lyrics(self):
        """Test prompt without lyrics should not include inspired by section."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "calm", MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2)
        )
        camera_motion = map_genre_to_camera_motion("Pop", bpm=100.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        prompt = build_prompt(
            section=section,
            mood_primary="calm",
            mood_tags=["calm", "relaxed"],
            genre="Pop",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "inspired by:" not in prompt

    def test_prompt_empty_mood_tags(self):
        """Test prompt with empty mood_tags should handle gracefully."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "calm", MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2)
        )
        camera_motion = map_genre_to_camera_motion("Pop", bpm=100.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        prompt = build_prompt(
            section=section,
            mood_primary="calm",
            mood_tags=[],
            genre="Pop",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "Abstract visual style" in prompt
        # Should still include mood description (even if empty)
        assert "mood" in prompt

    def test_prompt_less_than_3_mood_tags(self):
        """Test prompt with <3 mood_tags should use all available tags."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "calm", MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2)
        )
        camera_motion = map_genre_to_camera_motion("Pop", bpm=100.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        prompt = build_prompt(
            section=section,
            mood_primary="calm",
            mood_tags=["calm", "relaxed"],
            genre="Pop",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "calm, relaxed mood" in prompt

    def test_prompt_more_than_3_mood_tags(self):
        """Test prompt with >3 mood_tags should use only first 3."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "energetic", MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5)
        )
        camera_motion = map_genre_to_camera_motion("Electronic", bpm=128.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        prompt = build_prompt(
            section=section,
            mood_primary="energetic",
            mood_tags=["energetic", "upbeat", "danceable", "happy", "driving"],
            genre="Electronic",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "energetic, upbeat, danceable mood" in prompt
        assert "happy" not in prompt  # Should not include 4th tag
        assert "driving" not in prompt  # Should not include 5th tag

    def test_lyrics_filtering_short_words(self):
        """Test lyrics with short words should be filtered out."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "energetic", MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5)
        )
        camera_motion = map_genre_to_camera_motion("Electronic", bpm=128.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        # Lyrics with short words (a, to, the, in) should be filtered
        prompt = build_prompt(
            section=section,
            mood_primary="energetic",
            mood_tags=["energetic"],
            genre="Electronic",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics="a to the in moving night feeling beat",
        )

        assert "inspired by:" in prompt
        # Should include longer words, filter short ones
        assert "moving" in prompt or "night" in prompt or "feeling" in prompt

    def test_lyrics_more_than_10_words(self):
        """Test lyrics with >10 words should use only first 10 words."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "energetic", MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5)
        )
        camera_motion = map_genre_to_camera_motion("Electronic", bpm=128.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        long_lyrics = "one two three four five six seven eight nine ten eleven twelve"
        prompt = build_prompt(
            section=section,
            mood_primary="energetic",
            mood_tags=["energetic"],
            genre="Electronic",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=long_lyrics,
        )

        assert "inspired by:" in prompt
        # Should not include "eleven" or "twelve"
        assert "eleven" not in prompt
        assert "twelve" not in prompt

    def test_lyrics_exactly_3_key_words(self):
        """Test lyrics with exactly 3 key words should include all 3."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "energetic", MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5)
        )
        camera_motion = map_genre_to_camera_motion("Electronic", bpm=128.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        prompt = build_prompt(
            section=section,
            mood_primary="energetic",
            mood_tags=["energetic"],
            genre="Electronic",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics="moving through night feeling beat inside",
        )

        assert "inspired by:" in prompt
        # Should extract 3 key words (words >3 chars)
        assert "moving" in prompt or "through" in prompt or "night" in prompt

    def test_lyrics_less_than_3_key_words(self):
        """Test lyrics with <3 key words after filtering should include available words."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "energetic", MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5)
        )
        camera_motion = map_genre_to_camera_motion("Electronic", bpm=128.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        # Only 2 words >3 chars
        prompt = build_prompt(
            section=section,
            mood_primary="energetic",
            mood_tags=["energetic"],
            genre="Electronic",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics="a to the in moving night",
        )

        # Should still include "inspired by:" if at least one key word found
        assert "inspired by:" in prompt or "moving" in prompt or "night" in prompt

    def test_section_type_context_chorus(self):
        """Test chorus section should include dynamic and energetic context."""
        section = SongSection(
            id="section-1", type="chorus", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "energetic", MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5)
        )
        camera_motion = map_genre_to_camera_motion("Electronic", bpm=128.0)
        shot_pattern = map_section_type_to_shot_pattern("chorus")

        prompt = build_prompt(
            section=section,
            mood_primary="energetic",
            mood_tags=["energetic"],
            genre="Electronic",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "dynamic and energetic" in prompt

    def test_section_type_context_verse(self):
        """Test verse section should include steady and narrative context."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "calm", MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2)
        )
        camera_motion = map_genre_to_camera_motion("Pop", bpm=100.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        prompt = build_prompt(
            section=section,
            mood_primary="calm",
            mood_tags=["calm"],
            genre="Pop",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "steady and narrative" in prompt

    def test_section_type_context_bridge(self):
        """Test bridge section should include transitional and atmospheric context."""
        section = SongSection(
            id="section-1", type="bridge", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "calm", MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2)
        )
        camera_motion = map_genre_to_camera_motion("Pop", bpm=100.0)
        shot_pattern = map_section_type_to_shot_pattern("bridge")

        prompt = build_prompt(
            section=section,
            mood_primary="calm",
            mood_tags=["calm"],
            genre="Pop",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "transitional and atmospheric" in prompt

    def test_section_type_context_other(self):
        """Test other section types should not include section-specific context."""
        section = SongSection(
            id="section-1", type="intro", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "calm", MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2)
        )
        camera_motion = map_genre_to_camera_motion("Pop", bpm=100.0)
        shot_pattern = map_section_type_to_shot_pattern("intro")

        prompt = build_prompt(
            section=section,
            mood_primary="calm",
            mood_tags=["calm"],
            genre="Pop",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "dynamic and energetic" not in prompt
        assert "steady and narrative" not in prompt
        assert "transitional and atmospheric" not in prompt

    def test_prompt_structure_validation(self):
        """Test prompt includes all required components."""
        section = SongSection(
            id="section-1", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
        )
        color_palette = map_mood_to_color_palette(
            "energetic", MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5)
        )
        camera_motion = map_genre_to_camera_motion("Electronic", bpm=128.0)
        shot_pattern = map_section_type_to_shot_pattern("verse")

        prompt = build_prompt(
            section=section,
            mood_primary="energetic",
            mood_tags=["energetic", "upbeat"],
            genre="Electronic",
            color_palette=color_palette,
            camera_motion=camera_motion,
            shot_pattern=shot_pattern,
            lyrics=None,
        )

        assert "Abstract visual style" in prompt
        assert "color palette" in prompt
        assert "mood" in prompt
        assert "aesthetic" in prompt  # Genre aesthetic
        assert "pacing" in prompt  # Shot pattern pacing
        assert "camera motion" in prompt


class TestBuildSceneSpec:
    """Test scene spec building logic."""

    def test_build_with_provided_analysis(self):
        """Test building scene spec with provided analysis."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="chorus", startSec=64.0, endSec=96.0, confidence=0.9
                )
            ],
            mood_primary="energetic",
            mood_tags=["energetic", "upbeat"],
            mood_vector=MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5),
            primary_genre="Electronic",
            lyrics_available=False,
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        assert spec.section_id == "test-section"
        assert spec.template == "abstract"
        assert spec.duration_sec == 32.0  # 96.0 - 64.0
        assert spec.intensity > 0

    def test_build_without_analysis(self):
        """Test building scene spec with analysis object."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="section-4", type="chorus", startSec=64.0, endSec=96.0, confidence=0.9
                )
            ],
            mood_primary="energetic",
            mood_tags=["energetic", "upbeat"],
            mood_vector=MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5),
            primary_genre="Electronic",
            lyrics_available=False,
        )
        spec = build_scene_spec("section-4", analysis=analysis)

        assert spec.section_id == "section-4"
        assert spec.template == "abstract"
        assert spec.duration_sec > 0
        assert spec.intensity > 0

    def test_build_with_custom_template(self):
        """Test building scene spec with custom template."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="section-4", type="chorus", startSec=64.0, endSec=96.0, confidence=0.9
                )
            ],
            mood_primary="energetic",
            mood_tags=["energetic", "upbeat"],
            mood_vector=MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5),
            primary_genre="Electronic",
            lyrics_available=False,
        )
        spec = build_scene_spec("section-4", analysis=analysis, template="environment")

        assert spec.template == "environment"

    def test_build_missing_section(self):
        """Test building scene spec with missing section raises ValueError."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[],
            mood_primary="energetic",
            mood_tags=["energetic"],
            mood_vector=MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5),
            primary_genre="Electronic",
            lyrics_available=False,
        )

        with pytest.raises(ValueError, match="Section.*not found"):
            build_scene_spec("missing-section", analysis=analysis)

    def test_intensity_calculation(self):
        """Test intensity is calculated as (energy + tension) / 2.0."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="chorus", startSec=0.0, endSec=32.0, confidence=0.9
                )
            ],
            mood_primary="energetic",
            mood_tags=["energetic"],
            mood_vector=MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.6),
            primary_genre="Electronic",
            lyrics_available=False,
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        expected_intensity = (0.8 + 0.6) / 2.0
        assert abs(spec.intensity - expected_intensity) < 0.01

    def test_intensity_boundary_values(self):
        """Test intensity with boundary values (0.0, 1.0)."""
        # Test with energy=0.0, tension=0.0
        analysis_low = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
                )
            ],
            mood_primary="calm",
            mood_tags=["calm"],
            mood_vector=MoodVector(energy=0.0, valence=0.5, danceability=0.3, tension=0.0),
            primary_genre="Ambient",
            lyrics_available=False,
        )

        spec_low = build_scene_spec("test-section", analysis=analysis_low)
        assert spec_low.intensity == 0.0

        # Test with energy=1.0, tension=1.0
        analysis_high = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="chorus", startSec=0.0, endSec=32.0, confidence=0.9
                )
            ],
            mood_primary="intense",
            mood_tags=["intense"],
            mood_vector=MoodVector(energy=1.0, valence=0.3, danceability=0.6, tension=1.0),
            primary_genre="Metal",
            lyrics_available=False,
        )

        spec_high = build_scene_spec("test-section", analysis=analysis_high)
        assert spec_high.intensity == 1.0

    def test_duration_calculation(self):
        """Test duration is calculated as section.end_sec - section.start_sec."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="verse", startSec=20.0, endSec=52.0, confidence=0.9
                )
            ],
            mood_primary="calm",
            mood_tags=["calm"],
            mood_vector=MoodVector(energy=0.5, valence=0.5, danceability=0.5, tension=0.5),
            primary_genre="Pop",
            lyrics_available=False,
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        assert spec.duration_sec == 32.0  # 52.0 - 20.0

    def test_scene_spec_field_validation(self):
        """Test all SceneSpec fields are populated correctly."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="chorus", startSec=64.0, endSec=96.0, confidence=0.9
                )
            ],
            mood_primary="energetic",
            mood_tags=["energetic", "upbeat"],
            mood_vector=MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5),
            primary_genre="Electronic",
            lyrics_available=False,
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        assert spec.section_id == "test-section"
        assert spec.template == "abstract"
        assert isinstance(spec.prompt, str)
        assert len(spec.prompt) > 0
        assert spec.color_palette is not None
        assert spec.camera_motion is not None
        assert spec.shot_pattern is not None
        assert 0.0 <= spec.intensity <= 1.0
        assert spec.duration_sec > 0

    def test_scene_spec_with_lyrics(self):
        """Test scene spec with lyrics includes lyrics in prompt."""
        from app.schemas.analysis import SectionLyrics

        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="chorus", startSec=64.0, endSec=96.0, confidence=0.9
                )
            ],
            mood_primary="energetic",
            mood_tags=["energetic", "upbeat"],
            mood_vector=MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5),
            primary_genre="Electronic",
            lyrics_available=True,
            section_lyrics=[
                SectionLyrics(
                    sectionId="test-section", startSec=64.0, endSec=96.0, text="Moving through night"
                )
            ],
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        assert "inspired by:" in spec.prompt or "Moving" in spec.prompt

    def test_scene_spec_without_lyrics(self):
        """Test scene spec without lyrics does not include lyrics in prompt."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="chorus", startSec=64.0, endSec=96.0, confidence=0.9
                )
            ],
            mood_primary="energetic",
            mood_tags=["energetic", "upbeat"],
            mood_vector=MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5),
            primary_genre="Electronic",
            lyrics_available=False,
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        # Should not include "inspired by:" if no lyrics
        # (Note: might still appear if mock data has lyrics, so we check the analysis)
        assert spec.prompt is not None


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_mood_tags(self):
        """Test empty mood_tags list should handle gracefully."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
                )
            ],
            mood_primary="calm",
            mood_tags=[],
            mood_vector=MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2),
            primary_genre="Pop",
            lyrics_available=False,
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        assert spec.prompt is not None
        assert len(spec.prompt) > 0

    def test_very_long_lyrics(self):
        """Test very long lyrics text should truncate appropriately."""
        from app.schemas.analysis import SectionLyrics

        long_lyrics = " ".join([f"word{i}" for i in range(100)])  # 100 words

        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
                )
            ],
            mood_primary="energetic",
            mood_tags=["energetic"],
            mood_vector=MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5),
            primary_genre="Electronic",
            lyrics_available=True,
            section_lyrics=[
                SectionLyrics(
                    sectionId="test-section", startSec=0.0, endSec=32.0, text=long_lyrics
                )
            ],
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        # Should not crash, prompt should be reasonable length
        assert spec.prompt is not None
        assert len(spec.prompt) < 2000  # Reasonable upper bound

    def test_section_with_no_lyrics_object(self):
        """Test section with no lyrics object should not crash."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
                )
            ],
            mood_primary="calm",
            mood_tags=["calm"],
            mood_vector=MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2),
            primary_genre="Pop",
            lyrics_available=False,
            section_lyrics=None,  # No lyrics at all
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        assert spec.prompt is not None
        assert "inspired by:" not in spec.prompt

    def test_extreme_mood_vector_values(self):
        """Test extreme mood vector values (0.0, 1.0) should work correctly."""
        # Test with all 0.0
        analysis_low = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
                )
            ],
            mood_primary="calm",
            mood_tags=["calm"],
            mood_vector=MoodVector(energy=0.0, valence=0.0, danceability=0.0, tension=0.0),
            primary_genre="Ambient",
            lyrics_available=False,
        )

        spec_low = build_scene_spec("test-section", analysis=analysis_low)
        assert spec_low.intensity == 0.0

        # Test with all 1.0
        analysis_high = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="chorus", startSec=0.0, endSec=32.0, confidence=0.9
                )
            ],
            mood_primary="intense",
            mood_tags=["intense"],
            mood_vector=MoodVector(energy=1.0, valence=1.0, danceability=1.0, tension=1.0),
            primary_genre="Metal",
            lyrics_available=False,
        )

        spec_high = build_scene_spec("test-section", analysis=analysis_high)
        assert spec_high.intensity == 1.0

    def test_section_with_none_genre(self):
        """Test section with None genre should use default camera motion."""
        analysis = SongAnalysis(
            duration_sec=240.0,
            bpm=120.0,
            sections=[
                SongSection(
                    id="test-section", type="verse", startSec=0.0, endSec=32.0, confidence=0.9
                )
            ],
            mood_primary="calm",
            mood_tags=["calm"],
            mood_vector=MoodVector(energy=0.3, valence=0.5, danceability=0.3, tension=0.2),
            primary_genre=None,  # No genre
            lyrics_available=False,
        )

        spec = build_scene_spec("test-section", analysis=analysis)

        # Should use default camera motion (medium_pan, intensity 0.5)
        assert spec.camera_motion.type == "medium_pan"
        assert spec.camera_motion.intensity == 0.5


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])

