"""Base job management utilities."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from sqlmodel import SQLModel

from app.core.database import session_scope

JobModel = TypeVar("JobModel", bound=SQLModel)


class BaseJobService(ABC, Generic[JobModel]):
    """Base class for job management services."""

    @abstractmethod
    def get_job_model(self) -> type[JobModel]:
        """Return the job model class."""
        pass

    def update_progress(self, job_id: str, progress: int, status: str | None = None) -> None:
        """
        Update job progress.

        Args:
            job_id: Job ID
            progress: Progress percentage (0-100)
            status: Optional status to update
        """
        with session_scope() as session:
            job = session.get(self.get_job_model(), job_id)
            if not job:
                return

            job.progress = max(0, min(100, progress))
            if status:
                job.status = status
            elif hasattr(job, "status") and getattr(job, "status") == "queued":
                job.status = "processing"

            session.add(job)
            session.commit()

    def complete_job(self, job_id: str, **kwargs) -> None:
        """
        Mark job as completed.

        Args:
            job_id: Job ID
            **kwargs: Additional fields to update (e.g., result_id)
        """
        with session_scope() as session:
            job = session.get(self.get_job_model(), job_id)
            if not job:
                return

            job.status = "completed"
            job.progress = 100

            # Update any additional fields
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)

            session.add(job)
            session.commit()

    def fail_job(self, job_id: str, error_message: str) -> None:
        """
        Mark job as failed.

        Args:
            job_id: Job ID
            error_message: Error message
        """
        with session_scope() as session:
            job = session.get(self.get_job_model(), job_id)
            if not job:
                return

            job.status = "failed"
            if hasattr(job, "error"):
                job.error = error_message
            # Don't reset progress, keep it at current value

            session.add(job)
            session.commit()

