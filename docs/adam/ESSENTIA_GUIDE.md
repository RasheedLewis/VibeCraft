# Essentia Guide for VibeCraft

## What is Essentia?

**Essentia** is a C++ library for audio analysis and music information retrieval (MIR) developed by the [Music Technology Group (MTG)](https://essentia.upf.edu/) at Universitat Pompeu Fabra. It provides Python bindings, making it accessible from Python code.

### Key Features

- **Advanced audio analysis**: BPM detection, beat tracking, key detection, onset detection
- **Music descriptors**: Spectral features, rhythm features, tonal features
- **Pre-trained models**: Genre classification, mood detection, music similarity
- **High performance**: C++ backend with optimized algorithms
- **Comprehensive**: 400+ algorithms for audio analysis

## Essentia vs Librosa

| Feature | Librosa | Essentia |
|---------|---------|----------|
| **Language** | Pure Python | C++ with Python bindings |
| **Performance** | Good | Excellent (C++ backend) |
| **Ease of use** | Very easy | Moderate (more complex API) |
| **Features** | Core MIR features | Extensive (400+ algorithms) |
| **Installation** | `pip install librosa` | Requires C++ build or pre-built wheels |
| **Pre-trained models** | Limited | Extensive (genre, mood, etc.) |

## Installation

### Option 1: Pre-built Wheels (Recommended)

Essentia can be installed via pip, but availability depends on your platform:

```bash
# Try installing directly (may not work on all platforms)
pip install essentia

# If that fails, you may need to build from source or use conda
```

### Option 2: Conda (Most Reliable)

```bash
conda install -c conda-forge essentia
```

### Option 3: Build from Source

If pre-built wheels aren't available, you'll need to build from source:

```bash
# Install dependencies
# macOS:
brew install libyaml fftw

# Ubuntu/Debian:
sudo apt-get install build-essential libyaml-dev libfftw3-dev

# Then build Essentia
git clone https://github.com/MTG/essentia.git
cd essentia
python3 waf configure --mode=release --with-python
python3 waf
python3 waf install
```

### Option 4: Essentia-TensorFlow (For ML Models)

If you want pre-trained models for genre/mood classification:

```bash
pip install essentia-tensorflow
```

This includes TensorFlow-based models for:
- Genre classification
- Mood detection
- Music similarity

## Usage in VibeCraft

### Current Status

According to `PR05_READINESS.md`, Essentia is **optional** for PR-05. The recommendation is to:

1. **Start simple**: Use `librosa` for MVP (already installed)
2. **Upgrade later**: Add Essentia if you need more advanced features or better performance

### When to Use Essentia

**Use Essentia if you need:**
- More accurate BPM detection (especially for complex rhythms)
- Pre-trained genre/mood models (via `essentia-tensorflow`)
- Advanced rhythm features (beat tracking, onset detection)
- Better performance on large audio files
- Key detection and harmonic analysis

**Stick with Librosa if:**
- You're building an MVP quickly
- You need simple spectral features (centroid, rolloff, etc.)
- You want easier Python integration
- You don't need pre-trained models

### Example: BPM Detection with Essentia

```python
import essentia.standard as es

# Load audio
audio = es.MonoLoader(filename='song.mp3', sampleRate=44100)()

# Detect BPM
rhythm_extractor = es.RhythmExtractor2013(method="multifeature")
bpm, beats, beats_confidence, _, beats_intervals = rhythm_extractor(audio)

print(f"BPM: {bpm}")
print(f"Beats: {beats}")
```

### Example: Genre Classification with Essentia-TensorFlow

```python
import essentia.standard as es
from essentia_tensorflow import EssentiaTensorflowPredictMusiCNN

# Load audio
audio = es.MonoLoader(filename='song.mp3', sampleRate=16000)()

# Load pre-trained genre model
predictor = EssentiaTensorflowPredictMusiCNN(
    graphFilename='models/genre_dortmund-musicnn-msd-1.pb',
    output='model/Softmax'
)

# Extract features and predict
pool = es.Pool()
for frame in es.FrameGenerator(audio, frameSize=512, hopSize=256):
    pool.add('frames', frame)

predictions = predictor(pool['frames'])
genres = ['rock', 'pop', 'electronic', 'hip-hop', 'jazz', 'classical']
genre_scores = dict(zip(genres, predictions[0]))
```

### Example: Mood Detection

```python
import essentia.standard as es
from essentia_tensorflow import EssentiaTensorflowPredictMusiCNN

# Load audio
audio = es.MonoLoader(filename='song.mp3', sampleRate=16000)()

# Extract mood features
pool = es.Pool()
for frame in es.FrameGenerator(audio, frameSize=512, hopSize=256):
    pool.add('frames', frame)

# Use pre-trained mood model (if available)
# Or compute low-level features for mood inference
spectral_centroid = es.SpectralCentroid()
centroid = spectral_centroid(audio)

# Energy
rms = es.RMS()
energy = rms(audio)

# These can be mapped to mood dimensions:
# - Energy: RMS energy
# - Valence: Spectral centroid (brightness)
# - Tension: Spectral rolloff
```

## Integration into VibeCraft

### For PR-05 (Genre & Mood Classification)

**Recommended approach:**

1. **Start with librosa** (already installed):
   ```python
   import librosa
   
   # Extract features
   y, sr = librosa.load('song.mp3')
   tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
   spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
   ```

2. **Add Essentia later** if needed:
   - More accurate BPM detection
   - Pre-trained genre/mood models
   - Better beat tracking

### Adding to requirements.txt

If you decide to use Essentia, add it to `backend/requirements.txt`:

```txt
# Optional: Advanced audio analysis
# essentia  # Uncomment if using Essentia
# essentia-tensorflow  # Uncomment for pre-trained models
```

**Note:** Essentia installation can be tricky, so it's marked as optional. The project works fine with just `librosa` for MVP.

## Resources

- **Official Website**: https://essentia.upf.edu/
- **GitHub**: https://github.com/MTG/essentia
- **Documentation**: https://essentia.upf.edu/documentation/
- **Python Tutorial**: https://essentia.upf.edu/essentia_python_tutorial.html
- **Algorithms Reference**: https://essentia.upf.edu/reference/

## Summary

- **Essentia** = C++ library with Python bindings for advanced audio analysis
- **Optional** for VibeCraft PR-05 (librosa is sufficient for MVP)
- **Use Essentia if**: You need pre-trained models, better BPM accuracy, or advanced features
- **Start with librosa**: Easier to use, already installed, sufficient for MVP
- **Upgrade path**: Can add Essentia later without breaking existing code

