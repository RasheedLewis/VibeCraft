#!/usr/bin/env python3
"""Integration test script for lyric extraction service.

Tests full pipeline with real audio files and Replicate API - exercises extract_lyrics_with_whisper()
(requires Replicate API token). End-to-end: audio → Whisper ASR → segmentation → alignment.
Human-readable output for manual verification.

Complementary to tests/unit/test_lyric_extraction.py: This verifies full pipeline works
with real audio and API; unit tests verify rules/logic work correctly.

Run with: python backend/tests/test_lyrics.py
Or from backend/: python tests/test_lyrics.py
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.services.lyric_extraction import (  # noqa: E402
    align_lyrics_to_sections,
    extract_lyrics_with_whisper,
    segment_lyrics_into_lines,
)
from app.schemas.analysis import SongSection  # noqa: E402

if __name__ == "__main__":
    # Test with sample files
    sample_files = [
        "samples/audio/country/Bryan Mathys - It's Not Hard to Get Lost.mp3",
    ]

    for audio_path in sample_files:
        # samples/ is at repo root, not backend/
        path = Path(__file__).parent.parent.parent / audio_path
        if not path.exists():
            print(f"⚠️  File not found: {path}")
            continue

        print(f"\n🎵 Extracting lyrics from: {path.name}")
        print("=" * 60)

        # Define mock sections for testing alignment
        mock_sections = [
            SongSection(
                id="section-1",
                type="verse",
                startSec=0.0,
                endSec=30.0,
                confidence=0.9,
            ),
            SongSection(
                id="section-2",
                type="chorus",
                startSec=30.0,
                endSec=60.0,
                confidence=0.9,
            ),
        ]

        # Extract lyrics
        print("\n📝 Extracting lyrics with Whisper...")
        segments = extract_lyrics_with_whisper(str(path))
        print(f"   Found {len(segments)} segments")

        if segments:
            # Show first few segments
            print("\n   First 3 segments:")
            for seg in segments[:3]:
                print(f"   [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text'][:60]}")

            # Segment into lines
            print("\n📄 Segmenting into lines...")
            lines = segment_lyrics_into_lines(segments)
            print(f"   Created {len(lines)} lines")

            if lines:
                print("\n   First 3 lines:")
                for line in lines[:3]:
                    print(f"   [{line['start']:.1f}s - {line['end']:.1f}s] {line['text'][:60]}")

            # Test alignment with mock sections
            print("\n🔗 Aligning to mock sections...")
            section_lyrics = align_lyrics_to_sections(lines, mock_sections)
            print(f"   Aligned to {len(section_lyrics)} sections")

            for sl in section_lyrics:
                print(f"\n   Section {sl.section_id}:")
                print(f"   [{sl.start_sec:.1f}s - {sl.end_sec:.1f}s]")
                print(f"   {sl.text[:100]}...")

        # Test full pipeline (reuse segments from above to avoid duplicate API call)
        print("\n🔄 Testing full pipeline logic...")
        if segments:
            # We already have segments, so test the pipeline functions directly
            # This tests segment_lyrics_into_lines + align_lyrics_to_sections
            lyric_lines = segment_lyrics_into_lines(segments)
            pipeline_section_lyrics = align_lyrics_to_sections(lyric_lines, mock_sections)
            print("   Lyrics available: True")
            print(f"   Section lyrics: {len(pipeline_section_lyrics)}")
        else:
            print("   Skipping (no segments extracted)")

    print("\n✅ Lyric extraction test complete!")

