#!/usr/bin/env python3
"""Local video composition script for rapid iteration and testing.

Usage:
    python scripts/compose_local.py \
      --clips ~/Desktop/clip1.mp4 ~/Desktop/clip2.mp4 \
      --audio ~/Desktop/song.mp3 \
      --output ~/Desktop/composed.mp4

Run from project root directory.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Add backend directory to path so we can import app modules
# Script should be run from project root
backend_path = Path(__file__).parent.parent / "backend"
if backend_path.exists():
    sys.path.insert(0, str(backend_path))
else:
    # Fallback: try parent directory (if running from scripts/)
    sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import get_settings
from app.services.video_composition import (
    concatenate_clips,
    extend_last_clip,
    normalize_clip,
    validate_composition_inputs,
    verify_composed_video,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Progress milestones (matching composition_execution.py)
PROGRESS_VALIDATION = 10
PROGRESS_DOWNLOAD_START = 10
PROGRESS_DOWNLOAD_END = 30
PROGRESS_NORMALIZE_START = 30
PROGRESS_NORMALIZE_END = 80
PROGRESS_STITCH = 80
PROGRESS_UPLOAD = 90
PROGRESS_VERIFY = 95
PROGRESS_COMPLETE = 100


def expand_path(path_str: str) -> Path:
    """Expand user home directory and resolve path."""
    return Path(path_str).expanduser().resolve()


def log_progress(progress: int, stage: str) -> None:
    """Log progress update (local script version of update_job_progress)."""
    logger.info(f"[{progress}%] {stage}")


def get_clip_duration(clip_path: Path, ffprobe_bin: str) -> float:
    """Get clip duration using ffprobe (used when validation is skipped)."""
    probe_cmd = [
        ffprobe_bin,
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(clip_path),
    ]
    result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, timeout=30)
    probe_data = json.loads(result.stdout)
    return float(probe_data["format"]["duration"])


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compose video clips locally for rapid testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--defaultNames",
        action="store_true",
        help="Use default names: clip1-4.mp4, testAudio.mp3, output testComp (in samples/compTest/)",
    )
    parser.add_argument(
        "--40clips",
        action="store_true",
        dest="clips40",
        help="Create 40 clips from clip1-4 by making 9 copies of each and interleaving (requires --defaultNames)",
    )
    parser.add_argument(
        "--clips",
        nargs="+",
        required=False,
        help="Input video clip files (not needed if --defaultNames is used)",
    )
    parser.add_argument(
        "--audio",
        required=False,
        help="Input audio file (not needed if --defaultNames is used)",
    )
    parser.add_argument(
        "--output",
        required=False,
        help="Output video file path (not needed if --defaultNames is used)",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=24,
        help="Target FPS (default: 24)",
    )
    parser.add_argument(
        "--resolution",
        nargs=2,
        type=int,
        default=[1920, 1080],
        metavar=("WIDTH", "HEIGHT"),
        help="Target resolution (default: 1920 1080)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed progress",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files after completion",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip pre-flight validation (faster but less safe)",
    )
    parser.add_argument(
        "--ffmpeg-bin",
        help="Custom FFmpeg binary path",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle --defaultNames flag
    if args.defaultNames:
        # Use samples/compTest directory as base
        script_dir = Path(__file__).parent.parent
        base_dir = script_dir / "samples" / "compTest"
        base_clips = [
            base_dir / "clip1.mp4",
            base_dir / "clip2.mp4",
            base_dir / "clip3.mp4",
            base_dir / "clip4.mp4",
        ]
        audio_path = base_dir / "testAudio.mp3"
        # Use different output name for 40-clip test
        if args.clips40:
            output_path = base_dir / "testComp40.mp4"
        else:
            output_path = base_dir / "testComp.mp4"
        logger.info(f"Using default names in: {base_dir}")
        
        # Handle --40clips flag: create 9 copies of each clip and interleave
        temp_looped_audio = None  # Will be set if we create looped audio
        if args.clips40:  # Note: argparse converts --40clips to args.clips40
            import shutil
            # First, verify all 4 base clips exist before doing anything
            missing_clips = []
            for clip in base_clips:
                if not clip.exists():
                    missing_clips.append(clip.name)
            
            if missing_clips:
                logger.error("=" * 60)
                logger.error("ERROR: Missing base clips for --40clips flag")
                logger.error("=" * 60)
                logger.error(f"Required clips in {base_dir}:")
                for clip in base_clips:
                    status = "✓" if clip.exists() else "✗ MISSING"
                    logger.error(f"  {status} {clip.name}")
                logger.error("=" * 60)
                logger.error("Please ensure all 4 base clips exist before using --40clips")
                return 1
            
            # Verify audio exists
            if not audio_path.exists():
                logger.error(f"ERROR: Audio file not found: {audio_path}")
                return 1
            
            # Create looped audio (10x) for 40 clips
            # 40 clips × 4 seconds each = 160 seconds, so loop audio 10 times
            logger.info("Creating looped audio (10x) for 40-clip test...")
            temp_looped_audio = Path(tempfile.mktemp(suffix=".mp3", prefix="compose_looped_audio_"))
            
            # Import loop_audio function (or call the script)
            # We'll use subprocess to call the loop_audio script
            settings = get_settings()
            ffmpeg_bin = args.ffmpeg_bin or settings.ffmpeg_bin
            loop_cmd = [
                sys.executable,
                str(Path(__file__).parent / "loop_audio.py"),
                str(audio_path),
                str(temp_looped_audio),
                "--loops", "10",
                "--ffmpeg-bin", ffmpeg_bin,
            ]
            try:
                result = subprocess.run(loop_cmd, capture_output=True, text=True, check=True)
                logger.info(f"✓ Created looped audio: {temp_looped_audio} (10x {audio_path.name})")
                audio_path = temp_looped_audio  # Use looped audio instead
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create looped audio: {e}")
                if e.stderr:
                    logger.error(e.stderr)
                return 1
            
            # All clips exist, proceed with creating copies
            # Create temp directory for copies
            temp_copy_dir = Path(tempfile.mkdtemp(prefix="compose_40clips_"))
            logger.info(f"Creating 40 clips (10 copies of each, interleaved) in: {temp_copy_dir}")
            
            # Create 9 copies of each clip (10 total including original)
            clip_paths = []
            for copy_num in range(10):  # 0-9 (0 is original, 1-9 are copies)
                for i, base_clip in enumerate(base_clips, 1):
                    if copy_num == 0:
                        # Use original
                        clip_paths.append(base_clip)
                    else:
                        # Create copy
                        copy_name = f"clip{i}_copy{copy_num}.mp4"
                        copy_path = temp_copy_dir / copy_name
                        shutil.copy2(base_clip, copy_path)
                        clip_paths.append(copy_path)
                        logger.debug(f"Created copy: {copy_name}")
            
            logger.info(f"Created {len(clip_paths)} clips (interleaved: clip1, clip2, clip3, clip4, clip1-copy1, clip2-copy1, ...)")
            # Note: temp_copy_dir will be cleaned up when script exits (unless --keep-temp)
        else:
            clip_paths = base_clips
    else:
        # Require explicit arguments
        if not args.clips:
            parser.error("--clips is required when --defaultNames is not used")
        if not args.audio:
            parser.error("--audio is required when --defaultNames is not used")
        if not args.output:
            parser.error("--output is required when --defaultNames is not used")
        
        # Expand paths
        clip_paths = [expand_path(c) for c in args.clips]
        audio_path = expand_path(args.audio)
        output_path = expand_path(args.output)

    # Validate inputs exist
    for clip_path in clip_paths:
        if not clip_path.exists():
            logger.error(f"Clip not found: {clip_path}")
            return 1

    if not audio_path.exists():
        logger.error(f"Audio file not found: {audio_path}")
        return 1

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    target_resolution = tuple(args.resolution)
    target_fps = args.fps

    logger.info("=" * 60)
    logger.info("Video Composition - Local Testing")
    logger.info("=" * 60)
    logger.info(f"Clips: {len(clip_paths)} files")
    logger.info(f"Audio: {audio_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Target: {target_resolution[0]}x{target_resolution[1]} @ {target_fps}fps")
    logger.info("=" * 60)

    # Use temporary directory for intermediate files
    if args.keep_temp:
        # If keeping temp files, create a named directory
        temp_dir = Path(tempfile.mkdtemp(prefix="compose_"))
        logger.info(f"Temporary files will be kept in: {temp_dir}")
        temp_dir_context = None
    else:
        temp_dir_context = tempfile.TemporaryDirectory(prefix="compose_")
        temp_dir = Path(temp_dir_context.__enter__())

    try:
        # Step 1: Validate inputs (optional)
        if not args.skip_validation:
            logger.info("\n[1/4] Validating clips...")
            log_progress(PROGRESS_VALIDATION, "Validating inputs")
            try:
                # Verify files exist and are readable
                for i, clip_path in enumerate(clip_paths, 1):
                    if not clip_path.exists():
                        logger.error(f"Clip {i} not found: {clip_path}")
                        return 1
                    if not clip_path.is_file():
                        logger.error(f"Clip {i} is not a file: {clip_path}")
                        return 1
                    file_size = clip_path.stat().st_size
                    if file_size == 0:
                        logger.error(f"Clip {i} is empty (0 bytes): {clip_path}")
                        return 1
                    if args.verbose:
                        logger.debug(f"Clip {i}: {clip_path} ({file_size} bytes)")
                
                clip_urls = [str(p) for p in clip_paths]
                metadata_list = validate_composition_inputs(
                    clip_urls,
                    ffmpeg_bin=args.ffmpeg_bin,
                )
                total_duration = sum(m.duration_sec for m in metadata_list)
                logger.info(f"✓ Validated {len(metadata_list)} clips")
                logger.info(f"  Total duration: {total_duration:.2f}s")
                for i, m in enumerate(metadata_list):
                    logger.info(
                        f"  Clip {i+1}: {m.width}x{m.height} @ {m.fps:.1f}fps, "
                        f"{m.duration_sec:.2f}s"
                    )
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                if args.verbose:
                    import traceback
                    logger.debug(traceback.format_exc())
                logger.error("\nTroubleshooting:")
                logger.error("1. Verify files are valid video files (try playing them)")
                logger.error("2. Try running with --skip-validation to bypass this check")
                logger.error("3. Run with --verbose for more details")
                return 1
        else:
            logger.info("\n[1/4] Skipping validation...")
            metadata_list = None

        # Step 2: Normalize clips (parallel)
        logger.info("\n[2/4] Normalizing clips...")
        log_progress(PROGRESS_NORMALIZE_START, "Normalizing clips")
        normalized_paths = []
        normalize_progress_per_clip = (PROGRESS_NORMALIZE_END - PROGRESS_NORMALIZE_START) / len(clip_paths)

        def normalize_single_clip(i: int, clip_path: Path) -> Path:
            """Normalize a single clip."""
            normalized_path = temp_dir / f"normalized_{i}.mp4"
            normalize_clip(
                str(clip_path),
                str(normalized_path),
                target_resolution=target_resolution,
                target_fps=target_fps,
                ffmpeg_bin=args.ffmpeg_bin,
            )
            logger.info(f"  ✓ Normalized clip {i+1}/{len(clip_paths)}: {clip_path.name}")
            return normalized_path

        # Normalize in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_index = {
                executor.submit(normalize_single_clip, i, clip_path): i
                for i, clip_path in enumerate(clip_paths)
            }

            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                try:
                    normalized_path = future.result(timeout=300)  # 5 minute timeout per clip
                    normalized_paths.append(normalized_path)
                    progress = PROGRESS_NORMALIZE_START + int(
                        len(normalized_paths) * normalize_progress_per_clip
                    )
                    log_progress(progress, f"Normalized {len(normalized_paths)}/{len(clip_paths)} clips")
                except Exception as e:
                    logger.error(f"  ✗ Failed to normalize clip {i+1}: {e}")
                    return 1

        # Sort normalized paths by original order
        normalized_paths.sort(key=lambda p: int(p.stem.split("_")[1]))

        # Step 3: Concatenate and mux audio
        logger.info("\n[3/4] Stitching clips and muxing audio...")
        log_progress(PROGRESS_STITCH, "Stitching clips")
        temp_output = temp_dir / "composed.mp4"
        try:
            # Get audio duration for reference
            settings = get_settings()
            ffprobe_bin = (args.ffmpeg_bin or settings.ffmpeg_bin).replace("ffmpeg", "ffprobe")
            probe_cmd = [
                ffprobe_bin,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                str(audio_path),
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
            audio_data = json.loads(result.stdout)
            audio_duration = float(audio_data["format"]["duration"])

            # Handle duration mismatch (extend last clip if needed)
            # Calculate total clip duration from metadata_list if available, otherwise use ffprobe
            if metadata_list:
                total_clip_duration = sum(m.duration_sec for m in metadata_list)
                last_clip_duration = metadata_list[-1].duration_sec
            else:
                # If validation was skipped, get durations using ffprobe
                logger.info("  Calculating clip durations (validation was skipped)...")
                clip_durations = [
                    get_clip_duration(normalized_path, ffprobe_bin) for normalized_path in normalized_paths
                ]
                total_clip_duration = sum(clip_durations)
                last_clip_duration = clip_durations[-1]

            # Handle duration mismatch (same logic as production pipeline)
            MAX_DURATION_MISMATCH_SECONDS = 5.0  # Maximum allowed duration mismatch
            
            if audio_duration > 0:
                duration_diff = total_clip_duration - audio_duration
                
                # Check for large mismatches (fail if > 5 seconds either way)
                if abs(duration_diff) > MAX_DURATION_MISMATCH_SECONDS:
                    logger.error("=" * 60)
                    logger.error("ERROR: Duration mismatch too large")
                    logger.error("=" * 60)
                    logger.error(f"Clips: {total_clip_duration:.2f}s")
                    logger.error(f"Audio: {audio_duration:.2f}s")
                    logger.error(f"Difference: {abs(duration_diff):.2f}s (max allowed: {MAX_DURATION_MISMATCH_SECONDS}s)")
                    logger.error("=" * 60)
                    logger.error("Tip: Use scripts/loop_audio.py to extend audio, or trim clips")
                    return 1
                
                # Handle small mismatches
                if duration_diff < 0:
                    # Clips are shorter: extend last clip
                    logger.info(
                        f"  Extending last clip: clips={total_clip_duration:.2f}s, "
                        f"audio={audio_duration:.2f}s, diff={duration_diff:.2f}s"
                    )
                    last_clip_path = normalized_paths[-1]
                    extended_path = temp_dir / "last_clip_extended.mp4"
                    extend_last_clip(
                        str(last_clip_path),
                        str(extended_path),
                        target_duration_sec=audio_duration - total_clip_duration + last_clip_duration,
                        ffmpeg_bin=args.ffmpeg_bin,
                    )
                    normalized_paths[-1] = extended_path
                elif duration_diff > 0:
                    # Clips are longer: trim last clip
                    logger.info(
                        f"  Trimming last clip: clips={total_clip_duration:.2f}s, "
                        f"audio={audio_duration:.2f}s, diff={duration_diff:.2f}s"
                    )
                    from app.services.video_composition import trim_last_clip
                    last_clip_path = normalized_paths[-1]
                    trimmed_path = temp_dir / "last_clip_trimmed.mp4"
                    last_clip_target_duration = last_clip_duration - duration_diff
                    trim_last_clip(
                        str(last_clip_path),
                        str(trimmed_path),
                        target_duration_sec=last_clip_target_duration,
                        ffmpeg_bin=args.ffmpeg_bin,
                    )
                    normalized_paths[-1] = trimmed_path

            # Log clip count and expected duration for debugging
            logger.info(f"  Concatenating {len(normalized_paths)} clips...")
            expected_video_duration = sum(
                get_clip_duration(p, (args.ffmpeg_bin or get_settings().ffmpeg_bin).replace("ffmpeg", "ffprobe"))
                for p in normalized_paths
            )
            logger.info(f"  Expected video duration: {expected_video_duration:.2f}s (audio: {audio_duration:.2f}s)")
            
            composition_result = concatenate_clips(
                normalized_clip_paths=[str(p) for p in normalized_paths],
                audio_path=str(audio_path),
                output_path=str(temp_output),
                song_duration_sec=audio_duration,
                ffmpeg_bin=args.ffmpeg_bin,
            )
            logger.info(f"✓ Composed video: {composition_result.duration_sec:.2f}s")
            if composition_result.duration_sec < expected_video_duration * 0.9:
                logger.warning(
                    f"⚠ WARNING: Output duration ({composition_result.duration_sec:.2f}s) is much shorter than "
                    f"expected ({expected_video_duration:.2f}s). Concatenation may have failed."
                )
            logger.info(
                f"  Resolution: {composition_result.width}x{composition_result.height} "
                f"@ {composition_result.fps}fps"
            )
            logger.info(f"  File size: {composition_result.file_size_bytes / 1024 / 1024:.2f} MB")
        except Exception as e:
            logger.error(f"✗ Failed to compose video: {e}")
            return 1

        # Step 4: Verify and copy to output
        logger.info("\n[4/4] Verifying output...")
        log_progress(PROGRESS_VERIFY, "Verifying output")
        try:
            verify_composed_video(
                str(temp_output),
                expected_resolution=target_resolution,
                expected_fps=target_fps,
                ffmpeg_bin=args.ffmpeg_bin,
            )
            logger.info("✓ Verification passed")

            # Copy to final output location
            shutil.copy2(temp_output, output_path)
            logger.info(f"✓ Saved to: {output_path}")
            log_progress(PROGRESS_COMPLETE, "Composition complete")
        except Exception as e:
            logger.error(f"✗ Verification failed: {e}")
            return 1

        logger.info("\n" + "=" * 60)
        logger.info("✓ Composition complete!")
        logger.info(f"  Output: {output_path}")
        if args.keep_temp:
            logger.info(f"  Temp files: {temp_dir}")
        logger.info("=" * 60)

        return 0

    except KeyboardInterrupt:
        logger.warning("\n\nInterrupted by user")
        return 1
    except Exception as e:
        logger.exception(f"\n\nUnexpected error: {e}")
        return 1
    finally:
        if temp_dir_context is not None:
            temp_dir_context.__exit__(None, None, None)
        # Clean up looped audio if it was created
        if temp_looped_audio and temp_looped_audio.exists() and not args.keep_temp:
            try:
                temp_looped_audio.unlink()
                logger.debug(f"Cleaned up looped audio: {temp_looped_audio}")
            except Exception as e:
                logger.warning(f"Failed to clean up looped audio: {e}")


if __name__ == "__main__":
    sys.exit(main())

