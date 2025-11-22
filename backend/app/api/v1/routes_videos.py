"""Video generation API routes."""

import logging
import random

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlmodel import Session, select

from app.api.deps import get_db
from app.core.config import is_sections_enabled
from app.models.section_video import SectionVideo
from app.models.song import DEFAULT_USER_ID, Song
from app.schemas.section_video import (
    SectionVideoGenerateRequest,
    SectionVideoGenerateResponse,
    SectionVideoRead,
)
from app.services.scene_planner import build_scene_spec
from app.services.video_generation import generate_section_video

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sections", tags=["videos"])


@router.post(
    "/{section_id}/generate",
    response_model=SectionVideoGenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_section_video_endpoint(
    section_id: str,
    request: SectionVideoGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> SectionVideoGenerateResponse:
    """
    Generate a video for a section.

    Args:
        section_id: Section identifier
        request: Request body with optional template
        db: Database session

    Returns:
        SectionVideoGenerateResponse with job status
    """
    # Check if sections are enabled
    if not is_sections_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Section-based video generation is disabled. Use direct clip generation instead.",
        )

    # Validate section_id matches request
    if section_id != request.section_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Section ID in path must match request body",
        )

    # Build scene spec (uses mock analysis for now)
    try:
        scene_spec = build_scene_spec(
            section_id=section_id,
            analysis=None,  # Uses mock data until PR-04 complete
            template=request.template or "abstract",
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Get or create a test song for mock sections (until PR-04 provides real song_id)
    # In production, song_id will come from the request or section lookup
    test_song = db.exec(select(Song)).first()
    if not test_song:
        # Create a test song if none exists
        test_song = Song(
            user_id=DEFAULT_USER_ID,
            title="Test Song (Mock)",
            original_filename="test.mp3",
            original_file_size=0,
            original_s3_key="test/test.mp3",
        )
        db.add(test_song)
        db.commit()
        db.refresh(test_song)
    song_id = test_song.id

    # Check if video already exists for this section (completed or failed)
    existing = db.exec(
        select(SectionVideo).where(
            SectionVideo.section_id == section_id,
        ).order_by(SectionVideo.created_at.desc())
    ).first()

    if existing and existing.status == "completed":
        return SectionVideoGenerateResponse(
            section_video_id=existing.id,
            status="completed",
            message="Video already exists for this section",
        )
    
    # If previous attempt failed, allow retry (will create new record)

    # Generate seed for reproducibility
    seed = random.randint(0, 2**31 - 1)

    # Create SectionVideo record (one video per section)
    # Note: sectionVideoId is the database record ID, not multiple API calls
    section_video = SectionVideo(
        song_id=song_id,
        section_id=section_id,
        template=scene_spec.template,
        prompt=scene_spec.prompt,
        duration_sec=scene_spec.duration_sec,
        seed=seed,
        status="processing",
    )
    db.add(section_video)
    db.commit()
    db.refresh(section_video)

    # Start video generation in background (returns 202 immediately)
    async def generate_video_background():
        """Background task to generate video and update database."""
        # Get a new database session for background task
        from app.core.database import get_session

        for session in get_session():
            try:
                # Reload section_video in this session
                db_section_video = session.get(SectionVideo, section_video.id)
                if not db_section_video:
                    logger.error(f"SectionVideo {section_video.id} not found in background task")
                    return

                # Generate video
                success, video_url, metadata = generate_section_video(
                    scene_spec=scene_spec,
                    seed=seed,
                )

                # Update SectionVideo record
                # Always store replicate_job_id (even on failure) so we can check Replicate later
                if metadata and metadata.get("job_id"):
                    db_section_video.replicate_job_id = metadata.get("job_id")
                
                if success and video_url:
                    db_section_video.video_url = video_url
                    db_section_video.status = "completed"
                    db_section_video.fps = metadata.get("fps")
                    db_section_video.resolution_width = metadata.get("resolution_width")
                    db_section_video.resolution_height = metadata.get("resolution_height")
                else:
                    db_section_video.status = "failed"
                    db_section_video.error_message = metadata.get("error", "Unknown error") if metadata else "Generation failed"

                session.add(db_section_video)
                session.commit()
            except Exception as e:
                logger.error(f"Error in background video generation: {e}", exc_info=True)
                # Update status to failed (but we won't have job_id if exception happened before generation started)
                try:
                    db_section_video = session.get(SectionVideo, section_video.id)
                    if db_section_video:
                        db_section_video.status = "failed"
                        db_section_video.error_message = str(e)
                        # Note: replicate_job_id won't be set if exception happened before job creation
                        session.add(db_section_video)
                        session.commit()
                except Exception:
                    pass
            # Exit the generator after first iteration
            break

    # Add background task
    background_tasks.add_task(generate_video_background)

    # Return immediately with 202 Accepted
    return SectionVideoGenerateResponse(
        section_video_id=section_video.id,
        status="processing",
        message="Video generation started",
    )


@router.get("/{section_id}/video", response_model=SectionVideoRead)
async def get_section_video(
    section_id: str,
    db: Session = Depends(get_db),
) -> SectionVideoRead:
    """
    Get the generated video for a section (or check status if still processing).

    Args:
        section_id: Section identifier
        db: Database session

    Returns:
        SectionVideoRead with video details (includes videoUrl if completed)
    """
    # Check if sections are enabled
    if not is_sections_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Section-based video generation is disabled. Use direct clip generation instead.",
        )
    # Get the most recent video for this section (any status)
    section_video = db.exec(
        select(SectionVideo).where(SectionVideo.section_id == section_id).order_by(SectionVideo.created_at.desc())
    ).first()

    if not section_video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No video found for section {section_id}",
        )

    return SectionVideoRead.model_validate(section_video)

