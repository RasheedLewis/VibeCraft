"""Unit tests for clip retry functionality.

Tests retry logic with mocked repositories and queues - no database or Redis needed.
Covers state reset, error handling, and queue integration.

Run with: pytest backend/tests/unit/test_clip_retry.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

# Add backend directory to path for direct execution
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest  # noqa: E402
from app.exceptions import ClipNotFoundError  # noqa: E402
from app.models.clip import SongClip  # noqa: E402
from app.services.clip_generation import retry_clip_generation  # noqa: E402


class DummyJob:
    """Mock RQ job."""

    def __init__(self, job_id: str):
        self.id = job_id


class DummyQueue:
    """Mock RQ queue."""

    def __init__(self):
        self.enqueued_jobs = []

    def enqueue(self, func, clip_id, job_timeout=None, meta=None):
        job = DummyJob(f"job-{clip_id}")
        self.enqueued_jobs.append((func, clip_id, job_timeout, meta))
        return job


class TestRetryClipGeneration:
    """Test retry clip generation function."""

    @patch("app.services.clip_generation.get_queue")
    @patch("app.services.clip_generation.ClipRepository")
    @patch("app.services.clip_generation.get_settings")
    def test_clip_not_found(self, mock_get_settings, mock_repo, mock_get_queue):
        """Test that clip not found raises ValueError."""
        mock_settings = MagicMock()
        mock_settings.rq_worker_queue = "test-queue"
        mock_get_settings.return_value = mock_settings

        mock_repo.get_by_id.side_effect = ClipNotFoundError("Clip not found")

        with pytest.raises(ValueError, match="not found"):
            retry_clip_generation(uuid4())

    @patch("app.services.clip_generation.get_queue")
    @patch("app.services.clip_generation.ClipRepository")
    @patch("app.services.clip_generation.get_settings")
    def test_clip_already_processing(self, mock_get_settings, mock_repo, mock_get_queue):
        """Test that clip already processing raises RuntimeError."""
        mock_settings = MagicMock()
        mock_settings.rq_worker_queue = "test-queue"
        mock_get_settings.return_value = mock_settings

        clip = MagicMock(spec=SongClip)
        clip.status = "processing"
        clip.song_id = uuid4()
        clip.clip_index = 0
        clip.fps = 8
        clip.num_frames = 100
        clip.duration_sec = 10.0

        mock_repo.get_by_id.return_value = clip

        with pytest.raises(RuntimeError, match="already queued or processing"):
            retry_clip_generation(uuid4())

    @patch("app.services.clip_generation.get_queue")
    @patch("app.services.clip_generation.ClipRepository")
    @patch("app.services.clip_generation.get_settings")
    def test_clip_already_queued(self, mock_get_settings, mock_repo, mock_get_queue):
        """Test that clip already queued raises RuntimeError."""
        mock_settings = MagicMock()
        mock_settings.rq_worker_queue = "test-queue"
        mock_get_settings.return_value = mock_settings

        clip = MagicMock(spec=SongClip)
        clip.status = "queued"
        clip.song_id = uuid4()
        clip.clip_index = 0
        clip.fps = 8
        clip.num_frames = 100
        clip.duration_sec = 10.0

        mock_repo.get_by_id.return_value = clip

        with pytest.raises(RuntimeError, match="already queued or processing"):
            retry_clip_generation(uuid4())

    @patch("app.services.clip_generation.get_queue")
    @patch("app.services.clip_generation.ClipRepository")
    @patch("app.services.clip_generation.get_settings")
    def test_successful_retry(self, mock_get_settings, mock_repo, mock_get_queue):
        """Test successful retry resets state and enqueues job."""
        clip_id = uuid4()
        song_id = uuid4()

        mock_settings = MagicMock()
        mock_settings.rq_worker_queue = "test-queue"
        mock_get_settings.return_value = mock_settings

        # Create mock clip with all required fields
        clip = MagicMock(spec=SongClip)
        clip.id = clip_id
        clip.status = "failed"
        clip.error = "Some error"
        clip.video_url = "https://example.com/video.mp4"
        clip.replicate_job_id = "replicate-123"
        clip.rq_job_id = "old-job-123"
        clip.song_id = song_id
        clip.clip_index = 0
        clip.fps = 8
        clip.num_frames = 100
        clip.duration_sec = 10.0
        clip.start_sec = 0.0
        clip.end_sec = 10.0
        clip.start_beat_index = None
        clip.end_beat_index = None
        clip.source = "test"

        # Mock repository
        mock_repo.get_by_id.return_value = clip
        mock_repo.update.return_value = clip

        # Mock queue
        dummy_queue = DummyQueue()
        mock_get_queue.return_value = dummy_queue

        # Call retry
        retry_clip_generation(clip_id)

        # Verify state was reset (before rq_job_id is set)
        # Note: rq_job_id is set after enqueue, so we check it was updated
        assert clip.status == "queued"
        assert clip.error is None
        assert clip.video_url is None
        assert clip.replicate_job_id is None
        # rq_job_id should be set to the job ID after enqueue
        assert clip.rq_job_id is not None
        assert clip.rq_job_id == f"job-{clip_id}"

        # Verify repository update was called
        assert mock_repo.update.call_count == 2  # Once for reset, once for rq_job_id

        # Verify queue was called with correct parameters
        assert len(dummy_queue.enqueued_jobs) == 1
        enqueued_func, enqueued_clip_id, enqueued_timeout, enqueued_meta = dummy_queue.enqueued_jobs[0]
        assert enqueued_clip_id == clip_id
        assert enqueued_meta["song_id"] == str(song_id)
        assert enqueued_meta["clip_index"] == 0
        assert enqueued_meta["retry"] is True

        # Verify rq_job_id was set
        assert clip.rq_job_id == f"job-{clip_id}"

    @patch("app.services.clip_generation.get_queue")
    @patch("app.services.clip_generation.ClipRepository")
    @patch("app.services.clip_generation.get_settings")
    def test_num_frames_recalculated(self, mock_get_settings, mock_repo, mock_get_queue):
        """Test that num_frames is recalculated if <= 0."""
        clip_id = uuid4()
        song_id = uuid4()

        mock_settings = MagicMock()
        mock_settings.rq_worker_queue = "test-queue"
        mock_get_settings.return_value = mock_settings

        clip = MagicMock(spec=SongClip)
        clip.id = clip_id
        clip.status = "failed"
        clip.error = None
        clip.video_url = None
        clip.replicate_job_id = None
        clip.rq_job_id = None
        clip.song_id = song_id
        clip.clip_index = 0
        clip.fps = 8
        clip.num_frames = 0  # Zero frames
        clip.duration_sec = 10.0  # 10 seconds
        clip.start_sec = 0.0
        clip.end_sec = 10.0
        clip.start_beat_index = None
        clip.end_beat_index = None
        clip.source = "test"

        mock_repo.get_by_id.return_value = clip
        mock_repo.update.return_value = clip

        dummy_queue = DummyQueue()
        mock_get_queue.return_value = dummy_queue

        retry_clip_generation(clip_id)

        # num_frames should be recalculated: 10.0 * 8 = 80
        assert clip.num_frames == 80

    @patch("app.services.clip_generation.get_queue")
    @patch("app.services.clip_generation.ClipRepository")
    @patch("app.services.clip_generation.get_settings")
    def test_num_frames_minimum_one(self, mock_get_settings, mock_repo, mock_get_queue):
        """Test that num_frames is at least 1 even for very short clips."""
        clip_id = uuid4()
        song_id = uuid4()

        mock_settings = MagicMock()
        mock_settings.rq_worker_queue = "test-queue"
        mock_get_settings.return_value = mock_settings

        clip = MagicMock(spec=SongClip)
        clip.id = clip_id
        clip.status = "failed"
        clip.error = None
        clip.video_url = None
        clip.replicate_job_id = None
        clip.rq_job_id = None
        clip.song_id = song_id
        clip.clip_index = 0
        clip.fps = 8
        clip.num_frames = 0
        clip.duration_sec = 0.01  # Very short duration
        clip.start_sec = 0.0
        clip.end_sec = 0.01
        clip.start_beat_index = None
        clip.end_beat_index = None
        clip.source = "test"

        mock_repo.get_by_id.return_value = clip
        mock_repo.update.return_value = clip

        dummy_queue = DummyQueue()
        mock_get_queue.return_value = dummy_queue

        retry_clip_generation(clip_id)

        # num_frames should be at least 1
        assert clip.num_frames >= 1

    @patch("app.services.clip_generation.get_queue")
    @patch("app.services.clip_generation.ClipRepository")
    @patch("app.services.clip_generation.get_settings")
    def test_clip_disappears_after_enqueue(self, mock_get_settings, mock_repo, mock_get_queue):
        """Test that clip disappearing after enqueue raises ValueError."""
        clip_id = uuid4()
        song_id = uuid4()

        mock_settings = MagicMock()
        mock_settings.rq_worker_queue = "test-queue"
        mock_get_settings.return_value = mock_settings

        clip = MagicMock(spec=SongClip)
        clip.id = clip_id
        clip.status = "failed"
        clip.error = None
        clip.video_url = None
        clip.replicate_job_id = None
        clip.rq_job_id = None
        clip.song_id = song_id
        clip.clip_index = 0
        clip.fps = 8
        clip.num_frames = 100
        clip.duration_sec = 10.0

        # First call succeeds, second call (after enqueue) fails
        mock_repo.get_by_id.side_effect = [clip, ClipNotFoundError("Clip disappeared")]

        dummy_queue = DummyQueue()
        mock_get_queue.return_value = dummy_queue

        with pytest.raises(ValueError, match="disappeared after enqueue"):
            retry_clip_generation(clip_id)

    @patch("app.services.clip_generation.get_queue")
    @patch("app.services.clip_generation.ClipRepository")
    @patch("app.services.clip_generation.get_settings")
    def test_queue_name_with_suffix(self, mock_get_settings, mock_repo, mock_get_queue):
        """Test that queue name uses main queue (no :clip-generation suffix)."""
        clip_id = uuid4()
        song_id = uuid4()

        mock_settings = MagicMock()
        mock_settings.rq_worker_queue = "test-queue"
        mock_get_settings.return_value = mock_settings

        clip = MagicMock(spec=SongClip)
        clip.id = clip_id
        clip.status = "failed"
        clip.error = None
        clip.video_url = None
        clip.replicate_job_id = None
        clip.rq_job_id = None
        clip.song_id = song_id
        clip.clip_index = 0
        clip.fps = 8
        clip.num_frames = 100
        clip.duration_sec = 10.0
        clip.start_sec = 0.0
        clip.end_sec = 10.0
        clip.start_beat_index = None
        clip.end_beat_index = None
        clip.source = "test"  # Required string field

        mock_repo.get_by_id.return_value = clip
        mock_repo.update.return_value = clip

        dummy_queue = DummyQueue()
        mock_get_queue.return_value = dummy_queue

        retry_clip_generation(clip_id)

        # Verify queue was created with correct name (main queue, no suffix)
        mock_get_queue.assert_called_once()
        call_kwargs = mock_get_queue.call_args[1]
        assert call_kwargs["queue_name"] == "test-queue"

