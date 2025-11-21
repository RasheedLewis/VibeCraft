#!/usr/bin/env python3
"""
Mock Backend Server for Frontend Testing

OVERVIEW:
---------
This script provides a complete mock FastAPI server that simulates the VibeCraft backend
pipelines to makes it easy to test frontend changes quickly.

USAGE: `python scripts/mock_backend.py`

- Run in one command, no configuration required
- Option to add mock delays to more realistically simulate backend job processing
- Preserves progress updates (0-100%)
- Runs on localhost:3000 (hardcoded)
- Mocks all these API endpoints
   - POST /api/v1/songs/ - Upload a song
   - POST /api/v1/songs/{id}/analyze - Start analysis
   - GET  /api/v1/songs/{id}/analysis - Get analysis results
   - POST /api/v1/songs/{id}/clips/plan - Plan clips
   - POST /api/v1/songs/{id}/clips/generate - Generate clips
   - GET  /api/v1/songs/{id}/clips/status - Get clip status
   - POST /api/v1/songs/{id}/clips/compose/async - Compose video
   - GET  /api/v1/songs/{id}/compose/{job_id}/status - Get composition status
   - GET  /api/v1/jobs/{job_id} - Get job status
"""


import asyncio
import json
import logging
import os
import signal
import subprocess
import sys
import time
import uuid
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="VibeCraft Mock Backend", version="1.0.0")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory state storage
songs: Dict[UUID, dict] = {}
analyses: Dict[UUID, dict] = {}
jobs: Dict[str, dict] = {}
clips: Dict[UUID, List[dict]] = {}
composed_videos: Dict[UUID, dict] = {}

# Configuration
MOCK_DELAYS = {
    "analysis": 0.0,  # seconds to simulate analysis (0 = instant)
    "clip_generation": 0.0,  # seconds per clip (0 = instant)
    "composition": 0.0,  # seconds for composition (0 = instant)
}
PORT = 3000  # Server port (hardcoded)

# Mock video URLs (placeholder videos)
MOCK_VIDEO_URL = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
MOCK_AUDIO_URL = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"


def generate_mock_analysis(song_id: UUID, duration_sec: float) -> dict:
    """Generate a mock song analysis."""
    bpm = 120.0
    beat_interval = 60.0 / bpm
    beat_times = [i * beat_interval for i in range(int(duration_sec / beat_interval) + 1)]
    
    # Generate sections
    sections = []
    section_types = ["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus", "outro"]
    section_duration = duration_sec / len(section_types)
    
    for i, section_type in enumerate(section_types):
        start_sec = i * section_duration
        end_sec = min((i + 1) * section_duration, duration_sec)
        sections.append({
            "id": f"section_{i}",
            "type": section_type,
            "startSec": start_sec,
            "endSec": end_sec,
            "confidence": 0.85,
            "repetitionGroup": "group_1" if section_type == "chorus" else None,
        })
    
    return {
        "durationSec": duration_sec,
        "bpm": bpm,
        "beatTimes": beat_times[:int(duration_sec / beat_interval) + 1],
        "sections": sections,
        "moodPrimary": "energetic",
        "moodTags": ["energetic", "upbeat", "danceable"],
        "moodVector": {
            "energy": 0.8,
            "valence": 0.7,
            "danceability": 0.85,
            "tension": 0.3,
        },
        "primaryGenre": "electronic",
        "subGenres": ["house", "dance"],
        "lyricsAvailable": False,
        "sectionLyrics": None,
    }


def generate_mock_clip_boundaries(duration_sec: float, clip_count: int = 5) -> List[dict]:
    """Generate mock clip boundaries."""
    boundaries = []
    clip_duration = duration_sec / clip_count
    
    for i in range(clip_count):
        start_time = i * clip_duration
        end_time = min((i + 1) * clip_duration, duration_sec)
        start_beat = int(start_time * 2)  # Assuming 120 BPM = 2 beats/sec
        end_beat = int(end_time * 2)
        
        boundaries.append({
            "startTime": start_time,
            "endTime": end_time,
            "startBeatIndex": start_beat,
            "endBeatIndex": end_beat,
            "startFrameIndex": int(start_time * 8),  # 8 FPS
            "endFrameIndex": int(end_time * 8),
            "startAlignmentError": 0.01,
            "endAlignmentError": 0.01,
            "durationSec": end_time - start_time,
            "beatsInClip": list(range(start_beat, end_beat)),
        })
    
    return boundaries


@app.get("/healthz")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api/v1/songs/")
async def list_songs():
    """List all songs."""
    return [songs[song_id] for song_id in sorted(songs.keys(), reverse=True)]


@app.post("/api/v1/songs/", status_code=status.HTTP_201_CREATED)
async def upload_song(file: UploadFile = File(...)):
    """Mock song upload endpoint."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    # Simulate file processing (instant with 0 delays)
    
    song_id = uuid4()
    song_title = file.filename.rsplit(".", 1)[0] if "." in file.filename else file.filename
    
    # Mock duration (30 seconds)
    duration_sec = 30.0
    
    song = {
        "id": str(song_id),
        "userId": "mock_user",
        "title": song_title,
        "originalFilename": file.filename,
        "originalFileSize": 5000000,  # 5MB mock
        "originalContentType": file.content_type or "audio/mpeg",
        "originalS3Key": f"songs/{song_id}/original.mp3",
        "processedS3Key": f"songs/{song_id}/processed.mp3",
        "processedSampleRate": 44100,
        "waveformJson": json.dumps([0.1, 0.3, 0.5, 0.7, 0.5, 0.3, 0.1] * 100),
        "durationSec": duration_sec,
        "description": None,
        "attribution": None,
        "composedVideoS3Key": None,
        "composedVideoPosterS3Key": None,
        "composedVideoDurationSec": None,
        "composedVideoFps": None,
        "createdAt": datetime.now().isoformat(),
        "updatedAt": datetime.now().isoformat(),
    }
    
    songs[song_id] = song
    
    return {
        "songId": str(song_id),
        "audioUrl": MOCK_AUDIO_URL,
        "s3Key": f"songs/{song_id}/original.mp3",
        "status": "uploaded",
    }


@app.get("/api/v1/songs/{song_id}")
async def get_song(song_id: UUID):
    """Get song details."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    return songs[song_id]


@app.post("/api/v1/songs/{song_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_song(song_id: UUID):
    """Mock song analysis endpoint - enqueues analysis job."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    
    job_id = f"analysis_{uuid4()}"
    song = songs[song_id]
    
    jobs[job_id] = {
        "jobId": job_id,
        "songId": str(song_id),
        "status": "queued",
        "progress": 0,
        "type": "analysis",
        "started_at": time.time(),
    }
    
    # Simulate analysis in background
    asyncio.create_task(simulate_analysis(song_id, job_id))
    
    return {
        "jobId": job_id,
        "songId": str(song_id),
        "status": "queued",
    }


async def simulate_analysis(song_id: UUID, job_id: str):
    """Simulate song analysis with realistic delays."""
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["progress"] = 20
    
    await asyncio.sleep(MOCK_DELAYS["analysis"] * 0.3)
    jobs[job_id]["progress"] = 50
    
    await asyncio.sleep(MOCK_DELAYS["analysis"] * 0.3)
    jobs[job_id]["progress"] = 80
    
    await asyncio.sleep(MOCK_DELAYS["analysis"] * 0.4)
    
    # Generate and store analysis
    song = songs[song_id]
    analysis = generate_mock_analysis(song_id, song["durationSec"])
    analyses[song_id] = analysis
    
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["progress"] = 100
    jobs[job_id]["analysisId"] = str(uuid4())
    jobs[job_id]["result"] = analysis


@app.get("/api/v1/songs/{song_id}/analysis")
async def get_song_analysis(song_id: UUID):
    """Get song analysis."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    if song_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found. Trigger analysis first.")
    return analyses[song_id]


@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id].copy()
    if job.get("type") == "analysis" and job.get("status") == "completed":
        job["result"] = analyses[UUID(job["songId"])]
    
    return job


@app.get("/api/v1/songs/{song_id}/beat-aligned-boundaries")
async def get_beat_aligned_boundaries(
    song_id: UUID,
    fps: float = Query(24.0, ge=1.0),
):
    """Get beat-aligned clip boundaries."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    if song_id not in analyses:
        raise HTTPException(status_code=404, detail="Analysis not found. Trigger analysis first.")
    
    analysis = analyses[song_id]
    boundaries = generate_mock_clip_boundaries(analysis["durationSec"])
    
    return {
        "boundaries": boundaries,
        "clipCount": len(boundaries),
        "songDuration": analysis["durationSec"],
        "bpm": analysis["bpm"],
        "fps": fps,
        "totalBeats": len(analysis["beatTimes"]),
        "maxAlignmentError": 0.05,
        "avgAlignmentError": 0.02,
        "validationStatus": "valid",
    }


@app.post("/api/v1/songs/{song_id}/clips/plan", status_code=status.HTTP_202_ACCEPTED)
async def plan_clips_for_song(
    song_id: UUID,
    clip_count: Optional[int] = Query(None, ge=1, le=64),
    min_clip_sec: float = Query(3.0, ge=0.5),
    max_clip_sec: float = Query(6.0, ge=1.0),
):
    """Plan clips for a song."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    if song_id not in analyses:
        raise HTTPException(status_code=409, detail="Analysis not found. Run analysis before planning clips.")
    
    analysis = analyses[song_id]
    duration_sec = analysis["durationSec"]
    
    # Calculate clip count if not provided
    if clip_count is None:
        clip_count = max(3, int(duration_sec / max_clip_sec))
    
    # Generate mock clip plans
    boundaries = generate_mock_clip_boundaries(duration_sec, clip_count)
    clip_plans = []
    
    for i, boundary in enumerate(boundaries):
        clip_id = uuid4()
        clip_plans.append({
            "id": str(clip_id),
            "songId": str(song_id),
            "clipIndex": i,
            "startSec": boundary["startTime"],
            "endSec": boundary["endTime"],
            "durationSec": boundary["durationSec"],
            "startBeat": boundary["startBeatIndex"],
            "endBeat": boundary["endBeatIndex"],
            "numFrames": int(boundary["durationSec"] * 8),  # 8 FPS
            "fps": 8,
            "status": "planned",
            "source": "beat",
            "videoUrl": None,
            "prompt": f"Visual representation of {analysis['moodPrimary']} {analysis['primaryGenre']} music",
            "styleSeed": None,
            "rqJobId": None,
            "replicateJobId": None,
            "error": None,
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
        })
    
    clips[song_id] = clip_plans
    
    return {"clipsPlanned": len(clip_plans)}


@app.get("/api/v1/songs/{song_id}/clips")
async def list_planned_clips(song_id: UUID):
    """List planned clips for a song."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    
    if song_id not in clips:
        return []
    
    return clips[song_id]


@app.get("/api/v1/songs/{song_id}/clips/status")
async def get_clip_generation_status(song_id: UUID):
    """Get clip generation status."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    
    song = songs[song_id]
    song_clips = clips.get(song_id, [])
    
    completed = sum(1 for clip in song_clips if clip["status"] == "completed")
    failed = sum(1 for clip in song_clips if clip["status"] == "failed")
    processing = sum(1 for clip in song_clips if clip["status"] == "processing")
    queued = sum(1 for clip in song_clips if clip["status"] in ["planned", "queued"])
    
    total = len(song_clips)
    progress_total = total * 100 if total > 0 else 0
    progress_completed = completed * 100
    
    clip_statuses = [
        {
            "id": clip["id"],
            "clipIndex": clip["clipIndex"],
            "startSec": clip["startSec"],
            "endSec": clip["endSec"],
            "durationSec": clip["durationSec"],
            "startBeat": clip.get("startBeat"),
            "endBeat": clip.get("endBeat"),
            "status": clip["status"],
            "source": clip["source"],
            "numFrames": clip["numFrames"],
            "fps": clip["fps"],
            "videoUrl": clip.get("videoUrl"),
            "rqJobId": clip.get("rqJobId"),
            "replicateJobId": clip.get("replicateJobId"),
            "error": clip.get("error"),
        }
        for clip in song_clips
    ]
    
    return {
        "songId": str(song_id),
        "songDurationSec": song["durationSec"],
        "totalClips": total,
        "completedClips": completed,
        "failedClips": failed,
        "processingClips": processing,
        "queuedClips": queued,
        "progressCompleted": progress_completed,
        "progressTotal": progress_total,
        "clips": clip_statuses,
        "analysis": analyses.get(song_id),
        "composedVideoUrl": composed_videos.get(song_id, {}).get("videoUrl"),
        "composedVideoPosterUrl": composed_videos.get(song_id, {}).get("posterUrl"),
    }


@app.post("/api/v1/songs/{song_id}/clips/generate", status_code=status.HTTP_202_ACCEPTED)
async def generate_clip_batch(
    song_id: UUID,
    max_parallel: int = Query(2, ge=1, le=8),
):
    """Start clip generation job."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    if song_id not in clips:
        raise HTTPException(status_code=409, detail="No clip plans found. Plan clips first.")
    
    job_id = f"clip_gen_{uuid4()}"
    
    jobs[job_id] = {
        "jobId": job_id,
        "songId": str(song_id),
        "status": "queued",
        "progress": 0,
        "type": "clip_generation",
        "started_at": time.time(),
    }
    
    # Simulate clip generation in background
    asyncio.create_task(simulate_clip_generation(song_id, job_id, max_parallel))
    
    return {
        "jobId": job_id,
        "songId": str(song_id),
        "status": "queued",
    }


async def simulate_clip_generation(song_id: UUID, job_id: str, max_parallel: int):
    """Simulate clip generation with realistic delays."""
    jobs[job_id]["status"] = "processing"
    song_clips = clips[song_id]
    total_clips = len(song_clips)
    
    # Process clips in batches
    for i, clip in enumerate(song_clips):
        clip["status"] = "processing"
        clip["rqJobId"] = f"rq_{uuid4()}"
        clip["replicateJobId"] = f"rep_{uuid4()}"
        
        # Simulate generation delay
        await asyncio.sleep(MOCK_DELAYS["clip_generation"])
        
        clip["status"] = "completed"
        clip["videoUrl"] = MOCK_VIDEO_URL
        clip["updatedAt"] = datetime.now().isoformat()
        
        # Update job progress
        progress = int((i + 1) / total_clips * 100)
        jobs[job_id]["progress"] = progress
    
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["progress"] = 100


@app.post("/api/v1/songs/{song_id}/clips/compose/async", status_code=status.HTTP_202_ACCEPTED)
async def compose_song_clips_async(song_id: UUID):
    """Enqueue async composition job."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    if song_id not in clips:
        raise HTTPException(status_code=404, detail="No clip plans found for this song.")
    
    song_clips = clips[song_id]
    total = len(song_clips)
    completed = sum(1 for clip in song_clips if clip["status"] == "completed")
    
    if total == 0:
        raise HTTPException(status_code=409, detail="No clips available for composition.")
    if completed != total:
        raise HTTPException(status_code=409, detail="Clip generation must be complete before composing.")
    
    if song_id in composed_videos:
        raise HTTPException(status_code=409, detail="Video already composed. Refresh to see the result.")
    
    job_id = f"compose_{uuid4()}"
    
    jobs[job_id] = {
        "jobId": job_id,
        "songId": str(song_id),
        "status": "queued",
        "progress": 0,
        "type": "composition",
        "started_at": time.time(),
    }
    
    # Simulate composition in background
    asyncio.create_task(simulate_composition(song_id, job_id))
    
    return {
        "jobId": job_id,
        "status": "queued",
        "songId": str(song_id),
    }


async def simulate_composition(song_id: UUID, job_id: str):
    """Simulate video composition with realistic delays."""
    jobs[job_id]["status"] = "processing"
    jobs[job_id]["progress"] = 20
    
    await asyncio.sleep(MOCK_DELAYS["composition"] * 0.3)
    jobs[job_id]["progress"] = 50
    
    await asyncio.sleep(MOCK_DELAYS["composition"] * 0.3)
    jobs[job_id]["progress"] = 80
    
    await asyncio.sleep(MOCK_DELAYS["composition"] * 0.4)
    
    # Store composed video
    song = songs[song_id]
    composed_videos[song_id] = {
        "id": str(uuid4()),
        "songId": str(song_id),
        "videoUrl": MOCK_VIDEO_URL,
        "posterUrl": MOCK_VIDEO_URL,  # Same URL for simplicity
        "durationSec": song["durationSec"],
        "fileSizeBytes": 50000000,  # 50MB mock
        "resolutionWidth": 1920,
        "resolutionHeight": 1080,
        "fps": 30,
        "status": "completed",
        "createdAt": datetime.now().isoformat(),
    }
    
    jobs[job_id]["status"] = "completed"
    jobs[job_id]["progress"] = 100


@app.get("/api/v1/songs/{song_id}/compose/{job_id}/status")
async def get_composition_job_status(song_id: UUID, job_id: str):
    """Get composition job status."""
    if song_id not in songs:
        raise HTTPException(status_code=404, detail="Song not found")
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id].copy()
    if job.get("status") == "completed" and song_id in composed_videos:
        job["result"] = composed_videos[song_id]
    
    return job


def configure_frontend_env():
    """
    Set VITE_API_BASE_URL in frontend/.env.local (doesn't modify .env).
    
    Returns:
        tuple: (Path to .env.local file, bool indicating if file was created by this script)
    """
    frontend_env_local_path = Path(__file__).parent.parent / "frontend" / ".env.local"
    api_url = f"http://localhost:{PORT}"
    new_content = f"VITE_API_BASE_URL={api_url}\n"
    
    # Track if file existed before we touched it
    file_existed_before = frontend_env_local_path.exists()
    
    # Only write if content changed to avoid triggering Vite restarts
    if file_existed_before:
        with open(frontend_env_local_path, "r") as f:
            existing_content = f.read()
        if existing_content == new_content:
            return frontend_env_local_path, False  # File existed, no change needed
    
    # Write to .env.local (takes precedence over .env, typically gitignored)
    frontend_env_local_path.parent.mkdir(parents=True, exist_ok=True)
    with open(frontend_env_local_path, "w") as f:
        f.write(new_content)
    
    logger.info(f"✅ Configured frontend/.env.local with VITE_API_BASE_URL={api_url}")
    
    # Return True if we created it (didn't exist before), False if we just modified it
    return frontend_env_local_path, not file_existed_before


def kill_port(port: int):
    """Kill any process using the specified port."""
    try:
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                    logger.info(f"Killed process {pid} on port {port}")
                except (ProcessLookupError, ValueError):
                    pass
    except FileNotFoundError:
        # lsof not available, try alternative method
        try:
            result = subprocess.run(
                ["netstat", "-vanp", "tcp"],
                capture_output=True,
                text=True
            )
            # Parse and kill if needed (simpler to just try lsof first)
        except FileNotFoundError:
            pass


def start_frontend():
    """Start the frontend dev server."""
    project_root = Path(__file__).parent.parent
    frontend_dir = project_root / "frontend"
    
    if not frontend_dir.exists():
        logger.warning("Frontend directory not found, skipping frontend startup")
        return None
    
    logger.info("Starting frontend on http://localhost:5173...")
    process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--host"],
        cwd=str(frontend_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return process


def open_browser(url: str, delay: float = 2.0):
    """Open URL in browser after delay."""
    def _open():
        time.sleep(delay)
        try:
            webbrowser.open(url)
            logger.info(f"Opened {url} in browser")
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
    
    import threading
    thread = threading.Thread(target=_open, daemon=True)
    thread.start()


def cleanup_env_file(env_file_path: Path, should_delete: bool):
    """Delete .env.local file if it was created by this script."""
    if should_delete and env_file_path.exists():
        try:
            env_file_path.unlink()
            logger.info(f"✅ Cleaned up frontend/.env.local (deleted)")
        except Exception as e:
            logger.warning(f"⚠️  Could not delete frontend/.env.local: {e}")


def setup_cleanup(frontend_process, env_file_path: Path, should_delete_env: bool):
    """Set up signal handlers for cleanup."""
    def signal_handler(sig, frame):
        logger.info("\nShutting down...")
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait(timeout=5)
        cleanup_env_file(env_file_path, should_delete_env)
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    import uvicorn
    import threading
    
    # Kill any process on port 3000
    kill_port(PORT)
    
    # Configure frontend .env file and track if we created it
    env_file_path, env_file_created = configure_frontend_env()
    
    # Start frontend
    frontend_process = start_frontend()
    
    # Open browser after delay
    open_browser("http://localhost:5173", delay=2.0)
    
    logger.info(f"Starting mock backend server on http://localhost:{PORT}")
    logger.info("This server mocks the VibeCraft backend for frontend testing")
    logger.info("All operations complete instantly (delays set to 0)")
    logger.info("Frontend: http://localhost:5173")
    logger.info("Press Ctrl+C to stop")
    
    # Set up cleanup handlers
    setup_cleanup(frontend_process, env_file_path, env_file_created)
    
    try:
        # Run the backend server
        uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
    finally:
        # Cleanup on normal exit (e.g., KeyboardInterrupt caught elsewhere)
        cleanup_env_file(env_file_path, env_file_created)

