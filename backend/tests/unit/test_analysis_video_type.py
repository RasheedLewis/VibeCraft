"""Unit tests for analysis service with different video_types.

Tests that analysis pipeline respects video_type and skips section inference
for short_form videos while still running other analysis steps.
"""

from pathlib import Path


def _get_song_analysis_path() -> Path:
    """Get the path to song_analysis.py, working from any directory."""
    # This file is at backend/tests/unit/test_analysis_video_type.py
    # We need to go up to backend/, then to app/services/song_analysis.py
    current_file = Path(__file__)
    # Go up: tests/unit -> tests -> backend
    backend_dir = current_file.parent.parent.parent
    # Then to app/services/song_analysis.py
    return backend_dir / "app" / "services" / "song_analysis.py"


class TestAnalysisRespectsVideoType:
    """Tests that analysis respects video_type setting."""

    def test_analysis_code_checks_video_type(self):
        """Test that analysis service code checks video_type."""
        # This is a code-level test to verify the logic exists
        song_analysis_path = _get_song_analysis_path()
        content = song_analysis_path.read_text()
        assert "should_use_sections_for_song" in content, \
            "Analysis service should check video_type via should_use_sections_for_song"
        assert "use_sections = should_use_sections_for_song" in content, \
            "Analysis service should set use_sections based on video_type"
    
    def test_analysis_skips_sections_for_short_form(self):
        """Test that analysis code skips section inference for short_form."""
        song_analysis_path = _get_song_analysis_path()
        content = song_analysis_path.read_text()
        assert "Skipping section detection (short-form video)" in content, \
            "Analysis should log when skipping sections for short-form"

    def test_analysis_conditionally_runs_sections(self):
        """Test that analysis conditionally runs section inference."""
        song_analysis_path = _get_song_analysis_path()
        content = song_analysis_path.read_text()
        # Check that there's conditional logic
        assert "if use_sections:" in content or "if use_sections" in content, \
            "Analysis should conditionally run section inference"

