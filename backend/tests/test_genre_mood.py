#!/usr/bin/env python3
"""Integration test script for genre and mood analysis.

Tests full pipeline with real audio files - exercises compute_mood_features()
(requires librosa to load audio). End-to-end: audio → mood features → tags → genre.
Human-readable output for manual verification.

Complementary to tests/unit/test_genre_mood_analysis.py: This verifies full pipeline works
with real audio; unit tests verify rules/logic work correctly.

Run with: python backend/tests/test_genre_mood.py
Or from backend/: python tests/test_genre_mood.py
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.genre_mood_analysis import (  # noqa: E402
    compute_genre,
    compute_mood_features,
    compute_mood_tags,
)

if __name__ == "__main__":
    # Test with sample files
    sample_files = [
        "samples/audio/electronic/sample1.mp3",
        "samples/audio/country/Bryan Mathys - It's Not Hard to Get Lost.mp3",
    ]

    for audio_path in sample_files:
        # samples/ is at repo root, not backend/
        path = Path(__file__).parent.parent.parent / audio_path
        if not path.exists():
            print(f"⚠️  File not found: {path}")
            continue

        print(f"\n🎵 Analyzing: {path.name}")
        print("=" * 60)

        # Compute mood features
        mood_vector = compute_mood_features(str(path))
        print("\n📊 Mood Vector:")
        print(f"  Energy:      {mood_vector.energy:.3f}")
        print(f"  Valence:     {mood_vector.valence:.3f}")
        print(f"  Danceability: {mood_vector.danceability:.3f}")
        print(f"  Tension:     {mood_vector.tension:.3f}")

        # Compute mood tags
        primary_mood, mood_tags = compute_mood_tags(mood_vector)
        print("\n🏷️  Mood Tags:")
        print(f"  Primary: {primary_mood}")
        print(f"  Tags: {', '.join(mood_tags)}")

        # Compute genre
        primary_genre, sub_genres, confidence = compute_genre(
            str(path), mood_vector=mood_vector
        )
        print("\n🎸 Genre:")
        print(f"  Primary: {primary_genre} ({confidence:.1%})")
        if sub_genres:
            print(f"  Sub-genres: {', '.join(sub_genres)}")

    print("\n✅ Analysis complete!")

