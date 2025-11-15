"""Unit tests for lyric extraction service.

Tests logic for segmenting and aligning lyrics - no audio files or API calls needed, fast.
Validates segment_lyrics_into_lines() and align_lyrics_to_sections() in isolation.

Complementary to tests/test_lyrics.py: This verifies rules/logic work correctly;
tests/test_lyrics.py verifies the full pipeline works with real audio files and Replicate API.

Run with: pytest backend/tests/unit/test_lyric_extraction.py -v
Or from backend/: pytest tests/unit/test_lyric_extraction.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from app.schemas.analysis import SongSection  # noqa: E402
from app.services.lyric_extraction import (  # noqa: E402
    align_lyrics_to_sections,
    segment_lyrics_into_lines,
)


class TestSegmentLyricsIntoLines:
    """Test lyric line segmentation logic."""

    def test_empty_segments(self):
        """Test that empty segments list returns empty list."""
        result = segment_lyrics_into_lines([])
        assert result == []

    def test_single_segment(self):
        """Test single segment becomes single line."""
        segments = [{"start": 0.0, "end": 2.0, "text": "Hello world"}]
        result = segment_lyrics_into_lines(segments)
        assert len(result) == 1
        assert result[0]["text"] == "Hello world"
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 2.0

    def test_combine_short_segments(self):
        """Test that short segments close together are combined."""
        segments = [
            {"start": 0.0, "end": 0.3, "text": "Hello"},
            {"start": 0.5, "end": 0.7, "text": "world"},  # Gap < 1.0, duration < 0.5
        ]
        result = segment_lyrics_into_lines(segments)
        assert len(result) == 1
        assert result[0]["text"] == "Hello world"
        assert result[0]["start"] == 0.0
        assert result[0]["end"] == 0.7

    def test_separate_long_segments(self):
        """Test that segments with large gaps are kept separate."""
        segments = [
            {"start": 0.0, "end": 2.0, "text": "First line"},
            {"start": 5.0, "end": 7.0, "text": "Second line"},  # Gap > 1.0
        ]
        result = segment_lyrics_into_lines(segments)
        assert len(result) == 2
        assert result[0]["text"] == "First line"
        assert result[1]["text"] == "Second line"

    def test_filter_short_lines(self):
        """Test that lines shorter than min_line_duration are filtered out."""
        segments = [
            {"start": 0.0, "end": 0.2, "text": "Too short"},  # Duration < 0.5
            {"start": 1.0, "end": 2.0, "text": "Long enough"},  # Duration >= 0.5
        ]
        result = segment_lyrics_into_lines(segments, min_line_duration=0.5)
        assert len(result) == 1
        assert result[0]["text"] == "Long enough"

    def test_skip_empty_text(self):
        """Test that segments with empty text are skipped."""
        segments = [
            {"start": 0.0, "end": 1.0, "text": "Valid text"},
            {"start": 2.0, "end": 3.0, "text": ""},  # Empty
            {"start": 4.0, "end": 5.0, "text": "   "},  # Whitespace only
            {"start": 6.0, "end": 7.0, "text": "Another valid"},
        ]
        result = segment_lyrics_into_lines(segments)
        assert len(result) == 2
        assert result[0]["text"] == "Valid text"
        assert result[1]["text"] == "Another valid"

    def test_multiple_combinations(self):
        """Test complex scenario with multiple combinations."""
        segments = [
            {"start": 0.0, "end": 0.3, "text": "First"},
            {"start": 0.5, "end": 0.7, "text": "part"},  # Combine with First (gap < 1.0, short)
            {"start": 2.0, "end": 4.0, "text": "Second line"},  # Separate (gap > 1.0 from First)
            {"start": 4.2, "end": 4.4, "text": "Third"},  # Short, close to Second (gap 0.2 < 1.0)
            {"start": 4.6, "end": 4.8, "text": "part"},  # Combine with Third (gap < 1.0, short)
        ]
        result = segment_lyrics_into_lines(segments)
        # "Second line" and "Third part" combine because gap (4.2-4.0=0.2) < 1.0 and Third is short
        assert len(result) == 2
        assert result[0]["text"] == "First part"
        assert "Second line" in result[1]["text"]
        assert "Third part" in result[1]["text"]


class TestAlignLyricsToSections:
    """Test lyric-to-section alignment logic."""

    def test_empty_lyrics(self):
        """Test that empty lyrics returns empty list."""
        sections = [
            SongSection(id="s1", type="verse", startSec=0.0, endSec=10.0, confidence=0.9)
        ]
        result = align_lyrics_to_sections([], sections)
        assert result == []

    def test_empty_sections(self):
        """Test that empty sections returns empty list."""
        lyrics = [{"start": 0.0, "end": 2.0, "text": "Some lyrics"}]
        result = align_lyrics_to_sections(lyrics, [])
        assert result == []

    def test_lyrics_inside_section(self):
        """Test lyrics that fall entirely within a section."""
        lyrics = [
            {"start": 1.0, "end": 3.0, "text": "First line"},
            {"start": 3.5, "end": 5.0, "text": "Second line"},
        ]
        sections = [
            SongSection(id="verse-1", type="verse", startSec=0.0, endSec=10.0, confidence=0.9)
        ]
        result = align_lyrics_to_sections(lyrics, sections)
        assert len(result) == 1
        assert result[0].section_id == "verse-1"
        assert "First line" in result[0].text
        assert "Second line" in result[0].text

    def test_lyrics_overlapping_section_boundary(self):
        """Test lyrics that overlap section boundaries."""
        lyrics = [
            {"start": 8.0, "end": 12.0, "text": "Overlapping line"},  # Overlaps both sections
        ]
        sections = [
            SongSection(id="verse-1", type="verse", startSec=0.0, endSec=10.0, confidence=0.9),
            SongSection(id="chorus-1", type="chorus", startSec=10.0, endSec=20.0, confidence=0.9),
        ]
        result = align_lyrics_to_sections(lyrics, sections)
        # Should appear in both sections
        assert len(result) == 2
        assert any(sl.section_id == "verse-1" for sl in result)
        assert any(sl.section_id == "chorus-1" for sl in result)

    def test_lyrics_outside_sections(self):
        """Test lyrics that don't overlap any sections."""
        lyrics = [
            {"start": 0.0, "end": 2.0, "text": "Before section"},
            {"start": 5.0, "end": 7.0, "text": "Inside section"},
            {"start": 15.0, "end": 17.0, "text": "After section"},
        ]
        sections = [
            SongSection(id="verse-1", type="verse", startSec=3.0, endSec=10.0, confidence=0.9)
        ]
        result = align_lyrics_to_sections(lyrics, sections)
        assert len(result) == 1
        assert result[0].section_id == "verse-1"
        assert "Inside section" in result[0].text
        assert "Before section" not in result[0].text
        assert "After section" not in result[0].text

    def test_multiple_sections_multiple_lyrics(self):
        """Test complex scenario with multiple sections and lyrics."""
        lyrics = [
            {"start": 1.0, "end": 3.0, "text": "Verse line 1"},
            {"start": 4.0, "end": 6.0, "text": "Verse line 2"},
            {"start": 12.0, "end": 14.0, "text": "Chorus line 1"},
            {"start": 15.0, "end": 17.0, "text": "Chorus line 2"},
        ]
        sections = [
            SongSection(id="verse-1", type="verse", startSec=0.0, endSec=10.0, confidence=0.9),
            SongSection(id="chorus-1", type="chorus", startSec=10.0, endSec=20.0, confidence=0.9),
        ]
        result = align_lyrics_to_sections(lyrics, sections)
        assert len(result) == 2

        verse_lyrics = next(sl for sl in result if sl.section_id == "verse-1")
        chorus_lyrics = next(sl for sl in result if sl.section_id == "chorus-1")

        assert "Verse line 1" in verse_lyrics.text
        assert "Verse line 2" in verse_lyrics.text
        assert "Chorus line 1" in chorus_lyrics.text
        assert "Chorus line 2" in chorus_lyrics.text

    def test_text_truncation(self):
        """Test that long section text is truncated."""
        # Create very long lyrics
        long_text = " ".join(["word"] * 100)  # ~500 chars
        lyrics = [{"start": 1.0, "end": 3.0, "text": long_text}]
        sections = [
            SongSection(id="verse-1", type="verse", startSec=0.0, endSec=10.0, confidence=0.9)
        ]
        result = align_lyrics_to_sections(lyrics, sections)
        assert len(result) == 1
        assert len(result[0].text) <= 203  # 200 + "..."
        assert result[0].text.endswith("...")

    def test_section_timestamps_preserved(self):
        """Test that section start/end times are preserved in SectionLyrics."""
        lyrics = [{"start": 5.0, "end": 7.0, "text": "Some lyrics"}]
        sections = [
            SongSection(id="verse-1", type="verse", startSec=0.0, endSec=10.0, confidence=0.9)
        ]
        result = align_lyrics_to_sections(lyrics, sections)
        assert result[0].start_sec == 0.0
        assert result[0].end_sec == 10.0


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])

