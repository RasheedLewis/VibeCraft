# Sample Audio Files Guide

This guide helps you find and use royalty-free, legal music for testing and development.

---

## 🎵 **Recommended Sources for Royalty-Free Music**

### **1. Free Music Archive (FMA)**
- **URL:** https://freemusicarchive.org/
- **License:** Various (CC0, CC BY, etc.) - check individual tracks
- **Best for:** Diverse genres, high quality
- **How to use:** Search by genre, download MP3/WAV
- **Note:** Many tracks are CC0 (public domain) or CC BY (attribution required)

### **2. Incompetech (Kevin MacLeod)**
- **URL:** https://incompetech.com/music/royalty-free/
- **License:** CC BY 3.0 (attribution required)
- **Best for:** Background music, various moods
- **How to use:** Browse by genre/mood, download MP3
- **Note:** Very popular for YouTube/video projects

### **3. YouTube Audio Library**
- **URL:** https://www.youtube.com/audiolibrary
- **License:** Free to use (check individual track licenses)
- **Best for:** Quick access, diverse selection
- **How to use:** Filter by genre/mood/duration, download MP3
- **Note:** Requires YouTube account, but free

### **4. Freesound (for samples, not full songs)**
- **URL:** https://freesound.org/
- **License:** Various CC licenses
- **Best for:** Audio samples, loops, sound effects
- **Note:** More for samples than full songs

### **5. Jamendo**
- **URL:** https://www.jamendo.com/
- **License:** Various (check per track)
- **Best for:** Independent artists, diverse genres
- **Note:** Some tracks require attribution

### **6. Pixabay Music**
- **URL:** https://pixabay.com/music/
- **License:** Pixabay License (free for commercial use, no attribution required)
- **Best for:** Commercial projects, no attribution needed
- **How to use:** Search by genre/mood, download MP3
- **Note:** Excellent for testing without attribution concerns

### **7. Bensound**
- **URL:** https://www.bensound.com/
- **License:** Free with attribution (or paid without)
- **Best for:** Professional-sounding tracks
- **Note:** Attribution required for free tier

---

## 📁 **Recommended Directory Structure**

Create a `samples/` directory in the project root:

```
VibeCraft/
  samples/
    audio/
      electronic/
        track-1.mp3
        track-2.mp3
      pop-rock/
        track-1.mp3
      hip-hop/
        track-1.mp3
    metadata/
      track-1.json  # Optional: store metadata about each track
```

---

## 🎯 **Recommended Test Tracks**

For development, aim to have at least 3-5 sample tracks covering:

1. **Electronic/EDM** (120-140 BPM)
   - Good for testing beat detection
   - Clear sections (intro, drop, breakdown)
   - Example: Search FMA for "electronic" or "EDM"

2. **Pop/Rock** (80-120 BPM)
   - Good for testing verse/chorus detection
   - Clear vocal sections
   - Example: Search Incompetech for "pop" or "rock"

3. **Hip-Hop** (70-100 BPM)
   - Good for testing hook/verse patterns
   - Strong beat grid
   - Example: Search FMA for "hip hop" or "rap"

4. **Ambient/Chill** (60-80 BPM)
   - Good for testing mood classification
   - Less clear sections (challenging)
   - Example: Search Pixabay for "ambient" or "chill"

5. **High Energy** (140+ BPM)
   - Good for testing tempo detection limits
   - Fast transitions
   - Example: Search for "drum and bass" or "hardcore"

---

## ⚖️ **License Checklist**

Before using any track, verify:

- [ ] License allows commercial use (if needed)
- [ ] Attribution requirements (if any)
- [ ] Modification allowed (if you plan to process/analyze)
- [ ] Redistribution allowed (if storing in repo)

**For development/testing:** CC0 or CC BY licenses are usually fine.

**For demo/showcase:** Use tracks that allow commercial use.

---

## 📝 **Sample Metadata Template**

Create a `metadata.json` file for each track:

```json
{
  "filename": "track-1.mp3",
  "source": "Free Music Archive",
  "license": "CC BY 4.0",
  "artist": "Artist Name",
  "title": "Track Title",
  "url": "https://freemusicarchive.org/...",
  "genre": "Electronic",
  "expectedBPM": 128,
  "expectedDuration": 210,
  "notes": "Good for testing beat detection"
}
```

---

## 🚀 **Quick Start**

1. **Download 3-5 sample tracks** from Pixabay or FMA
2. **Create `samples/audio/` directory** in project root
3. **Organize by genre** (electronic, pop-rock, hip-hop)
4. **Add to `.gitignore`** if files are large:
   ```
   # Sample audio files (optional - can commit small samples)
   samples/audio/*.mp3
   samples/audio/*.wav
   ```
5. **Use in development:**
   - Backend: Point analysis to sample files
   - Frontend: Use for upload testing
   - Mock data: Reference in mock section data

---

## 💡 **Tips**

- **Keep files small:** Use MP3 192kbps or lower for testing (faster uploads)
- **Duration:** 2-4 minute tracks are ideal for testing
- **Variety:** Get tracks with different structures (some with clear sections, some without)
- **Documentation:** Note which tracks work well for which test cases

---

## 🔗 **Quick Links**

- **Pixabay Music:** https://pixabay.com/music/ (Recommended - no attribution needed)
- **Free Music Archive:** https://freemusicarchive.org/
- **Incompetech:** https://incompetech.com/music/royalty-free/
- **YouTube Audio Library:** https://www.youtube.com/audiolibrary

---

**Remember:** Always check the license for each track you download, especially if you plan to use it in demos or showcase videos!

