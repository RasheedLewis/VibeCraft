"""Tests for video type API endpoint.

Tests the PATCH /songs/{song_id}/video-type endpoint including validation,
error cases, and successful updates.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import select

from app.core.database import init_db, session_scope
from app.main import create_app
from app.models.analysis import SongAnalysisRecord
from app.models.song import DEFAULT_USER_ID, Song

init_db()


def _cleanup_song(song_id: uuid4) -> None:
    """Clean up test song and related records."""
    with session_scope() as session:
        from app.models.clip import SongClip

        for clip in session.exec(select(SongClip).where(SongClip.song_id == song_id)).all():
            session.delete(clip)
        records = session.exec(
            select(SongAnalysisRecord).where(SongAnalysisRecord.song_id == song_id)
        ).all()
        for record in records:
            session.delete(record)
        song = session.get(Song, song_id)
        if song:
            session.delete(song)
            session.commit()


class TestVideoTypeEndpoint:
    """Tests for PATCH /songs/{song_id}/video-type endpoint."""

    def setup_method(self):
        """Set up test client and create a test song."""
        self.app = create_app()
        self.client = TestClient(self.app)
        
        # Create a test song
        with session_scope() as session:
            song = Song(
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.mp3",
                original_file_size=1024,
                original_s3_key="songs/test/original.mp3",
                processed_s3_key="songs/test/processed.mp3",
                duration_sec=30.0,
            )
            session.add(song)
            session.commit()
            session.refresh(song)
            self.song_id = song.id

    def teardown_method(self):
        """Clean up test song."""
        _cleanup_song(self.song_id)

    def test_set_video_type_full_length_success(self):
        """Test setting video_type to full_length succeeds."""
        response = self.client.patch(
            f"/api/v1/songs/{self.song_id}/video-type",
            json={"video_type": "full_length"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_type"] == "full_length"
        
        # Verify it's persisted
        with session_scope() as session:
            song = session.get(Song, self.song_id)
            assert song.video_type == "full_length"

    def test_set_video_type_short_form_success(self):
        """Test setting video_type to short_form succeeds."""
        response = self.client.patch(
            f"/api/v1/songs/{self.song_id}/video-type",
            json={"video_type": "short_form"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["video_type"] == "short_form"
        
        # Verify it's persisted
        with session_scope() as session:
            song = session.get(Song, self.song_id)
            assert song.video_type == "short_form"

    def test_set_video_type_invalid_value(self):
        """Test that invalid video_type returns 422 (Pydantic validation error)."""
        response = self.client.patch(
            f"/api/v1/songs/{self.song_id}/video-type",
            json={"video_type": "invalid"},
        )
        
        # FastAPI returns 422 for Pydantic validation errors
        assert response.status_code == 422
        # Check that the error detail mentions the validation issue
        detail = response.json().get("detail", [])
        assert isinstance(detail, list)
        # Find the error about video_type
        video_type_errors = [err for err in detail if "video_type" in str(err).lower()]
        assert len(video_type_errors) > 0

    def test_set_video_type_song_not_found(self):
        """Test that setting video_type for non-existent song returns 404."""
        fake_id = uuid4()
        response = self.client.patch(
            f"/api/v1/songs/{fake_id}/video-type",
            json={"video_type": "full_length"},
        )
        
        assert response.status_code == 404

    def test_set_video_type_after_analysis_fails(self):
        """Test that changing video_type after analysis returns 409."""
        # Create a complete analysis record with all required fields
        from app.schemas.analysis import SongAnalysis
        
        complete_analysis = SongAnalysis(
            durationSec=30.0,
            bpm=128.0,
            beatTimes=[i * 0.5 for i in range(60)],
            sections=[],
            moodPrimary="energetic",
            moodTags=["energetic"],
            moodVector={"energy": 0.8, "valence": 0.7, "danceability": 0.6, "tension": 0.5},
            primaryGenre="Electronic",
            subGenres=[],
            lyricsAvailable=False,
            sectionLyrics=[],
        )
        
        # Create analysis record with complete JSON
        with session_scope() as session:
            analysis_record = SongAnalysisRecord(
                song_id=self.song_id,
                analysis_json=complete_analysis.model_dump_json(by_alias=True),
                duration_sec=30.0,
                bpm=128.0,
            )
            session.add(analysis_record)
            session.commit()
        
        # Try to set video_type
        response = self.client.patch(
            f"/api/v1/songs/{self.song_id}/video-type",
            json={"video_type": "full_length"},
        )
        
        assert response.status_code == 409
        assert "analysis" in response.json()["detail"].lower()

    def test_update_video_type_before_analysis_succeeds(self):
        """Test that updating video_type before analysis succeeds."""
        # Set initial video_type
        response1 = self.client.patch(
            f"/api/v1/songs/{self.song_id}/video-type",
            json={"video_type": "full_length"},
        )
        assert response1.status_code == 200
        
        # Update to different type (before analysis)
        response2 = self.client.patch(
            f"/api/v1/songs/{self.song_id}/video-type",
            json={"video_type": "short_form"},
        )
        assert response2.status_code == 200
        assert response2.json()["video_type"] == "short_form"

    def test_video_type_in_song_read_response(self):
        """Test that video_type is included in GET /songs/{id} response."""
        # Set video_type
        self.client.patch(
            f"/api/v1/songs/{self.song_id}/video-type",
            json={"video_type": "full_length"},
        )
        
        # Get song
        response = self.client.get(f"/api/v1/songs/{self.song_id}")
        assert response.status_code == 200
        data = response.json()
        assert "video_type" in data
        assert data["video_type"] == "full_length"

