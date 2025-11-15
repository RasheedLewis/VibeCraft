# Quick Testing Guide

## PR-05 — Genre & Mood Classification

**Unit tests:** `pytest backend/tests/unit/test_genre_mood_analysis.py -v` (fast, no audio files)

**Integration test:** `source .venv/bin/activate && python backend/tests/test_genre_mood.py` with sample audio. Verify analysis response includes `primaryGenre`, `moodTags`, and `moodVector` fields.

**Frontend:** Start dev server and verify `GenreBadge` and `MoodBadge` components render correctly with no console errors at `http://localhost:5173`.

## PR-06 — Lyric Extraction & Section Alignment

**Unit tests:** `pytest backend/tests/unit/test_lyric_extraction.py -v` (fast, no audio files or API calls)

**Integration test:** `source .venv/bin/activate && python backend/tests/test_lyrics.py` with sample audio (requires Replicate API token). Verify `sectionLyrics[]` array is populated with timed text aligned to sections. Check lyric previews appear in section cards.
