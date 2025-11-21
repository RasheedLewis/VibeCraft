# Sample Audio Files Guide

Quick guide for finding royalty-free Electronic/EDM tracks for testing and development.

---

## 🎵 **Recommended Sources**

### **1. Pixabay Music** (Recommended)
- **URL:** https://pixabay.com/music/
- **License:** Free for commercial use, no attribution required
- **How to use:** 
  - Search terms: "electronic", "EDM", "house music", "techno", "dance"
  - Filter by mood: "energetic", "uplifting", "intense"
  - Filter by duration (2-4 minutes ideal)
  - Download MP3 format
- **Best for:** Testing without attribution concerns, good selection of modern EDM

### **2. Free Music Archive (FMA)**
- **URL:** https://freemusicarchive.org/
- **License:** Various (CC0, CC BY) - check individual tracks
- **How to use:** 
  - Browse by genre: "Electronic" or "Dance" categories
  - Search terms: "electronic", "EDM", "house", "techno", "trance", "dubstep"
  - Filter by license (CC0 = no attribution needed)
  - Download MP3/WAV formats
- **Best for:** High quality, diverse selection, often includes BPM metadata

### **3. YouTube Audio Library**
- **URL:** https://www.youtube.com/audiolibrary
- **License:** Free to use (check individual track licenses)
- **How to use:** Filter by "Electronic" genre, download MP3
- **Best for:** Quick access

---

## 📁 **Directory Structure**

Create a `samples/` directory in the project root:

```
VibeCraft/
  samples/
    audio/
      electronic/
        track-1.mp3
        track-2.mp3
    metadata/
      track-1.json  # Optional: store metadata
```

---

## 🎯 **Recommended Test Tracks**

For development, aim for 3-5 Electronic/EDM tracks (120-140 BPM):

- **Good for testing:** Beat detection, clear sections (intro, build-up, drop, breakdown)
- **Sources:** Search FMA or Pixabay for "electronic", "EDM", "house", "trance", or "techno"
- **Duration:** 2-4 minute tracks are ideal
- **EDM-specific characteristics to look for:**
  - Clear kick drum pattern (essential for beat detection)
  - Defined drops and build-ups (good for section detection)
  - Consistent tempo (120-140 BPM range is ideal)
  - Layered synths and bass (tests audio analysis complexity)

---

## ⚖️ **License Checklist**

Before using any track, verify:

- [ ] License allows commercial use (if needed)
- [ ] Attribution requirements (if any)
- [ ] Modification allowed (if processing/analyzing)
- [ ] Redistribution allowed (if storing in repo)

**For development/testing:** CC0 or CC BY licenses are usually fine.

---

## 📝 **Sample Metadata Template**

Create a `metadata.json` file for each track:

```json
{
  "filename": "track-1.mp3",
  "source": "Pixabay Music",
  "license": "Pixabay License",
  "artist": "Artist Name",
  "title": "Track Title",
  "url": "https://pixabay.com/...",
  "genre": "Electronic",
  "expectedBPM": 128,
  "expectedDuration": 210,
  "notes": "Good for testing beat detection"
}
```

---

## 🚀 **Quick Start**

1. **Download 3-5 Electronic/EDM tracks** from Pixabay or FMA
2. **Create `samples/audio/electronic/` directory** in project root
3. **Add to `.gitignore`** if files are large:
   ```
   samples/audio/*.mp3
   samples/audio/*.wav
   ```
4. **Use in development:**
   - Backend: Point analysis to sample files
   - Frontend: Use for upload testing

---

## 💡 **EDM-Specific Tips**

- **Keep files small:** Use MP3 192kbps or lower for testing (faster uploads)
- **Duration:** 2-4 minute tracks are ideal (full EDM tracks can be 5-7 minutes)
- **BPM range:** Focus on 120-140 BPM tracks (standard EDM range)
- **Structure variety:** 
  - Get tracks with clear drops and build-ups (good for section detection)
  - Include some with consistent beats (good for beat detection)
  - Mix of instrumental and vocal tracks (tests different analysis paths)
- **EDM characteristics to test:**
  - Strong kick drum patterns (essential for beat grid accuracy)
  - Layered synths and bass (tests frequency analysis)
  - Build-up sections (tests section boundary detection)
  - Consistent tempo vs. tempo changes (tests BPM detection)
- **Documentation:** Note which tracks work well for which test cases (e.g., "good for beat detection", "challenging for section detection")

---

## 🔗 **Quick Links**

- **Pixabay Music:** https://pixabay.com/music/ (Recommended - no attribution needed)
- **Free Music Archive:** https://freemusicarchive.org/
- **YouTube Audio Library:** https://www.youtube.com/audiolibrary

---

**Remember:** Always check the license for each track you download, especially if you plan to use it in demos or showcase videos!
