"""Unit tests for genre and mood analysis service.

Tests logic with mocked MoodVector objects - no audio files needed, fast (~0.1s).
17 pytest cases covering edge cases and rule-based classification.
Validates compute_mood_tags() and compute_genre() in isolation.

Complementary to test_genre_mood.py: This verifies rules/logic work correctly;
test_genre_mood.py verifies the full pipeline works with real audio files.

Run with: pytest tests/test_genre_mood_analysis.py -v
Or from backend/: pytest tests/test_genre_mood_analysis.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from app.schemas.analysis import MoodVector  # noqa: E402
from app.services.genre_mood_analysis import compute_genre, compute_mood_tags  # noqa: E402


class TestComputeMoodTags:
    """Test mood tag computation logic."""

    def test_energetic_upbeat_mood(self):
        """Test high energy and high valence produces energetic/upbeat tags."""
        mood = MoodVector(energy=0.8, valence=0.8, danceability=0.7, tension=0.5)
        primary, tags = compute_mood_tags(mood)

        assert primary == "energetic"
        assert "energetic" in tags
        assert "upbeat" in tags
        assert "happy" in tags

    def test_calm_relaxed_mood(self):
        """Test low energy and low tension produces calm/relaxed tags."""
        mood = MoodVector(energy=0.2, valence=0.5, danceability=0.2, tension=0.2)
        primary, tags = compute_mood_tags(mood)

        assert primary == "calm"
        assert "calm" in tags
        assert "relaxed" in tags
        assert "ambient" in tags  # danceability < 0.3 triggers ambient tag

    def test_melancholic_mood(self):
        """Test low valence produces melancholic/sad tags."""
        mood = MoodVector(energy=0.5, valence=0.2, danceability=0.4, tension=0.3)
        primary, tags = compute_mood_tags(mood)

        assert primary == "melancholic"
        assert "melancholic" in tags
        assert "sad" in tags

    def test_intense_mood(self):
        """Test high tension produces intense tag."""
        mood = MoodVector(energy=0.6, valence=0.5, danceability=0.5, tension=0.8)
        primary, tags = compute_mood_tags(mood)

        assert primary == "intense"
        assert "intense" in tags

    def test_danceable_mood(self):
        """Test high danceability produces danceable tag."""
        mood = MoodVector(energy=0.6, valence=0.6, danceability=0.8, tension=0.4)
        primary, tags = compute_mood_tags(mood)

        assert "danceable" in tags

    def test_neutral_mood(self):
        """Test middle values produce neutral mood."""
        mood = MoodVector(energy=0.5, valence=0.5, danceability=0.5, tension=0.5)
        primary, tags = compute_mood_tags(mood)

        # Should have a primary mood (even if neutral)
        assert primary is not None
        assert isinstance(primary, str)


class TestComputeGenre:
    """Test genre classification logic."""

    def test_electronic_genre_high_bpm_high_energy(self):
        """Test electronic genre detection for high BPM, high energy tracks."""
        mood = MoodVector(energy=0.8, valence=0.6, danceability=0.8, tension=0.5)
        genre, sub_genres, confidence = compute_genre(
            "fake_path.mp3", bpm=130.0, mood_vector=mood
        )

        assert genre == "Electronic"
        assert confidence >= 0.6

    def test_pop_genre_moderate_bpm_high_valence(self):
        """Test pop genre detection for moderate BPM, high valence tracks."""
        mood = MoodVector(energy=0.6, valence=0.8, danceability=0.7, tension=0.4)
        genre, sub_genres, confidence = compute_genre(
            "fake_path.mp3", bpm=120.0, mood_vector=mood
        )

        assert genre == "Pop"
        assert confidence >= 0.5

    def test_rock_genre_moderate_bpm_high_energy(self):
        """Test rock genre detection for moderate BPM, high energy tracks."""
        mood = MoodVector(energy=0.8, valence=0.5, danceability=0.5, tension=0.7)
        genre, sub_genres, confidence = compute_genre(
            "fake_path.mp3", bpm=110.0, mood_vector=mood
        )

        assert genre == "Rock"
        assert confidence >= 0.5

    def test_hip_hop_genre_low_bpm_high_danceability(self):
        """Test hip-hop genre detection for low BPM, high danceability tracks."""
        # Use BPM 95 and higher tension to avoid Country match (Country requires tension < 0.6)
        mood = MoodVector(energy=0.6, valence=0.6, danceability=0.8, tension=0.65)
        genre, sub_genres, confidence = compute_genre(
            "fake_path.mp3", bpm=95.0, mood_vector=mood
        )

        assert genre == "Hip-Hop"
        assert confidence >= 0.5

    def test_ambient_genre_low_bpm_low_energy(self):
        """Test ambient genre detection for low BPM, low energy tracks."""
        mood = MoodVector(energy=0.3, valence=0.4, danceability=0.2, tension=0.3)
        genre, sub_genres, confidence = compute_genre(
            "fake_path.mp3", bpm=70.0, mood_vector=mood
        )

        assert genre == "Ambient"
        assert confidence >= 0.5

    def test_metal_genre_very_high_bpm_very_high_energy(self):
        """Test metal genre detection for very high BPM, very high energy tracks."""
        mood = MoodVector(energy=0.9, valence=0.4, danceability=0.5, tension=0.8)
        genre, sub_genres, confidence = compute_genre(
            "fake_path.mp3", bpm=160.0, mood_vector=mood
        )

        assert genre == "Metal"
        assert confidence >= 0.5

    def test_other_genre_fallback(self):
        """Test that unknown patterns fall back to 'Other' genre."""
        mood = MoodVector(energy=0.4, valence=0.4, danceability=0.4, tension=0.4)
        genre, sub_genres, confidence = compute_genre(
            "fake_path.mp3", bpm=60.0, mood_vector=mood
        )

        # Should return a genre (even if "Other")
        assert genre is not None
        assert isinstance(genre, str)
        assert isinstance(sub_genres, list)
        assert 0.0 <= confidence <= 1.0

    def test_genre_confidence_range(self):
        """Test that confidence is always in valid range."""
        test_cases = [
            (MoodVector(energy=0.8, valence=0.7, danceability=0.7, tension=0.5), 130.0),
            (MoodVector(energy=0.5, valence=0.5, danceability=0.5, tension=0.5), 100.0),
            (MoodVector(energy=0.3, valence=0.3, danceability=0.3, tension=0.3), 70.0),
        ]

        for mood, bpm in test_cases:
            _, _, confidence = compute_genre("fake_path.mp3", bpm=bpm, mood_vector=mood)
            assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} out of range"


class TestMoodVectorValidation:
    """Test MoodVector schema validation."""

    def test_mood_vector_valid_range(self):
        """Test that MoodVector accepts values in 0-1 range."""
        mood = MoodVector(energy=0.5, valence=0.5, danceability=0.5, tension=0.5)
        assert mood.energy == 0.5

    def test_mood_vector_boundary_values(self):
        """Test MoodVector with boundary values (0.0 and 1.0)."""
        mood = MoodVector(energy=0.0, valence=1.0, danceability=0.0, tension=1.0)
        assert mood.energy == 0.0
        assert mood.valence == 1.0

    def test_mood_vector_invalid_range(self):
        """Test that MoodVector rejects values outside 0-1 range."""
        with pytest.raises(Exception):  # Pydantic validation error
            MoodVector(energy=1.5, valence=0.5, danceability=0.5, tension=0.5)


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])

