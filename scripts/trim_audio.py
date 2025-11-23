#!/usr/bin/env python3
"""Trim audio file to exact duration.

Usage:
    python scripts/trim_audio.py input.mp3 16.333333 output.mp3
"""

import subprocess
import sys
from pathlib import Path


def trim_audio(input_path: Path, duration_sec: float, output_path: Path):
    """Trim audio to exact duration using ffmpeg."""
    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        str(input_path),
        "-t",
        str(duration_sec),
        "-c",
        "copy",  # Stream copy (no re-encoding) for speed
        "-y",  # Overwrite output
        str(output_path),
    ]
    
    subprocess.run(ffmpeg_cmd, check=True)
    print(f"✓ Trimmed audio: {input_path.name} → {output_path.name}")
    print(f"  Duration: {duration_sec:.6f}s")


def main():
    """Trim audio to specified duration."""
    if len(sys.argv) != 4:
        print("Usage: python scripts/trim_audio.py input.mp3 duration_sec output.mp3")
        print("Example: python scripts/trim_audio.py song.mp3 16.333333 song_trimmed.mp3")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    duration_sec = float(sys.argv[2])
    output_path = Path(sys.argv[3])

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    trim_audio(input_path, duration_sec, output_path)


if __name__ == "__main__":
    main()

