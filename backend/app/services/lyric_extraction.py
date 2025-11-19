"""Lyric extraction service using Whisper via Replicate API."""

import logging
import time
from pathlib import Path
from typing import List, Optional

import replicate

from app.core.config import get_settings
from app.core.constants import WHISPER_MODEL
from app.schemas.analysis import SectionLyrics, SongSection

logger = logging.getLogger(__name__)


def extract_lyrics_with_whisper(audio_path: str | Path) -> List[dict]:
    """
    Extract lyrics from audio file using Whisper via Replicate.

    Args:
        audio_path: Path to audio file

    Returns:
        List of dicts with 'start', 'end', 'text' keys (timestamps in seconds)
    """
    try:
        settings = get_settings()
        if not settings.replicate_api_token:
            logger.error("REPLICATE_API_TOKEN not configured")
            return []

        # Create Replicate client with API token
        client = replicate.Client(api_token=settings.replicate_api_token)

        # Replicate expects audio as a file object (it handles upload automatically)
        # Open audio file
        whisper_start = time.time()
        with open(audio_path, "rb") as audio_file:
            # Run Whisper on Replicate
            # Note: audio parameter accepts file-like objects, Replicate handles upload
            output = client.run(
                WHISPER_MODEL,
                input={
                    "audio": audio_file,
                    "transcription": "plain text",  # Format: plain text, srt, vtt, json, verbose_json, text
                    "translate": False,  # Don't translate to English
                    "language": "auto",  # Auto-detect language
                    "temperature": 0,
                    "condition_on_previous_text": True,
                },
            )
        whisper_time = time.time() - whisper_start
        logger.info("Lyric extraction - Whisper API call: %.2fs", whisper_time)

        # Parse output - Replicate Whisper returns segments with start, end, text
        segments = []
        if isinstance(output, dict) and "segments" in output:
            segments = output["segments"]
        elif isinstance(output, list):
            segments = output
        else:
            logger.warning(f"Unexpected Whisper output format: {type(output)}")
            return []

        # Format segments
        result = []
        for segment in segments:
            if isinstance(segment, dict) and "start" in segment and "text" in segment:
                result.append(
                    {
                        "start": float(segment["start"]),
                        "end": float(segment.get("end", segment["start"] + 1.0)),
                        "text": segment["text"].strip(),
                    }
                )

        logger.info(f"Extracted {len(result)} lyric segments from {audio_path}")
        return result

    except Exception as e:
        logger.error(f"Error extracting lyrics with Whisper: {e}")
        return []


def segment_lyrics_into_lines(segments: List[dict], min_line_duration: float = 0.5) -> List[dict]:
    """
    Segment ASR output into timed lines, combining short segments.

    Args:
        segments: List of dicts with 'start', 'end', 'text' keys
        min_line_duration: Minimum duration for a line (seconds)

    Returns:
        List of dicts with 'start', 'end', 'text' keys (segmented into lines)
    """
    if not segments:
        return []

    lines = []
    current_line = None

    for segment in segments:
        start = segment["start"]
        end = segment["end"]
        text = segment["text"]

        # Skip empty segments (including whitespace-only)
        if not text or not text.strip():
            continue

        # Start new line if we don't have one
        if current_line is None:
            current_line = {"start": start, "end": end, "text": text}
            continue

        # If segment is close to current line and short, combine them
        gap = start - current_line["end"]
        segment_duration = end - start

        if gap < 1.0 and segment_duration < min_line_duration:
            # Combine with current line
            current_line["end"] = end
            current_line["text"] += " " + text
        else:
            # Save current line and start new one
            if current_line["end"] - current_line["start"] >= min_line_duration:
                lines.append(current_line)
            current_line = {"start": start, "end": end, "text": text}

    # Add final line
    if current_line and current_line["end"] - current_line["start"] >= min_line_duration:
        lines.append(current_line)

    return lines


def align_lyrics_to_sections(
    lyric_lines: List[dict], sections: List[SongSection]
) -> List[SectionLyrics]:
    """
    Align lyric lines to song sections based on timestamps.

    Args:
        lyric_lines: List of dicts with 'start', 'end', 'text' keys
        sections: List of SongSection objects

    Returns:
        List of SectionLyrics objects aligned to sections
    """
    if not lyric_lines or not sections:
        return []

    section_lyrics: List[SectionLyrics] = []

    for section in sections:
        section_start = section.start_sec
        section_end = section.end_sec

        # Find all lyric lines that overlap with this section
        section_text_lines = []
        for line in lyric_lines:
            line_start = line["start"]
            line_end = line["end"]

            # Check if line overlaps with section (with small tolerance)
            if line_start < section_end and line_end > section_start:
                section_text_lines.append(line["text"])

        # Combine lines into section text
        if section_text_lines:
            section_text = " ".join(section_text_lines)
            # Truncate if too long (keep first ~200 chars for preview)
            if len(section_text) > 200:
                section_text = section_text[:200] + "..."

            section_lyrics.append(
                SectionLyrics(
                    sectionId=section.id,
                    startSec=section_start,
                    endSec=section_end,
                    text=section_text,
                )
            )

    return section_lyrics


def extract_and_align_lyrics(
    audio_path: str | Path, sections: Optional[List[SongSection]] = None
) -> tuple[bool, List[SectionLyrics]]:
    """
    Complete lyric extraction and alignment pipeline.

    Args:
        audio_path: Path to audio file
        sections: Optional list of SongSection objects (if None, returns empty list)

    Returns:
        Tuple of (lyrics_available, section_lyrics_list)
    """
    # Extract lyrics with Whisper
    segments = extract_lyrics_with_whisper(audio_path)
    if not segments:
        return False, []

    # Segment into lines
    lyric_lines = segment_lyrics_into_lines(segments)

    # Align to sections if provided
    if sections:
        section_lyrics = align_lyrics_to_sections(lyric_lines, sections)
        return True, section_lyrics

    # If no sections, return empty list but indicate lyrics are available
    return True, []

