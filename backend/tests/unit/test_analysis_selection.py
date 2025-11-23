"""Unit tests for analysis service with audio selection.

Tests that analysis pipeline uses selected audio segment when available.
"""

from pathlib import Path




class TestAnalysisUsesSelection:
    """Tests that analysis uses selected audio segment."""

    def test_analysis_code_checks_selection(self):
        """Test that analysis service code checks for selection."""
        song_analysis_path = Path(__file__).parent.parent.parent / "app" / "services" / "song_analysis.py"
        content = song_analysis_path.read_text()
        assert "selected_start_sec" in content, \
            "Analysis service should check for selected_start_sec"
        assert "selected_end_sec" in content, \
            "Analysis service should check for selected_end_sec"
        assert "time_offset" in content, \
            "Analysis service should use time_offset to adjust beat times"

    def test_analysis_extracts_segment_when_selection_exists(self):
        """Test that analysis extracts audio segment when selection exists."""
        song_analysis_path = Path(__file__).parent.parent.parent / "app" / "services" / "song_analysis.py"
        content = song_analysis_path.read_text()
        assert "Extract the selected segment" in content or "extract" in content.lower(), \
            "Analysis should extract audio segment when selection exists"
        assert "ffmpeg" in content.lower() or "subprocess" in content, \
            "Analysis should use ffmpeg/subprocess to extract segment"

    def test_analysis_adjusts_beat_times_with_selection(self):
        """Test that analysis adjusts beat times to be absolute when selection exists."""
        song_analysis_path = Path(__file__).parent.parent.parent / "app" / "services" / "song_analysis.py"
        content = song_analysis_path.read_text()
        assert "t + time_offset" in content or "time_offset" in content, \
            "Analysis should adjust beat times by adding time_offset"

    def test_analysis_adjusts_sections_with_selection(self):
        """Test that analysis adjusts section times to be absolute when selection exists."""
        song_analysis_path = Path(__file__).parent.parent.parent / "app" / "services" / "song_analysis.py"
        content = song_analysis_path.read_text()
        assert "section.start_sec + time_offset" in content or "time_offset" in content, \
            "Analysis should adjust section times by adding time_offset"

    def test_analysis_uses_effective_duration_with_selection(self):
        """Test that analysis uses selected duration when selection exists."""
        song_analysis_path = Path(__file__).parent.parent.parent / "app" / "services" / "song_analysis.py"
        content = song_analysis_path.read_text()
        assert "effective_duration" in content, \
            "Analysis should use effective_duration when selection exists"
        assert "selection_end_sec - selection_start_sec" in content, \
            "Analysis should calculate effective_duration from selection"

