# Code Analysis Report: VibeCraft Repository

**Generated:** Analysis of all backend and frontend code files (excluding tests)  
**Goals:** (a) Identify dead code, (b) Understand repository structure

---

## Frontend Analysis

### Overview

The frontend is a **React + TypeScript** application built with **Vite**. It's a single-page application (SPA) focused on uploading songs, analyzing them, generating video clips, and composing final videos.

**Tech Stack:**
- React 18+ (with hooks)
- TypeScript
- Vite (build tool)
- Tailwind CSS (via `vibecraft-theme.css`)
- Axios (HTTP client)
- clsx (CSS class utility)

**Architecture:**
- Single-page app with one main page (`UploadPage`)
- Component-based UI with reusable VibeCraft design system components
- Type-safe API client with TypeScript interfaces
- State management via React hooks (no Redux/Zustand)

---

### Entry Points

#### `frontend/src/main.tsx`
**Status:** ✅ Active  
**Usage:** Application entry point
- Renders React app into DOM
- Imports global CSS (`index.css`)
- Uses React 18 `createRoot` API
- **Used by:** Vite build system

#### `frontend/src/App.tsx`
**Status:** ✅ Active  
**Usage:** Root React component
- Simple wrapper that renders `UploadPage`
- No routing (single page app)
- **Used by:** `main.tsx`

---

### Pages

#### `frontend/src/pages/UploadPage.tsx`
**Status:** ✅ Active (2,283 lines - main application logic)  
**Usage:** The only page in the application - handles entire user flow

**Key Responsibilities:**
1. **File Upload**
   - Drag & drop or file input
   - Validates MIME types (MP3, WAV, M4A, FLAC, OGG, etc.)
   - Enforces 7-minute max duration
   - Shows upload progress

2. **Song Analysis**
   - Triggers analysis job after upload
   - Polls analysis job status
   - Displays analysis results (BPM, mood, genre, sections, lyrics)

3. **Clip Generation**
   - Plans clips (beat-aligned)
   - Generates video clips via Replicate API
   - Polls clip generation status
   - Shows clip queue and progress

4. **Video Composition**
   - Composes final video from clips
   - Polls composition job status
   - Displays final composed video

5. **UI States**
   - Idle (upload prompt)
   - Uploading (progress bar)
   - Uploaded (analysis in progress)
   - Song Profile (full analysis + clip management)

**Key Features:**
- Complex state management (20+ useState hooks)
- Multiple polling loops (analysis, clips, composition)
- Real-time progress updates
- Error handling and retry logic
- URL parameter support (`?songId=...`) for loading existing songs

**Dependencies:**
- `apiClient` - All API calls
- `MainVideoPlayer` - Video preview
- VibeCraft components (`VCButton`, `VCCard`, `SectionCard`, `SectionMoodTag`)
- Type definitions from `types/song.ts` and `types/analysis.ts`

**Helper Functions (internal):**
- `formatBytes`, `formatSeconds`, `formatBpm` - Formatting utilities
- `mapMoodToMoodKind` - Mood mapping
- `normalizeJobStatus`, `normalizeClipStatus` - Status normalization
- `extractErrorMessage` - Error parsing
- `parseWaveformJson` - Waveform data parsing
- `computeDuration` - Audio duration detection (client-side)

**Sub-components (internal):**
- `SongTimeline` - Section timeline visualization
- `WaveformDisplay` - Waveform with beat grid overlay
- `MoodVectorMeter` - Mood vector visualization
- `ClipStatusBadge` - Clip status indicator
- `AnalysisSectionRow` - Section analysis display
- `RequirementPill` - Upload requirements display
- `SummaryStat` - Analysis summary stat
- `WaveformPlaceholder` - Loading placeholder
- `BackgroundOrbs` - Background decoration
- Various icon components (MusicNoteIcon, UploadIcon, etc.)

---

### Components

#### `frontend/src/components/MainVideoPlayer.tsx`
**Status:** ✅ Active (934 lines - complex video player)  
**Usage:** Full-featured video player component

**Features:**
- Video playback with external audio sync
- Clip-based navigation (jump between clips)
- Beat grid visualization
- Lyrics overlay
- Waveform visualization
- A/B loop functionality
- Keyboard shortcuts (Space/K, J/L, arrows, M, etc.)
- Picture-in-picture support
- Playback rate control
- Volume/mute controls

**Props:**
- `videoUrl` - Video source URL
- `audioUrl` - Optional external audio (for sync)
- `posterUrl` - Video poster image
- `durationSec` - Total duration
- `clips` - Array of clip segments
- `activeClipId` - Currently active clip
- `onClipSelect` - Clip selection callback
- `beatGrid` - Beat timing data
- `lyrics` - Lyrics with timing
- `waveform` - Waveform data array
- `onDownload` - Download callback

**Key Logic:**
- Syncs video playback with external audio when `audioUrl` provided
- Maps global time to clip-relative time for video seeking
- Handles clip transitions automatically
- Real-time sync correction (every 250ms)

**Dependencies:**
- `clsx` - CSS class utility
- React hooks (useState, useEffect, useRef, useMemo, useCallback)

**Sub-components (internal):**
- `TransportButton` - Control button
- `Playhead` - Playback position indicator
- `HoverTime` - Hover time tooltip
- `BeatTick` - Beat marker
- `Marker` - A/B loop markers
- `ClipSpan` - Clip segment visualization
- `WaveBars` - Waveform bars
- Icon components (PlayIcon, PauseIcon, etc.)

---

#### `frontend/src/components/vibecraft/` - Design System Components

**Status:** ✅ All Active  
**Usage:** Reusable UI components following VibeCraft design system

##### `VCButton.tsx`
**Status:** ✅ Active  
**Usage:** Primary button component
- Variants: `primary`, `secondary`, `ghost`
- Sizes: `sm`, `md`, `lg`
- Supports left/right icons
- Loading state
- **Used by:** `UploadPage`, `SectionCard`

##### `VCCard.tsx`
**Status:** ✅ Active  
**Usage:** Card container component
- Optional padding
- **Used by:** `UploadPage`, `SectionCard`

##### `VCBadge.tsx`
**Status:** ✅ Active  
**Usage:** Badge/label component
- Tones: `default`, `success`, `warning`, `danger`
- **Used by:** `SectionMoodTag`, `UploadPage` (ClipStatusBadge)

##### `SectionMoodTag.tsx`
**Status:** ✅ Active  
**Usage:** Mood tag badge
- Maps mood to badge tone
- Moods: `chill`, `energetic`, `dark`, `uplifting`
- **Used by:** `SectionCard`, `UploadPage`

##### `SectionCard.tsx`
**Status:** ✅ Active  
**Usage:** Section display card
- Shows section name, time range, mood tag
- Optional lyric snippet
- Action buttons (Generate, Regenerate, Use in full)
- **Used by:** `UploadPage` (in song profile view)

##### `GenerationProgress.tsx`
**Status:** ⚠️ Exported but NOT used  
**Usage:** Generation progress indicator
- Stages: `idle`, `uploading`, `analyzing`, `generatingSections`, `compositing`, `done`
- **Status:** Component exists but is never imported or used in `UploadPage`
- **Note:** `UploadPage` implements its own progress indicators instead

##### `index.ts`
**Status:** ✅ Active  
**Usage:** Barrel export for all vibecraft components
- Re-exports all components for convenient importing
- **Used by:** `UploadPage`

---

### Utilities & Libraries

#### `frontend/src/lib/apiClient.ts`
**Status:** ✅ Active  
**Usage:** HTTP client configuration

**Features:**
- Axios instance with base URL configuration
- Environment variable support (`VITE_API_BASE_URL`)
- Development fallback to localhost (build-time replacement)
- Automatic `/api/v1` suffix handling
- Production error if API URL not configured

**Exports:**
- `apiClient` - Axios instance (used throughout app)
- `API_BASE_URL` - Resolved base URL

**Used by:** `UploadPage` (all API calls)

---

### Types

#### `frontend/src/types/song.ts`
**Status:** ✅ Active  
**Usage:** TypeScript interfaces for song-related API responses

**Interfaces:**
- `SongUploadResponse` - Upload response
- `SongAnalysisJobResponse` - Analysis job response
- `SongClipStatus` - Individual clip status
- `ClipGenerationSummary` - Clip generation summary
- `JobStatusResponse` - Generic job status
- `ComposeVideoResponse` - Composition job response
- `CompositionJobStatusResponse` - Composition job status
- `MoodVector` - Mood feature vector
- `SongSectionType` - Section type union
- `SongSection` - Section data
- `SectionLyrics` - Lyrics with timing
- `SongAnalysis` - Full analysis result
- `SongRead` - Song database record

**Used by:** `UploadPage` (type annotations, API responses)

#### `frontend/src/types/analysis.ts`
**Status:** ⚠️ Partially redundant  
**Usage:** TypeScript interfaces for analysis data

**Interfaces:**
- `SongSectionType` - Duplicate of `song.ts`
- `SongSection` - Duplicate of `song.ts` (slightly different - missing `repetitionGroup` nullability)
- `MoodVector` - Duplicate of `song.ts`
- `SectionLyrics` - Duplicate of `song.ts`
- `SongAnalysis` - Duplicate of `song.ts` (missing `beatTimes` field)

**Status:** This file appears to be a duplicate/older version of types in `song.ts`. The `UploadPage` imports from `song.ts`, not `analysis.ts`.

**Recommendation:** Consider removing `analysis.ts` if it's not used, or consolidate types into a single file.

---

### Styling

#### `frontend/src/index.css`
**Status:** ✅ Active  
**Usage:** Global CSS styles
- Imports Tailwind CSS
- Imports VibeCraft theme (`styles/vibecraft-theme.css`)
- Global styles and CSS variables

#### `frontend/src/styles/vibecraft-theme.css`
**Status:** ✅ Active  
**Usage:** VibeCraft design system CSS
- Design tokens (colors, spacing, typography)
- Component classes (`.vc-btn`, `.vc-card`, `.vc-badge`, etc.)
- Utility classes
- Animations (gradient shift, pulse, shimmer)
- Dark theme (default)

**Used by:** All components via Tailwind classes and custom CSS classes

---

### Configuration Files

#### `frontend/vite.config.ts`
**Status:** ✅ Active  
**Usage:** Vite build configuration
- Defines build-time replacements (e.g., `__DEV_DEFAULT_API__`)
- Configures development server
- **Used by:** Vite build system

#### `frontend/tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`
**Status:** ✅ Active  
**Usage:** TypeScript configuration
- Type checking configuration
- Path aliases
- **Used by:** TypeScript compiler, IDE

#### `frontend/tailwind.config.ts`
**Status:** ✅ Active  
**Usage:** Tailwind CSS configuration
- Design tokens from design system
- Custom theme extensions
- **Used by:** Tailwind CSS processor

#### `frontend/eslint.config.js`
**Status:** ✅ Active  
**Usage:** ESLint configuration
- Code quality rules
- **Used by:** ESLint linter

#### `frontend/postcss.config.js`
**Status:** ✅ Active  
**Usage:** PostCSS configuration
- Tailwind CSS plugin
- **Used by:** PostCSS processor

---

### Dead Code Analysis

#### Unused Components

1. **`GenerationProgress.tsx`**
   - **Status:** Exported but never imported
   - **Location:** `frontend/src/components/vibecraft/GenerationProgress.tsx`
   - **Reason:** `UploadPage` implements its own progress indicators
   - **Recommendation:** Remove if not planned for future use

#### Redundant Types

2. **`frontend/src/types/analysis.ts`**
   - **Status:** Duplicate types that exist in `song.ts`
   - **Usage:** Not imported by any component (checked via grep)
   - **Recommendation:** Remove or consolidate into `song.ts`

#### Unused Imports/Exports

3. **`frontend/src/components/vibecraft/index.ts`**
   - Exports `GenerationProgress` but it's never used
   - **Recommendation:** Remove `GenerationProgress` export if component is deleted

---

### Usage Patterns

#### State Management
- **Pattern:** React hooks (`useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`)
- **No global state:** All state is local to `UploadPage`
- **Complexity:** `UploadPage` has 20+ state variables (could benefit from reducer or state machine)

#### API Communication
- **Pattern:** Axios client (`apiClient`) with TypeScript types
- **Polling:** Multiple `useEffect` hooks with `setTimeout` for polling
- **Error handling:** Try/catch with error message extraction

#### Component Structure
- **Pattern:** Functional components with TypeScript
- **Reusability:** Design system components (`vibecraft/`) are well-structured
- **Composition:** Components compose well (e.g., `SectionCard` uses `VCCard`, `VCButton`, `SectionMoodTag`)

#### Styling Approach
- **Pattern:** Tailwind CSS + custom CSS classes
- **Design system:** Centralized in `vibecraft-theme.css`
- **Consistency:** Components use design tokens consistently

---

### File Dependencies Graph

```
main.tsx
  └─> App.tsx
       └─> UploadPage.tsx
            ├─> apiClient (lib/apiClient.ts)
            ├─> MainVideoPlayer (components/MainVideoPlayer.tsx)
            └─> vibecraft components (components/vibecraft/)
                 ├─> VCButton
                 ├─> VCCard
                 ├─> VCBadge
                 ├─> SectionCard
                 │    ├─> VCCard
                 │    ├─> VCButton
                 │    └─> SectionMoodTag
                 │         └─> VCBadge
                 └─> SectionMoodTag
                      └─> VCBadge

Types:
  UploadPage.tsx
    └─> types/song.ts (all types)
    └─> types/analysis.ts (NOT USED - redundant)
```

---

### Summary

**Total Frontend Files Analyzed:** 15 TypeScript/TSX files

**Active Files:** 13
- Entry points: 2
- Pages: 1
- Components: 7 (6 vibecraft + 1 MainVideoPlayer)
- Utilities: 1
- Types: 2 (1 active, 1 redundant)

**Dead Code Identified:**
1. `GenerationProgress.tsx` - Exported but never used
2. `types/analysis.ts` - Duplicate types, not imported

**Key Findings:**
- Single-page application with complex state management in `UploadPage`
- Well-structured design system components
- Type-safe API communication
- No routing (single page)
- Complex video player with sync logic
- Multiple polling loops for async operations

**Recommendations:**
1. Remove `GenerationProgress.tsx` if not planned
2. Consolidate or remove `types/analysis.ts`
3. Consider state management refactor (reducer/state machine) for `UploadPage`
4. Consider routing if multiple pages are planned

---

### UploadPage.tsx Refactoring Analysis

**File:** `frontend/src/pages/UploadPage.tsx`  
**Size:** 2,283 lines  
**Complexity:** Very High

#### Current State

`UploadPage.tsx` is a monolithic component that handles the entire application flow:
1. File upload
2. Song analysis polling
3. Clip generation management
4. Video composition
5. UI rendering for all states

**State Management:**
- **20+ `useState` hooks** managing:
  - Upload state (stage, progress, metadata, error)
  - Analysis state (job ID, progress, data, error)
  - Clip generation state (job ID, status, progress, summary, error)
  - Composition state (job ID, progress)
  - Video player state (active clip, selection lock)
  - UI state (highlighted section, fetching flags)

**Polling Logic:**
- **4 separate polling loops** via `useEffect`:
  1. Analysis job polling (every 3s)
  2. Clip job polling (every 3s, with retry logic)
  3. Composition job polling (every 2s)
  4. Clip summary polling (every 2-6s, conditional)

**Code Organization:**
- Helper functions mixed with component (100+ lines of utilities)
- Sub-components defined inline (SongTimeline, WaveformDisplay, etc.)
- Complex conditional rendering logic
- Section-related code that references removed types (needs update)

#### Refactoring Opportunities

##### 1. **State Management Consolidation** (High Priority)

**Problem:** 20+ individual `useState` hooks make state updates error-prone and hard to reason about.

**Solution Options:**

**Option A: `useReducer` Pattern**
```typescript
type UploadPageState = {
  upload: { stage: UploadStage; progress: number; metadata: UploadMetadata | null; error: string | null }
  analysis: { state: AnalysisState; jobId: string | null; progress: number; data: SongAnalysis | null; error: string | null }
  clips: { jobId: string | null; status: ClipJobStatus; progress: number; summary: ClipGenerationSummary | null; error: string | null }
  composition: { isComposing: boolean; jobId: string | null; progress: number }
  // ... etc
}

const [state, dispatch] = useReducer(uploadPageReducer, initialState)
```

**Benefits:**
- Single source of truth
- Predictable state updates
- Easier to debug (action logging)
- Better TypeScript inference

**Option B: State Machine (XState or custom)**
- Explicit state transitions
- Guards and actions
- Better for complex workflows

**Recommendation:** Start with `useReducer` for immediate improvement, consider state machine if complexity grows.

##### 2. **Extract Custom Hooks** (High Priority)

**Polling Hooks:**
```typescript
// hooks/useJobPolling.ts
function useJobPolling<T>(jobId: string | null, fetchStatus: () => Promise<JobStatusResponse<T>>) {
  // Encapsulates polling logic, cancellation, error handling
}

// Usage:
const analysisPolling = useJobPolling(analysisJobId, () => 
  apiClient.get(`/jobs/${analysisJobId}`)
)
```

**Benefits:**
- Reusable polling logic
- Consistent error handling
- Automatic cleanup
- Testable in isolation

**State Hooks:**
```typescript
// hooks/useUploadState.ts
function useUploadState() {
  // Encapsulates upload-related state and handlers
}

// hooks/useClipGeneration.ts
function useClipGeneration(songId: string | null) {
  // Encapsulates clip generation state and operations
}
```

##### 3. **Component Extraction** (Medium Priority)

**Extract Sub-components:**

**Upload Flow:**
- `UploadCard` - Idle/uploading/uploaded states
- `AnalysisProgress` - Analysis polling and display
- `UploadRequirements` - Requirements pills

**Song Profile:**
- `SongProfileHeader` - Header with genre/mood card
- `ClipGenerationPanel` - Clip generation status and controls
- `ClipQueue` - List of clips with status
- `CompletedClipsGrid` - Grid of completed clip thumbnails
- `SongTimeline` - Already defined inline, extract to separate file
- `WaveformDisplay` - Already defined inline, extract to separate file
- `SectionsList` - Section cards grid

**Benefits:**
- Smaller, focused components
- Easier to test
- Better code organization
- Potential for reuse

##### 4. **Utility Functions Extraction** (Low Priority)

**Extract to `utils/formatting.ts`:**
- `formatBytes`
- `formatSeconds`
- `formatBpm`
- `formatMoodTags`
- `formatDurationShort`
- `formatTimeRange`
- `getFileTypeLabel`

**Extract to `utils/validation.ts`:**
- `isSongAnalysis`
- `isClipGenerationSummary`
- `extractErrorMessage`

**Extract to `utils/sections.ts`:**
- `getSectionTitle`
- `buildSectionsWithDisplayNames`
- `mapMoodToMoodKind`

**Benefits:**
- Reusable across components
- Easier to test
- Better organization

##### 5. **Type Safety Improvements** (Medium Priority)

**Current Issues:**
- `SongSection` type removed from `types/song.ts` but still referenced
- Section-related code needs type definitions (can use stashed types or define locally)

**Solution:**
- Define local section types in `UploadPage.tsx` or create `types/display.ts` for UI-only types
- Or import from `.stash/types/section-types.ts` (not ideal for production)

##### 6. **Constants Extraction** (Low Priority)

**Extract to `constants/upload.ts`:**
- `ACCEPTED_MIME_TYPES`
- `MAX_DURATION_SECONDS`
- `SECTION_TYPE_LABELS`
- `SECTION_COLORS`
- `WAVEFORM_BASE_PATTERN`

**Benefits:**
- Centralized configuration
- Easier to modify
- Better discoverability

#### Refactoring Priority

**Phase 1: Critical (Do First)**
1. Fix type errors from removed section types
2. Extract polling logic to custom hooks
3. Consolidate state with `useReducer`

**Phase 2: High Value (Do Next)**
4. Extract sub-components (UploadCard, ClipGenerationPanel, etc.)
5. Extract utility functions

**Phase 3: Polish (Do Later)**
6. Extract constants
7. Consider state machine if complexity grows

#### Estimated Impact

**Before Refactoring:**
- File size: 2,283 lines
- State variables: 20+
- Polling loops: 4
- Testability: Low (monolithic component)
- Maintainability: Low (hard to navigate)

**After Refactoring (Phase 1 + 2):**
- Main component: ~500-800 lines
- Extracted hooks: 3-4 files
- Extracted components: 8-10 files
- Extracted utilities: 2-3 files
- Testability: High (isolated units)
- Maintainability: High (clear separation of concerns)

#### Migration Strategy

1. **Incremental Refactoring:**
   - Start with polling hooks (low risk, high value)
   - Then extract utilities (no behavior change)
   - Then extract components (one at a time)
   - Finally consolidate state (bigger change, do last)

2. **Testing:**
   - Extract hooks first (easy to test)
   - Test each extracted component in isolation
   - Integration tests for main component

3. **Backwards Compatibility:**
   - Keep existing API surface during refactor
   - No breaking changes to props/state structure initially

---

## Backend Analysis

*(To be completed)*
