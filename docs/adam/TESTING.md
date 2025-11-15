# Quick Testing Guide

## PR-05 — Genre & Mood Classification

Run `source .venv/bin/activate && python backend/test_genre_mood.py` with sample audio. Verify analysis response includes `primaryGenre`, `moodTags`, and `moodVector` fields. Start dev server and verify `GenreBadge` and `MoodBadge` components render correctly with no console errors at `http://localhost:5173`.
