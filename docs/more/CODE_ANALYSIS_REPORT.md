# Code Analysis Report: VibeCraft Repository

**Generated:** Analysis of all backend and frontend code files (excluding tests)  
**Goals:** (a) Identify dead code, (b) Understand repository structure, (c) Document current architecture  
**Last Updated:** Current analysis of codebase with authentication, character consistency, video types, and advanced features

---

## Frontend Analysis

### Overview

The frontend is a **React + TypeScript** application built with **Vite**. It's a multi-page application focused on uploading songs, analyzing them, generating video clips, and composing final videos with advanced features like character consistency, video type selection, and audio segment selection.

**Tech Stack:**

- React 18+ (with hooks)
- TypeScript
- Vite (build tool)
- React Router (routing)
- TanStack Query (React Query) for data fetching
- Tailwind CSS (via `vibecraft-theme.css`)
- Axios (HTTP client)
- clsx (CSS class utility)

**Architecture:**

- Multi-page app with routing (`/`, `/public`, `/login`, `/projects`)
- Component-based UI with reusable VibeCraft design system components
- Type-safe API client with TypeScript interfaces
- State management via React hooks with custom polling hooks
- React Query for server state management
- Error boundaries for error handling
- Well-organized utilities and constants

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
**Usage:** Root React component with routing

- Sets up React Router with BrowserRouter
- Defines routes: `/` (UploadPage), `/public` (UploadPage public view), `/login` (LoginPage), `/projects` (ProjectsPage)
- **Used by:** `main.tsx`

---

### Pages

#### `frontend/src/pages/UploadPage.tsx`

**Status:** ✅ Active (~1,700+ lines - comprehensive upload and video generation flow)  
**Usage:** Main page for uploading songs and generating videos

**Key Responsibilities:**

1. **File Upload**
   - Delegates to `UploadCard` component
   - Validates MIME types (MP3, WAV, M4A, FLAC, OGG, etc.)
   - Enforces 7-minute max duration
   - Shows upload progress

2. **Video Type Selection**
   - Uses `useVideoTypeSelection` hook
   - Supports `full_length` and `short_form` video types
   - Triggers analysis automatically for full_length videos
   - Requires audio selection for short_form videos

3. **Audio Selection** (for short_form videos)
   - Uses `useAudioSelection` hook
   - `AudioSelectionTimeline` component for selecting song segment
   - Validates selection duration (min/max constraints)
   - Saves selection to backend

4. **Template Character Selection**
   - `TemplateSelector` component for choosing character templates
   - `TemplateCharacterModal` for viewing template details
   - `CharacterImageUpload` for custom character images
   - Character consistency options

5. **Song Analysis**
   - Uses `useAnalysisPolling` hook for analysis job polling
   - Displays analysis results via `SongProfileView`
   - Handles analysis state transitions

6. **Clip Generation**
   - Uses `useClipPolling` hook for clip generation status
   - Delegates clip management to `SongProfileView`
   - Handles clip generation job lifecycle

7. **Video Composition**
   - Uses `useCompositionPolling` hook for composition job status
   - Manages composition job state
   - Displays final composed video

**Key Features:**

- Authentication integration with `useAuth` hook
- Public view mode (`/public` route)
- Animations control based on user preferences
- Error boundaries for graceful error handling
- Projects modal for accessing saved projects
- Template character system integration
- Character consistency workflow
- Video type-specific flows

**Dependencies:**

- `apiClient` - All API calls
- `MainVideoPlayer` - Video preview
- Custom hooks: `useAnalysisPolling`, `useClipPolling`, `useCompositionPolling`, `useVideoTypeSelection`, `useAudioSelection`, `useAuth`
- Components: `UploadCard`, `SongProfileView`, `BackgroundOrbs`, `RequirementPill`, `AudioSelectionTimeline`, `VideoTypeSelector`, `TemplateSelector`, `CharacterImageUpload`, `TemplateCharacterModal`, `SelectedTemplateDisplay`, `ProjectsModal`, `AuthModal`
- Utilities: `extractErrorMessage`, `mapMoodToMoodKind`, `computeDuration`, `normalizeClipStatus`, `shouldDisableAnimations`
- Constants: `ACCEPTED_MIME_TYPES`, `MAX_DURATION_SECONDS`

**State Management:**

- Multiple focused state variables for different concerns
- Polling logic extracted to custom hooks
- React Query for server state
- Component composition replaces inline sub-components

#### `frontend/src/pages/LoginPage.tsx`

**Status:** ✅ Active  
**Usage:** User authentication page

- Login and registration forms
- Uses `useAuth` hook for authentication
- Redirects to home page on success
- Error handling for auth failures
- **Used by:** React Router (`/login` route)

#### `frontend/src/pages/ProjectsPage.tsx`

**Status:** ✅ Active  
**Usage:** User projects listing page

- Lists all user's songs/projects
- Uses React Query to fetch songs
- Requires authentication (redirects to login if not authenticated)
- Navigation to individual projects
- Create new project button
- **Used by:** React Router (future route)

---

### Components

#### `frontend/src/components/MainVideoPlayer.tsx`

**Status:** ✅ Active  
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

---

#### `frontend/src/components/upload/` - Upload Flow Components

**Status:** ✅ All Active  
**Usage:** Components for the upload and analysis flow

##### `UploadCard.tsx`

**Status:** ✅ Active  
**Usage:** Upload interface component

- Drag & drop file upload
- File input fallback
- Upload progress display
- Error handling
- **Used by:** `UploadPage`

##### `AnalysisProgress.tsx`

**Status:** ✅ Active  
**Usage:** Analysis progress indicator

- Shows analysis job status
- Progress bar
- Error display
- **Used by:** `UploadPage`

##### `RequirementPill.tsx`

**Status:** ✅ Active  
**Usage:** Upload requirement badge

- Displays file requirements (format, size, duration)
- **Used by:** `UploadCard`

##### `SummaryStat.tsx`

**Status:** ✅ Active  
**Usage:** Analysis summary statistic display

- Shows BPM, duration, genre, mood
- **Used by:** `UploadPage` (via `SongProfileView`)

##### `BackgroundOrbs.tsx`

**Status:** ✅ Active  
**Usage:** Decorative background element

- Animated gradient orbs
- **Used by:** `UploadPage`

##### `Icons.tsx`

**Status:** ✅ Active  
**Usage:** Icon components

- SVG icons for upload flow
- **Used by:** Upload components

##### `AudioSelectionTimeline.tsx`

**Status:** ✅ Active  
**Usage:** Audio segment selection component

- Interactive timeline for selecting song segment
- Visual selection range
- Duration validation
- **Used by:** `UploadPage`

##### `VideoTypeSelector.tsx`

**Status:** ✅ Active  
**Usage:** Video type selection component

- Radio buttons for `full_length` vs `short_form`
- Visual descriptions of each type
- **Used by:** `UploadPage`

##### `TemplateSelector.tsx`

**Status:** ✅ Active  
**Usage:** Template character selection component

- Displays available template characters
- Character previews
- **Used by:** `UploadPage`

##### `TemplateCharacterModal.tsx`

**Status:** ✅ Active  
**Usage:** Modal for viewing template character details

- Shows character poses (A and B)
- Character description
- Apply template functionality
- **Used by:** `UploadPage`

##### `CharacterImageUpload.tsx`

**Status:** ✅ Active  
**Usage:** Custom character image upload component

- File upload for character reference image
- Image preview
- Character consistency options
- **Used by:** `UploadPage`

##### `CharacterPreview.tsx`

**Status:** ✅ Active  
**Usage:** Character preview component

- Displays character image preview
- **Used by:** Character-related components

##### `SelectedTemplateDisplay.tsx`

**Status:** ✅ Active  
**Usage:** Display selected template character

- Shows currently selected template
- Pose selection (A/B)
- **Used by:** `UploadPage`

---

#### `frontend/src/components/song/` - Song Profile Components

**Status:** ✅ All Active  
**Usage:** Components for displaying song analysis and clip management

##### `SongProfileView.tsx`

**Status:** ✅ Active  
**Usage:** Main song profile view component

- Displays full song analysis
- Clip generation panel
- Section timeline
- Waveform display
- Clip queue management
- **Used by:** `UploadPage`

##### `SongTimeline.tsx`

**Status:** ✅ Active  
**Usage:** Section timeline visualization

- Shows song sections on timeline
- Section highlighting
- **Used by:** `SongProfileView`

##### `WaveformDisplay.tsx`

**Status:** ✅ Active  
**Usage:** Waveform visualization with beat grid

- Displays audio waveform
- Beat grid overlay
- Interactive seeking
- **Used by:** `SongProfileView`

##### `WaveformPlaceholder.tsx`

**Status:** ✅ Active  
**Usage:** Loading placeholder for waveform

- Shows while waveform loads
- **Used by:** `SongProfileView`

##### `ClipGenerationPanel.tsx`

**Status:** ✅ Active  
**Usage:** Clip generation status and controls

- Shows clip generation progress
- Start/retry controls
- Error display
- **Used by:** `SongProfileView`

##### `ClipStatusBadge.tsx`

**Status:** ✅ Active  
**Usage:** Clip status indicator badge

- Visual status indicator (queued, processing, completed, failed)
- **Used by:** `SongProfileView`

##### `AnalysisSectionRow.tsx`

**Status:** ✅ Active  
**Usage:** Section analysis display row

- Shows section details (name, time range, mood)
- **Used by:** `SongProfileView`

##### `MoodVectorMeter.tsx`

**Status:** ✅ Active  
**Usage:** Mood vector visualization

- Visual representation of mood features
- **Used by:** `SongProfileView`

##### `PromptViewer.tsx`

**Status:** ✅ Active  
**Usage:** Prompt display component

- Shows generation prompts for clips
- **Used by:** `SongProfileView`

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
- **Used by:** `UploadPage`, `SectionCard`, `SongProfileView`, `LoginPage`, `ProjectsPage`

##### `VCIconButton.tsx`

**Status:** ✅ Active  
**Usage:** Icon-only button component

- Icon buttons for compact UI
- **Used by:** Various components

##### `VCCard.tsx`

**Status:** ✅ Active  
**Usage:** Card container component

- Optional padding
- **Used by:** `UploadPage`, `SectionCard`, `SongProfileView`

##### `VCBadge.tsx`

**Status:** ✅ Active  
**Usage:** Badge/label component

- Tones: `default`, `success`, `warning`, `danger`
- **Used by:** `SectionMoodTag`, `ClipStatusBadge`, `GenreBadge`, `MoodBadge`

##### `SectionMoodTag.tsx`

**Status:** ✅ Active  
**Usage:** Mood tag badge

- Maps mood to badge tone
- Moods: `chill`, `energetic`, `dark`, `uplifting`
- **Used by:** `SectionCard`, `SongProfileView`

##### `SectionCard.tsx`

**Status:** ✅ Active  
**Usage:** Section display card

- Shows section name, time range, mood tag
- Optional lyric snippet
- Action buttons (Generate, Regenerate, Use in full)
- **Used by:** `SongProfileView`

##### `SectionAudioPlayer.tsx`

**Status:** ✅ Active  
**Usage:** Audio player for section preview

- Plays section audio
- **Used by:** `SectionCard`

##### `GenreBadge.tsx`

**Status:** ✅ Active  
**Usage:** Genre display badge

- Shows song genre
- **Used by:** `SongProfileView`

##### `MoodBadge.tsx`

**Status:** ✅ Active  
**Usage:** Mood display badge

- Shows song mood tags
- **Used by:** `SongProfileView`

##### `index.ts`

**Status:** ✅ Active  
**Usage:** Barrel export for all vibecraft components

- Re-exports all components for convenient importing
- **Used by:** `UploadPage`, `SongProfileView`, `LoginPage`, `ProjectsPage`

---

#### `frontend/src/components/auth/` - Authentication Components

**Status:** ✅ All Active  
**Usage:** Authentication-related components

##### `AuthModal.tsx`

**Status:** ✅ Active  
**Usage:** Authentication modal component

- Login and registration forms
- Modal overlay
- Uses `useAuth` hook
- **Used by:** `UploadPage`

---

#### `frontend/src/components/projects/` - Projects Components

**Status:** ✅ All Active  
**Usage:** Projects management components

##### `ProjectsModal.tsx`

**Status:** ✅ Active  
**Usage:** Projects listing modal

- Shows user's projects/songs
- Navigation to projects
- Create new project
- **Used by:** `UploadPage`

---

#### `frontend/src/components/ErrorFallback.tsx`

**Status:** ✅ Active  
**Usage:** Global error boundary fallback

- Catches React errors
- Displays error message
- **Used by:** Error boundary wrapper

#### `frontend/src/components/SectionErrorFallback.tsx`

**Status:** ✅ Active  
**Usage:** Section-specific error fallback

- Catches errors in section components
- **Used by:** Section error boundaries

#### `frontend/src/components/VideoPlayerErrorFallback.tsx`

**Status:** ✅ Active  
**Usage:** Video player error fallback

- Catches video player errors
- **Used by:** Video player error boundaries

---

### Custom Hooks

#### `frontend/src/hooks/useJobPolling.ts`

**Status:** ✅ Active  
**Usage:** Generic job polling hook

- Reusable polling logic for any job type
- Handles polling intervals, cancellation, error handling
- Generic type support
- **Used by:** `useAnalysisPolling`, `useClipPolling`, `useCompositionPolling`

#### `frontend/src/hooks/useAnalysisPolling.ts`

**Status:** ✅ Active  
**Usage:** Song analysis job polling hook

- Polls analysis job status
- Fetches analysis results when complete
- Manages analysis state (queued, processing, completed, failed)
- **Used by:** `UploadPage`

#### `frontend/src/hooks/useClipPolling.ts`

**Status:** ✅ Active  
**Usage:** Clip generation job polling hook

- Polls clip generation job status
- Fetches clip summary
- Manages clip generation state
- Handles retry logic
- **Used by:** `UploadPage`

#### `frontend/src/hooks/useCompositionPolling.ts`

**Status:** ✅ Active  
**Usage:** Video composition job polling hook

- Polls composition job status
- Manages composition state
- **Used by:** `UploadPage`

#### `frontend/src/hooks/useAuth.ts`

**Status:** ✅ Active  
**Usage:** Authentication hook

- Manages authentication state
- Login, register, logout functions
- Token management (localStorage)
- User info fetching with React Query
- API client header management
- **Used by:** `UploadPage`, `LoginPage`, `ProjectsPage`, `AuthModal`

#### `frontend/src/hooks/useAudioSelection.ts`

**Status:** ✅ Active  
**Usage:** Audio selection hook

- Manages audio segment selection state
- Saves selection to backend
- Loads existing selection from song
- **Used by:** `UploadPage`

#### `frontend/src/hooks/useVideoTypeSelection.ts`

**Status:** ✅ Active  
**Usage:** Video type selection hook

- Manages video type state (`full_length` or `short_form`)
- Saves video type to backend
- Triggers analysis for full_length videos
- **Used by:** `UploadPage`

#### `frontend/src/hooks/useFeatureFlags.ts`

**Status:** ✅ Active  
**Usage:** Feature flags hook

- Fetches feature flags from backend
- React Query integration
- **Used by:** Components that need feature flags

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
- Authorization header management (for JWT tokens)

**Exports:**

- `apiClient` - Axios instance (used throughout app)
- `API_BASE_URL` - Resolved base URL

**Used by:** All components and hooks (all API calls)

---

#### `frontend/src/utils/formatting.ts`

**Status:** ✅ Active  
**Usage:** Formatting utility functions

**Functions:**

- `formatBytes` - Format file sizes
- `formatSeconds` - Format time durations
- `formatBpm` - Format BPM values
- `formatMoodTags` - Format mood tag arrays
- `formatDurationShort` - Short duration format
- `formatTimeRange` - Time range format
- `clamp` - Clamp numeric values
- `getFileTypeLabel` - Get file type label

**Used by:** `UploadPage`, `SongProfileView`, various components

---

#### `frontend/src/utils/validation.ts`

**Status:** ✅ Active  
**Usage:** Validation utility functions

**Functions:**

- `isSongAnalysis` - Type guard for song analysis
- `isClipGenerationSummary` - Type guard for clip summary
- `extractErrorMessage` - Extract error message from exceptions

**Used by:** `UploadPage`, polling hooks

---

#### `frontend/src/utils/sections.ts`

**Status:** ✅ Active  
**Usage:** Section-related utility functions

**Functions:**

- `getSectionTitle` - Get section display title
- `buildSectionsWithDisplayNames` - Build sections with display names
- `mapMoodToMoodKind` - Map mood to mood kind

**Used by:** `UploadPage`, `SongProfileView`

---

#### `frontend/src/utils/status.ts`

**Status:** ✅ Active  
**Usage:** Status normalization utilities

**Functions:**

- `normalizeClipStatus` - Normalize clip status values
- `normalizeJobStatus` - Normalize job status values

**Used by:** `UploadPage`, `useClipPolling`

---

#### `frontend/src/utils/audio.ts`

**Status:** ✅ Active  
**Usage:** Audio-related utilities

**Functions:**

- `computeDuration` - Compute audio duration from file

**Used by:** `UploadPage`

---

#### `frontend/src/utils/waveform.ts`

**Status:** ✅ Active  
**Usage:** Waveform data utilities

**Functions:**

- `parseWaveformJson` - Parse waveform JSON data

**Used by:** `WaveformDisplay`, `SongProfileView`

---

#### `frontend/src/utils/animations.ts`

**Status:** ✅ Active  
**Usage:** Animation control utilities

**Functions:**

- `shouldDisableAnimations` - Determine if animations should be disabled
- Checks public view mode and user preferences

**Used by:** `UploadPage`

---

### Constants

#### `frontend/src/constants/upload.ts`

**Status:** ✅ Active  
**Usage:** Upload-related constants

**Constants:**

- `ACCEPTED_MIME_TYPES` - Allowed audio MIME types
- `MAX_DURATION_SECONDS` - Maximum song duration (7 minutes)
- `MAX_AUDIO_FILE_SIZE_MB` - Maximum file size in MB
- `MAX_AUDIO_FILE_SIZE_BYTES` - Maximum file size in bytes

**Used by:** `UploadPage`, `UploadCard`

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
- `SongRead` - Song database record (includes new fields: `selected_start_sec`, `selected_end_sec`, `video_type`, `template`, `character_reference_image_s3_key`, `character_pose_b_s3_key`, `character_selected_pose`, `character_consistency_enabled`, `total_generation_cost_usd`, etc.)

**Used by:** All components and hooks (type annotations, API responses)

#### `frontend/src/types/analysis.ts`

**Status:** ✅ Active  
**Usage:** TypeScript interfaces for analysis data

**Interfaces:**

- Analysis-related type definitions
- May overlap with `song.ts` but serves specific analysis needs

**Used by:** Analysis-related components

#### `frontend/src/types/sectionVideo.ts`

**Status:** ✅ Active  
**Usage:** TypeScript interfaces for section video data

**Interfaces:**

- Section video-related type definitions

**Used by:** Section video components

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

**None identified** - All components appear to be actively used.

#### Redundant Types

**None identified** - Type files serve distinct purposes or are actively used.

#### Unused Imports/Exports

**None identified** - All exports appear to be used.

---

### Usage Patterns

#### State Management

- **Pattern:** React hooks (`useState`, `useEffect`, `useCallback`, `useMemo`, `useRef`)
- **Custom hooks:** Polling logic extracted to reusable hooks
- **Server state:** React Query (TanStack Query) for API data
- **Complexity:** `UploadPage` has multiple focused state variables for different concerns
- **Separation:** State management separated by concern (upload, analysis, clips, composition, auth, video type, audio selection)

#### API Communication

- **Pattern:** Axios client (`apiClient`) with TypeScript types
- **Polling:** Custom hooks (`useJobPolling`, `useAnalysisPolling`, `useClipPolling`, `useCompositionPolling`)
- **Data fetching:** React Query for server state
- **Error handling:** Centralized error extraction utilities
- **Authentication:** JWT tokens in Authorization header

#### Component Structure

- **Pattern:** Functional components with TypeScript
- **Reusability:** Design system components (`vibecraft/`) are well-structured
- **Composition:** Components compose well (e.g., `SongProfileView` uses multiple sub-components)
- **Extraction:** Large components broken down into focused sub-components
- **Error boundaries:** React error boundaries for graceful error handling

#### Routing

- **Pattern:** React Router with BrowserRouter
- **Routes:** `/` (UploadPage), `/public` (UploadPage public view), `/login` (LoginPage), `/projects` (ProjectsPage)
- **Navigation:** Programmatic navigation with `useNavigate`

#### Styling Approach

- **Pattern:** Tailwind CSS + custom CSS classes
- **Design system:** Centralized in `vibecraft-theme.css`
- **Consistency:** Components use design tokens consistently
- **Animations:** User-controlled animations (can be disabled)

---

### File Dependencies Graph

```text
main.tsx
  └─> App.tsx (with React Router)
       ├─> UploadPage.tsx
       │    ├─> apiClient (lib/apiClient.ts)
       │    ├─> useAuth (hooks/useAuth.ts)
       │    │    └─> React Query
       │    ├─> useAnalysisPolling (hooks/useAnalysisPolling.ts)
       │    │    └─> useJobPolling (hooks/useJobPolling.ts)
       │    ├─> useClipPolling (hooks/useClipPolling.ts)
       │    │    └─> useJobPolling (hooks/useJobPolling.ts)
       │    ├─> useCompositionPolling (hooks/useCompositionPolling.ts)
       │    │    └─> useJobPolling (hooks/useJobPolling.ts)
       │    ├─> useVideoTypeSelection (hooks/useVideoTypeSelection.ts)
       │    ├─> useAudioSelection (hooks/useAudioSelection.ts)
       │    ├─> UploadCard (components/upload/UploadCard.tsx)
       │    │    ├─> RequirementPill
       │    │    └─> Icons
       │    ├─> AudioSelectionTimeline (components/upload/AudioSelectionTimeline.tsx)
       │    ├─> VideoTypeSelector (components/upload/VideoTypeSelector.tsx)
       │    ├─> TemplateSelector (components/upload/TemplateSelector.tsx)
       │    ├─> CharacterImageUpload (components/upload/CharacterImageUpload.tsx)
       │    ├─> TemplateCharacterModal (components/upload/TemplateCharacterModal.tsx)
       │    ├─> SelectedTemplateDisplay (components/upload/SelectedTemplateDisplay.tsx)
       │    ├─> SongProfileView (components/song/SongProfileView.tsx)
       │    │    ├─> SongTimeline
       │    │    ├─> WaveformDisplay
       │    │    ├─> ClipGenerationPanel
       │    │    ├─> AnalysisSectionRow
       │    │    ├─> MoodVectorMeter
       │    │    ├─> PromptViewer
       │    │    ├─> GenreBadge
       │    │    ├─> MoodBadge
       │    │    └─> SectionCard
       │    │         ├─> SectionMoodTag
       │    │         └─> SectionAudioPlayer
       │    ├─> MainVideoPlayer (components/MainVideoPlayer.tsx)
       │    ├─> BackgroundOrbs
       │    ├─> ProjectsModal (components/projects/ProjectsModal.tsx)
       │    ├─> AuthModal (components/auth/AuthModal.tsx)
       │    └─> vibecraft components (components/vibecraft/)
       │         ├─> VCButton
       │         ├─> VCCard
       │         ├─> VCBadge
       │         ├─> VCIconButton
       │         └─> SectionCard
       │              ├─> VCCard
       │              ├─> VCButton
       │              └─> SectionMoodTag
       │                   └─> VCBadge
       ├─> LoginPage.tsx
       │    └─> useAuth (hooks/useAuth.ts)
       └─> ProjectsPage.tsx
            └─> useAuth (hooks/useAuth.ts)

Types:
  UploadPage.tsx
    └─> types/song.ts (all types)
    └─> types/analysis.ts
    └─> types/sectionVideo.ts

Utils:
  UploadPage.tsx
    ├─> utils/formatting.ts
    ├─> utils/validation.ts
    ├─> utils/sections.ts
    ├─> utils/status.ts
    ├─> utils/audio.ts
    ├─> utils/waveform.ts
    └─> utils/animations.ts
```

---

### Summary

**Total Frontend Files Analyzed:** ~60+ TypeScript/TSX files

**Active Files:** ~60+

- Entry points: 2
- Pages: 3 (UploadPage, LoginPage, ProjectsPage)
- Components: 35+ (vibecraft: 9, upload: 12, song: 8, auth: 1, projects: 1, error boundaries: 3, MainVideoPlayer: 1)
- Hooks: 8
- Utilities: 7
- Types: 3
- Constants: 1

**Dead Code Identified:**

- None - All code appears to be actively used

**Key Findings:**

- **Authentication system:** JWT-based auth with login/register
- **Routing:** React Router for multi-page navigation
- **Video type selection:** Support for full_length and short_form videos
- **Audio selection:** Interactive timeline for selecting song segments
- **Template characters:** Pre-defined character templates with pose selection
- **Character consistency:** Custom character images with AI generation
- **Error boundaries:** Graceful error handling with React error boundaries
- **React Query:** Server state management with TanStack Query
- **Animations control:** User preference to disable animations
- **Projects management:** Projects page for accessing saved songs
- **Well-structured design system:** Consistent component library
- **Type-safe API communication:** Full TypeScript coverage

**New Features Since Last Update:**

1. ✅ Authentication system (JWT-based)
2. ✅ Routing (React Router)
3. ✅ Video type selection (full_length/short_form)
4. ✅ Audio selection for short_form videos
5. ✅ Template character system
6. ✅ Character consistency workflow
7. ✅ Error boundaries
8. ✅ React Query integration
9. ✅ Projects page
10. ✅ Animations control
11. ✅ Cost tracking display
12. ✅ Prompt viewer

**Recommendations:**

1. Consider adding more routes if needed
2. Consider state management library (Zustand/Redux) if state complexity grows further
3. Add unit tests for custom hooks
4. Add integration tests for component interactions
5. Consider adding E2E tests for critical flows

---

## Backend Analysis

### Overview

The backend is a **FastAPI** application built with **Python 3.12+**. It handles audio processing, music analysis, video generation, and composition orchestration with advanced features including authentication, character consistency, video type support, beat-synchronized effects, and cost tracking.

**Tech Stack:**

- FastAPI (async web framework)
- SQLModel (ORM with Pydantic integration)
- PostgreSQL (database)
- Redis + RQ (job queue)
- S3-compatible storage
- Librosa (audio analysis)
- FFmpeg (audio/video processing)
- Replicate API (video generation)
- Minimax API (via Replicate - video generation)
- Audjust API (music structure analysis)
- OpenAI API (image interrogation for character consistency)
- PyJWT (JWT authentication)

**Architecture:**

- RESTful API with FastAPI
- Repository pattern for data access
- Service layer for business logic
- RQ workers for async job processing
- SQLModel for database models
- Pydantic schemas for API contracts
- JWT-based authentication
- Rate limiting middleware
- Video provider abstraction (base + Minimax provider)

---

### Entry Points

#### `backend/app/main.py`

**Status:** ✅ Active  
**Usage:** FastAPI application entry point

**Features:**

- Creates FastAPI app instance
- Configures CORS middleware
- Sets up lifespan events
- Includes API router
- Health check endpoint (`/healthz`)
- **Rate limiting middleware** - Applies rate limiting to all requests

**Dependencies:**

- `app.api.v1.api_router` - Main API router
- `app.core.config` - Settings configuration
- `app.core.database` - Database initialization
- `app.core.logging` - Logging configuration
- `app.core.rate_limiting` - Rate limiting middleware

**Used by:** Uvicorn server

---

### API Routes

#### `backend/app/api/v1/routes_songs.py`

**Status:** ✅ Active (1,000+ lines - comprehensive song management)  
**Usage:** Song-related API endpoints

**Endpoints:**

- `GET /songs/` - List all songs (authenticated)
- `POST /songs/` - Upload new song
- `GET /songs/{song_id}` - Get song details
- `PATCH /songs/{song_id}/video-type` - Set video type (full_length/short_form)
- `PATCH /songs/{song_id}/selection` - Set audio selection (start/end times)
- `POST /songs/{song_id}/analyze` - Enqueue song analysis
- `GET /songs/{song_id}/analysis` - Get latest analysis
- `GET /songs/{song_id}/beat-aligned-boundaries` - Get beat-aligned clip boundaries
- `POST /songs/{song_id}/clips/plan` - Plan clips for song
- `GET /songs/{song_id}/clips` - List planned clips
- `GET /songs/{song_id}/clips/status` - Get clip generation status
- `GET /songs/{song_id}/clips/job` - Get active clip generation job
- `POST /songs/{song_id}/clips/generate` - Start clip generation job
- `POST /songs/{song_id}/clips/{clip_id}/retry` - Retry clip generation
- `POST /songs/{song_id}/clips/compose` - Compose completed clips (sync)
- `POST /songs/{song_id}/clips/compose/async` - Compose completed clips (async)
- `POST /songs/{song_id}/compose` - Enqueue video composition job
- `GET /songs/{song_id}/compose/{job_id}/status` - Get composition job status
- `POST /songs/{song_id}/compose/{job_id}/cancel` - Cancel composition job
- `GET /songs/{song_id}/composed-videos/{composed_video_id}` - Get composed video

**Dependencies:**

- `app.services.song_analysis` - Analysis service
- `app.services.clip_generation` - Clip generation service
- `app.services.clip_planning` - Clip planning service
- `app.services.composition_job` - Composition job service
- `app.services.beat_alignment` - Beat alignment service
- `app.services.storage` - Storage service
- `app.services.audio_preprocessing` - Audio preprocessing
- `app.services.audio_selection` - Audio selection validation
- `app.core.auth` - Authentication dependencies

#### `backend/app/api/v1/routes_auth.py`

**Status:** ✅ Active  
**Usage:** Authentication endpoints

**Endpoints:**

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info
- `PATCH /auth/me` - Update current user info

**Dependencies:**

- `app.core.auth` - Authentication utilities
- `app.models.user` - User model

#### `backend/app/api/v1/routes_template_characters.py`

**Status:** ✅ Active  
**Usage:** Template character endpoints

**Endpoints:**

- `GET /template-characters/` - List all template characters
- `GET /template-characters/{character_id}` - Get template character details
- `GET /template-characters/{character_id}/image/{pose}` - Get template character image
- `POST /songs/{song_id}/template-character` - Apply template character to song

**Dependencies:**

- `app.services.template_characters` - Template character service
- `app.services.storage` - Storage service
- `app.services.image_validation` - Image validation

#### `backend/app/api/v1/routes_config.py`

**Status:** ✅ Active  
**Usage:** Configuration endpoints

**Endpoints:**

- `GET /config/features` - Get feature flags

**Dependencies:**

- `app.core.config` - Configuration settings

#### `backend/app/api/v1/routes_jobs.py`

**Status:** ✅ Active  
**Usage:** Job status endpoints

**Endpoints:**

- `GET /jobs/{job_id}` - Get job status (routes to analysis or clip generation)

**Dependencies:**

- `app.services.song_analysis` - Analysis job status
- `app.services.clip_generation` - Clip generation job status

#### `backend/app/api/v1/routes_health.py`

**Status:** ✅ Active  
**Usage:** Health check endpoints

**Endpoints:**

- Health check endpoints for monitoring

#### `backend/app/api/v1/routes_scenes.py`

**Status:** ✅ Active  
**Usage:** Scene-related endpoints

**Endpoints:**

- Scene planning and management endpoints

#### `backend/app/api/v1/routes_videos.py`

**Status:** ✅ Active  
**Usage:** Video-related endpoints

**Endpoints:**

- Video management endpoints

#### `backend/app/api/v1/__init__.py`

**Status:** ✅ Active  
**Usage:** API router aggregation

- Combines all route modules into main API router
- Includes: health, auth, songs, jobs, scenes, videos, config, template-characters
- **Used by:** `app.main`

#### `backend/app/api/deps.py`

**Status:** ✅ Active  
**Usage:** FastAPI dependencies

- Database session dependency
- Authentication dependencies
- Other shared dependencies

---

### Models

#### `backend/app/models/song.py`

**Status:** ✅ Active  
**Usage:** Song database model

**Fields:**

- `id` - UUID primary key
- `user_id` - User foreign key (indexed, authenticated users)
- `title` - Song title
- `original_filename` - Original uploaded filename
- `original_file_size` - File size in bytes
- `original_content_type` - MIME type
- `original_s3_key` - S3 key for original audio
- `processed_s3_key` - S3 key for processed audio
- `processed_sample_rate` - Processed audio sample rate
- `waveform_json` - Waveform data (JSON)
- `duration_sec` - Song duration in seconds
- `description` - Optional description
- `attribution` - Optional attribution
- `composed_video_s3_key` - S3 key for composed video
- `composed_video_poster_s3_key` - S3 key for video poster
- `composed_video_duration_sec` - Composed video duration
- `composed_video_fps` - Composed video FPS
- `selected_start_sec` - Audio selection start time (for short_form)
- `selected_end_sec` - Audio selection end time (for short_form)
- `video_type` - Video type: "full_length" or "short_form"
- `template` - Visual style template: "abstract", "environment", "character", "minimal"
- `character_reference_image_s3_key` - S3 key for user's character reference image
- `character_pose_b_s3_key` - S3 key for character pose B image
- `character_selected_pose` - Selected pose: "A" or "B"
- `character_consistency_enabled` - Whether character consistency is enabled
- `character_interrogation_prompt` - Prompt extracted from character image
- `character_generated_image_s3_key` - S3 key for AI-generated consistent character
- `total_generation_cost_usd` - Total cost in USD for video generation
- `created_at` - Creation timestamp (indexed)
- `updated_at` - Update timestamp

#### `backend/app/models/user.py`

**Status:** ✅ Active  
**Usage:** User database model

**Fields:**

- `id` - String primary key
- `email` - Email (unique, indexed)
- `password_hash` - Hashed password (SHA-256)
- `display_name` - Optional display name
- `animations_disabled` - Whether animations are disabled (user preference)
- `created_at` - Creation timestamp
- `updated_at` - Update timestamp

**Note:** Now actively used for authentication. Songs are associated with authenticated users.

#### `backend/app/models/analysis.py`

**Status:** ✅ Active  
**Usage:** Analysis-related models

**Models:**

- `SongAnalysisRecord` - Stores song analysis results (JSON)
- `AnalysisJob` - Tracks analysis job status
- `ClipGenerationJob` - Tracks clip generation job status

#### `backend/app/models/clip.py`

**Status:** ✅ Active  
**Usage:** Clip database model

**Fields:**

- `id` - UUID primary key
- `song_id` - Song foreign key
- `clip_index` - Clip index in sequence
- `start_sec`, `end_sec` - Clip time boundaries
- `duration_sec` - Clip duration
- `start_beat_index`, `end_beat_index` - Beat indices
- `num_frames` - Number of video frames
- `fps` - Video FPS
- `status` - Clip status (queued, processing, completed, failed)
- `source` - Clip source (beat, manual, etc.)
- `video_url` - Video URL
- `prompt` - Generation prompt
- `style_seed` - Style seed for generation
- `rq_job_id` - RQ job ID
- `replicate_job_id` - Replicate job ID
- `error` - Error message if failed
- `created_at`, `updated_at` - Timestamps

#### `backend/app/models/composition.py`

**Status:** ✅ Active  
**Usage:** Composition-related models

**Models:**

- `CompositionJob` - Tracks composition job status
- `ComposedVideo` - Stores composed video metadata

#### `backend/app/models/section_video.py`

**Status:** ✅ Active  
**Usage:** Section video model

**Fields:**

- Section video metadata and relationships

---

### Repositories

#### `backend/app/repositories/song_repository.py`

**Status:** ✅ Active  
**Usage:** Song data access operations

**Methods:**

- `get_by_id(song_id)` - Get song by ID
- `get_all()` - Get all songs
- `get_by_user_id(user_id)` - Get songs by user ID
- `create(song)` - Create new song
- `update(song)` - Update existing song

**Used by:** Services, API routes

#### `backend/app/repositories/clip_repository.py`

**Status:** ✅ Active  
**Usage:** Clip data access operations

**Methods:**

- `get_by_id(clip_id)` - Get clip by ID
- `get_by_song_id(song_id)` - Get all clips for song
- `get_completed_by_song_id(song_id)` - Get completed clips for song
- `create(clip)` - Create new clip
- `update(clip)` - Update existing clip

**Used by:** Services, API routes

---

### Services

#### `backend/app/services/song_analysis.py`

**Status:** ✅ Active  
**Usage:** Song analysis orchestration

**Functions:**

- `enqueue_song_analysis(song_id)` - Enqueue analysis job
- `run_song_analysis_job(song_id, job_id)` - RQ worker function for analysis
- `get_job_status(job_id)` - Get analysis job status
- `get_latest_analysis(song_id)` - Get latest analysis for song

**Features:**

- Uses Audjust API for structure analysis
- Uses Librosa for BPM and beat detection
- Uses Whisper for lyric extraction
- Computes genre and mood features
- Infers section types
- Stores results in `SongAnalysisRecord`

**Dependencies:**

- `app.services.audjust_client` - Audjust API client
- `app.services.lyric_extraction` - Lyric extraction
- `app.services.genre_mood_analysis` - Genre/mood analysis
- `app.services.section_inference` - Section type inference
- `app.services.storage` - Storage operations

#### `backend/app/services/clip_generation.py`

**Status:** ✅ Active  
**Usage:** Clip generation orchestration

**Functions:**

- `start_clip_generation_job(song_id, max_parallel)` - Start clip generation job
- `run_clip_generation_job(clip_id)` - RQ worker function for single clip
- `enqueue_clip_generation_batch(...)` - Enqueue batch of clips
- `retry_clip_generation(clip_id)` - Retry failed clip
- `get_clip_generation_summary(song_id)` - Get clip generation status
- `get_clip_generation_job_status(job_id)` - Get batch job status
- `compose_song_video(song_id, job_id)` - Compose video from clips

**Features:**

- Generates clips via Replicate API (with provider abstraction)
- Manages clip generation jobs
- Handles retries and errors
- Composes final video from clips
- Supports character consistency
- Supports video type-specific generation (full_length/short_form)
- Cost tracking

**Dependencies:**

- `app.services.video_generation` - Video generation
- `app.services.scene_planner` - Scene planning
- `app.services.video_composition` - Video composition
- `app.services.storage` - Storage operations
- `app.services.character_consistency` - Character consistency
- `app.services.cost_tracking` - Cost tracking

#### `backend/app/services/clip_planning.py`

**Status:** ✅ Active  
**Usage:** Beat-aligned clip planning

**Functions:**

- `plan_beat_aligned_clips(...)` - Plan clips with beat alignment
- `persist_clip_plans(song_id, plans, ...)` - Save clip plans to database

**Features:**

- Calculates beat-aligned clip boundaries
- Ensures clips are 3-6 seconds
- Aligns to video frames

**Dependencies:**

- `app.services.beat_alignment` - Beat alignment calculations

#### `backend/app/services/beat_alignment.py`

**Status:** ✅ Active  
**Usage:** Beat alignment calculations

**Functions:**

- `calculate_beat_aligned_boundaries(...)` - Calculate aligned boundaries
- `validate_boundaries(...)` - Validate boundary alignment

**Features:**

- Aligns clip boundaries to beats
- Validates alignment accuracy

#### `backend/app/services/video_generation.py`

**Status:** ✅ Active  
**Usage:** Video generation via Replicate (with provider abstraction)

**Functions:**

- `generate_section_video(scene_spec, seed, num_frames, fps, video_type, reference_image_url)` - Generate video
- `poll_video_generation_status(...)` - Poll generation status

**Features:**

- Interfaces with Replicate API
- Uses video provider abstraction (base + Minimax provider)
- Handles video generation polling
- Downloads and stores generated videos
- Supports image-to-video (for character consistency)
- Supports video type-specific parameters

**Dependencies:**

- Replicate API client
- `app.services.video_providers.base` - Video provider base class
- `app.services.video_providers.minimax_provider` - Minimax provider
- `app.services.storage` - Storage operations

#### `backend/app/services/video_providers/base.py`

**Status:** ✅ Active  
**Usage:** Base class for video generation providers

**Features:**

- Abstract base class for video providers
- Defines interface for text-to-video and image-to-video
- Provider abstraction for different video generation APIs

#### `backend/app/services/video_providers/minimax_provider.py`

**Status:** ✅ Active  
**Usage:** Minimax Hailuo 2.3 video generation provider

**Features:**

- Implements Minimax Hailuo 2.3 via Replicate
- Supports image-to-video via `first_frame_image`
- Handles video type-specific parameters (resolution, duration)
- Supports 1080p (short_form) and 768p (full_length)

#### `backend/app/services/scene_planner.py`

**Status:** ✅ Active  
**Usage:** Scene specification generation

**Functions:**

- `build_scene_spec(clip_id, analysis)` - Build scene spec for clip
- `get_section_from_analysis(...)` - Get section from analysis
- `get_section_lyrics_from_analysis(...)` - Get section lyrics

**Features:**

- Generates prompts from analysis
- Incorporates mood, genre, lyrics
- Creates scene specifications for video generation
- Uses prompt enhancement for beat synchronization
- Incorporates character consistency prompts

**Dependencies:**

- `app.services.prompt_enhancement` - Prompt enhancement
- `app.services.character_consistency` - Character consistency

#### `backend/app/services/prompt_enhancement.py`

**Status:** ✅ Active  
**Usage:** Prompt enhancement for beat synchronization

**Functions:**

- `enhance_prompt_with_beat_sync(...)` - Enhance prompt with beat-synchronized motion descriptors
- `get_motion_type_for_bpm(...)` - Get motion type based on BPM
- `get_tempo_descriptor(...)` - Get tempo descriptor

**Features:**

- Adds rhythmic motion descriptors to prompts
- BPM-based motion type selection (bouncing, dancing, pulsing, rotating, stepping, looping)
- Tempo descriptors (slow, medium, fast)
- Enhances prompts for better beat synchronization

#### `backend/app/services/video_composition.py`

**Status:** ✅ Active  
**Usage:** Video composition operations

**Functions:**

- `concatenate_clips(...)` - Concatenate clips into single video
- `normalize_clip(...)` - Normalize clip format
- `generate_video_poster(...)` - Generate video poster image
- `apply_beat_filters(...)` - Apply beat-synchronized visual effects

**Features:**

- Uses FFmpeg for video composition
- Handles transitions and normalization
- Generates poster images
- Applies beat-synchronized visual effects (flash, color_burst, zoom_pulse, brightness_pulse, glitch)

**Dependencies:**

- FFmpeg
- `app.services.storage` - Storage operations
- `app.services.beat_filters` - Beat filter effects
- `app.services.beat_filter_applicator` - Beat filter application

#### `backend/app/services/beat_filters.py`

**Status:** ✅ Active  
**Usage:** Beat-reactive FFmpeg filter service

**Functions:**

- `convert_beat_times_to_frames(...)` - Convert beat times to frame indices
- `build_beat_filter_chain(...)` - Build FFmpeg filter chain for beat effects

**Features:**

- Defines beat-synchronized visual effects (flash, color_burst, zoom_pulse, brightness_pulse, glitch)
- Converts beat timestamps to frame-accurate indices
- Builds FFmpeg filter chains for effects

#### `backend/app/services/beat_filter_applicator.py`

**Status:** ✅ Active  
**Usage:** Applies beat filters to video composition

**Functions:**

- Applies beat-synchronized effects during video composition

**Dependencies:**

- `app.services.beat_filters` - Beat filter definitions

#### `backend/app/services/composition_job.py`

**Status:** ✅ Active  
**Usage:** Composition job orchestration

**Functions:**

- `enqueue_composition(...)` - Enqueue composition job
- `enqueue_song_clip_composition(song_id)` - Enqueue song clip composition
- `run_composition_job(...)` - RQ worker function
- `run_song_clip_composition_job(song_id)` - RQ worker for song clips
- `get_job_status(job_id)` - Get composition job status
- `get_composed_video(composed_video_id)` - Get composed video
- `cancel_job(job_id)` - Cancel composition job
- `update_job_progress(job_id, progress)` - Update job progress

**Features:**

- Manages composition job lifecycle
- Tracks progress
- Handles errors and cancellation

**Dependencies:**

- `app.services.composition_execution` - Composition execution
- `app.services.clip_generation` - Clip access

#### `backend/app/services/composition_execution.py`

**Status:** ✅ Active  
**Usage:** Composition execution pipeline

**Functions:**

- `execute_composition_pipeline(...)` - Execute composition pipeline

**Features:**

- Orchestrates video composition steps
- Handles clip downloading, normalization, concatenation
- Applies beat filters if enabled

**Dependencies:**

- `app.services.video_composition` - Video composition operations
- `app.services.storage` - Storage operations

#### `backend/app/services/audio_preprocessing.py`

**Status:** ✅ Active  
**Usage:** Audio preprocessing

**Functions:**

- `preprocess_audio(file_bytes, original_suffix)` - Preprocess audio file

**Features:**

- Converts audio to standard format
- Extracts waveform data
- Computes duration and sample rate

**Dependencies:**

- FFmpeg
- Librosa

#### `backend/app/services/audio_selection.py`

**Status:** ✅ Active  
**Usage:** Audio selection validation service

**Functions:**

- `validate_audio_selection(start_sec, end_sec, song_duration_sec)` - Validate audio selection

**Features:**

- Validates audio selection parameters
- Checks min/max duration constraints
- Validates time boundaries

**Dependencies:**

- `app.core.constants` - Audio selection constants

#### `backend/app/services/storage.py`

**Status:** ✅ Active  
**Usage:** S3 storage operations

**Functions:**

- `upload_bytes_to_s3(...)` - Upload bytes to S3
- `download_bytes_from_s3(...)` - Download bytes from S3
- `generate_presigned_get_url(...)` - Generate presigned URL
- `check_s3_object_exists(...)` - Check if object exists
- `get_character_image_s3_key(...)` - Get S3 key for character images
- `upload_consistent_character_image(...)` - Upload consistent character image

**Features:**

- S3-compatible storage interface
- Presigned URL generation
- Error handling
- Character image storage helpers

#### `backend/app/services/template_characters.py`

**Status:** ✅ Active  
**Usage:** Template character management service

**Functions:**

- `get_template_characters()` - Get all template characters
- `get_template_character(character_id)` - Get template character by ID
- `get_template_character_image(character_id, pose)` - Get template character image

**Features:**

- Manages pre-defined character templates
- Character definitions with poses (A and B)
- Image retrieval from S3

**Dependencies:**

- `app.services.storage` - Storage operations

#### `backend/app/services/character_consistency.py`

**Status:** ✅ Active  
**Usage:** Character consistency orchestration service

**Functions:**

- `generate_character_image_job(song_id)` - RQ job for generating consistent character image

**Features:**

- Downloads user's character reference image
- Interrogates image to extract detailed prompt
- Generates consistent character image via AI
- Uploads consistent image to S3
- Updates song record

**Dependencies:**

- `app.services.character_image_generation` - Character image generation
- `app.services.image_interrogation` - Image interrogation
- `app.services.storage` - Storage operations

#### `backend/app/services/character_image_generation.py`

**Status:** ✅ Active  
**Usage:** Character image generation service

**Functions:**

- `generate_consistent_character_image(...)` - Generate consistent character image

**Features:**

- Generates character images via Replicate/OpenAI
- Ensures character consistency across clips

#### `backend/app/services/image_interrogation.py`

**Status:** ✅ Active  
**Usage:** Image interrogation service

**Functions:**

- `interrogate_reference_image(...)` - Interrogate image to extract prompt

**Features:**

- Uses OpenAI Vision API or Replicate to interrogate images
- Extracts detailed prompts from character reference images

#### `backend/app/services/image_processing.py`

**Status:** ✅ Active  
**Usage:** Image processing utilities

**Functions:**

- Image processing and manipulation utilities

#### `backend/app/services/image_validation.py`

**Status:** ✅ Active  
**Usage:** Image validation service

**Functions:**

- `normalize_image_format(...)` - Normalize image format

**Features:**

- Validates image formats
- Normalizes images for processing

#### `backend/app/services/clip_model_selector.py`

**Status:** ✅ Active  
**Usage:** Clip model selection service

**Functions:**

- Selects appropriate video generation model based on video type and features

**Features:**

- Model selection logic
- Supports different models for different use cases

#### `backend/app/services/cost_tracking.py`

**Status:** ✅ Active  
**Usage:** Cost tracking service for video generation

**Functions:**

- `estimate_video_generation_cost(...)` - Estimate cost for video generation
- `track_generation_cost(...)` - Track actual generation cost
- `update_song_cost(...)` - Update song's total cost

**Features:**

- Tracks costs for video generation
- Estimates costs per model
- Tracks character consistency costs
- Updates song's total cost in database

**Dependencies:**

- `app.repositories.song_repository` - Song repository

#### `backend/app/services/prompt_logger.py`

**Status:** ✅ Active  
**Usage:** Prompt logging service

**Functions:**

- Logs generation prompts for debugging and analysis

#### `backend/app/services/audjust_client.py`

**Status:** ✅ Active  
**Usage:** Audjust API client

**Functions:**

- `fetch_structure_segments(...)` - Fetch structure segments from Audjust

**Features:**

- Interfaces with Audjust API for music structure analysis
- Handles errors and timeouts

#### `backend/app/services/genre_mood_analysis.py`

**Status:** ✅ Active  
**Usage:** Genre and mood analysis

**Functions:**

- `compute_genre(...)` - Compute genre
- `compute_mood_features(...)` - Compute mood features
- `compute_mood_tags(...)` - Compute mood tags

**Features:**

- Analyzes audio features for genre/mood
- Generates mood vectors and tags

#### `backend/app/services/lyric_extraction.py`

**Status:** ✅ Active  
**Usage:** Lyric extraction and alignment

**Functions:**

- `extract_and_align_lyrics(...)` - Extract and align lyrics
- `extract_lyrics_with_whisper(...)` - Extract lyrics with Whisper
- `align_lyrics_to_sections(...)` - Align lyrics to sections
- `segment_lyrics_into_lines(...)` - Segment lyrics into lines

**Features:**

- Uses Whisper for transcription
- Aligns lyrics to song sections
- Handles timing and segmentation

#### `backend/app/services/section_inference.py`

**Status:** ✅ Active  
**Usage:** Section type inference

**Functions:**

- `infer_section_types(...)` - Infer section types from structure

**Features:**

- Infers section types (verse, chorus, bridge, etc.) from structure analysis

#### `backend/app/services/base_job.py`

**Status:** ✅ Active  
**Usage:** Base job utilities

**Functions:**

- Base job functionality and utilities

---

### Core

#### `backend/app/core/config.py`

**Status:** ✅ Active  
**Usage:** Application configuration

**Features:**

- Pydantic Settings for configuration
- Environment variable support
- Database, Redis, S3, API keys configuration
- Feature flags (e.g., `is_sections_enabled()`)
- **Used by:** All services and routes

#### `backend/app/core/database.py`

**Status:** ✅ Active  
**Usage:** Database connection and initialization

**Features:**

- SQLModel engine creation
- Database session management
- Schema initialization
- Default user creation (if needed)

**Dependencies:**

- SQLModel
- PostgreSQL (via psycopg)

#### `backend/app/core/auth.py`

**Status:** ✅ Active  
**Usage:** Authentication utilities

**Functions:**

- `hash_password(password)` - Hash password (SHA-256)
- `verify_password(password, hashed)` - Verify password
- `create_access_token(user_id)` - Create JWT token
- `decode_access_token(token)` - Decode JWT token
- `get_current_user(...)` - Get current authenticated user (FastAPI dependency)

**Features:**

- JWT-based authentication
- Password hashing (SHA-256)
- Token creation and validation
- FastAPI dependency for protected routes

**Dependencies:**

- PyJWT
- `app.models.user` - User model

#### `backend/app/core/rate_limiting.py`

**Status:** ✅ Active  
**Usage:** Rate limiting middleware

**Features:**

- Rate limiting middleware for FastAPI
- Sliding window algorithm
- Per-user or per-IP rate limiting
- Exempts polling endpoints
- Configurable limits (per minute, hour, day)

**Dependencies:**

- FastAPI middleware

#### `backend/app/core/queue.py`

**Status:** ✅ Active  
**Usage:** RQ queue management

**Functions:**

- `get_queue(queue_name, timeout)` - Get RQ queue instance

**Features:**

- Redis connection management
- Queue instance caching
- **Used by:** All job services

#### `backend/app/core/logging.py`

**Status:** ✅ Active  
**Usage:** Logging configuration

**Features:**

- Configures application logging
- Structured logging setup

#### `backend/app/core/constants.py`

**Status:** ✅ Active  
**Usage:** Application constants

**Constants:**

- `MAX_DURATION_SECONDS` - Maximum song duration
- `ALLOWED_CONTENT_TYPES` - Allowed audio MIME types
- `ACCEPTABLE_ALIGNMENT` - Beat alignment tolerance
- `DEFAULT_MAX_CONCURRENCY` - Default max parallel jobs
- `MIN_AUDIO_SELECTION_DURATION_SEC` - Minimum audio selection duration
- `MAX_AUDIO_SELECTION_DURATION_SEC` - Maximum audio selection duration
- Queue timeouts

#### `backend/app/core/migrations.py`

**Status:** ✅ Active  
**Usage:** Database migration utilities

**Features:**

- Migration helpers
- Schema update utilities

---

### Schemas

#### `backend/app/schemas/song.py`

**Status:** ✅ Active  
**Usage:** Song-related Pydantic schemas

**Schemas:**

- `SongRead` - Song read response
- `SongUploadResponse` - Upload response

#### `backend/app/schemas/analysis.py`

**Status:** ✅ Active  
**Usage:** Analysis-related Pydantic schemas

**Schemas:**

- `SongAnalysis` - Full analysis result
- `SongSection` - Section data
- `BeatAlignedBoundariesResponse` - Beat alignment response
- `ClipBoundaryMetadata` - Clip boundary metadata

#### `backend/app/schemas/clip.py`

**Status:** ✅ Active  
**Usage:** Clip-related Pydantic schemas

**Schemas:**

- `SongClipRead` - Clip read response
- `SongClipStatus` - Clip status response
- `ClipGenerationSummary` - Clip generation summary
- `ClipPlanBatchResponse` - Clip plan response

#### `backend/app/schemas/composition.py`

**Status:** ✅ Active  
**Usage:** Composition-related Pydantic schemas

**Schemas:**

- `ComposeVideoRequest` - Composition request
- `ComposeVideoResponse` - Composition response
- `CompositionJobStatusResponse` - Job status response
- `ComposedVideoResponse` - Composed video response

#### `backend/app/schemas/job.py`

**Status:** ✅ Active  
**Usage:** Job-related Pydantic schemas

**Schemas:**

- `JobStatusResponse` - Generic job status
- `SongAnalysisJobResponse` - Analysis job response
- `ClipGenerationJobResponse` - Clip generation job response

#### `backend/app/schemas/scene.py`

**Status:** ✅ Active  
**Usage:** Scene-related Pydantic schemas

**Schemas:**

- `SceneSpec` - Scene specification for video generation

#### `backend/app/schemas/section_video.py`

**Status:** ✅ Active  
**Usage:** Section video Pydantic schemas

#### `backend/app/schemas/template_character.py`

**Status:** ✅ Active  
**Usage:** Template character Pydantic schemas

**Schemas:**

- `TemplateCharacter` - Template character data
- `CharacterPose` - Character pose data
- `TemplateCharacterListResponse` - List response
- `TemplateCharacterApply` - Apply template request

---

### Exceptions

#### `backend/app/exceptions.py`

**Status:** ✅ Active  
**Usage:** Custom exception classes

**Exceptions:**

- `SongNotFoundError`
- `ClipNotFoundError`
- `JobNotFoundError`
- `JobStateError`
- `AnalysisError`
- `ClipGenerationError`
- `CompositionError`
- `StorageError`
- `ClipPlanningError`
- `AudjustConfigurationError`
- `AudjustRequestError`

---

### Dead Code Analysis

#### Unused Services

**None identified** - All services appear to be actively used.

#### Unused Models

**None identified** - All models are used by services or API routes.

#### Unused Schemas

**None identified** - All schemas are used for API contracts.

---

### Usage Patterns

#### API Design

- **Pattern:** RESTful API with FastAPI
- **Structure:** Resource-based routes (`/songs/{id}/...`)
- **Async:** Async endpoints for I/O operations
- **Error handling:** Custom exceptions with HTTP status codes
- **Authentication:** JWT-based auth with protected routes
- **Rate limiting:** Middleware for rate limiting

#### Data Access

- **Pattern:** Repository pattern
- **ORM:** SQLModel (SQLAlchemy + Pydantic)
- **Sessions:** Context managers for database sessions
- **Transactions:** Automatic commit/rollback
- **User isolation:** Songs filtered by user_id

#### Job Processing

- **Pattern:** RQ (Redis Queue) for async jobs
- **Workers:** Separate RQ worker processes
- **Job tracking:** Database records for job status
- **Progress:** Job progress tracking in database

#### Service Layer

- **Pattern:** Service functions for business logic
- **Separation:** Services separated by domain (analysis, generation, composition, auth, characters, etc.)
- **Dependencies:** Services depend on repositories and other services
- **Error handling:** Custom exceptions propagated to API layer
- **Provider abstraction:** Video generation uses provider pattern

#### Configuration

- **Pattern:** Pydantic Settings with environment variables
- **Validation:** Settings validated at startup
- **Caching:** Settings cached with `lru_cache`
- **Feature flags:** Feature flags for gradual rollout

#### Authentication

- **Pattern:** JWT-based authentication
- **Password hashing:** SHA-256 (simple, not production-grade - should use bcrypt)
- **Token management:** JWT tokens with expiration
- **Protected routes:** FastAPI dependencies for authentication

---

### File Dependencies Graph

```text
main.py
  └─> api/v1/api_router
       ├─> routes_songs.py
       │    ├─> services/song_analysis
       │    ├─> services/clip_generation
       │    ├─> services/clip_planning
       │    ├─> services/composition_job
       │    ├─> services/beat_alignment
       │    ├─> services/storage
       │    ├─> services/audio_preprocessing
       │    ├─> services/audio_selection
       │    └─> core/auth
       ├─> routes_auth.py
       │    └─> core/auth
       ├─> routes_template_characters.py
       │    ├─> services/template_characters
       │    ├─> services/storage
       │    └─> services/image_validation
       ├─> routes_config.py
       │    └─> core/config
       ├─> routes_jobs.py
       │    ├─> services/song_analysis
       │    └─> services/clip_generation
       ├─> routes_health.py
       ├─> routes_scenes.py
       └─> routes_videos.py

services/song_analysis.py
  ├─> repositories/song_repository
  ├─> services/audjust_client
  ├─> services/lyric_extraction
  ├─> services/genre_mood_analysis
  ├─> services/section_inference
  └─> services/storage

services/clip_generation.py
  ├─> repositories/clip_repository
  ├─> repositories/song_repository
  ├─> services/video_generation
  ├─> services/scene_planner
  ├─> services/video_composition
  ├─> services/storage
  ├─> services/character_consistency
  └─> services/cost_tracking

services/video_generation.py
  ├─> services/video_providers/base
  ├─> services/video_providers/minimax_provider
  └─> services/storage

services/scene_planner.py
  ├─> services/prompt_enhancement
  └─> services/character_consistency

services/video_composition.py
  ├─> services/beat_filters
  ├─> services/beat_filter_applicator
  └─> services/storage

services/character_consistency.py
  ├─> services/character_image_generation
  ├─> services/image_interrogation
  └─> services/storage

repositories/
  └─> core/database

core/
  ├─> config.py (used by all)
  ├─> database.py
  ├─> auth.py
  ├─> rate_limiting.py
  ├─> queue.py
  ├─> logging.py
  └─> constants.py
```

---

### Summary

**Total Backend Files Analyzed:** ~70+ Python files

**Active Files:** ~70+

- Entry points: 1
- API routes: 8
- Models: 6
- Repositories: 2
- Services: 30+
- Schemas: 7
- Core: 7
- Exceptions: 1

**Dead Code Identified:**

- None - All code appears to be actively used

**Key Findings:**

- **Authentication system:** JWT-based authentication with user management
- **Rate limiting:** Middleware for API rate limiting
- **Video type support:** full_length and short_form video types
- **Audio selection:** Validation and storage for audio segment selection
- **Template characters:** Pre-defined character templates with pose selection
- **Character consistency:** AI-generated character images with consistency
- **Video provider abstraction:** Base class + Minimax provider
- **Beat-synchronized effects:** Visual effects synchronized to beats
- **Prompt enhancement:** Beat-synchronized motion descriptors
- **Cost tracking:** Track and display generation costs
- **Image processing:** Image validation, interrogation, and processing
- **Well-structured architecture:** Clear separation of concerns
- **Repository pattern:** Clean data access layer
- **Service layer:** Business logic separated from API routes
- **Async job processing:** RQ workers for long-running tasks
- **Type safety:** Pydantic schemas for API contracts
- **Error handling:** Custom exceptions with proper HTTP status codes
- **Configuration:** Centralized settings management
- **Database:** SQLModel for type-safe ORM

**New Features Since Last Update:**

1. ✅ Authentication system (JWT-based)
2. ✅ Rate limiting middleware
3. ✅ Video type support (full_length/short_form)
4. ✅ Audio selection validation and storage
5. ✅ Template character system
6. ✅ Character consistency workflow
7. ✅ Video provider abstraction
8. ✅ Minimax Hailuo 2.3 provider
9. ✅ Beat-synchronized visual effects
10. ✅ Prompt enhancement for beat sync
11. ✅ Cost tracking
12. ✅ Image interrogation and processing
13. ✅ Feature flags
14. ✅ User preferences (animations_disabled)

**Architecture Strengths:**

1. ✅ Clear separation: API → Services → Repositories → Database
2. ✅ Async job processing with RQ
3. ✅ Type-safe API contracts with Pydantic
4. ✅ Repository pattern for data access
5. ✅ Service layer for business logic
6. ✅ Comprehensive error handling
7. ✅ Configuration management
8. ✅ Authentication and authorization
9. ✅ Rate limiting
10. ✅ Provider abstraction for video generation
11. ✅ Cost tracking
12. ✅ Character consistency system

**Recommendations:**

1. Add unit tests for services
2. Add integration tests for API routes
3. Add worker health checks
4. Consider upgrading password hashing to bcrypt (currently SHA-256)
5. Consider adding request/response logging middleware
6. Add database migration system (Alembic)
7. Consider adding caching layer for frequently accessed data
8. Consider adding API versioning strategy
9. Consider adding WebSocket support for real-time updates

---

## Overall Architecture Summary

### System Flow

1. **Authentication:**
   - User registers/logs in → JWT token issued → Token used for authenticated requests

2. **Upload & Preprocessing:**
   - User uploads audio file → API validates → Preprocesses audio → Stores in S3 → Creates Song record

3. **Video Type & Audio Selection:**
   - User selects video type (full_length or short_form)
   - For short_form: User selects audio segment via timeline
   - Selection validated and saved to database

4. **Template Character Selection (Optional):**
   - User selects template character or uploads custom character image
   - If custom: Image interrogated → Consistent character generated → Stored in S3

5. **Analysis:**
   - User triggers analysis → API enqueues analysis job → RQ worker processes:
     - Fetches structure from Audjust
     - Analyzes BPM/beats with Librosa
     - Extracts lyrics with Whisper
     - Computes genre/mood
     - Infers section types
     - Stores analysis in database

6. **Clip Planning:**
   - User plans clips → API calculates beat-aligned boundaries → Stores clip plans

7. **Clip Generation:**
   - User starts generation → API enqueues clip jobs → RQ workers:
     - Build scene specs from analysis (with prompt enhancement)
     - Generate videos via Replicate (using provider abstraction)
     - Apply character consistency if enabled
     - Store clips in S3
     - Update clip status
     - Track costs

8. **Composition:**
   - User composes video → API enqueues composition job → RQ worker:
     - Downloads clips from S3
     - Normalizes clips
     - Applies beat-synchronized effects (if enabled)
     - Concatenates with FFmpeg
     - Generates poster
     - Stores final video in S3
     - Updates Song record

### Technology Stack Summary

**Frontend:**

- React 18 + TypeScript
- Vite
- React Router
- TanStack Query (React Query)
- Tailwind CSS
- Axios

**Backend:**

- FastAPI
- Python 3.12+
- SQLModel (ORM)
- PostgreSQL
- Redis + RQ
- S3-compatible storage
- Librosa (audio)
- FFmpeg (video)
- Replicate API (video generation)
- Minimax Hailuo 2.3 (via Replicate)
- Audjust API (structure analysis)
- Whisper (lyrics)
- OpenAI API (image interrogation)
- PyJWT (authentication)

### Key Architectural Decisions

1. **Multi-page application:** React Router for navigation
2. **Authentication:** JWT-based with user management
3. **Rate limiting:** Middleware for API protection
4. **Video types:** Support for full_length and short_form videos
5. **Audio selection:** Interactive timeline for segment selection
6. **Template characters:** Pre-defined characters with pose selection
7. **Character consistency:** AI-generated consistent characters
8. **Video provider abstraction:** Base class + provider implementations
9. **Beat-synchronized effects:** Visual effects synchronized to beats
10. **Prompt enhancement:** Beat-synchronized motion descriptors
11. **Cost tracking:** Track and display generation costs
12. **Custom polling hooks:** Reusable polling patterns
13. **Component extraction:** Maintainable, testable components
14. **Repository pattern:** Clean data access
15. **Service layer:** Business logic separation
16. **RQ workers:** Async job processing
17. **Type safety:** TypeScript + Pydantic throughout
18. **S3 storage:** Scalable file storage
19. **React Query:** Server state management
20. **Error boundaries:** Graceful error handling

---

**Report Generated:** Based on current codebase state  
**Last Updated:** Current analysis with authentication, character consistency, video types, beat effects, and cost tracking features
