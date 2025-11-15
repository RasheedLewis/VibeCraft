"""Genre and mood analysis service using librosa."""

import logging
from pathlib import Path
from typing import Optional

import librosa
import numpy as np

from app.schemas.analysis import MoodVector

logger = logging.getLogger(__name__)

# Standardized genre list
GENRES = [
    "Electronic",
    "Pop",
    "Rock",
    "Hip-Hop",
    "R&B",
    "Country",
    "Jazz",
    "Classical",
    "Ambient",
    "Metal",
    "Folk",
    "Reggae",
    "Blues",
    "Other",
]


def compute_mood_features(audio_path: str | Path, bpm: Optional[float] = None) -> MoodVector:
    """
    Compute mood features from audio file.

    Args:
        audio_path: Path to audio file
        bpm: Optional BPM (if already computed, saves computation)

    Returns:
        MoodVector with energy, valence, danceability, tension
    """
    try:
        # Load audio file
        y, sr = librosa.load(str(audio_path), sr=22050, mono=True)

        # Compute spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        rms = librosa.feature.rms(y=y)[0]

        # Energy: RMS energy (normalized)
        # RMS values from librosa are typically 0.05-0.3 for normal music
        # Use percentile-based normalization for better distribution
        rms_mean = float(np.mean(rms))
        # Normalize: use mean as reference, cap at reasonable threshold
        # Most music has RMS mean around 0.1-0.3, so scale accordingly
        energy = min(1.0, max(0.0, rms_mean / 0.3))  # Scale to 0-1 range

        # Valence: Spectral centroid (brightness) - higher = happier/brighter
        valence_raw = float(np.mean(spectral_centroids))
        # Normalize: typical range is 1000-5000 Hz, map to 0-1
        valence = min(1.0, max(0.0, (valence_raw - 1000) / 4000))

        # Tension: Spectral rolloff (high frequency content)
        tension_raw = float(np.mean(spectral_rolloff))
        # Normalize: typical range is 2000-8000 Hz, map to 0-1
        tension = min(1.0, max(0.0, (tension_raw - 2000) / 6000))

        # Danceability: Based on tempo and beat strength
        if bpm is None:
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            bpm = float(tempo)

        # Compute beat strength
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        beat_strength = len(onset_frames) / (len(y) / sr)  # Beats per second
        beat_strength_norm = min(1.0, beat_strength / 4.0)  # Normalize

        # Danceability: Higher for moderate-high BPM (100-140) with strong beats
        bpm_factor = 1.0
        if bpm < 80:
            bpm_factor = 0.3
        elif bpm < 100:
            bpm_factor = 0.6
        elif bpm > 160:
            bpm_factor = 0.7

        danceability = float(bpm_factor * beat_strength_norm)
        danceability = min(1.0, max(0.0, danceability))

        return MoodVector(
            energy=round(energy, 3),
            valence=round(valence, 3),
            danceability=round(danceability, 3),
            tension=round(tension, 3),
        )

    except Exception as e:
        logger.error(f"Error computing mood features: {e}")
        # Return neutral values on error
        return MoodVector(energy=0.5, valence=0.5, danceability=0.5, tension=0.5)


def compute_genre(
    audio_path: str | Path, bpm: Optional[float] = None, mood_vector: Optional[MoodVector] = None
) -> tuple[str, list[str], float]:
    """
    Classify genre using rule-based approach (BPM + spectral features).

    Args:
        audio_path: Path to audio file
        bpm: Optional BPM (if already computed)
        mood_vector: Optional mood vector (if already computed)

    Returns:
        Tuple of (primary_genre, sub_genres, confidence)
    """
    try:
        # Load audio if we need to compute features
        if bpm is None or mood_vector is None:
            y, sr = librosa.load(str(audio_path), sr=22050, mono=True)

            if bpm is None:
                tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
                bpm = float(tempo)

            if mood_vector is None:
                mood_vector = compute_mood_features(audio_path, bpm)

        # Rule-based genre classification
        # Note: This is a simplified rule-based approach. For production, consider using
        # ML models (CLAP, Essentia) trained on genre-labeled datasets.
        genre_scores: dict[str, float] = {}

        # Electronic: High BPM (>120), high energy, high danceability, high valence
        if bpm > 120 and mood_vector.energy > 0.6 and mood_vector.danceability > 0.6:
            genre_scores["Electronic"] = 0.9
        elif bpm > 120 and mood_vector.danceability > 0.5:
            genre_scores["Electronic"] = 0.6

        # Pop: Moderate-high BPM (100-140), high valence, moderate-high energy
        if 100 <= bpm <= 140 and mood_vector.valence > 0.6 and mood_vector.energy > 0.5:
            genre_scores["Pop"] = 0.8
        elif 90 <= bpm <= 150 and mood_vector.valence > 0.6:
            genre_scores["Pop"] = 0.5

        # Country: Moderate BPM (75-120), moderate energy, moderate valence, moderate danceability, lower tension
        # Country typically has less aggressive/tense sound than rock
        # Check Country first to avoid false Rock matches
        if 75 <= bpm <= 120 and 0.4 <= mood_vector.energy <= 0.75 and 0.3 <= mood_vector.valence <= 0.7 and mood_vector.danceability > 0.4 and mood_vector.tension < 0.6:
            genre_scores["Country"] = 0.9
        elif 70 <= bpm <= 125 and 0.4 <= mood_vector.energy <= 0.7 and mood_vector.valence > 0.3 and mood_vector.tension < 0.65:
            genre_scores["Country"] = 0.7

        # Rock: Moderate BPM (90-140), high energy, high tension, lower valence
        # Rock typically has more aggressive/tense sound than pop/country
        if 90 <= bpm <= 140 and mood_vector.energy > 0.7 and mood_vector.tension > 0.6 and mood_vector.valence < 0.5:
            genre_scores["Rock"] = 0.8
        elif 85 <= bpm <= 145 and mood_vector.energy > 0.75 and mood_vector.tension > 0.65:
            genre_scores["Rock"] = 0.6

        # Hip-Hop: Moderate BPM (70-100), high danceability, moderate energy
        if 70 <= bpm <= 100 and mood_vector.danceability > 0.6 and 0.4 <= mood_vector.energy <= 0.8:
            genre_scores["Hip-Hop"] = 0.8
        elif 60 <= bpm <= 110 and mood_vector.danceability > 0.6:
            genre_scores["Hip-Hop"] = 0.5

        # Ambient: Low BPM (<80), low energy, low tension, low danceability
        if bpm < 80 and mood_vector.energy < 0.4 and mood_vector.tension < 0.4 and mood_vector.danceability < 0.3:
            genre_scores["Ambient"] = 0.9
        elif bpm < 85 and mood_vector.energy < 0.5 and mood_vector.tension < 0.5:
            genre_scores["Ambient"] = 0.6

        # R&B: Moderate BPM (70-100), moderate-high energy, moderate-high valence, high danceability
        if 70 <= bpm <= 100 and mood_vector.energy > 0.5 and mood_vector.valence > 0.5 and mood_vector.danceability > 0.5:
            genre_scores["R&B"] = 0.8
        elif 65 <= bpm <= 105 and mood_vector.valence > 0.5 and mood_vector.danceability > 0.5:
            genre_scores["R&B"] = 0.5

        # Metal: High BPM (>140), very high energy, very high tension, low valence
        if bpm > 140 and mood_vector.energy > 0.8 and mood_vector.tension > 0.7 and mood_vector.valence < 0.4:
            genre_scores["Metal"] = 0.9
        elif bpm > 130 and mood_vector.energy > 0.75 and mood_vector.tension > 0.7:
            genre_scores["Metal"] = 0.7

        # If no strong match, default to "Other"
        if not genre_scores:
            return "Other", [], 0.3

        # Get primary genre (highest score)
        primary_genre = max(genre_scores.items(), key=lambda x: x[1])[0]
        confidence = genre_scores[primary_genre]

        # Get sub-genres (other genres with score > 0.4)
        sub_genres = [
            genre for genre, score in genre_scores.items() if genre != primary_genre and score > 0.4
        ]

        return primary_genre, sub_genres, round(confidence, 3)

    except Exception as e:
        logger.error(f"Error classifying genre: {e}")
        return "Other", [], 0.0


def compute_mood_tags(mood_vector: MoodVector) -> tuple[str, list[str]]:
    """
    Convert mood vector to primary mood and tags.

    Args:
        mood_vector: MoodVector with numeric features

    Returns:
        Tuple of (primary_mood, mood_tags)
    """
    tags = []

    # Energy-based tags
    if mood_vector.energy > 0.7:
        tags.append("energetic")
    elif mood_vector.energy < 0.3:
        tags.append("calm")

    # Valence-based tags
    if mood_vector.valence > 0.7:
        tags.append("upbeat")
        tags.append("happy")
    elif mood_vector.valence < 0.3:
        tags.append("melancholic")
        tags.append("sad")

    # Danceability-based tags
    if mood_vector.danceability > 0.7:
        tags.append("danceable")
    elif mood_vector.danceability < 0.3:
        tags.append("ambient")

    # Tension-based tags
    if mood_vector.tension > 0.7:
        tags.append("intense")
    elif mood_vector.tension < 0.3:
        tags.append("relaxed")

    # Determine primary mood
    if not tags:
        primary_mood = "neutral"
    elif "energetic" in tags and "upbeat" in tags:
        primary_mood = "energetic"
    elif "calm" in tags and "relaxed" in tags:
        primary_mood = "calm"
    elif "melancholic" in tags or "sad" in tags:
        primary_mood = "melancholic"
    elif "intense" in tags:
        primary_mood = "intense"
    else:
        primary_mood = tags[0] if tags else "neutral"

    return primary_mood, tags

