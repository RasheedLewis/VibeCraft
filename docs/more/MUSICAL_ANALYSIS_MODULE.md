# Musical Analysis Module

## Current Implementation

VibeCraft uses **librosa** for all audio analysis tasks. The implementation is in `backend/app/services/`:

- **`song_analysis.py`** - Main analysis pipeline (BPM, beat tracking, sections)
- **`genre_mood_analysis.py`** - Genre and mood classification
- **`audio_preprocessing.py`** - Audio preprocessing and waveform generation

## What We Use: Librosa

### BPM Detection & Beat Tracking

```python
# backend/app/services/song_analysis.py
y, sr = librosa.load(str(audio_path), sr=None, mono=True)
tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
beat_times = librosa.frames_to_time(beat_frames, sr=sr).tolist()
```

### Mood Features (Energy, Valence, Danceability, Tension)

```python
# backend/app/services/genre_mood_analysis.py
# Uses librosa spectral features:
- spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
- spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
- rms = librosa.feature.rms(y=y)
```

**Mood Vector Mapping:**

- **Energy**: RMS energy (normalized)
- **Valence**: Spectral centroid (brightness) - higher = happier/brighter
- **Tension**: Spectral rolloff (high frequency content)
- **Danceability**: Based on tempo and beat strength

### Genre Classification

```python
# backend/app/services/genre_mood_analysis.py
# Rule-based approach using BPM + mood features
# Uses librosa for tempo detection and spectral features
```

**Current Approach:** Rule-based classification using:

- BPM ranges
- Mood vector values (energy, valence, danceability, tension)
- Spectral features from librosa

**Note:** The code comments mention Essentia/CLAP as potential future ML-based alternatives, but
the current implementation is rule-based using librosa features.

### Section Detection

```python
# backend/app/services/song_analysis.py
# Uses librosa for section segmentation
sections = _detect_sections(y, sr, duration)
```

## Essentia: Not Currently Used

**Essentia** was considered but **not implemented** in the current codebase. The codebase uses
**librosa exclusively** for all audio analysis.

### Why Librosa?

**Advantages:**

- ✅ Easy installation (`pip install librosa`)
- ✅ Simple Python API
- ✅ Sufficient for MVP needs
- ✅ Already integrated and working

**Current Limitations:**

- Rule-based genre classification (not ML-based)
- No pre-trained models for genre/mood
- May be less accurate for complex rhythms

### When to Consider Essentia

**Consider Essentia if you need:**

- Pre-trained ML models for genre/mood classification
- More accurate BPM detection for complex rhythms
- Advanced rhythm features (better beat tracking)
- Key detection and harmonic analysis
- Better performance on large audio files

**Current Status:** The codebase works well with librosa for the MVP. Essentia remains a
potential future enhancement if ML-based genre/mood classification is needed.

## Code Locations

### Main Analysis Pipeline

- **File:** `backend/app/services/song_analysis.py`
- **Function:** `_execute_analysis_pipeline()`
- **What it does:**
  1. Loads audio with librosa
  2. Detects BPM and beat times
  3. Detects song sections
  4. Computes mood features
  5. Classifies genre
  6. Extracts lyrics (Whisper)

### Mood & Genre Analysis

- **File:** `backend/app/services/genre_mood_analysis.py`
- **Functions:**
  - `compute_mood_features()` - Extracts energy, valence, danceability, tension
  - `compute_genre()` - Rule-based genre classification
  - `compute_mood_tags()` - Converts mood vector to tags

### Audio Preprocessing

- **File:** `backend/app/services/audio_preprocessing.py`
- **Function:** `preprocess_audio()`
- **What it does:**
  - Resamples audio to 44.1kHz (via FFmpeg)
  - Generates waveform data (via librosa)

## Dependencies

**Current (in `backend/requirements.txt`):**

- `librosa==0.10.2.post1` - Audio analysis
- `ffmpeg-python==0.2.0` - Audio preprocessing
- `openai-whisper` (via system) - Lyric extraction

**Not used:**

- `essentia` - Not installed or used
- `essentia-tensorflow` - Not installed or used

## Future Enhancements

If you want to add Essentia for ML-based genre/mood classification:

1. **Install Essentia:**

   ```bash
   # Option 1: Try pip (may not work on all platforms)
   pip install essentia
   
   # Option 2: Use conda (most reliable)
   conda install -c conda-forge essentia
   ```

2. **Add to requirements.txt:**

   ```txt
   essentia  # For advanced audio analysis
   essentia-tensorflow  # For pre-trained models
   ```

3. **Update genre_mood_analysis.py:**
   - Replace rule-based classification with Essentia ML models
   - Use pre-trained genre/mood models from essentia-tensorflow

4. **Consider hybrid approach:**
   - Keep librosa for BPM/beat tracking (simpler, works well)
   - Use Essentia for genre/mood ML models (more accurate)

## Resources

- **Librosa Documentation:** <https://librosa.org/doc/latest/>
- **Essentia Website:** <https://essentia.upf.edu/> (not currently used)
- **Essentia GitHub:** <https://github.com/MTG/essentia>
