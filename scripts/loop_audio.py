#!/usr/bin/env python3
"""Loop an audio file multiple times to create a longer test file.

Usage:
    python scripts/loop_audio.py input.mp3 output.mp3 --loops 10
"""

import argparse
import subprocess
import sys
from pathlib import Path


def loop_audio(input_path: Path, output_path: Path, loops: int, ffmpeg_bin: str = "ffmpeg") -> None:
    """Loop an audio file N times using FFmpeg."""
    if loops < 1:
        raise ValueError("Number of loops must be at least 1")
    
    if loops == 1:
        # Just copy the file
        subprocess.run(
            [ffmpeg_bin, "-i", str(input_path), "-c", "copy", "-y", str(output_path)],
            check=True,
            capture_output=True,
        )
        print(f"Copied {input_path} to {output_path}")
        return
    
    # Create a concat file for FFmpeg
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as concat_file:
        concat_path = Path(concat_file.name)
        for _ in range(loops):
            escaped_path = str(input_path).replace("'", "'\\''").replace("\\", "\\\\")
            concat_file.write(f"file '{escaped_path}'\n")
    
    try:
        # Use FFmpeg concat demuxer to loop the audio
        subprocess.run(
            [
                ffmpeg_bin,
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_path),
                "-c", "copy",  # Stream copy (no re-encoding) for speed
                "-y",
                str(output_path),
            ],
            check=True,
            capture_output=True,
        )
        print(f"✓ Created {output_path} with {loops} loops of {input_path.name}")
    finally:
        # Clean up concat file
        concat_path.unlink(missing_ok=True)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Loop an audio file multiple times",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Input audio file")
    parser.add_argument("output", help="Output audio file")
    parser.add_argument(
        "--loops",
        type=int,
        default=10,
        help="Number of times to loop (default: 10)",
    )
    parser.add_argument(
        "--ffmpeg-bin",
        default="ffmpeg",
        help="Path to ffmpeg binary (default: ffmpeg)",
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        return 1
    
    try:
        loop_audio(input_path, output_path, args.loops, args.ffmpeg_bin)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error: FFmpeg failed: {e}")
        if e.stderr:
            print(e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

