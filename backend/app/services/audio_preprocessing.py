from __future__ import annotations

import json
import math
import tempfile
from dataclasses import dataclass
from pathlib import Path

import ffmpeg
import librosa
import numpy as np

from app.core.config import get_settings


@dataclass(slots=True)
class AudioPreprocessingResult:
    processed_bytes: bytes
    processed_extension: str
    content_type: str
    sample_rate: int
    duration_sec: float
    waveform_json: str


def preprocess_audio(
    *,
    file_bytes: bytes,
    original_suffix: str,
    target_sample_rate: int = 44_100,
    waveform_points: int = 512,
) -> AudioPreprocessingResult:
    """
    Downmix audio to mono, resample to the target rate, and generate waveform data.

    Args:
        file_bytes: Raw bytes from the uploaded audio file.
        original_suffix: File suffix (extension) used for temporary storage.
        target_sample_rate: Desired output sample rate in Hz.
        waveform_points: Number of samples to keep in the waveform JSON payload.

    Raises:
        RuntimeError: If ffmpeg or librosa fail to process the file.
    """

    settings = get_settings()
    input_suffix = original_suffix if original_suffix.startswith(".") else f".{original_suffix}"
    output_suffix = ".wav"

    with tempfile.NamedTemporaryFile(delete=False, suffix=input_suffix) as input_tmp:
        input_path = Path(input_tmp.name)
        input_tmp.write(file_bytes)

    with tempfile.NamedTemporaryFile(delete=False, suffix=output_suffix) as output_tmp:
        output_path = Path(output_tmp.name)

    try:
        _run_ffmpeg_resample(
            input_path=input_path,
            output_path=output_path,
            sample_rate=target_sample_rate,
            ffmpeg_bin=settings.ffmpeg_bin,
        )

        processed_bytes = output_path.read_bytes()
        waveform = _generate_waveform(output_path, sample_rate=target_sample_rate, points=waveform_points)

        duration_sec = float(librosa.get_duration(path=str(output_path), sr=target_sample_rate))

        return AudioPreprocessingResult(
            processed_bytes=processed_bytes,
            processed_extension=output_suffix,
            content_type="audio/wav",
            sample_rate=target_sample_rate,
            duration_sec=duration_sec,
            waveform_json=json.dumps(waveform),
        )
    finally:
        try:
            input_path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass
        try:
            output_path.unlink(missing_ok=True)
        except FileNotFoundError:
            pass


def _run_ffmpeg_resample(
    *,
    input_path: Path,
    output_path: Path,
    sample_rate: int,
    ffmpeg_bin: str = "ffmpeg",
) -> None:
    try:
        (
            ffmpeg.input(str(input_path))
            .output(
                str(output_path),
                ac=1,  # mono downmix
                ar=sample_rate,
                format="wav",
            )
            .overwrite_output()
            .run(cmd=ffmpeg_bin, quiet=True)
        )
    except ffmpeg.Error as exc:  # type: ignore[attr-defined]
        raise RuntimeError("Failed to resample audio with ffmpeg") from exc


def _generate_waveform(audio_path: Path, *, sample_rate: int, points: int) -> list[float]:
    try:
        samples, _ = librosa.load(str(audio_path), sr=sample_rate, mono=True)
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("Failed to load processed audio for waveform generation") from exc

    if samples.size == 0:
        return [0.0] * points

    # Chunk the samples so we end up with the desired number of points.
    total_samples = samples.size
    chunk_size = max(1, math.floor(total_samples / points))

    chunks = _chunk_array(samples, chunk_size)
    rms = np.sqrt(np.mean(np.square(chunks), axis=1))

    max_rms = float(np.max(rms))
    if max_rms > 0:
        rms /= max_rms

    if rms.size < points:
        padding = np.zeros(points - rms.size)
        rms = np.concatenate([rms, padding])
    elif rms.size > points:
        rms = rms[:points]

    return rms.astype(float).tolist()


def _chunk_array(array: np.ndarray, chunk_size: int) -> np.ndarray:
    length = len(array)
    trimmed_length = (length // chunk_size) * chunk_size
    trimmed = array[:trimmed_length]
    if trimmed.size == 0:
        return array.reshape(-1, 1)
    reshaped = trimmed.reshape(-1, chunk_size)
    return reshaped

