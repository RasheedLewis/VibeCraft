"""Tests for audio selection API endpoint.

Tests the PATCH /songs/{song_id}/selection endpoint including validation,
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
from app.schemas.analysis import SongAnalysis

init_db()


def make_analysis(beat_times: list[float]) -> SongAnalysis:
    return SongAnalysis(
        durationSec=max(beat_times) + 0.5 if beat_times else 30.0,
        bpm=120.0,
        beatTimes=beat_times,
        sections=[],
        moodPrimary="energetic",
        moodTags=[],
        moodVector={"energy": 0.8, "valence": 0.6, "danceability": 0.7, "tension": 0.4},
        primaryGenre="Test",
        subGenres=[],
        lyricsAvailable=False,
        sectionLyrics=[],
    )


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


class TestAudioSelectionEndpoint:
    """Tests for PATCH /songs/{song_id}/selection endpoint."""

    def test_update_selection_success(self):
        """Test successful selection update."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 10.0, "end_sec": 40.0},
                )
                assert response.status_code == 200, response.text
                data = response.json()
                assert data["selected_start_sec"] == 10.0
                assert data["selected_end_sec"] == 40.0

                # Verify persistence
                with session_scope() as session:
                    song = session.get(Song, song_id)
                    assert song is not None
                    assert song.selected_start_sec == 10.0
                    assert song.selected_end_sec == 40.0
        finally:
            _cleanup_song(song_id)

    def test_update_selection_song_not_found(self):
        """Test selection update on non-existent song."""
        fake_song_id = uuid4()

        with TestClient(create_app()) as client:
            response = client.patch(
                f"/api/v1/songs/{fake_song_id}/selection",
                json={"start_sec": 10.0, "end_sec": 40.0},
            )
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_update_selection_no_duration(self):
        """Test selection update when song has no duration."""
        song_id = uuid4()

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=None,  # No duration
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 10.0, "end_sec": 40.0},
                )
                assert response.status_code == 400
                assert "duration not available" in response.json()["detail"].lower()
        finally:
            _cleanup_song(song_id)

    def test_update_selection_exceeds_song_duration(self):
        """Test selection that exceeds song duration."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                # Note: This will be caught by Pydantic validation first (duration > 30s)
                # so it returns 422, not 400
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 10.0, "end_sec": 70.0},  # Duration 60s exceeds 30s max
                )
                assert response.status_code == 422  # Pydantic validation error
                assert "exceeds maximum" in response.json()["detail"][0]["msg"].lower()
                
                # Test case where duration is valid but end exceeds song duration
                response2 = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 35.0, "end_sec": 70.0},  # Duration 35s exceeds 30s, but also exceeds song
                )
                assert response2.status_code == 422  # Still caught by Pydantic (duration > 30s)
                
                # Test case that passes Pydantic but fails endpoint validation
                response3 = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 35.0, "end_sec": 65.0},  # Duration 30s OK, but end > song duration
                )
                assert response3.status_code == 400  # Endpoint validation error
                assert "exceeds song duration" in response3.json()["detail"].lower()
        finally:
            _cleanup_song(song_id)

    def test_update_selection_exceeds_30s(self):
        """Test selection that exceeds 30 second maximum."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 10.0, "end_sec": 45.0},  # 35s duration
                )
                assert response.status_code == 422  # Pydantic validation error
                detail = response.json()["detail"][0]["msg"]
                assert "exceeds maximum" in detail.lower()
                assert "30" in detail
        finally:
            _cleanup_song(song_id)

    def test_update_selection_below_1s(self):
        """Test selection that is below 1 second minimum."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 10.0, "end_sec": 10.5},  # 0.5s duration
                )
                assert response.status_code == 422  # Pydantic validation error
                detail = response.json()["detail"][0]["msg"]
                assert "below minimum" in detail.lower()
                assert "1" in detail
        finally:
            _cleanup_song(song_id)

    def test_update_selection_end_before_start(self):
        """Test selection where end is before start."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 20.0, "end_sec": 10.0},  # End before start
                )
                assert response.status_code == 422  # Pydantic validation error
                detail = response.json()["detail"][0]["msg"]
                assert "greater than start" in detail.lower() or "end_sec must be greater" in detail.lower()
        finally:
            _cleanup_song(song_id)

    def test_update_selection_negative_start(self):
        """Test selection with negative start time."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": -5.0, "end_sec": 30.0},
                )
                assert response.status_code == 422  # Pydantic Field validation error
                detail = response.json()["detail"][0]["msg"]
                assert "greater than or equal" in detail.lower() or "ge" in detail.lower()
        finally:
            _cleanup_song(song_id)

    def test_update_selection_boundary_30s(self):
        """Test selection at exactly 30 seconds (boundary condition)."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 10.0, "end_sec": 40.0},  # Exactly 30s
                )
                assert response.status_code == 200
                data = response.json()
                assert data["selected_start_sec"] == 10.0
                assert data["selected_end_sec"] == 40.0
        finally:
            _cleanup_song(song_id)

    def test_update_selection_boundary_1s(self):
        """Test selection at exactly 1 second (boundary condition)."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 10.0, "end_sec": 11.0},  # Exactly 1s
                )
                assert response.status_code == 200
                data = response.json()
                assert data["selected_start_sec"] == 10.0
                assert data["selected_end_sec"] == 11.0
        finally:
            _cleanup_song(song_id)

    def test_update_selection_short_song(self):
        """Test selection on song shorter than 30 seconds."""
        song_id = uuid4()
        song_duration = 15.0  # Shorter than 30s

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                # Should allow selection of entire song (15s)
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 0.0, "end_sec": 15.0},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["selected_start_sec"] == 0.0
                assert data["selected_end_sec"] == 15.0
        finally:
            _cleanup_song(song_id)

    def test_update_selection_at_song_start(self):
        """Test selection starting at 0 seconds."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 0.0, "end_sec": 30.0},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["selected_start_sec"] == 0.0
                assert data["selected_end_sec"] == 30.0
        finally:
            _cleanup_song(song_id)

    def test_update_selection_at_song_end(self):
        """Test selection ending at song duration."""
        song_id = uuid4()
        song_duration = 60.0

        with session_scope() as session:
            song = Song(
                id=song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.wav",
                original_file_size=2048,
                original_s3_key="s3://test/test.wav",
                duration_sec=song_duration,
            )
            session.add(song)
            session.commit()

        try:
            with TestClient(create_app()) as client:
                response = client.patch(
                    f"/api/v1/songs/{song_id}/selection",
                    json={"start_sec": 30.0, "end_sec": 60.0},
                )
                assert response.status_code == 200
                data = response.json()
                assert data["selected_start_sec"] == 30.0
                assert data["selected_end_sec"] == 60.0
        finally:
            _cleanup_song(song_id)

