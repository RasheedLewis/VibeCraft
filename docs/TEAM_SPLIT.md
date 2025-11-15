# Team Split Strategy: First Half of Roadmap (PR-01 through PR-09)

## Overview

This document outlines how to split the first 9 PRs (67 subtasks) between two developers with minimal dependencies and conflicts.

**Goal:** Enable parallel work streams where each person owns complete features end-to-end (backend + frontend).

---

## 🎯 **Split Strategy: Feature-Based Ownership**

### **Person A: Upload & Analysis Feature** 
*Owns: Complete upload-to-analysis flow, including UI*
- **PRs:** PR-02 (Upload), PR-03 (Preprocessing), PR-04 (Analysis), PR-07 (Song Profile UI)
- **Focus:** Getting audio in, analyzing it, and displaying results

### **Person B: Video Generation Feature**
*Owns: Complete video generation flow, including UI*
- **PRs:** PR-05 (Genre/Mood), PR-06 (Lyrics), PR-08 (Scene Planner), PR-09 (Video Generation)
- **Focus:** Enhancing analysis data and generating videos

### **Why This Split Works:**
✅ **Balanced workload:** ~30 subtasks each  
✅ **Full-stack ownership:** Each person owns complete features end-to-end  
✅ **Minimal dependencies:** Can work mostly in parallel with mock data  
✅ **Clear boundaries:** Natural feature boundaries reduce conflicts  
✅ **Better collaboration:** Each person understands their entire feature deeply

---

## 📋 **Detailed Task Assignment**

### **PR-01: Project Initialization** (Shared - Do Together)
**Subtasks 1-8:** Both work together
- Initialize monorepo structure
- Set up package managers
- Configure TypeScript/Python
- Set up linting/CI
- **Critical:** Define API contracts early (see "Integration Points" below)

**Time:** ~2-3 hours together, then split

---

### **Person A: Upload & Analysis Feature** 
*Owns complete user journey from upload to viewing analyzed song*

#### **PR-02: Audio Upload Service** (Full Stack)
**Subtasks 9-16:**
- ✅ Create `/api/songs` POST endpoint
- ✅ Implement audio file validation
- ✅ Implement multipart file handling
- ✅ Upload to object storage (S3/Supabase)
- ✅ Generate and store metadata
- ✅ Return `songId` and `audioUrl`
- ✅ Build Upload UI screen
- ✅ Show upload success + waveform placeholder UI

**Deliverable:** Complete upload feature (backend + frontend)

---

#### **PR-03: Audio Preprocessing Pipeline** (Backend)
**Subtasks 17-22:**
- ✅ Mono downmix + resampling to 44.1kHz
- ✅ Extract waveform JSON via librosa
- ✅ Store processed audio file
- ✅ Link processed file to database record
- ✅ Add preprocessing stage to analysis job

**Deliverable:** Preprocessed audio ready for analysis

---

#### **PR-04: Music Analysis Engine** (Full Stack)
**Subtasks 23-31:**
- ✅ BPM detection module
- ✅ Beat onset detection + beat grid
- ✅ Novelty curve calculation
- ✅ Structural boundary detection
- ✅ Section grouping (chorus/verse identification)
- ✅ `/api/songs/:id/analyze` orchestration endpoint
- ✅ Store `SongAnalysis` results in DB
- ✅ Add frontend loading steps for analysis progress
- ✅ Poll `/api/jobs/:jobId` for status
- ✅ Display analysis results when complete

**Deliverable:** Complete analysis feature with progress UI

---

#### **PR-07: Song Profile UI** (Frontend)
**Subtasks 46-52:**
- ✅ Build timeline segmented into intro/verse/chorus/etc
- ✅ Create SectionCard component
- ✅ Render mood tags inside section card (using Person B's data)
- ✅ Render lyric snippet inside section card (using Person B's data)
- ✅ Add Generate/Regenerate buttons (connects to Person B's API)
- ✅ Add waveform visual under header
- ✅ Display genre + mood summary (using Person B's data)

**Deliverable:** Complete song profile page with section cards

**Note:** Can use mock data for genre/mood/lyrics initially, integrate real data when Person B completes PR-05 & PR-06

---

### **Person B: Video Generation Feature**
*Owns complete video generation flow from scene planning to preview*

#### **PR-05: Genre & Mood Classification** (Full Stack)
**Subtasks 32-37:**
- ✅ Compute mood features (energy, valence, tension)
- ✅ Build genre classifier (CLAP/embedding model)
- ✅ Map to standardized genres
- ✅ Compute `moodTags` and `moodVector`
- ✅ Integrate genre/mood outputs into analysis object
- ✅ Add genre/mood display UI badges

**Deliverable:** Genre/mood analysis with UI display

---

#### **PR-06: Lyric Extraction & Section Alignment** (Full Stack)
**Subtasks 38-45:**
- ✅ Track recognition (optional)
- ✅ Lyrics API integration
- ✅ Whisper ASR for unrecognized tracks
- ✅ Vocal stem extraction (Demucs/Spleeter)
- ✅ Segment ASR output into timed lines
- ✅ Align lyrics to section timestamps
- ✅ Add `sectionLyrics[]` to analysis
- ✅ Display lyric previews inside section cards

**Deliverable:** Complete lyrics feature with UI display

---

#### **PR-08: Section Scene Planner** (Backend)
**Subtasks 53-59:**
- ✅ Template definitions (Abstract first)
- ✅ Mood → intensity + color palette mapping
- ✅ Genre → camera motion presets
- ✅ Section type → shot patterns
- ✅ `buildSceneSpec(sectionId)` function
- ✅ Prompt builder combining all features
- ✅ Internal `/build-scene` debugging endpoint

**Deliverable:** Scene planning service that generates prompts

---

#### **PR-09: Section Video Generation Pipeline** (Full Stack)
**Subtasks 60-67:**
- ✅ Connect backend to Replicate API
- ✅ `generateSectionVideo(sceneSpec)` function
- ✅ AI job polling utility
- ✅ Persist `SectionVideo` record on completion
- ✅ Save seed, prompts, duration, resolution metadata
- ✅ Build frontend loading spinner for generation
- ✅ Build video preview player UI
- ✅ Build "Regenerate Section Video" button

**Deliverable:** Complete section video generation with preview UI

---

## 🔗 **Critical Integration Points**

### **1. API Contract Definition (Do in PR-01)**
Both developers must agree on these schemas before splitting:

```typescript
// Shared types (define in PR-01)
interface SongCreateResponse {
  songId: string;
  audioUrl: string;
  status: "uploaded" | "processing" | "ready";
}

interface SongAnalysis {
  durationSec: number;
  bpm?: number;
  sections: SongSection[];
  moodPrimary: string;
  moodTags: string[];
  moodVector: MoodVector;
  primaryGenre?: string;
  subGenres?: string[];
  lyricsAvailable: boolean;
  sectionLyrics?: SectionLyrics[];
}

interface JobStatus {
  jobId: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress?: number;
  result?: any;
}
```

**Action:** Create `backend/app/schemas/` and `frontend/src/types/` with matching definitions in PR-01.

---

### **2. Mock Data Strategy (Both Developers)**
Each developer creates mock data for features they don't own yet:

**Person A (for PR-07 - Song Profile UI):**
```typescript
// frontend/src/mocks/genreMoodLyrics.mock.ts
export const mockGenreMoodData = {
  primaryGenre: "Electronic",
  moodTags: ["energetic", "upbeat"],
  moodVector: { energy: 0.8, valence: 0.7, ... },
  sectionLyrics: [...]
};
```
Use this in PR-07 until Person B completes PR-05 & PR-06.

**Person B (for PR-09 - Video Generation):**
```typescript
// frontend/src/mocks/sections.mock.ts
export const mockSections = [
  { id: "1", type: "verse", startSec: 0, endSec: 30, ... },
  { id: "2", type: "chorus", startSec: 30, endSec: 60, ... }
];
```
Use this in PR-09 until Person A completes PR-04.

This allows both developers to work on their UI features independently before integration.

---

## ⚠️ **Dependency Management**

### **Minimal Blockers:**
1. **PR-01:** Must be done together (shared setup)
2. **PR-02:** Person A owns completely - no dependency
3. **PR-07 (Person A):** Can use mock data for genre/mood/lyrics initially, integrates real data when Person B completes PR-05 & PR-06
4. **PR-09 (Person B):** Needs Person A's analysis data (sections) from PR-04, but can work with mock data initially

### **Parallel Work Opportunities:**
- **Person A** can work on PR-02, PR-03, PR-04 completely independently
- **Person B** can work on PR-05, PR-06, PR-08 independently (uses Person A's analysis results, but can mock them)
- **Person A** builds PR-07 UI with mock genre/mood/lyrics data
- **Person B** completes PR-05 & PR-06, then Person A integrates real data into PR-07
- **Person B** can start PR-09 with mock section data, integrates real data when Person A completes PR-04

---

## 📅 **Suggested Workflow**

### **Day 1: Setup & Initial Split**
- **Morning:** Both do PR-01 together, define API contracts
- **Afternoon:** 
  - **Person A:** Start PR-02 (upload feature - backend + frontend)
  - **Person B:** Start PR-05 (genre/mood classification - backend + frontend)

### **Day 2-3: Parallel Feature Development**
- **Person A:** 
  - Complete PR-02 (upload)
  - PR-03 (audio preprocessing)
  - Start PR-04 (music analysis - backend + frontend)
- **Person B:**
  - Complete PR-05 (genre/mood)
  - Start PR-06 (lyrics extraction - backend + frontend)

### **Day 4-5: Continued Parallel Work**
- **Person A:**
  - Complete PR-04 (analysis)
  - Start PR-07 (Song Profile UI with mock genre/mood/lyrics data)
- **Person B:**
  - Complete PR-06 (lyrics)
  - Start PR-08 (scene planner)

### **Day 6-7: Integration & Video Generation**
- **Person A:**
  - Complete PR-07 (integrate real genre/mood/lyrics data from Person B)
- **Person B:**
  - Complete PR-08 (scene planner)
  - Start PR-09 (section video generation - backend + frontend)

### **Day 8: Final Integration**
- **Person A:** Polish PR-07, ensure Generate buttons connect to Person B's API
- **Person B:** Complete PR-09, ensure video preview works in Person A's UI
- **Both:** Integration testing, bug fixes

---

## 🎯 **Success Criteria for First Half**

By the end of PR-09, both developers should have:

1. ✅ User can upload an audio file
2. ✅ System analyzes the song (BPM, sections, genre, mood, lyrics)
3. ✅ User sees a song profile with section cards
4. ✅ User can generate a video for any section
5. ✅ User can preview and regenerate section videos

---

## 🔄 **Communication Protocol**

### **Daily Sync Points:**
- **Morning:** Share what you're working on today
- **End of Day:** Demo progress, flag any API changes needed

### **API Changes:**
- If Person A needs to change an API contract, notify Person B immediately
- Update shared type definitions in both repos
- Person B updates mocks if needed

### **Blockers:**
- If Person B is blocked waiting for an endpoint, Person A creates a stub
- If Person A needs UI feedback, Person B provides mock screenshots

---

## 📊 **Estimated Time Split**

| Person | PRs | Subtasks | Backend | Frontend | Estimated Time |
|--------|-----|----------|---------|----------|----------------|
| **Person A** | PR-02, PR-03, PR-04, PR-07 | 8 + 6 + 9 + 7 = **30 subtasks** | ~18 | ~12 | 3.5-4 days |
| **Person B** | PR-05, PR-06, PR-08, PR-09 | 6 + 8 + 7 + 8 = **29 subtasks** | ~20 | ~9 | 3.5-4 days |
| **Shared** | PR-01 | 8 subtasks | - | - | 0.5 days |

**Total:** ~4-5 days for first half (PR-01 through PR-09)

**Balance:** Both developers have similar workload (~30 subtasks each) and work on both backend and frontend, giving each full ownership of their features.

---

## 🚀 **Next Steps After PR-09**

Once PR-09 is complete, the natural next split would continue the feature-based approach:

### **Person A: Full Video Pipeline**
- PR-10 (Clip Management - full stack)
- PR-11 (Full Song Scene Planner - backend)
- PR-13 (Composition Engine - backend)
- PR-14 (Full Video Generation API - full stack)

### **Person B: Polish & Optimization**
- PR-12 (Full-Length Video Generation - backend orchestration)
- PR-15 (Deployment - infrastructure)
- PR-16 (Sample Videos & Showcase - content)
- PR-17 (Cost Optimization & Caching - backend)
- PR-18 (Final Polish & Bugfixes - both)

This maintains feature ownership while balancing the remaining work.

