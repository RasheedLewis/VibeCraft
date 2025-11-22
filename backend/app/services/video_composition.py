"""Video composition service for stitching clips together with FFmpeg."""

from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import ffmpeg

from app.core.config import get_settings
from app.services.composition_job import update_job_progress

logger = logging.getLogger(__name__)

# Default composition settings
DEFAULT_TARGET_RESOLUTION = (1920, 1080)
DEFAULT_TARGET_FPS = 24
DEFAULT_VIDEO_CODEC = "libx264"
DEFAULT_AUDIO_CODEC = "aac"
DEFAULT_AUDIO_BITRATE = "192k"
DEFAULT_CRF = 23  # Quality setting for H.264 (lower = better quality, 18-28 is typical range)


@dataclass
class ClipMetadata:
    """Metadata for a video clip."""

    duration_sec: float
    fps: float
    width: int
    height: int
    codec: str
    has_audio: bool


@dataclass
class CompositionResult:
    """Result of video composition."""

    output_path: Path
    duration_sec: float
    file_size_bytes: int
    width: int
    height: int
    fps: int


def validate_composition_inputs(
    clip_urls: list[str],
    ffmpeg_bin: str | None = None,
    ffprobe_bin: str | None = None,
) -> list[ClipMetadata]:
    """
    Validate clip URLs and extract metadata using ffprobe.

    Args:
        clip_urls: List of URLs or file paths to video clips
        ffmpeg_bin: Path to ffmpeg binary (defaults to config)
        ffprobe_bin: Path to ffprobe binary (defaults to ffmpeg_bin + 'probe')

    Returns:
        List of ClipMetadata objects

    Raises:
        RuntimeError: If validation fails or clips are inaccessible
    """
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin
    ffprobe_bin = ffprobe_bin or ffmpeg_bin.replace("ffmpeg", "ffprobe")

    metadata_list = []

    for i, clip_url in enumerate(clip_urls):
        try:
            # Use ffprobe to get clip metadata
            probe_cmd = [
                ffprobe_bin,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=width,height,r_frame_rate,codec_name,codec_type",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                clip_url,
            ]

            try:
                result = subprocess.run(
                    probe_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError(f"Failed to validate clip {i + 1}: {e.stderr or str(e)}") from e

            probe_data = json.loads(result.stdout)

            # Extract video stream info
            # When using -select_streams v:0, the stream should be the first (and only) one
            # But we check codec_type if available, or assume it's video if selected
            streams = probe_data.get("streams", [])
            video_stream = None
            
            if streams:
                # If we selected v:0, the first stream should be video
                # But check codec_type if available for safety
                first_stream = streams[0]
                if first_stream.get("codec_type") == "video" or "width" in first_stream:
                    video_stream = first_stream
                else:
                    # Fallback: search for video stream by codec_type
                    for stream in streams:
                        if stream.get("codec_type") == "video":
                            video_stream = stream
                            break

            if not video_stream:
                raise RuntimeError(f"No video stream found in clip {i + 1}")

            # Parse frame rate (can be "30/1" or "29.97")
            r_frame_rate = video_stream.get("r_frame_rate", "30/1")
            if "/" in r_frame_rate:
                num, den = map(int, r_frame_rate.split("/"))
                fps = num / den if den > 0 else 30.0
            else:
                fps = float(r_frame_rate)

            # Get duration from format
            format_info = probe_data.get("format", {})
            duration_sec = float(format_info.get("duration", 0))

            # Check for audio stream
            audio_check_cmd = [
                ffprobe_bin,
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_name",
                "-of",
                "json",
                clip_url,
            ]

            has_audio = False
            try:
                audio_result = subprocess.run(
                    audio_check_cmd,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10,
                )
                audio_data = json.loads(audio_result.stdout)
                has_audio = len(audio_data.get("streams", [])) > 0
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                has_audio = False

            metadata = ClipMetadata(
                duration_sec=duration_sec,
                fps=fps,
                width=int(video_stream.get("width", 0)),
                height=int(video_stream.get("height", 0)),
                codec=video_stream.get("codec_name", "unknown"),
                has_audio=has_audio,
            )

            metadata_list.append(metadata)
            logger.info(
                f"Validated clip {i + 1}/{len(clip_urls)}: {metadata.width}x{metadata.height} @ {metadata.fps}fps, "
                f"duration={metadata.duration_sec:.2f}s, codec={metadata.codec}"
            )

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Timeout validating clip {i + 1} (URL: {clip_url})")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to validate clip {i + 1} (URL: {clip_url}): {e.stderr}"
            ) from e
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            raise RuntimeError(
                f"Failed to parse metadata for clip {i + 1} (URL: {clip_url}): {e}"
            ) from e

    return metadata_list


def normalize_clip(
    input_path: str | Path,
    output_path: str | Path,
    target_resolution: tuple[int, int] = DEFAULT_TARGET_RESOLUTION,
    target_fps: int = DEFAULT_TARGET_FPS,
    ffmpeg_bin: str | None = None,
) -> None:
    """
    Normalize a clip to target resolution and FPS.

    Args:
        input_path: Path to input video file
        output_path: Path to output video file
        target_resolution: Target resolution (width, height)
        target_fps: Target FPS
        ffmpeg_bin: Path to ffmpeg binary (defaults to config)

    Raises:
        RuntimeError: If normalization fails
    """
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin

    target_width, target_height = target_resolution

    # Build video filter: scale with letterboxing, then set FPS
    # scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=24
    vf_parts = [
        f"scale={target_width}:{target_height}:force_original_aspect_ratio=decrease",
        f"pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2",
        f"fps={target_fps}",
    ]
    video_filter = ",".join(vf_parts)

    try:
        (
            ffmpeg.input(str(input_path))
            .output(
                str(output_path),
                vf=video_filter,
                vcodec=DEFAULT_VIDEO_CODEC,
                preset="medium",
                crf=DEFAULT_CRF,
                **{"an": None},  # Remove audio (we'll add song audio later)
            )
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:  # type: ignore[attr-defined]
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"Failed to normalize clip: {stderr}") from e


def concatenate_clips(
    normalized_clip_paths: list[str | Path],
    audio_path: str | Path,
    output_path: str | Path,
    song_duration_sec: float,
    ffmpeg_bin: str | None = None,
    job_id: str | None = None,
    beat_times: Optional[list[float]] = None,  # NEW PARAMETER
    filter_type: str = "flash",  # NEW PARAMETER
    frame_rate: float = 24.0,  # NEW PARAMETER
) -> CompositionResult:
    """
    Concatenate normalized clips and mux with audio.

    Args:
        normalized_clip_paths: List of paths to normalized video clips
        audio_path: Path to audio file (song)
        output_path: Path to output video file
        song_duration_sec: Expected song duration in seconds
        ffmpeg_bin: Path to ffmpeg binary (defaults to config)

    Returns:
        CompositionResult with output metadata

    Raises:
        RuntimeError: If concatenation fails
    """
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin

    if not normalized_clip_paths:
        raise ValueError("No clips provided for concatenation")

    # Create concat file for FFmpeg concat demuxer
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as concat_file:
        concat_path = Path(concat_file.name)
        for clip_path in normalized_clip_paths:
            # Escape single quotes and backslashes in path
            escaped_path = str(clip_path).replace("'", "'\\''").replace("\\", "\\\\")
            concat_file.write(f"file '{escaped_path}'\n")
        
        # Log concat file for debugging (first few and last few entries)
        logger.debug(f"Created concat file with {len(normalized_clip_paths)} clips")
        if len(normalized_clip_paths) > 10:
            logger.debug(f"  First 3: {normalized_clip_paths[:3]}")
            logger.debug(f"  Last 3: {normalized_clip_paths[-3:]}")

    try:
        # First, get the total video duration after concatenation
        # We'll use a temporary output to measure duration, or calculate from clips
        # For now, let's use FFmpeg to get the concatenated video duration
        temp_video_path = Path(output_path).parent / "temp_concatenated.mp4"
        try:
            # Concatenate clips first (without audio) to get video duration
            if job_id:
                update_job_progress(job_id, 70, "processing")  # Concatenating clips
            
            video_input = ffmpeg.input(str(concat_path), format="concat", safe=0)
            (
                ffmpeg.output(
                    video_input["v"],
                    str(temp_video_path),
                    vcodec=DEFAULT_VIDEO_CODEC,
                )
                .overwrite_output()
                .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
            )
            
            # Get the concatenated video duration
            probe_cmd = [
                ffmpeg_bin.replace("ffmpeg", "ffprobe"),
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                str(temp_video_path),
            ]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, timeout=30)
            probe_data = json.loads(result.stdout)
            video_duration = float(probe_data["format"]["duration"])
            
            logger.info(
                f"Concatenated video duration: {video_duration:.2f}s, "
                f"Song duration: {song_duration_sec:.2f}s"
            )
            
            # If video is shorter than audio, loop it to match audio duration
            if video_duration < song_duration_sec:
                if job_id:
                    update_job_progress(job_id, 75, "processing")  # Looping video to match duration
                logger.info(
                    f"Video ({video_duration:.2f}s) is shorter than audio ({song_duration_sec:.2f}s). "
                    f"Looping video to match audio duration."
                )
                # Calculate how many times to loop
                loop_count = int(song_duration_sec / video_duration) + 1
                # Create a new concat file with looped clips
                temp_dir = Path(temp_video_path).parent
                loop_concat_path = temp_dir / "loop_concat.txt"
                with open(loop_concat_path, "w") as loop_concat_file:
                    # Use absolute path and proper escaping for concat demuxer
                    abs_video_path = temp_video_path.resolve()
                    # For concat demuxer, we need to escape single quotes and backslashes
                    escaped_path = str(abs_video_path).replace("'", "'\\''").replace("\\", "\\\\")
                    for _ in range(loop_count):
                        loop_concat_file.write(f"file '{escaped_path}'\n")
                
                # Create output path for looped video (don't overwrite temp_video_path yet)
                looped_output_path = temp_dir / "looped_video.mp4"
                
                try:
                    # Now concatenate the looped video
                    looped_video_input = ffmpeg.input(str(loop_concat_path), format="concat", safe=0)
                    # Trim to exact song duration
                    (
                        ffmpeg.output(
                            looped_video_input["v"],
                            str(looped_output_path),
                            vcodec=DEFAULT_VIDEO_CODEC,
                            t=song_duration_sec,  # Trim to exact duration
                        )
                        .overwrite_output()
                        .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
                    )
                    
                    # Replace temp_video_path with looped version
                    temp_video_path.unlink(missing_ok=True)
                    looped_output_path.rename(temp_video_path)
                except ffmpeg.Error as e:  # type: ignore[attr-defined]
                    stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
                    logger.error(f"Failed to loop video: {stderr}")
                    raise RuntimeError(f"Failed to loop video: {stderr}") from e
                finally:
                    # Clean up loop concat file
                    try:
                        loop_concat_path.unlink(missing_ok=True)
                    except Exception:
                        pass
            elif video_duration > song_duration_sec:
                # Video is longer - trim it to match audio
                if job_id:
                    update_job_progress(job_id, 75, "processing")  # Trimming video to match duration
                logger.info(
                    f"Video ({video_duration:.2f}s) is longer than audio ({song_duration_sec:.2f}s). "
                    f"Trimming video to match audio duration."
                )
                trimmed_output_path = temp_video_path.parent / "temp_trimmed.mp4"
                trimmed_video_input = ffmpeg.input(str(temp_video_path))
                try:
                    (
                        ffmpeg.output(
                            trimmed_video_input["v"],
                            str(trimmed_output_path),
                            vcodec=DEFAULT_VIDEO_CODEC,
                            t=song_duration_sec,  # Trim to exact duration
                        )
                        .overwrite_output()
                        .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
                    )
                    temp_video_path.unlink(missing_ok=True)
                    trimmed_output_path.rename(temp_video_path)
                finally:
                    trimmed_output_path.unlink(missing_ok=True)
            
            # Apply beat filters if provided (before muxing with audio)
            if beat_times and len(beat_times) > 0:
                if job_id:
                    update_job_progress(job_id, 78, "processing")  # Applying beat filters
                logger.info(f"Applying {filter_type} beat filters for {len(beat_times)} beats")
                
                try:
                    from app.services.beat_filters import generate_beat_filter_complex
                    
                    # Generate filter complex for beat effects
                    beat_filters = generate_beat_filter_complex(
                        beat_times=beat_times,
                        filter_type=filter_type,
                        frame_rate=frame_rate,
                    )
                    
                    if beat_filters and filter_type == "flash":
                        # Apply brightness pulse on beats using time-based filter
                        filtered_video_path = temp_video_path.parent / "temp_filtered.mp4"
                        filtered_input = ffmpeg.input(str(temp_video_path))
                        
                        # Build time-based condition for all beats
                        # FFmpeg's between(t,start,end) returns 1 if true, 0 if false
                        tolerance_sec = 0.05  # 50ms tolerance
                        
                        # Create a filter expression that triggers on any beat
                        # We'll use a geq filter with a condition that checks if current time
                        # is within any beat window
                        beat_conditions = []
                        for beat_time in beat_times[:50]:  # Limit to first 50 beats for expression length
                            start_time = max(0, beat_time - tolerance_sec)
                            end_time = min(beat_time + tolerance_sec, song_duration_sec)
                            beat_conditions.append(f"between(t,{start_time},{end_time})")
                        
                        if beat_conditions:
                            # Combine conditions with OR (using addition since they return 0/1)
                            # In FFmpeg expressions, we can use min(1, sum) to create OR logic
                            condition_expr = "+".join(beat_conditions)
                            
                            # Apply brightness increase on beats using geq filter
                            # Increase RGB values by 30 when condition is true
                            filtered_video = filtered_input["v"].filter(
                                "geq",
                                r=f"r+if(min(1,{condition_expr}),30,0)",
                                g=f"g+if(min(1,{condition_expr}),30,0)",
                                b=f"b+if(min(1,{condition_expr}),30,0)",
                            )
                        else:
                            filtered_video = filtered_input["v"]
                        
                        (
                            ffmpeg.output(
                                filtered_video,
                                str(filtered_video_path),
                                vcodec=DEFAULT_VIDEO_CODEC,
                            )
                            .overwrite_output()
                            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
                        )
                        
                        # Replace temp video with filtered version
                        temp_video_path.unlink(missing_ok=True)
                        filtered_video_path.rename(temp_video_path)
                        logger.info("Beat filters applied successfully")
                except Exception as filter_exc:
                    logger.warning(f"Failed to apply beat filters, continuing without filters: {filter_exc}")
                    # Continue without filters if application fails
            
            # Now mux the video (which matches audio duration) with audio
            if job_id:
                update_job_progress(job_id, 80, "processing")  # Muxing video with audio
            
            final_video_input = ffmpeg.input(str(temp_video_path))
            audio_input = ffmpeg.input(str(audio_path))
            
            (
                ffmpeg.output(
                    final_video_input["v"],
                    audio_input["a"],
                    str(output_path),
                    vcodec=DEFAULT_VIDEO_CODEC,
                    acodec=DEFAULT_AUDIO_CODEC,
                    audio_bitrate=DEFAULT_AUDIO_BITRATE,
                    t=song_duration_sec,  # Ensure exact duration match
                    **{"async": 1},  # Audio resampling for sync
                )
                .overwrite_output()
                .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
            )
            
            # Clean up temp video
            try:
                temp_video_path.unlink(missing_ok=True)
            except Exception:
                pass
                
        except ffmpeg.Error as e:  # type: ignore[attr-defined]
            # Clean up temp video on error
            try:
                temp_video_path.unlink(missing_ok=True)
            except Exception:
                pass
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
            # Log concat file contents for debugging if concatenation fails
            logger.error(f"FFmpeg concatenation failed. Concat file had {len(normalized_clip_paths)} clips.")
            if len(normalized_clip_paths) > 0:
                logger.error(f"First clip: {normalized_clip_paths[0]}")
                logger.error(f"Last clip: {normalized_clip_paths[-1]}")
            raise RuntimeError(f"Failed to concatenate clips: {stderr}") from e
        except Exception as e:
            # Clean up temp video on error
            try:
                temp_video_path.unlink(missing_ok=True)
            except Exception:
                pass
            raise RuntimeError(f"Failed to concatenate clips: {e}") from e

        # Verify output using ffprobe
        result = verify_composed_video(str(output_path), ffmpeg_bin=ffmpeg_bin)

        return result

    finally:
        # Clean up concat file
        try:
            concat_path.unlink(missing_ok=True)
        except Exception:
            pass


def extend_last_clip(
    clip_path: str | Path,
    output_path: str | Path,
    target_duration_sec: float,
    fadeout_duration_sec: float = 2.0,
    ffmpeg_bin: str | None = None,
) -> None:
    """
    Extend the last clip to match target duration with fadeout.

    Args:
        clip_path: Path to input clip
        output_path: Path to output clip
        target_duration_sec: Target duration in seconds
        fadeout_duration_sec: Fadeout duration in seconds
        ffmpeg_bin: Path to ffmpeg binary (defaults to config)

    Raises:
        RuntimeError: If extension fails
    """
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin

    # Get current clip duration
    try:
        probe_cmd = [
            ffmpeg_bin.replace("ffmpeg", "ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(clip_path),
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, timeout=10)
        probe_data = json.loads(result.stdout)
        current_duration = float(probe_data["format"]["duration"])
    except Exception as e:
        raise RuntimeError(f"Failed to get clip duration: {e}") from e

    if current_duration >= target_duration_sec:
        # Clip is already long enough, just add fadeout
        fade_start = max(0, current_duration - fadeout_duration_sec)
        video_filter = f"fade=t=out:st={fade_start}:d={fadeout_duration_sec}"
    else:
        # Extend clip by cloning last frame, then fadeout
        extend_duration = target_duration_sec - current_duration
        fade_start = max(0, target_duration_sec - fadeout_duration_sec)
        video_filter = (
            f"tpad=stop_mode=clone:stop_duration={extend_duration},"
            f"fade=t=out:st={fade_start}:d={fadeout_duration_sec}"
        )

    try:
        (
            ffmpeg.input(str(clip_path))
            .output(
                str(output_path),
                vf=video_filter,
                vcodec=DEFAULT_VIDEO_CODEC,
                preset="medium",
                crf=DEFAULT_CRF,
                **{"an": None},  # Remove audio
            )
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:  # type: ignore[attr-defined]
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"Failed to extend clip: {stderr}") from e


def trim_last_clip(
    clip_path: str | Path,
    output_path: str | Path,
    target_duration_sec: float,
    fadeout_duration_sec: float = 1.0,
    ffmpeg_bin: str | None = None,
) -> None:
    """
    Trim the last clip to match target duration with fadeout.

    Args:
        clip_path: Path to input clip
        output_path: Path to output clip
        target_duration_sec: Target duration in seconds
        fadeout_duration_sec: Fadeout duration in seconds
        ffmpeg_bin: Path to ffmpeg binary (defaults to config)

    Raises:
        RuntimeError: If trimming fails
    """
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin

    # Get current clip duration
    try:
        probe_cmd = [
            ffmpeg_bin.replace("ffmpeg", "ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(clip_path),
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, timeout=10)
        probe_data = json.loads(result.stdout)
        current_duration = float(probe_data["format"]["duration"])
    except Exception as e:
        raise RuntimeError(f"Failed to get clip duration: {e}") from e

    if current_duration <= target_duration_sec:
        # Clip is already short enough, just add fadeout
        fade_start = max(0, current_duration - fadeout_duration_sec)
        video_filter = f"fade=t=out:st={fade_start}:d={fadeout_duration_sec}"
    else:
        # Trim clip and add fadeout
        fade_start = max(0, target_duration_sec - fadeout_duration_sec)
        video_filter = (
            f"trim=duration={target_duration_sec},"
            f"fade=t=out:st={fade_start}:d={fadeout_duration_sec}"
        )

    try:
        (
            ffmpeg.input(str(clip_path))
            .output(
                str(output_path),
                vf=video_filter,
                vcodec=DEFAULT_VIDEO_CODEC,
                preset="medium",
                crf=DEFAULT_CRF,
                **{"an": None},  # Remove audio
            )
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:  # type: ignore[attr-defined]
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"Failed to trim clip: {stderr}") from e


def trim_clip_to_beat_boundary(
    clip_path: str | Path,
    output_path: str | Path,
    target_start_time: float,
    target_end_time: float,
    beat_start_time: float,
    beat_end_time: float,
    fps: float = 24.0,
    ffmpeg_bin: str | None = None,
) -> None:
    """
    Trim clip to align with beat boundaries.
    
    Args:
        clip_path: Path to input clip
        output_path: Path to output clip
        target_start_time: Desired start time (may not be on beat)
        target_end_time: Desired end time (may not be on beat)
        beat_start_time: Nearest beat-aligned start time
        beat_end_time: Nearest beat-aligned end time
        fps: Video frame rate
        ffmpeg_bin: Path to ffmpeg binary
    """
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin
    
    # Calculate trim parameters relative to clip start
    # We need to trim from target_start to beat_start, and from beat_end to target_end
    trim_start_offset = max(0, beat_start_time - target_start_time)
    trim_end_offset = max(0, target_end_time - beat_end_time)
    
    # Calculate the actual trim start and end within the clip
    clip_start = trim_start_offset
    clip_end = (target_end_time - target_start_time) - trim_end_offset
    
    # Build trim filter
    # Format: trim=start=X:end=Y,setpts=PTS-STARTPTS
    video_filter = f"trim=start={clip_start:.3f}:end={clip_end:.3f},setpts=PTS-STARTPTS"
    
    try:
        (
            ffmpeg.input(str(clip_path))
            .output(
                str(output_path),
                vf=video_filter,
                vcodec=DEFAULT_VIDEO_CODEC,
                preset="medium",
                crf=DEFAULT_CRF,
                **{"an": None},  # Remove audio
            )
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:  # type: ignore[attr-defined]
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"Failed to trim clip to beat boundary: {stderr}") from e


def extend_clip_to_beat_boundary(
    clip_path: str | Path,
    output_path: str | Path,
    target_duration: float,
    beat_end_time: float,
    fadeout_duration: float = 0.5,
    ffmpeg_bin: str | None = None,
) -> None:
    """
    Extend clip to align with beat boundary using frame freeze + fadeout.
    
    Args:
        clip_path: Path to input clip
        output_path: Path to output clip
        target_duration: Current clip duration
        beat_end_time: Target beat-aligned end time
        fadeout_duration: Fadeout duration in seconds
        ffmpeg_bin: Path to ffmpeg binary
    """
    extension_needed = beat_end_time - target_duration
    
    if extension_needed <= 0:
        # No extension needed, just trim to beat boundary with fadeout
        trim_last_clip(clip_path, output_path, beat_end_time, fadeout_duration, ffmpeg_bin)
        return
    
    # Use tpad to extend by freezing last frame
    # Then add fadeout
    video_filter = (
        f"tpad=stop_mode=clone:stop_duration={extension_needed:.3f},"
        f"fade=t=out:st={beat_end_time - fadeout_duration:.3f}:d={fadeout_duration:.3f}"
    )
    
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin
    
    try:
        (
            ffmpeg.input(str(clip_path))
            .output(
                str(output_path),
                vf=video_filter,
                vcodec=DEFAULT_VIDEO_CODEC,
                preset="medium",
                crf=DEFAULT_CRF,
                **{"an": None},  # Remove audio
            )
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:  # type: ignore[attr-defined]
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"Failed to extend clip to beat boundary: {stderr}") from e


def verify_composed_video(
    video_path: str | Path,
    expected_resolution: tuple[int, int] = DEFAULT_TARGET_RESOLUTION,
    expected_fps: int = DEFAULT_TARGET_FPS,
    ffmpeg_bin: str | None = None,
) -> CompositionResult:
    """
    Verify composed video meets quality requirements.

    Args:
        video_path: Path to video file
        expected_resolution: Expected resolution (width, height)
        expected_fps: Expected FPS
        ffmpeg_bin: Path to ffmpeg binary (defaults to config)

    Returns:
        CompositionResult with video metadata

    Raises:
        RuntimeError: If verification fails or video doesn't meet requirements
    """
    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin
    ffprobe_bin = ffmpeg_bin.replace("ffmpeg", "ffprobe")

    try:
        probe_cmd = [
            ffprobe_bin,
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate,codec_type",
            "-show_entries",
            "format=duration,size",
            "-of",
            "json",
            str(video_path),
        ]

        result = subprocess.run(
            probe_cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        probe_data = json.loads(result.stdout)

        # Extract video stream info
        # When using -select_streams v:0, the stream should be the first (and only) one
        streams = probe_data.get("streams", [])
        video_stream = None
        
        if streams:
            # If we selected v:0, the first stream should be video
            # But check codec_type if available for safety
            first_stream = streams[0]
            if first_stream.get("codec_type") == "video" or "width" in first_stream:
                video_stream = first_stream
            else:
                # Fallback: search for video stream by codec_type
                for stream in streams:
                    if stream.get("codec_type") == "video":
                        video_stream = stream
                        break

        if not video_stream:
            raise RuntimeError("No video stream found in composed video")

        # Parse frame rate
        r_frame_rate = video_stream.get("r_frame_rate", "30/1")
        if "/" in r_frame_rate:
            num, den = map(int, r_frame_rate.split("/"))
            fps = round(num / den) if den > 0 else expected_fps
        else:
            fps = round(float(r_frame_rate))

        format_info = probe_data.get("format", {})
        duration_sec = float(format_info.get("duration", 0))
        file_size_bytes = int(format_info.get("size", 0))

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        # Verify requirements
        expected_width, expected_height = expected_resolution
        if width != expected_width or height != expected_height:
            raise RuntimeError(
                f"Resolution mismatch: expected {expected_width}x{expected_height}, got {width}x{height}"
            )

        if abs(fps - expected_fps) > 1:  # Allow 1 FPS tolerance
            logger.warning(f"FPS mismatch: expected {expected_fps}, got {fps}")

        if file_size_bytes == 0:
            raise RuntimeError("Composed video file is empty")

        if duration_sec <= 0:
            raise RuntimeError(f"Invalid duration: {duration_sec}")

        return CompositionResult(
            output_path=Path(video_path),
            duration_sec=duration_sec,
            file_size_bytes=file_size_bytes,
            width=width,
            height=height,
            fps=fps,
        )

    except subprocess.TimeoutExpired:
        raise RuntimeError("Timeout verifying composed video")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to verify composed video: {e.stderr}") from e
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Failed to parse video metadata: {e}") from e


def generate_video_poster(
    video_path: str | Path,
    output_path: str | Path,
    time_offset_sec: float = 0.5,
    ffmpeg_bin: str | None = None,
) -> None:
    """
    Capture a single frame from the composed video to use as a poster/thumbnail.

    Args:
        video_path: Path to the input video file.
        output_path: Path where the poster image will be written.
        time_offset_sec: Timestamp (in seconds) to capture the frame from.
        ffmpeg_bin: Path to the ffmpeg binary (defaults to config).
    """

    settings = get_settings()
    ffmpeg_bin = ffmpeg_bin or settings.ffmpeg_bin
    offset = max(time_offset_sec, 0.0)

    try:
        (
            ffmpeg.input(str(video_path), ss=offset)
            .output(str(output_path), vframes=1)
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True, capture_stderr=True)
        )
    except ffmpeg.Error as e:  # type: ignore[attr-defined]
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else str(e.stderr)
        raise RuntimeError(f"Failed to generate poster frame: {stderr}") from e

