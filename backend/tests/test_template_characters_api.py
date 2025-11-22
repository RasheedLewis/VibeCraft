"""Tests for template characters API endpoints.

Tests the GET /api/v1/template-characters and POST /api/v1/songs/{song_id}/character-image/template
endpoints including validation, error cases, and successful operations.
"""

from __future__ import annotations

from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.database import init_db, session_scope
from app.main import create_app
from app.models.song import DEFAULT_USER_ID, Song

init_db()


def _cleanup_song(song_id: uuid4) -> None:
    """Clean up test song and related records."""
    with session_scope() as session:
        song = session.get(Song, song_id)
        if song:
            session.delete(song)
        session.commit()


class TestListTemplateCharacters:
    """Tests for GET /api/v1/template-characters endpoint."""

    @patch("app.api.v1.routes_template_characters.get_template_characters")
    def test_list_template_characters_success(self, mock_get_templates):
        """Test successful listing of template characters."""
        mock_get_templates.return_value = [
            {
                "id": "character-1",
                "name": "Test Character",
                "description": "Test description",
                "poses": [
                    {
                        "id": "pose-a",
                        "thumbnail_url": "https://example.com/a.jpg",
                        "image_url": "https://example.com/a.jpg",
                    },
                    {
                        "id": "pose-b",
                        "thumbnail_url": "https://example.com/b.jpg",
                        "image_url": "https://example.com/b.jpg",
                    },
                ],
                "default_pose": "pose-a",
            }
        ]

        with TestClient(create_app()) as client:
            response = client.get("/api/v1/template-characters")

            assert response.status_code == 200
            data = response.json()
            assert "templates" in data
            assert len(data["templates"]) == 1
            assert data["templates"][0]["id"] == "character-1"
            assert len(data["templates"][0]["poses"]) == 2

    @patch("app.api.v1.routes_template_characters.get_template_characters")
    def test_list_template_characters_empty(self, mock_get_templates):
        """Test listing when no templates are available."""
        mock_get_templates.return_value = []

        with TestClient(create_app()) as client:
            response = client.get("/api/v1/template-characters")

            assert response.status_code == 200
            data = response.json()
            assert "templates" in data
            assert len(data["templates"]) == 0


class TestApplyTemplateCharacter:
    """Tests for POST /api/v1/songs/{song_id}/character-image/template endpoint."""

    def setup_method(self):
        """Set up test song."""
        self.song_id = uuid4()
        with session_scope() as session:
            song = Song(
                id=self.song_id,
                user_id=DEFAULT_USER_ID,
                title="Test Song",
                original_filename="test.mp3",
                original_file_size=1024,
                original_s3_key="songs/test/original.mp3",
                processed_s3_key="songs/test/processed.mp3",
                duration_sec=30.0,
                video_type="short_form",
            )
            session.add(song)
            session.commit()

    def teardown_method(self):
        """Clean up test song."""
        _cleanup_song(self.song_id)

    @patch("app.api.v1.routes_template_characters.get_template_character")
    @patch("app.api.v1.routes_template_characters.get_template_character_image")
    @patch("app.api.v1.routes_template_characters.upload_bytes_to_s3")
    @patch("app.api.v1.routes_template_characters.generate_presigned_get_url")
    @patch("app.api.v1.routes_template_characters.asyncio.to_thread")
    def test_apply_template_character_success(
        self,
        mock_to_thread,
        mock_presigned_url,
        mock_upload,
        mock_get_image,
        mock_get_character,
    ):
        """Test successful application of template character."""
        mock_get_character.return_value = {
            "id": "character-1",
            "name": "Test Character",
            "poses": {
                "pose-a": "template-characters/character1-pose1.png",
                "pose-b": "template-characters/character1-pose2.png",
            },
            "default_pose": "pose-a",
        }
        mock_get_image.side_effect = [b"pose-a-bytes", b"pose-b-bytes"]
        mock_to_thread.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs)
        mock_presigned_url.return_value = "https://s3.example.com/presigned-url"

        with TestClient(create_app()) as client:
            response = client.post(
                f"/api/v1/songs/{self.song_id}/character-image/template",
                json={"character_id": "character-1"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["character_id"] == "character-1"
            assert data["character_consistency_enabled"] is True
            assert "image_s3_key" in data
            assert "pose_b_s3_key" in data

            # Verify database was updated
            with session_scope() as session:
                song = session.get(Song, self.song_id)
                assert song.character_consistency_enabled is True
                assert song.character_reference_image_s3_key is not None
                assert song.character_pose_b_s3_key is not None

    def test_apply_template_character_song_not_found(self):
        """Test applying template to non-existent song."""
        fake_song_id = uuid4()

        with TestClient(create_app()) as client:
            response = client.post(
                f"/api/v1/songs/{fake_song_id}/character-image/template",
                json={"character_id": "character-1"},
            )

            assert response.status_code == 404

    def test_apply_template_character_invalid_character(self):
        """Test applying invalid character ID."""
        with TestClient(create_app()) as client:
            response = client.post(
                f"/api/v1/songs/{self.song_id}/character-image/template",
                json={"character_id": "character-999"},
            )

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_apply_template_character_wrong_video_type(self):
        """Test applying template to non-short_form video."""
        with session_scope() as session:
            song = session.get(Song, self.song_id)
            song.video_type = "full_length"
            session.commit()

        with TestClient(create_app()) as client:
            response = client.post(
                f"/api/v1/songs/{self.song_id}/character-image/template",
                json={"character_id": "character-1"},
            )

            assert response.status_code == 400
            assert "short_form" in response.json()["detail"].lower()

    @patch("app.api.v1.routes_template_characters.get_template_character")
    @patch("app.api.v1.routes_template_characters.get_template_character_image")
    @patch("app.api.v1.routes_template_characters.upload_bytes_to_s3")
    @patch("app.api.v1.routes_template_characters.asyncio.to_thread")
    def test_apply_template_character_stores_both_poses(
        self,
        mock_to_thread,
        mock_upload,
        mock_get_image,
        mock_get_character,
    ):
        """Test that both poses are stored when applying template."""
        mock_get_character.return_value = {
            "id": "character-1",
            "poses": {
                "pose-a": "template-characters/character1-pose1.png",
                "pose-b": "template-characters/character1-pose2.png",
            },
            "default_pose": "pose-a",
        }
        mock_get_image.side_effect = [b"pose-a-bytes", b"pose-b-bytes"]
        mock_to_thread.side_effect = lambda fn, *args, **kwargs: fn(*args, **kwargs)

        with TestClient(create_app()) as client:
            response = client.post(
                f"/api/v1/songs/{self.song_id}/character-image/template",
                json={"character_id": "character-1"},
            )

            assert response.status_code == 200

            # Verify both poses were uploaded
            assert mock_upload.call_count == 2
            upload_keys = [call.kwargs["key"] for call in mock_upload.call_args_list]
            assert any("character_reference" in key for key in upload_keys)
            assert any("character_pose_b" in key for key in upload_keys)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])

