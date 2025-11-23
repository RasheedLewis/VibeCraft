# Composition Script vs Real Pipeline Comparison

This document compares `scripts/compose_local.py` (local testing script) with `backend/app/services/composition_execution.py` (production pipeline) to identify ALL differences other than S3 download/upload.

## Summary of Differences

### 1. **Duration Source**
- **Local Script**: Uses `ffprobe` to get audio duration from audio file
  ```python
  probe_cmd = [ffprobe_bin, "-v", "error", "-show_entries", "format=duration", ...]
  audio_duration = float(audio_data["format"]["duration"])
  ```
- **Real Pipeline**: Uses `song.duration_sec` from database
  ```python
  song_duration = song.duration_sec or 0
  ```

### 2. **Duration Mismatch Calculation** ✅ FIXED
- **Local Script**: Uses `metadata_list` from validation if available, otherwise calculates using `ffprobe`
  ```python
  if metadata_list:
      total_clip_duration = sum(m.duration_sec for m in metadata_list)
      last_clip_duration = metadata_list[-1].duration_sec
  else:
      # If validation was skipped, get durations using ffprobe
      clip_durations = [get_clip_duration(normalized_path, ffprobe_bin) for ...]
      total_clip_duration = sum(clip_durations)
      last_clip_duration = clip_durations[-1]
  ```
- **Real Pipeline**: Always uses `clip_metadata_list` from validation
  ```python
  total_clip_duration = sum(m.duration_sec for m in clip_metadata_list)
  if song_duration > 0 and total_clip_duration < song_duration:
      # extend last clip
  ```
  **Note**: Both now handle duration mismatch correctly in all cases.

### 3. **Duration Mismatch Extension Calculation**
- **Local Script**: 
  ```python
  target_duration_sec=audio_duration - total_clip_duration + last_clip_duration
  ```
  (where `last_clip_duration` comes from `metadata_list[-1].duration_sec` or `ffprobe` if validation skipped)
- **Real Pipeline**:
  ```python
  target_duration_sec=song_duration - total_clip_duration + clip_metadata_list[-1].duration_sec
  ```
  **Note**: These are mathematically equivalent if `audio_duration == song.duration_sec` and durations match.

### 4. **Validation Step**
- **Local Script**: Optional (can skip with `--skip-validation` flag)
  ```python
  if not args.skip_validation:
      metadata_list = validate_composition_inputs(...)
  else:
      metadata_list = None
  ```
- **Real Pipeline**: Always validates
  ```python
  clip_metadata_list = validate_composition_inputs(clip_urls)
  ```

### 5. **Duration Cap Check**
- **Local Script**: No duration cap check
- **Real Pipeline**: Checks `MAX_DURATION_SECONDS` (5 minutes)
  ```python
  if song.duration_sec and song.duration_sec > MAX_DURATION_SECONDS:
      raise ValueError(f"Song duration ({song.duration_sec}s) exceeds maximum ({MAX_DURATION_SECONDS}s)")
  ```

### 6. **Job Cancellation Checks**
- **Local Script**: No cancellation checks
- **Real Pipeline**: Checks for cancellation at multiple points:
  - Before starting: `if job.status == "cancelled": return`
  - During download: Checks before each clip download
  - During normalization: Checks in `normalize_single_clip` function

### 7. **Target Resolution/FPS**
- **Local Script**: Configurable via command-line args (defaults: 1920x1080 @ 24fps)
  ```python
  parser.add_argument("--fps", type=int, default=24)
  parser.add_argument("--resolution", nargs=2, type=int, default=[1920, 1080])
  target_resolution = tuple(args.resolution)
  target_fps = args.fps
  ```
- **Real Pipeline**: Uses hardcoded defaults from `video_composition.py`
  ```python
  DEFAULT_TARGET_RESOLUTION = (1920, 1080)
  DEFAULT_TARGET_FPS = 24
  ```
  **Note**: Both use same defaults, but local script allows override.

### 8. **FFmpeg Binary Path**
- **Local Script**: Can override via `--ffmpeg-bin` command-line arg
  ```python
  parser.add_argument("--ffmpeg-bin", help="Custom FFmpeg binary path")
  normalize_clip(..., ffmpeg_bin=args.ffmpeg_bin)
  ```
- **Real Pipeline**: Always uses config default
  ```python
  normalize_clip(clip_path, normalized_path)  # Uses default from config
  ```

### 9. **Function Call Signatures**
- **Local Script**: Passes `str` paths and explicit parameters
  ```python
  normalize_clip(
      str(clip_path),
      str(normalized_path),
      target_resolution=target_resolution,
      target_fps=target_fps,
      ffmpeg_bin=args.ffmpeg_bin,
  )
  concatenate_clips(
      normalized_clip_paths=[str(p) for p in normalized_paths],
      audio_path=str(audio_path),
      output_path=str(temp_output),
      song_duration_sec=audio_duration,
      ffmpeg_bin=args.ffmpeg_bin,
  )
  extend_last_clip(
      str(last_clip_path),
      str(extended_path),
      target_duration_sec=...,
      ffmpeg_bin=args.ffmpeg_bin,
  )
  ```
- **Real Pipeline**: Passes `Path` objects and uses defaults
  ```python
  normalize_clip(clip_path, normalized_path)  # Uses defaults for resolution/FPS
  concatenate_clips(
      normalized_clip_paths=normalized_paths,  # Path objects
      audio_path=audio_path,
      output_path=output_path,
      song_duration_sec=song_duration,
  )
  extend_last_clip(
      last_clip_path,
      extended_path,
      target_duration_sec=...,
  )
  ```
  **Note**: Function signatures accept both `str | Path`, so this is just a style difference.

### 10. **Error Handling**
- **Local Script**: Returns exit codes (0/1) and logs errors
  ```python
  except Exception as e:
      logger.error(f"Validation failed: {e}")
      return 1
  ```
- **Real Pipeline**: Updates job status and raises exceptions
  ```python
  except Exception as e:
      logger.exception(f"Composition pipeline failed for job {job_id}")
      error_message = str(e)
      fail_job(job_id, error_message)
      raise
  ```

### 11. **Progress Tracking**
- **Local Script**: Logs progress to console (just added)
  ```python
  log_progress(progress, stage)  # Just logs: "[{progress}%] {stage}"
  ```
- **Real Pipeline**: Updates database via `update_job_progress()`
  ```python
  update_job_progress(job_id, progress, "processing")
  ```

### 12. **ComposedVideo Record Creation**
- **Local Script**: Does not create database record
- **Real Pipeline**: Creates `ComposedVideo` record after upload
  ```python
  composed_video = create_composed_video(
      song_id=song_id,
      s3_key=s3_key,
      duration_sec=verify_result.duration_sec,
      file_size_bytes=verify_result.file_size_bytes,
      resolution_width=verify_result.width,
      resolution_height=verify_result.height,
      fps=verify_result.fps,
      clip_ids=clip_ids,
  )
  ```

### 13. **Verification Parameters**
- **Local Script**: Passes explicit expected resolution/FPS
  ```python
  verify_composed_video(
      str(temp_output),
      expected_resolution=target_resolution,
      expected_fps=target_fps,
      ffmpeg_bin=args.ffmpeg_bin,
  )
  ```
- **Real Pipeline**: Uses defaults (no explicit expected values)
  ```python
  verify_result = verify_composed_video(output_path)
  ```
  **Note**: `verify_composed_video` has optional `expected_resolution` and `expected_fps` parameters, so this is just a difference in usage.

### 14. **Temp Directory Handling**
- **Local Script**: Can keep temp files with `--keep-temp` flag
  ```python
  if args.keep_temp:
      temp_dir = Path(tempfile.mkdtemp(prefix="compose_"))
      temp_dir_context = None
  else:
      temp_dir_context = tempfile.TemporaryDirectory(prefix="compose_")
      temp_dir = Path(temp_dir_context.__enter__())
  ```
- **Real Pipeline**: Always uses `TemporaryDirectory` context manager (auto-cleanup)
  ```python
  with tempfile.TemporaryDirectory() as temp_dir:
      temp_path = Path(temp_dir)
      # ... work ...
  ```

### 15. **Input Source**
- **Local Script**: Takes file paths from command-line args
  ```python
  clip_paths = [expand_path(c) for c in args.clips]
  audio_path = expand_path(args.audio)
  ```
- **Real Pipeline**: Downloads from URLs/S3
  ```python
  clip_urls = [clip.video_url for clip in clips]
  audio_bytes = download_bytes_from_s3(...)
  ```

### 16. **Output Destination**
- **Local Script**: Saves to local file path
  ```python
  shutil.copy2(temp_output, output_path)
  ```
- **Real Pipeline**: Uploads to S3 and creates database record
  ```python
  upload_bytes_to_s3(bucket_name=settings.s3_bucket_name, key=s3_key, data=video_bytes, ...)
  create_composed_video(...)
  ```

## Potential Issues

### 1. **Duration Mismatch Logic** ✅ FIXED
~~If validation is skipped in local script, `metadata_list` is `None`, so duration mismatch check won't work:~~
**Fixed**: Now calculates clip durations using `ffprobe` if validation is skipped, so duration mismatch handling works in all cases.

### 2. **Duration Source Mismatch**
Local script uses audio file duration from `ffprobe`, while real pipeline uses `song.duration_sec`. These might differ if:
- Song was processed/trimmed
- Database value is stale
- Audio file was modified

**Impact**: Duration mismatch detection might behave differently. However, for local testing, using the actual audio file duration is more accurate and appropriate. The real pipeline uses database values for consistency with the production data model.

**Recommendation**: This is acceptable for a local testing script. If you need to match production exactly, consider adding a `--song-duration` flag to override the audio file duration.

### 3. **Missing Duration Cap**
Local script doesn't check for 5-minute cap, so it could process longer videos.

**Impact**: Local testing might succeed where production would fail.

### 4. **No Cancellation Support**
Local script can't be cancelled mid-execution (except via Ctrl+C).

**Impact**: Long-running compositions can't be gracefully cancelled.

## Recommendations

1. **Fix duration mismatch logic**: Always validate or calculate clip durations even if validation is skipped
2. **Add duration cap check**: Match production behavior
3. **Use same duration source**: Consider using a config file or database lookup for local script
4. **Document differences**: Make it clear in script help text that it's for testing only

