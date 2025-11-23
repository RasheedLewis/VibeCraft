#!/usr/bin/env python3
"""Get precise total duration of video clips (to the frame, 1/24th second).

Usage:
    python scripts/get_clips_duration.py clip1.mp4 clip2.mp4 clip3.mp4 clip4.mp4
"""

import json
import subprocess
import sys
from pathlib import Path

FPS = 24  # Frames per second for precision


def get_clip_duration(clip_path: Path) -> float:
    """Get clip duration using ffprobe."""
    ffprobe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(clip_path),
    ]
    result = subprocess.run(ffprobe_cmd, capture_output=True, text=True, check=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def round_to_frame(duration_sec: float, fps: int = FPS) -> float:
    """Round duration to nearest frame (1/fps seconds)."""
    frame_duration = 1.0 / fps
    frames = round(duration_sec / frame_duration)
    return frames * frame_duration


def main():
    """Get total duration of clips."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/get_clips_duration.py clip1.mp4 clip2.mp4 ...")
        sys.exit(1)

    clip_paths = [Path(arg) for arg in sys.argv[1:]]
    
    # Validate files exist
    for clip_path in clip_paths:
        if not clip_path.exists():
            print(f"Error: File not found: {clip_path}")
            sys.exit(1)

    # Get durations
    durations = []
    for clip_path in clip_paths:
        duration = get_clip_duration(clip_path)
        durations.append(duration)
        print(f"{clip_path.name}: {duration:.6f}s")

    # Sum and round to nearest frame
    total_duration = sum(durations)
    rounded_duration = round_to_frame(total_duration, FPS)
    
    print(f"\nTotal duration: {total_duration:.6f}s")
    print(f"Rounded to frame (1/{FPS}s): {rounded_duration:.6f}s")
    print(f"\nUse this duration: {rounded_duration:.6f}")


if __name__ == "__main__":
    main()

