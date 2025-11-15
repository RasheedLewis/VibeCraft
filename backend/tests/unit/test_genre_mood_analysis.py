"""Unit tests for genre and mood analysis service.

Tests logic with mocked MoodVector objects and librosa functions - no audio files needed, fast (~0.1s).
24 pytest cases covering edge cases, normalization logic, and rule-based classification.
Validates compute_mood_features(), compute_mood_tags(), and compute_genre() in isolation.

Complementary to tests/test_genre_mood.py: This verifies rules/logic work correctly;
tests/test_genre_mood.py verifies the full pipeline works with real audio files.

Run with: pytest backend/tests/unit/test_genre_mood_analysis.py -v
Or from backend/: pytest tests/unit/test_genre_mood_analysis.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from unittest.mock import MagicMock, patch  # noqa: E402

import pytest  # noqa: E402
from app.schemas.analysis import MoodVector  # noqa: E402
from app.services.genre_mood_analysis import (  # noqa: E402
    compute_genre,
    compute_mood_features,
    compute_mood_tags,
)


class TestComputeMoodFeatures:
    """Test mood feature computation and normalization logic."""

    @patch("app.services.genre_mood_analysis.librosa.load")
    @patch("app.services.genre_mood_analysis.librosa.feature.rms")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_centroid")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_rolloff")
    @patch("app.services.genre_mood_analysis.librosa.beat.beat_track")
    @patch("app.services.genre_mood_analysis.librosa.onset.onset_detect")
    def test_energy_normalization(
        self, mock_onset, mock_beat, mock_rolloff, mock_centroid, mock_rms, mock_load
    ):
        """Test energy normalization from RMS values."""
        import numpy as np  # noqa: E402

        # Setup mocks - need to mock audio array with proper length
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 22050  # 1 second at 22050 Hz
        mock_load.return_value = (mock_audio, 22050)
        mock_beat.return_value = (120.0, MagicMock())
        mock_onset.return_value = [0, 100, 200, 300]

        # Mock librosa feature arrays (2D arrays, accessed with [0])
        mock_centroid.return_value = np.array([[3000.0] * 100])
        mock_rolloff.return_value = np.array([[5000.0] * 100])

        # Test RMS = 0.0 (silence)
        mock_rms.return_value = np.array([[0.0] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert result.energy == 0.0

        # Test RMS = 0.3 (typical max) → energy = 1.0
        mock_rms.return_value = np.array([[0.3] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert result.energy == 1.0

        # Test RMS > 0.3 (very loud) → energy clamped to 1.0
        mock_rms.return_value = np.array([[0.5] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert result.energy == 1.0

        # Test RMS = 0.15 (middle) → energy = 0.5
        mock_rms.return_value = np.array([[0.15] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert abs(result.energy - 0.5) < 0.01

    @patch("app.services.genre_mood_analysis.librosa.load")
    @patch("app.services.genre_mood_analysis.librosa.feature.rms")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_centroid")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_rolloff")
    @patch("app.services.genre_mood_analysis.librosa.beat.beat_track")
    @patch("app.services.genre_mood_analysis.librosa.onset.onset_detect")
    def test_valence_normalization(
        self, mock_onset, mock_beat, mock_rolloff, mock_centroid, mock_rms, mock_load
    ):
        """Test valence normalization from spectral centroid."""
        import numpy as np  # noqa: E402

        # Setup mocks - need to mock audio array with proper length
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 22050  # 1 second at 22050 Hz
        mock_load.return_value = (mock_audio, 22050)
        mock_beat.return_value = (120.0, MagicMock())
        mock_onset.return_value = [0, 100, 200, 300]
        mock_rms.return_value = np.array([[0.2] * 100])
        mock_rolloff.return_value = np.array([[5000.0] * 100])

        # Test spectral centroid < 1000 Hz → valence = 0.0
        mock_centroid.return_value = np.array([[500.0] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert result.valence == 0.0

        # Test spectral centroid = 5000 Hz → valence = 1.0
        mock_centroid.return_value = np.array([[5000.0] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert result.valence == 1.0

        # Test spectral centroid > 5000 Hz → valence clamped to 1.0
        mock_centroid.return_value = np.array([[7000.0] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert result.valence == 1.0

        # Test spectral centroid = 3000 Hz (middle) → valence = 0.5
        mock_centroid.return_value = np.array([[3000.0] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert abs(result.valence - 0.5) < 0.01

    @patch("app.services.genre_mood_analysis.librosa.load")
    @patch("app.services.genre_mood_analysis.librosa.feature.rms")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_centroid")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_rolloff")
    @patch("app.services.genre_mood_analysis.librosa.beat.beat_track")
    @patch("app.services.genre_mood_analysis.librosa.onset.onset_detect")
    def test_tension_normalization(
        self, mock_onset, mock_beat, mock_rolloff, mock_centroid, mock_rms, mock_load
    ):
        """Test tension normalization from spectral rolloff."""
        import numpy as np  # noqa: E402

        # Setup mocks - need to mock audio array with proper length
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 22050  # 1 second at 22050 Hz
        mock_load.return_value = (mock_audio, 22050)
        mock_beat.return_value = (120.0, MagicMock())
        mock_onset.return_value = [0, 100, 200, 300]
        mock_rms.return_value = np.array([[0.2] * 100])
        mock_centroid.return_value = np.array([[3000.0] * 100])

        # Test spectral rolloff < 2000 Hz → tension = 0.0
        mock_rolloff.return_value = np.array([[1000.0] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert result.tension == 0.0

        # Test spectral rolloff = 8000 Hz → tension = 1.0
        mock_rolloff.return_value = np.array([[8000.0] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert result.tension == 1.0

        # Test spectral rolloff > 8000 Hz → tension clamped to 1.0
        mock_rolloff.return_value = np.array([[10000.0] * 100])
        result = compute_mood_features("fake_path.mp3")
        assert result.tension == 1.0

    @patch("app.services.genre_mood_analysis.librosa.load")
    @patch("app.services.genre_mood_analysis.librosa.feature.rms")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_centroid")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_rolloff")
    @patch("app.services.genre_mood_analysis.librosa.beat.beat_track")
    @patch("app.services.genre_mood_analysis.librosa.onset.onset_detect")
    def test_danceability_bpm_factor(
        self, mock_onset, mock_beat, mock_rolloff, mock_centroid, mock_rms, mock_load
    ):
        """Test danceability BPM factor calculation."""
        import numpy as np  # noqa: E402

        # Setup mocks
        mock_load.return_value = (MagicMock(), 22050)
        mock_onset.return_value = [0, 100, 200, 300]  # 4 beats
        mock_rms.return_value = np.array([[0.2] * 100])
        mock_centroid.return_value = np.array([[3000.0] * 100])
        mock_rolloff.return_value = np.array([[5000.0] * 100])

        # Mock audio length for beat strength calculation (4 beats / 1 second = 4.0 beats/sec)
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 22050  # 1 second at 22050 Hz
        mock_load.return_value = (mock_audio, 22050)

        # Test BPM < 80 → factor = 0.3
        mock_beat.return_value = (70.0, MagicMock())
        result = compute_mood_features("fake_path.mp3")
        # Beat strength = 4.0, norm = 1.0, BPM factor = 0.3 → danceability = 0.3
        assert result.danceability == 0.3

        # Test 80 <= BPM < 100 → factor = 0.6
        mock_beat.return_value = (90.0, MagicMock())
        result = compute_mood_features("fake_path.mp3")
        assert result.danceability == 0.6

        # Test 100 <= BPM <= 160 → factor = 1.0
        mock_beat.return_value = (120.0, MagicMock())
        result = compute_mood_features("fake_path.mp3")
        assert result.danceability == 1.0

        # Test BPM > 160 → factor = 0.7
        mock_beat.return_value = (170.0, MagicMock())
        result = compute_mood_features("fake_path.mp3")
        assert result.danceability == 0.7

    @patch("app.services.genre_mood_analysis.librosa.load")
    @patch("app.services.genre_mood_analysis.librosa.feature.rms")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_centroid")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_rolloff")
    @patch("app.services.genre_mood_analysis.librosa.beat.beat_track")
    @patch("app.services.genre_mood_analysis.librosa.onset.onset_detect")
    def test_beat_strength_normalization(
        self, mock_onset, mock_beat, mock_rolloff, mock_centroid, mock_rms, mock_load
    ):
        """Test beat strength normalization."""
        import numpy as np  # noqa: E402

        # Setup mocks
        mock_load.return_value = (MagicMock(), 22050)
        mock_beat.return_value = (120.0, MagicMock())
        mock_rms.return_value = np.array([[0.2] * 100])
        mock_centroid.return_value = np.array([[3000.0] * 100])
        mock_rolloff.return_value = np.array([[5000.0] * 100])

        # Test beat strength = 0 (no beats) → danceability = 0.0
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 22050  # 1 second
        mock_load.return_value = (mock_audio, 22050)
        mock_onset.return_value = []  # No beats
        result = compute_mood_features("fake_path.mp3")
        assert result.danceability == 0.0

        # Test beat strength = 4.0 (very strong) → norm = 1.0
        mock_onset.return_value = [0, 5512, 11025, 16537]  # 4 beats in 1 second
        result = compute_mood_features("fake_path.mp3")
        # Beat strength = 4.0, norm = 1.0, BPM factor = 1.0 → danceability = 1.0
        assert result.danceability == 1.0

    @patch("app.services.genre_mood_analysis.librosa.load")
    @patch("app.services.genre_mood_analysis.librosa.feature.rms")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_centroid")
    @patch("app.services.genre_mood_analysis.librosa.feature.spectral_rolloff")
    @patch("app.services.genre_mood_analysis.librosa.beat.beat_track")
    @patch("app.services.genre_mood_analysis.librosa.onset.onset_detect")
    def test_all_values_in_valid_range(
        self, mock_onset, mock_beat, mock_rolloff, mock_centroid, mock_rms, mock_load
    ):
        """Test that all mood vector values are clamped to [0.0, 1.0] range."""
        import numpy as np  # noqa: E402

        # Setup mocks with extreme values - need to mock audio array with proper length
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 22050  # 1 second at 22050 Hz
        mock_load.return_value = (mock_audio, 22050)
        mock_beat.return_value = (120.0, MagicMock())
        mock_onset.return_value = [0, 100, 200, 300]

        # Extreme RMS (very loud)
        mock_rms.return_value = np.array([[1.0] * 100])  # Very high
        # Extreme spectral values
        mock_centroid.return_value = np.array([[10000.0] * 100])  # Very high
        mock_rolloff.return_value = np.array([[15000.0] * 100])  # Very high

        result = compute_mood_features("fake_path.mp3")
        assert 0.0 <= result.energy <= 1.0
        assert 0.0 <= result.valence <= 1.0
        assert 0.0 <= result.tension <= 1.0
        assert 0.0 <= result.danceability <= 1.0

    @patch("app.services.genre_mood_analysis.librosa.load")
    def test_uses_provided_bpm(self, mock_load):
        """Test that function uses provided BPM instead of computing it."""
        # Setup mocks - need to mock audio array with proper length
        mock_audio = MagicMock()
        mock_audio.__len__.return_value = 22050  # 1 second at 22050 Hz
        mock_load.return_value = (mock_audio, 22050)
        # Should not call beat_track if BPM is provided
        with patch("app.services.genre_mood_analysis.librosa.feature.rms") as mock_rms, patch(
            "app.services.genre_mood_analysis.librosa.feature.spectral_centroid"
        ) as mock_centroid, patch(
            "app.services.genre_mood_analysis.librosa.feature.spectral_rolloff"
        ) as mock_rolloff, patch(
            "app.services.genre_mood_analysis.librosa.beat.beat_track"
        ) as mock_beat, patch(
            "app.services.genre_mood_analysis.librosa.onset.onset_detect"
        ) as mock_onset:
            import numpy as np  # noqa: E402

            mock_rms.return_value = np.array([[0.2] * 100])
            mock_centroid.return_value = np.array([[3000.0] * 100])
            mock_rolloff.return_value = np.array([[5000.0] * 100])
            mock_onset.return_value = [0, 100, 200, 300]

            result = compute_mood_features("fake_path.mp3", bpm=130.0)
            # Should not call beat_track when BPM is provided
            mock_beat.assert_not_called()
            # Result should use provided BPM (130 is in 100-160 range, factor = 1.0)
            assert result.danceability > 0


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

