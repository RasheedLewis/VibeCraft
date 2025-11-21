from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.exceptions import JobNotFoundError
from app.schemas.job import JobStatusResponse
from app.services.clip_generation import get_clip_generation_job_status
from app.services.song_analysis import get_job_status

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusResponse, summary="Get job status")
def get_analysis_job(job_id: str) -> JobStatusResponse:
    # Check job ID format to route to the correct handler
    # Clip generation jobs use "clip-batch-" prefix, analysis jobs use "analysis-" prefix
    if job_id.startswith("clip-batch-") or job_id.startswith("clip-gen-"):
        try:
            return get_clip_generation_job_status(job_id)
        except JobNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    else:
        # Try analysis job first, then fall back to clip generation
        try:
            return get_job_status(job_id)
        except JobNotFoundError:
            try:
                return get_clip_generation_job_status(job_id)
            except JobNotFoundError as exc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


