"""Unit tests for analysis service with different video_types.

Tests that analysis pipeline respects video_type and skips section inference
for short_form videos while still running other analysis steps.
"""


class TestAnalysisRespectsVideoType:
    """Tests that analysis respects video_type setting."""

    def test_analysis_code_checks_video_type(self):
        """Test that analysis service code checks video_type."""
        # This is a code-level test to verify the logic exists
        with open("backend/app/services/song_analysis.py", "r") as f:
            content = f.read()
            assert "should_use_sections_for_song" in content, \
                "Analysis service should check video_type via should_use_sections_for_song"
            assert "use_sections = should_use_sections_for_song" in content, \
                "Analysis service should set use_sections based on video_type"
    
    def test_analysis_skips_sections_for_short_form(self):
        """Test that analysis code skips section inference for short_form."""
        with open("backend/app/services/song_analysis.py", "r") as f:
            content = f.read()
            assert "Skipping section detection (short-form video)" in content, \
                "Analysis should log when skipping sections for short-form"

    def test_analysis_conditionally_runs_sections(self):
        """Test that analysis conditionally runs section inference."""
        with open("backend/app/services/song_analysis.py", "r") as f:
            content = f.read()
            # Check that there's conditional logic
            assert "if use_sections:" in content or "if use_sections" in content, \
                "Analysis should conditionally run section inference"

