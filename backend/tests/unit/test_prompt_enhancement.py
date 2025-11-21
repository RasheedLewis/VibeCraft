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
    enhance_prompt_with_rhythm,
    get_motion_descriptor,
    get_motion_type_from_genre,
    get_tempo_classification,
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
        """Test dance genre maps to bouncing."""
        assert get_motion_type_from_genre("dance") == "bouncing"
        assert get_motion_type_from_genre("Dance Music") == "bouncing"

    def test_rock_genre(self):
        """Test rock genre maps to stepping."""
        assert get_motion_type_from_genre("rock") == "stepping"
        assert get_motion_type_from_genre("Rock") == "stepping"

    def test_jazz_genre(self):
        """Test jazz genre maps to looping."""
        assert get_motion_type_from_genre("jazz") == "looping"
        assert get_motion_type_from_genre("Jazz") == "looping"

    def test_hip_hop_genre(self):
        """Test hip-hop genre maps to bouncing."""
        assert get_motion_type_from_genre("hip-hop") == "bouncing"
        assert get_motion_type_from_genre("Hip-Hop") == "bouncing"

    def test_pop_genre(self):
        """Test pop genre maps to bouncing."""
        assert get_motion_type_from_genre("pop") == "bouncing"
        assert get_motion_type_from_genre("Pop") == "bouncing"

    def test_unknown_genre_defaults_to_bouncing(self):
        """Test that unknown genre defaults to bouncing."""
        assert get_motion_type_from_genre("unknown") == "bouncing"
        assert get_motion_type_from_genre("classical") == "bouncing"
        assert get_motion_type_from_genre(None) == "bouncing"

    def test_genre_substring_matching(self):
        """Test that genre matching works with substrings."""
        assert get_motion_type_from_genre("electronic dance music") == "pulsing"
        assert get_motion_type_from_genre("rock and roll") == "stepping"

