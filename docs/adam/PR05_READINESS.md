# PR-05 Readiness Checklist: Genre & Mood Classification

## ✅ Ready to Start

### Prerequisites Met

- [x] **Sample audio files available**
  - Found: `samples/audio/electronic/sample1.mp3`
  - Found: `samples/audio/country/Bryan Mathys - It's Not Hard to Get Lost.mp3`
  - ✅ 2 sample files ready for testing

- [x] **Backend structure in place**
  - `backend/app/services/` directory exists
  - `backend/app/schemas/` directory exists
  - FastAPI setup complete

- [x] **Core dependencies installed**
  - `librosa` ✅ (for audio analysis)
  - `numpy` ✅ (usually comes with librosa)
  - FastAPI, SQLModel, etc. ✅

- [x] **Can work independently**
  - PR-05 is independent (works directly with audio)
  - No dependency on PR-04 (can use mock sections if needed)

### What You Need to Add

#### Backend Dependencies (may need to install)

For **mood analysis** (energy, valence, tension):
- `librosa` ✅ (already installed - can compute spectral features)
- Optional: `essentia` or `essentia-tensorflow` (more advanced features)
- Or: Use librosa's built-in features (spectral centroid, rolloff, zero crossing rate)

For **genre classification**:
- Option 1: **CLAP** (Contrastive Language-Audio Pretraining)
  - `transformers` (Hugging Face)
  - `torch` (PyTorch)
  - Model: `laion/larger_clap_music_and_speech`
  
- Option 2: **Simpler approach** (MVP-friendly):
  - Use librosa features + simple classifier
  - Or: Use pre-trained models from `librosa` ecosystem
  - Or: Start with rule-based genre detection (BPM, spectral features)

#### Recommended: Start Simple

For MVP, you can:
1. **Mood features**: Use librosa's built-in features:
   - Energy: RMS energy
   - Valence: Spectral centroid (brightness)
   - Tension: Spectral rolloff
   - Danceability: Tempo + beat strength

2. **Genre**: Start with rule-based or simple ML:
   - Use BPM + spectral features
   - Map to genres: Electronic (>120 BPM), Pop (100-120), Rock (80-120), etc.
   - Can upgrade to CLAP later

## PR-05 Subtasks Breakdown

### Backend (Subtasks 32-36)

1. **Compute mood features** (librosa)
   - Extract audio features
   - Compute energy, valence, tension, danceability
   - Normalize to 0-1 range

2. **Build genre classifier**
   - Start simple: BPM + spectral features → genre
   - Or: Integrate CLAP model
   - Map to standardized genre list

3. **Map to standardized genres**
   - Define genre taxonomy (Electronic, Pop, Rock, Hip-Hop, etc.)
   - Map classifier output to standard genres

4. **Compute moodTags and moodVector**
   - Convert numeric features to tags (e.g., "energetic", "chill")
   - Create MoodVector object

5. **Integrate into analysis object**
   - Add to SongAnalysis schema
   - Store in database

### Frontend (Subtask 37)

6. **Add genre/mood display UI badges**
   - Create badge components
   - Display in Song Profile page
   - Style according to design system

## Next Steps

1. **Install additional dependencies** (if using CLAP):
   ```bash
   pip install transformers torch
   ```

2. **Or start simple** (recommended for MVP):
   - Use librosa features only
   - Implement rule-based genre detection
   - Can upgrade later

3. **Create service file**:
   - `backend/app/services/genre_mood_analysis.py`

4. **Create schemas**:
   - Add MoodVector, genre fields to analysis schemas

5. **Test with sample files**:
   - Run analysis on your 2 sample songs
   - Verify outputs make sense

## Files to Create

- `backend/app/services/genre_mood_analysis.py` - Main analysis logic
- `backend/app/schemas/analysis_schemas.py` - Add MoodVector, genre fields (if not exists)
- `frontend/src/components/vibecraft/GenreBadge.tsx` - Genre display component
- `frontend/src/components/vibecraft/MoodBadge.tsx` - Mood tag display component

## Recommendation

**Start simple for MVP:**
- Use librosa's built-in features for mood
- Use BPM + spectral features for genre (rule-based)
- Get it working end-to-end
- Upgrade to CLAP/ML models later if needed

This gets you a working feature faster and you can iterate.

---

**Status: ✅ READY TO START PR-05**

You have everything you need to begin. Start with the simple approach and iterate!

