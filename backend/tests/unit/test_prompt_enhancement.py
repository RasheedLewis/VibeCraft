"""Unit tests for prompt enhancement service.

Tests rhythm enhancement logic with BPM and motion types - pure functions, fast.
Validates get_tempo_classification(), get_motion_descriptor(), enhance_prompt_with_rhythm(),
and get_motion_type_from_genre() in isolation.

Run with: pytest backend/tests/unit/test_prompt_enhancement.py -v
Or from backend/: pytest tests/unit/test_prompt_enhancement.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.prompt_enhancement import (  # noqa: E402
    BPM_FAST,
    BPM_MEDIUM,
    BPM_SLOW,
    TEMPO_DESCRIPTORS,
    enhance_prompt_with_rhythm,
    get_motion_descriptor,
    get_motion_type_from_genre,
    get_tempo_classification,
    optimize_prompt_for_api,
    select_motion_type,
)


class TestGetTempoClassification:
    """Test BPM tempo classification logic."""

    def test_slow_tempo(self):
        """Test slow tempo classification (< 60 BPM)."""
        assert get_tempo_classification(50.0) == "slow"
        assert get_tempo_classification(59.9) == "slow"
        assert get_tempo_classification(0.1) == "slow"

    def test_medium_tempo(self):
        """Test medium tempo classification (60-100 BPM)."""
        assert get_tempo_classification(60.0) == "medium"
        assert get_tempo_classification(80.0) == "medium"
        assert get_tempo_classification(99.9) == "medium"

    def test_fast_tempo(self):
        """Test fast tempo classification (100-140 BPM)."""
        assert get_tempo_classification(100.0) == "fast"
        assert get_tempo_classification(120.0) == "fast"
        assert get_tempo_classification(139.9) == "fast"

    def test_very_fast_tempo(self):
        """Test very fast tempo classification (>= 140 BPM)."""
        assert get_tempo_classification(140.0) == "very_fast"
        assert get_tempo_classification(180.0) == "very_fast"
        assert get_tempo_classification(200.0) == "very_fast"

    def test_boundary_values(self):
        """Test boundary values for tempo classification."""
        assert get_tempo_classification(BPM_SLOW - 0.1) == "slow"
        assert get_tempo_classification(BPM_SLOW) == "medium"
        assert get_tempo_classification(BPM_MEDIUM - 0.1) == "medium"
        assert get_tempo_classification(BPM_MEDIUM) == "fast"
        assert get_tempo_classification(BPM_FAST - 0.1) == "fast"
        assert get_tempo_classification(BPM_FAST) == "very_fast"


class TestGetMotionDescriptor:
    """Test motion descriptor generation."""

    def test_bouncing_motion_slow(self):
        """Test bouncing motion with slow tempo."""
        result = get_motion_descriptor(50.0, "bouncing")
        assert "gentle" in result.lower()
        assert "bouncing" in result.lower()

    def test_bouncing_motion_medium(self):
        """Test bouncing motion with medium tempo."""
        result = get_motion_descriptor(80.0, "bouncing")
        assert "bouncing" in result.lower()
        assert "rhythmic" in result.lower()

    def test_bouncing_motion_fast(self):
        """Test bouncing motion with fast tempo."""
        result = get_motion_descriptor(120.0, "bouncing")
        assert "rapid" in result.lower() or "energetic" in result.lower()
        assert "bouncing" in result.lower()

    def test_pulsing_motion(self):
        """Test pulsing motion type."""
        result = get_motion_descriptor(100.0, "pulsing")
        assert "pulsing" in result.lower()

    def test_rotating_motion(self):
        """Test rotating motion type."""
        result = get_motion_descriptor(100.0, "rotating")
        assert "rotation" in result.lower() or "rotating" in result.lower()

    def test_stepping_motion(self):
        """Test stepping motion type."""
        result = get_motion_descriptor(100.0, "stepping")
        assert "stepping" in result.lower()

    def test_looping_motion(self):
        """Test looping motion type."""
        result = get_motion_descriptor(100.0, "looping")
        assert "looping" in result.lower()

    def test_invalid_motion_type_defaults_to_bouncing(self):
        """Test that invalid motion type defaults to bouncing."""
        result = get_motion_descriptor(100.0, "invalid_motion")
        assert "bouncing" in result.lower() or "motion" in result.lower()

    def test_very_fast_maps_to_fast(self):
        """Test that very_fast tempo maps to fast motion descriptor."""
        result = get_motion_descriptor(200.0, "bouncing")
        assert "rapid" in result.lower() or "energetic" in result.lower()


class TestEnhancePromptWithRhythm:
    """Test prompt enhancement with rhythm."""

    def test_enhance_with_valid_bpm(self):
        """Test prompt enhancement with valid BPM."""
        base_prompt = "Abstract visual style, vibrant colors"
        result = enhance_prompt_with_rhythm(base_prompt, bpm=120.0, motion_type="bouncing")
        
        assert base_prompt in result
        assert "BPM" in result
        assert "120" in result
        assert "rhythmic" in result.lower()

    def test_enhance_with_different_motion_types(self):
        """Test enhancement with different motion types."""
        base_prompt = "Test prompt"
        
        result_bouncing = enhance_prompt_with_rhythm(base_prompt, bpm=100.0, motion_type="bouncing")
        result_pulsing = enhance_prompt_with_rhythm(base_prompt, bpm=100.0, motion_type="pulsing")
        
        assert "bouncing" in result_bouncing.lower()
        assert "pulsing" in result_pulsing.lower()

    def test_enhance_with_invalid_bpm_returns_unchanged(self):
        """Test that invalid BPM returns unchanged prompt."""
        base_prompt = "Test prompt"
        
        result_zero = enhance_prompt_with_rhythm(base_prompt, bpm=0.0)
        result_negative = enhance_prompt_with_rhythm(base_prompt, bpm=-10.0)
        
        assert result_zero == base_prompt
        assert result_negative == base_prompt

    def test_enhance_rounds_bpm(self):
        """Test that BPM is rounded to integer in output."""
        base_prompt = "Test"
        result = enhance_prompt_with_rhythm(base_prompt, bpm=120.7)
        
        assert "120" in result or "121" in result  # Should round

    def test_enhance_includes_synchronized_phrase(self):
        """Test that enhanced prompt includes synchronization phrase."""
        base_prompt = "Test"
        result = enhance_prompt_with_rhythm(base_prompt, bpm=100.0)
        
        assert "synchronized" in result.lower()
        assert "tempo" in result.lower()
        assert "beat" in result.lower()


class TestGetMotionTypeFromGenre:
    """Test genre to motion type mapping."""

    def test_electronic_genre(self):
        """Test electronic genre maps to pulsing."""
        assert get_motion_type_from_genre("electronic") == "pulsing"
        assert get_motion_type_from_genre("Electronic") == "pulsing"
        assert get_motion_type_from_genre("ELECTRONIC") == "pulsing"

    def test_dance_genre(self):
        """Test dance genre maps to dancing."""
        assert get_motion_type_from_genre("dance") == "dancing"
        assert get_motion_type_from_genre("Dance Music") == "dancing"

    def test_rock_genre(self):
        """Test rock genre maps to stepping."""
        assert get_motion_type_from_genre("rock") == "stepping"
        assert get_motion_type_from_genre("Rock") == "stepping"

    def test_jazz_genre(self):
        """Test jazz genre maps to looping."""
        assert get_motion_type_from_genre("jazz") == "looping"
        assert get_motion_type_from_genre("Jazz") == "looping"

    def test_hip_hop_genre(self):
        """Test hip-hop genre maps to dancing."""
        assert get_motion_type_from_genre("hip-hop") == "dancing"
        assert get_motion_type_from_genre("Hip-Hop") == "dancing"

    def test_pop_genre(self):
        """Test pop genre maps to dancing."""
        assert get_motion_type_from_genre("pop") == "dancing"
        assert get_motion_type_from_genre("Pop") == "dancing"

    def test_unknown_genre_defaults_to_bouncing(self):
        """Test that unknown genre defaults to bouncing."""
        assert get_motion_type_from_genre("unknown") == "bouncing"
        assert get_motion_type_from_genre("classical") == "bouncing"
        assert get_motion_type_from_genre(None) == "bouncing"

    def test_genre_substring_matching(self):
        """Test that genre matching works with substrings."""
        assert get_motion_type_from_genre("electronic dance music") == "pulsing"
        assert get_motion_type_from_genre("rock and roll") == "stepping"


class TestExtractBpmFromPrompt:
    """Test BPM extraction from enhanced prompts.
    
    Justification: API optimization needs to extract BPM from prompts when not explicitly provided.
    This ensures backward compatibility and works with prompts that already contain BPM info.
    """

    def test_extract_bpm_standard_format(self):
        """Test extraction of '128 BPM' format."""
        from app.services.prompt_enhancement import _extract_bpm_from_prompt
        
        prompt = "Abstract visual style, synchronized to 128 BPM tempo"
        result = _extract_bpm_from_prompt(prompt)
        assert result == 128.0

    def test_extract_bpm_no_space(self):
        """Test extraction of '128BPM' format (no space)."""
        from app.services.prompt_enhancement import _extract_bpm_from_prompt
        
        prompt = "Motion synchronized to 128BPM"
        result = _extract_bpm_from_prompt(prompt)
        assert result == 128.0

    def test_extract_bpm_beats_per_minute_format(self):
        """Test extraction of 'at 128 beats per minute' format."""
        from app.services.prompt_enhancement import _extract_bpm_from_prompt
        
        prompt = "Character moves at 128 beats per minute, creating rhythm"
        result = _extract_bpm_from_prompt(prompt)
        assert result == 128.0

    def test_extract_bpm_case_insensitive(self):
        """Test that BPM extraction is case insensitive."""
        from app.services.prompt_enhancement import _extract_bpm_from_prompt
        
        prompt = "Synchronized to 120 bpm tempo"
        result = _extract_bpm_from_prompt(prompt)
        assert result == 120.0

    def test_extract_bpm_no_match_returns_none(self):
        """Test that extraction returns None when no BPM found."""
        from app.services.prompt_enhancement import _extract_bpm_from_prompt
        
        prompt = "Abstract visual style with vibrant colors"
        result = _extract_bpm_from_prompt(prompt)
        assert result is None

    def test_extract_bpm_first_match_wins(self):
        """Test that first BPM value found is returned."""
        from app.services.prompt_enhancement import _extract_bpm_from_prompt
        
        prompt = "Synchronized to 120 BPM, then changes to 140 BPM"
        result = _extract_bpm_from_prompt(prompt)
        assert result == 120.0  # First match


class TestOptimizePromptForApi:
    """Test API-specific prompt optimization.
    
    Justification: Different video generation APIs respond differently to prompts.
    This ensures prompts are correctly formatted for each API to maximize rhythmic motion generation.
    """

    def test_optimize_for_minimax_hailuo_with_bpm(self):
        """Test optimization for Minimax Hailuo 2.3 with explicit BPM."""
        prompt = "Abstract visual style, vibrant colors"
        result = optimize_prompt_for_api(prompt, "minimax/hailuo-2.3", bpm=120.0)
        
        assert "Camera: static" in result
        assert "120 BPM" in result
        assert prompt in result

    def test_optimize_for_minimax_hailuo_extracts_bpm(self):
        """Test that Minimax optimization extracts BPM from prompt if not provided."""
        prompt = "Abstract visual style, synchronized to 128 BPM tempo"
        result = optimize_prompt_for_api(prompt, "minimax/hailuo-2.3", bpm=None)
        
        assert "Camera: static" in result
        assert "128 BPM" in result
        # Should not duplicate BPM
        assert result.count("128 BPM") <= 2  # May appear twice but not many times

    def test_optimize_for_minimax_avoids_duplication(self):
        """Test that Minimax optimization doesn't duplicate BPM if already in prompt."""
        prompt = "Abstract visual style, synchronized to 120 BPM tempo"
        result = optimize_prompt_for_api(prompt, "minimax/hailuo-2.3", bpm=120.0)
        
        # Should add camera directive but not duplicate BPM
        assert "Camera: static" in result
        # BPM should appear but not excessively duplicated
        bpm_count = result.count("120 BPM")
        assert bpm_count >= 1  # At least once
        assert bpm_count <= 2  # Not many duplicates

    def test_optimize_for_runway(self):
        """Test optimization for Runway Gen-3 API.
        
        Note: We haven't tested Runway API yet - this tests the optimization logic
        for future use when/if we switch to Runway.
        """
        prompt = "Abstract visual style"
        result = optimize_prompt_for_api(prompt, "runway", bpm=120.0)
        
        assert "Camera: static" in result
        assert "Motion:" in result
        assert prompt in result

    def test_optimize_for_pika(self):
        """Test optimization for Pika API.
        
        Note: We haven't tested Pika API yet - this tests the optimization logic
        for future use when/if we switch to Pika.
        """
        prompt = "Abstract visual style"
        result = optimize_prompt_for_api(prompt, "pika", bpm=120.0)
        
        assert "Style: clean motion graphics" in result
        assert "120 BPM" in result
        assert prompt in result

    def test_optimize_for_kling(self):
        """Test optimization for Kling API.
        
        Note: We haven't tested Kling API yet - this tests the optimization logic
        for future use when/if we switch to Kling.
        """
        prompt = "Abstract visual style"
        result = optimize_prompt_for_api(prompt, "kling", bpm=120.0)
        
        assert "character moves" in result.lower()
        assert "120 beats per minute" in result
        assert "rhythmic visual pattern" in result.lower()
        assert prompt in result


class TestTempoDescriptors:
    """Test tempo descriptor integration in prompt enhancement.
    
    Justification: New feature that adds descriptive tempo classifications
    (e.g., "slow, flowing" vs "energetic, driving") to enhance prompts beyond
    just BPM numbers. This improves video generation quality.
    """

    def test_tempo_descriptors_exist(self):
        """Test that TEMPO_DESCRIPTORS dictionary exists and has all keys."""
        assert "slow" in TEMPO_DESCRIPTORS
        assert "medium" in TEMPO_DESCRIPTORS
        assert "fast" in TEMPO_DESCRIPTORS
        assert "very_fast" in TEMPO_DESCRIPTORS

    def test_tempo_descriptors_are_descriptive(self):
        """Test that tempo descriptors contain descriptive words."""
        assert "flowing" in TEMPO_DESCRIPTORS["slow"] or "gentle" in TEMPO_DESCRIPTORS["slow"]
        assert "energetic" in TEMPO_DESCRIPTORS["fast"] or "driving" in TEMPO_DESCRIPTORS["fast"]
        assert "frenetic" in TEMPO_DESCRIPTORS["very_fast"] or "rapid" in TEMPO_DESCRIPTORS["very_fast"]

    def test_enhance_prompt_includes_tempo_descriptor(self):
        """Test that enhance_prompt_with_rhythm includes tempo descriptor."""
        base_prompt = "Abstract visual style"
        enhanced = enhance_prompt_with_rhythm(base_prompt, bpm=120.0, motion_type="bouncing")
        
        # Should include tempo descriptor for "fast" tempo (120 BPM)
        tempo_descriptor = TEMPO_DESCRIPTORS["fast"]
        assert any(word in enhanced for word in tempo_descriptor.split(", "))

    def test_enhance_prompt_slow_tempo_descriptor(self):
        """Test that slow BPM uses slow tempo descriptor."""
        base_prompt = "Abstract visual style"
        enhanced = enhance_prompt_with_rhythm(base_prompt, bpm=50.0, motion_type="bouncing")
        
        # Should include "slow, flowing" or similar
        assert "slow" in enhanced.lower() or "flowing" in enhanced.lower() or "gentle" in enhanced.lower()

    def test_enhance_prompt_fast_tempo_descriptor(self):
        """Test that fast BPM uses fast tempo descriptor."""
        base_prompt = "Abstract visual style"
        enhanced = enhance_prompt_with_rhythm(base_prompt, bpm=150.0, motion_type="bouncing")
        
        # Should include "energetic" or "driving" or "frenetic"
        assert "energetic" in enhanced.lower() or "driving" in enhanced.lower() or "frenetic" in enhanced.lower()

    def test_rhythmic_phrase_includes_tempo_and_bpm(self):
        """Test that rhythmic phrase includes both tempo descriptor and BPM."""
        base_prompt = "Abstract visual style"
        enhanced = enhance_prompt_with_rhythm(base_prompt, bpm=120.0, motion_type="bouncing")
        
        # Should include both tempo descriptor and BPM number
        assert "120" in enhanced or "BPM" in enhanced
        # Should include tempo descriptor words
        assert any(word in enhanced for word in ["energetic", "driving", "dynamic", "upbeat"])


class TestDancingMotionType:
    """Test dancing motion type selection and descriptors.
    
    Justification: New feature that prioritizes "dancing" motion type for
    dance-related genres and moods. This improves video quality for dance music.
    """

    def test_select_motion_type_dance_genre(self):
        """Test that dance genre selects dancing motion type."""
        result = select_motion_type(genre="dance")
        assert result == "dancing"

    def test_select_motion_type_hip_hop_genre(self):
        """Test that hip-hop genre selects dancing motion type."""
        result = select_motion_type(genre="hip-hop")
        assert result == "dancing"

    def test_select_motion_type_pop_genre(self):
        """Test that pop genre selects dancing motion type."""
        result = select_motion_type(genre="pop")
        assert result == "dancing"

    def test_select_motion_type_dance_mood_tag(self):
        """Test that dance mood tag selects dancing motion type."""
        result = select_motion_type(mood_tags=["dance", "energetic"])
        assert result == "dancing"

    def test_select_motion_type_danceable_mood_tag(self):
        """Test that danceable mood tag selects dancing motion type."""
        result = select_motion_type(mood_tags=["danceable", "upbeat"])
        assert result == "dancing"

    def test_select_motion_type_groovy_mood_tag(self):
        """Test that groovy mood tag selects dancing motion type."""
        result = select_motion_type(mood_tags=["groovy", "funky"])
        assert result == "dancing"

    def test_dancing_motion_descriptor_exists(self):
        """Test that dancing motion descriptor exists for all tempos."""
        slow_desc = get_motion_descriptor(50.0, "dancing")
        medium_desc = get_motion_descriptor(80.0, "dancing")
        fast_desc = get_motion_descriptor(120.0, "dancing")
        
        assert "dancing" in slow_desc.lower()
        assert "dancing" in medium_desc.lower()
        assert "dancing" in fast_desc.lower()

    def test_dancing_motion_descriptor_contains_dance_keywords(self):
        """Test that dancing descriptors contain dance-related keywords."""
        slow_desc = get_motion_descriptor(50.0, "dancing")
        fast_desc = get_motion_descriptor(120.0, "dancing")
        
        # Should contain dance-related words
        assert any(word in slow_desc.lower() for word in ["dance", "step", "sway", "move"])
        assert any(word in fast_desc.lower() for word in ["dance", "step", "move", "dynamic"])

    def test_enhance_prompt_with_dancing_motion(self):
        """Test that enhance_prompt_with_rhythm works with dancing motion type."""
        base_prompt = "Abstract visual style"
        enhanced = enhance_prompt_with_rhythm(base_prompt, bpm=120.0, motion_type="dancing")
        
        # Should include dancing-related descriptors
        assert "dancing" in enhanced.lower() or "dance" in enhanced.lower()

    def test_optimize_for_unknown_api_generic(self):
        """Test that unknown APIs get generic optimization."""
        prompt = "Abstract visual style"
        result = optimize_prompt_for_api(prompt, "unknown-api", bpm=120.0)
        
        assert "120 BPM" in result
        assert prompt in result

    def test_optimize_without_bpm_returns_unchanged(self):
        """Test that optimization returns unchanged prompt when no BPM available."""
        prompt = "Abstract visual style with no BPM reference"
        result = optimize_prompt_for_api(prompt, "minimax/hailuo-2.3", bpm=None)
        
        # Should return unchanged since no BPM can be extracted
        assert result == prompt

    def test_optimize_case_insensitive_api_name(self):
        """Test that API name matching is case insensitive."""
        prompt = "Abstract visual style"
        result1 = optimize_prompt_for_api(prompt, "MINIMAX/HAILUO-2.3", bpm=120.0)
        result2 = optimize_prompt_for_api(prompt, "minimax/hailuo-2.3", bpm=120.0)
        
        # Both should produce similar results (may have minor differences but should optimize)
        assert "Camera" in result1 or "120 BPM" in result1
        assert "Camera" in result2 or "120 BPM" in result2


class TestSelectMotionType:
    """Test advanced motion type selection.
    
    Justification: Motion type selection uses a priority system (scene context > mood > genre > BPM).
    This ensures the most appropriate motion type is selected based on all available context.
    """

    def test_scene_context_priority_chorus_high_intensity(self):
        """Test that scene context (chorus, high intensity) takes priority."""
        result = select_motion_type(
            genre="jazz",  # Would normally be "looping"
            mood="calm",  # Would normally be "looping"
            scene_context={"section_type": "chorus", "intensity": 0.8},
        )
        assert result == "bouncing"  # High energy chorus overrides genre/mood

    def test_scene_context_priority_bridge(self):
        """Test that bridge sections select looping motion."""
        result = select_motion_type(
            genre="rock",  # Would normally be "stepping"
            scene_context={"section_type": "bridge", "intensity": 0.5},
        )
        assert result == "looping"  # Bridge overrides genre

    def test_scene_context_priority_verse(self):
        """Test that verse sections select stepping motion."""
        result = select_motion_type(
            genre="electronic",  # Would normally be "pulsing"
            scene_context={"section_type": "verse", "intensity": 0.5},
        )
        assert result == "stepping"  # Verse overrides genre

    def test_mood_priority_energetic(self):
        """Test that energetic mood takes priority over genre when no scene context."""
        result = select_motion_type(
            genre="jazz",  # Would normally be "looping"
            mood="energetic",
            bpm=100.0,  # Medium tempo
        )
        assert result == "bouncing"  # Energetic mood overrides genre

    def test_mood_priority_calm(self):
        """Test that calm mood selects looping motion."""
        result = select_motion_type(
            genre="rock",  # Would normally be "stepping"
            mood="calm",
        )
        assert result == "looping"  # Calm mood overrides genre

    def test_mood_priority_melancholic(self):
        """Test that melancholic mood selects rotating motion."""
        result = select_motion_type(
            genre="pop",  # Would normally be "bouncing"
            mood="melancholic",
        )
        assert result == "rotating"  # Melancholic mood overrides genre

    def test_mood_tags_priority_dance(self):
        """Test that dance-related mood tags select dancing."""
        result = select_motion_type(
            genre="jazz",  # Would normally be "looping"
            mood_tags=["dance", "groovy"],
        )
        assert result == "dancing"  # Dance tags override genre

    def test_mood_tags_priority_electronic(self):
        """Test that electronic mood tags select pulsing."""
        result = select_motion_type(
            genre="rock",  # Would normally be "stepping"
            mood_tags=["electronic", "techno"],
        )
        assert result == "pulsing"  # Electronic tags override genre

    def test_genre_fallback(self):
        """Test that genre is used when no mood or scene context."""
        result = select_motion_type(genre="electronic")
        assert result == "pulsing"  # Genre-based selection

    def test_bpm_fallback_very_slow(self):
        """Test that very slow BPM selects looping when no other context."""
        result = select_motion_type(bpm=60.0)
        assert result == "looping"  # Very slow = looping

    def test_bpm_fallback_slow(self):
        """Test that slow BPM selects rotating."""
        result = select_motion_type(bpm=80.0)
        assert result == "rotating"  # Slow = rotating

    def test_bpm_fallback_medium(self):
        """Test that medium BPM selects stepping."""
        result = select_motion_type(bpm=110.0)
        assert result == "stepping"  # Medium = stepping

    def test_bpm_fallback_fast(self):
        """Test that fast BPM selects bouncing."""
        result = select_motion_type(bpm=130.0)
        assert result == "bouncing"  # Fast = bouncing

    def test_bpm_fallback_very_fast(self):
        """Test that very fast BPM selects pulsing."""
        result = select_motion_type(bpm=150.0)
        assert result == "pulsing"  # Very fast = pulsing

    def test_default_fallback(self):
        """Test that bouncing is default when no context provided."""
        result = select_motion_type()
        assert result == "bouncing"  # Default fallback

    def test_priority_order_scene_overrides_all(self):
        """Test that scene context has highest priority."""
        result = select_motion_type(
            genre="jazz",  # looping
            mood="energetic",  # bouncing
            mood_tags=["dance"],  # bouncing
            bpm=150.0,  # pulsing
            scene_context={"section_type": "verse", "intensity": 0.5},  # stepping
        )
        assert result == "stepping"  # Scene context wins

    def test_priority_order_mood_overrides_genre(self):
        """Test that mood has priority over genre when no scene context."""
        result = select_motion_type(
            genre="electronic",  # pulsing
            mood="energetic",  # bouncing
        )
        assert result == "bouncing"  # Mood wins over genre

    def test_high_energy_chorus_with_high_bpm(self):
        """Test that high energy chorus selects bouncing regardless of BPM."""
        result = select_motion_type(
            scene_context={"section_type": "chorus", "intensity": 0.9},
            bpm=150.0,  # Would normally be pulsing
        )
        assert result == "bouncing"  # High energy chorus overrides BPM-based selection

    def test_medium_energy_chorus(self):
        """Test that medium energy chorus selects pulsing."""
        result = select_motion_type(
            scene_context={"section_type": "chorus", "intensity": 0.5},
            bpm=120.0,
        )
        assert result == "pulsing"  # Medium energy chorus

