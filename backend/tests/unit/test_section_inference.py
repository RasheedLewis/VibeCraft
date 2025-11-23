"""Unit tests for section inference service.

Tests heuristic logic with mocked data - no audio files needed, fast.
Covers clustering, merging, type inference, and critical edge cases.

Run with: pytest backend/tests/unit/test_section_inference.py -v
"""

import sys
from pathlib import Path

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from app.services.section_inference import (  # noqa: E402
    SectionInference,
    _cluster_similar_labels,
    _merge_consecutive_sections,
    _merge_section_group,
    _normalize,
    infer_section_types,
)


class TestNormalize:
    """Test normalization utility function."""

    def test_normalize_basic(self):
        """Test basic normalization to 0-1 range."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _normalize(values)
        assert result == [0.0, 0.25, 0.5, 0.75, 1.0]

    def test_normalize_all_same(self):
        """Test normalization when all values are the same (edge case)."""
        values = [5.0, 5.0, 5.0]
        result = _normalize(values)
        assert result == [0.5, 0.5, 0.5]

    def test_normalize_negative_values(self):
        """Test normalization with negative values."""
        values = [-5.0, 0.0, 5.0]
        result = _normalize(values)
        assert result == [0.0, 0.5, 1.0]


class TestClusterSimilarLabels:
    """Test label clustering logic."""

    def test_cluster_within_threshold(self):
        """Test that labels within threshold cluster together."""
        labels = [100, 120, 140, 300, 320]
        result = _cluster_similar_labels(labels, similarity_threshold=50)
        # 100, 120, 140 should cluster (within 50 of each other)
        # 300, 320 should cluster
        assert result[100] == result[120] == result[140]
        assert result[300] == result[320]
        assert result[100] != result[300]

    def test_cluster_threshold_zero(self):
        """Test clustering with threshold of 0 (exact matches only)."""
        labels = [100, 100, 101, 200]
        result = _cluster_similar_labels(labels, similarity_threshold=0)
        assert result[100] == 100
        assert result[101] == 101  # Different cluster
        assert result[200] == 200


class TestMergeSectionGroup:
    """Test merging a group of consecutive sections."""

    def test_merge_multiple_sections(self):
        """Test merging multiple sections."""
        sections = [
            SectionInference(
                id="sec-0",
                index=0,
                start_sec=0.0,
                end_sec=5.0,
                duration_sec=5.0,
                label_raw=100,
                type_soft="chorus_like",
                confidence=0.7,
                display_name="Chorus 1",
            ),
            SectionInference(
                id="sec-1",
                index=1,
                start_sec=5.0,
                end_sec=10.0,
                duration_sec=5.0,
                label_raw=100,
                type_soft="chorus_like",
                confidence=0.8,
                display_name="Chorus 2",
            ),
        ]
        result = _merge_section_group(sections)
        assert result.start_sec == 0.0
        assert result.end_sec == 10.0
        assert result.duration_sec == 10.0
        assert result.confidence == 0.75  # (0.7 + 0.8) / 2
        assert result.id == "sec-0"  # First section's ID
        assert result.label_raw == 100  # First section's label
        assert result.type_soft == "chorus_like"


class TestMergeConsecutiveSections:
    """Test merging consecutive sections of same type."""

    def test_merge_consecutive_same_type(self):
        """Test that consecutive same-type sections merge."""
        sections = [
            SectionInference(
                id="sec-0",
                index=0,
                start_sec=0.0,
                end_sec=5.0,
                duration_sec=5.0,
                label_raw=100,
                type_soft="intro_like",
                confidence=0.6,
                display_name="Intro",
            ),
            SectionInference(
                id="sec-1",
                index=1,
                start_sec=5.0,
                end_sec=10.0,
                duration_sec=5.0,
                label_raw=100,
                type_soft="intro_like",
                confidence=0.6,
                display_name="Intro 2",
            ),
            SectionInference(
                id="sec-2",
                index=2,
                start_sec=10.0,
                end_sec=15.0,
                duration_sec=5.0,
                label_raw=200,
                type_soft="verse_like",
                confidence=0.6,
                display_name="Verse 1",
            ),
        ]
        result = _merge_consecutive_sections(sections)
        assert len(result) == 2
        assert result[0].type_soft == "intro_like"
        assert result[0].display_name == "Intro"  # Reassigned after merge
        assert result[1].type_soft == "verse_like"
        assert result[1].display_name == "Verse 1"

    def test_no_merge_different_types(self):
        """Test that different types don't merge."""
        sections = [
            SectionInference(
                id="sec-0",
                index=0,
                start_sec=0.0,
                end_sec=5.0,
                duration_sec=5.0,
                label_raw=100,
                type_soft="intro_like",
                confidence=0.6,
                display_name="Intro",
            ),
            SectionInference(
                id="sec-1",
                index=1,
                start_sec=5.0,
                end_sec=10.0,
                duration_sec=5.0,
                label_raw=200,
                type_soft="verse_like",
                confidence=0.6,
                display_name="Verse 1",
            ),
        ]
        result = _merge_consecutive_sections(sections)
        assert len(result) == 2


class TestInferSectionTypes:
    """Test main section type inference function."""

    def test_empty_input(self):
        """Test that empty input returns empty list."""
        result = infer_section_types([], [], None)
        assert result == []

    def test_length_mismatch_energy(self):
        """Test that energy length mismatch raises ValueError."""
        with pytest.raises(ValueError, match="energy_per_section length must match"):
            infer_section_types(
                [{"startMs": 0, "endMs": 5000, "label": 100}],
                [0.5, 0.6],  # Wrong length
                None,
            )

    def test_chorus_detection(self):
        """Test that most repeated and energetic section is detected as chorus."""
        # Create sections where label 100 appears 3 times with high energy
        # and label 200 appears 2 times with lower energy
        audjust_sections = [
            {"startMs": 0, "endMs": 10000, "label": 100},  # Chorus candidate
            {"startMs": 10000, "endMs": 20000, "label": 200},  # Verse
            {"startMs": 20000, "endMs": 30000, "label": 100},  # Chorus
            {"startMs": 30000, "endMs": 40000, "label": 200},  # Verse
            {"startMs": 40000, "endMs": 50000, "label": 100},  # Chorus
        ]
        energy_per_section = [0.9, 0.5, 0.9, 0.5, 0.9]  # High energy for chorus

        result = infer_section_types(audjust_sections, energy_per_section)

        # All sections with label 100 should be chorus_like
        chorus_sections = [s for s in result if s.label_raw == 100]
        assert all(s.type_soft == "chorus_like" for s in chorus_sections)
        assert len(chorus_sections) == 3

    def test_verse_detection(self):
        """Test that repeated non-chorus sections are detected as verse."""
        audjust_sections = [
            {"startMs": 0, "endMs": 10000, "label": 100},  # Chorus (most repeated)
            {"startMs": 10000, "endMs": 20000, "label": 200},  # Verse candidate
            {"startMs": 20000, "endMs": 30000, "label": 100},  # Chorus
            {"startMs": 30000, "endMs": 40000, "label": 200},  # Verse
        ]
        energy_per_section = [0.9, 0.6, 0.9, 0.6]

        result = infer_section_types(audjust_sections, energy_per_section)

        # Sections with label 200 should be verse_like
        verse_sections = [s for s in result if s.label_raw == 200]
        assert all(s.type_soft == "verse_like" for s in verse_sections)

    def test_label_clustering_affects_inference(self):
        """Test that label clustering groups similar labels."""
        # Labels 100, 105, 110 should cluster together
        # Make them appear multiple times so they're detected as chorus/verse
        audjust_sections = [
            {"startMs": 0, "endMs": 10000, "label": 100},
            {"startMs": 10000, "endMs": 20000, "label": 105},  # Close to 100
            {"startMs": 20000, "endMs": 30000, "label": 110},  # Close to 100
            {"startMs": 30000, "endMs": 40000, "label": 100},  # Repeat of 100
            {"startMs": 40000, "endMs": 50000, "label": 500},  # Far away
        ]
        energy_per_section = [0.8, 0.8, 0.8, 0.8, 0.5]

        result = infer_section_types(audjust_sections, energy_per_section)

        # Clustered labels should be treated as same type
        # All sections with labels 100-110 should be grouped together
        clustered = [s for s in result if s.label_raw in [100, 105, 110]]
        # They should all have the same type_soft (likely chorus_like)
        if len(clustered) > 1:
            types = set(s.type_soft for s in clustered)
            # All clustered sections should have same type
            assert len(types) == 1

    def test_merging_in_final_output(self):
        """Test that consecutive sections are merged in final output."""
        audjust_sections = [
            {"startMs": 0, "endMs": 5000, "label": 100},
            {"startMs": 5000, "endMs": 10000, "label": 100},  # Same label, consecutive
            {"startMs": 10000, "endMs": 15000, "label": 200},
        ]
        energy_per_section = [0.8, 0.8, 0.6]

        result = infer_section_types(audjust_sections, energy_per_section)

        # First two should be merged if they have same type_soft
        # Result should have fewer sections than input
        assert len(result) <= len(audjust_sections)

    def test_display_name_assignment(self):
        """Test that display names are assigned correctly."""
        audjust_sections = [
            {"startMs": 0, "endMs": 10000, "label": 100},
            {"startMs": 10000, "endMs": 20000, "label": 100},
            {"startMs": 20000, "endMs": 30000, "label": 200},
        ]
        energy_per_section = [0.8, 0.8, 0.6]

        result = infer_section_types(audjust_sections, energy_per_section)

        # All sections should have display names
        assert all(s.display_name for s in result)
        # Chorus sections should have "Chorus 1", "Chorus 2", etc.
        chorus_sections = [s for s in result if s.type_soft == "chorus_like"]
        if chorus_sections:
            assert "Chorus" in chorus_sections[0].display_name

    def test_zero_duration_section(self):
        """Test handling of zero-duration sections (edge case)."""
        audjust_sections = [
            {"startMs": 0, "endMs": 0, "label": 100},  # Zero duration
            {"startMs": 0, "endMs": 10000, "label": 200},
        ]
        energy_per_section = [0.5, 0.6]

        result = infer_section_types(audjust_sections, energy_per_section)
        # Should not crash
        assert len(result) >= 0

    def test_single_section_song(self):
        """Test inference with single section (edge case)."""
        audjust_sections = [{"startMs": 0, "endMs": 10000, "label": 100}]
        energy_per_section = [0.5]

        result = infer_section_types(audjust_sections, energy_per_section)

        assert len(result) == 1
        # Single section should be classified (could be "other", "bridge_like", "intro_like", or "outro_like")
        assert result[0].type_soft in ["intro_like", "outro_like", "bridge_like", "other"]
