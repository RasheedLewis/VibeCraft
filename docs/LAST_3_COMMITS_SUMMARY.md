# Summary of Last 3 Commits

**Date Created:** 2025-11-19  
**Purpose:** Detailed documentation of code changes in commits `1d959cf`, `d0a90dc`, and `88c6da0` to enable integration into refactored codebase.

---

## Table of Contents

1. [High-Level Overview](#high-level-overview)
2. [Commit 1: Retry Logic on Clip Queue Items](#commit-1-retry-logic-on-clip-queue-items)
3. [Commit 2: Audjust API for Song Sections](#commit-2-audjust-api-for-song-sections)
4. [Commit 3: Song Section Label Logic](#commit-3-song-section-label-logic)
5. [Cross-Commit Dependencies](#cross-commit-dependencies)
6. [Integration Considerations](#integration-considerations)

---

## High-Level Overview

The last 3 commits introduce three major features:

1. **Clip Retry Mechanism** - Allows users to retry failed clip generation jobs without re-planning
2. **Audjust API Integration** - External API integration for automatic song structure analysis (section detection)
3. **Section Type Inference** - Heuristic-based labeling system that converts raw Audjust labels into human-readable section types (verse, chorus, bridge, etc.)

These changes span both backend (Python/FastAPI) and frontend (React/TypeScript) codebases, with significant additions to the song analysis pipeline and UI components.

---

## Commit 1: Retry Logic on Clip Queue Items

**Commit Hash:** `1d959cf47bea4b7d7968d73ecae4df8f61667234`  
**Date:** Tue Nov 18 19:28:44 2025 -0600  
**Author:** Rasheed Lewis

### High-Level Purpose

Adds the ability to retry individual failed clip generation jobs without requiring a full re-planning or batch regeneration. This improves user experience by allowing targeted recovery from transient failures.

### Conceptual Changes

1. **New API Endpoint**: `POST /api/v1/songs/{song_id}/clips/{clip_id}/retry`
   - Resets clip state to "queued"
   - Clears previous error messages and video URLs
   - Enqueues a new generation job for the specific clip

2. **Queue Naming Change**: Modified queue name from `settings.rq_worker_queue` to `f"{settings.rq_worker_queue}:clip-generation"` to provide better queue isolation

3. **Error Handling Improvements**: Enhanced error messages in upload endpoints with more specific details about storage configuration issues

4. **Summary Function Behavior**: Changed `get_clip_generation_summary()` to raise `ValueError` when no clips are found (instead of returning empty summary), allowing API to return 404

### Detailed Code Changes

#### Backend Changes

**File: `backend/app/api/v1/routes_songs.py`**

1. **Import Changes** (lines 17-22):
   - Added `SongClipStatus` to imports from `app.schemas.clip`
   - Added `retry_clip_generation` to imports from `app.services.clip_generation`

2. **Error Logging Enhancement** (lines 180-186):
   ```python
   # BEFORE: Generic exception handling
   except Exception as exc:
       db.delete(song)
       db.commit()
       raise HTTPException(...)
   
   # AFTER: Added detailed logging
   except Exception as exc:
       logger.exception(
           "Failed to upload audio assets to storage (bucket=%s, song_id=%s, filename=%s)",
           settings.s3_bucket_name,
           song.id,
           sanitized_filename,
       )
       # ... rest of error handling
   ```

3. **Error Message Improvements** (lines 189-191, 207-209):
   - Changed from: `"Failed to store audio file. Please try again later."`
   - Changed to: `"Failed to store audio file. Verify storage configuration and try again."`
   - Similar improvement for presigned URL generation errors

4. **Summary Endpoint Error Handling** (lines 472-479):
   ```python
   # BEFORE: Direct return
   return get_clip_generation_summary(song_id)
   
   # AFTER: Wrapped in try/except
   try:
       return get_clip_generation_summary(song_id)
   except ValueError as exc:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="No clip plans found for this song.",
       ) from exc
   ```

5. **New Retry Endpoint** (lines 505-537):
   ```python
   @router.post(
       "/{song_id}/clips/{clip_id}/retry",
       response_model=SongClipStatus,
       status_code=status.HTTP_202_ACCEPTED,
       summary="Retry generation for a single clip",
   )
   def retry_clip_generation_route(
       song_id: UUID,
       clip_id: UUID,
       db: Session = Depends(get_db),
   ) -> SongClipStatus:
       # Validates clip exists and belongs to song
       # Checks clip is not already queued/processing
       # Calls retry_clip_generation service function
       # Returns updated clip status
   ```

**File: `backend/app/services/__init__.py`**

- Added `retry_clip_generation` to `__all__` exports (line 49)

**File: `backend/app/services/clip_generation.py`**

1. **Queue Name Change** (lines 48-52):
   ```python
   # BEFORE:
   return Queue(settings.rq_worker_queue, connection=connection, default_timeout=QUEUE_TIMEOUT_SEC)
   
   # AFTER:
   queue_name = f"{settings.rq_worker_queue}:clip-generation"
   return Queue(queue_name, connection=connection, default_timeout=QUEUE_TIMEOUT_SEC)
   ```

2. **New Function: `retry_clip_generation()`** (lines 114-161):
   ```python
   def retry_clip_generation(clip_id: UUID) -> SongClipStatus:
       """
       Reset clip state and enqueue a new generation job.
       
       Process:
       1. Loads clip from database
       2. Validates clip is not already queued/processing
       3. Resets clip state: status="queued", error=None, video_url=None, etc.
       4. Calculates num_frames if missing (from duration_sec * fps)
       5. Enqueues new job with meta={"retry": True}
       6. Updates clip.rq_job_id with new job ID
       7. Returns SongClipStatus
       """
   ```
   
   **Key Implementation Details:**
   - Uses two separate `session_scope()` blocks (one for reset, one for job ID update)
   - Extracts `song_id`, `clip_index`, `fps`, `num_frames` from existing clip
   - Sets `meta={"song_id": str(song_id), "clip_index": clip_index, "retry": True}`
   - Raises `ValueError` if clip not found
   - Raises `RuntimeError` if clip already queued/processing

3. **Summary Function Behavior Change** (lines 247-268):
   ```python
   # BEFORE: Returned empty summary dict when no clips
   if not clips:
       status_counts = Counter()
       total = 0
       # ... return empty summary
   
   # AFTER: Raises ValueError
   if not clips:
       raise ValueError("No planned clips found for song.")
   ```

**File: `backend/tests/test_clip_generation.py`**

1. **DummyQueue Enhancement** (lines 51-52):
   - Modified to auto-generate job IDs if not provided: `job_identifier = job_id or f"job-{len(self.jobs) + 1}"`

2. **Test Parameter Change** (line 135):
   - Changed `max_clip_sec=10.0` to `max_clip_sec=6.0` (unrelated to retry feature, but part of commit)

3. **New Test: `test_retry_clip_generation_resets_state()`** (lines 266-303):
   - Tests that retry function resets clip state correctly
   - Verifies job is enqueued with correct metadata
   - Checks database state after retry

4. **New Test: `test_retry_clip_generation_endpoint()`** (lines 306-340):
   - Tests the HTTP endpoint
   - Verifies 202 status code
   - Checks response payload structure

#### Frontend Changes

**File: `frontend/src/pages/UploadPage.tsx`**

1. **Removed Placeholder Handler** (lines 485-491):
   - Removed the stub `handleRetryClip` that just logged and showed error

2. **New Implementation: `handleRetryClip()`** (lines 617-633):
   ```typescript
   const handleRetryClip = useCallback(
     async (clip: SongClipStatus) => {
       if (!result?.songId) return
       try {
         setClipJobError(null)
         setClipJobStatus('queued')
         setClipJobProgress(0)
         setClipJobId(null)
         await apiClient.post<SongClipStatus>(
           `/songs/${result.songId}/clips/${clip.id}/retry`,
         )
         await fetchClipSummary(result.songId)
       } catch (err) {
         setClipJobError(extractErrorMessage(err, 'Unable to retry clip generation.'))
       }
     },
     [result?.songId, fetchClipSummary],
   )
   ```
   
   **Key Behaviors:**
   - Resets UI state (error, status, progress, job ID)
   - Calls retry endpoint
   - Refreshes clip summary to show updated status
   - Handles errors gracefully

### Dependencies

- Requires `SongClipStatus` schema (already exists)
- Requires RQ (Redis Queue) infrastructure
- Requires `session_scope()` database context manager
- Frontend requires `apiClient` and `fetchClipSummary` function

### Integration Notes

- The queue name change (`:clip-generation` suffix) must be consistent across worker configuration
- The retry function assumes clips have `duration_sec` or `num_frames` set - ensure this is preserved in refactoring
- The two-session pattern in `retry_clip_generation()` is intentional to avoid long-running transactions

---

## Commit 2: Audjust API for Song Sections

**Commit Hash:** `d0a90dc5d56f17d45882fb8301cc4a1049348166`  
**Date:** Wed Nov 19 11:49:43 2025 -0600  
**Author:** Rasheed Lewis

### High-Level Purpose

Integrates the Audjust API as an external service for automatic song structure analysis. When configured, the system uses Audjust to detect song sections (boundaries and similarity labels) instead of relying solely on internal segmentation algorithms. This provides more accurate section detection for songs with clear verse/chorus structures.

### Conceptual Changes

1. **New External Service Integration**: Audjust API client that:
   - Uploads audio files to Audjust's storage
   - Calls structure analysis endpoint
   - Returns section boundaries with similarity labels

2. **Fallback Strategy**: If Audjust is not configured or fails, falls back to existing internal `_detect_sections()` function

3. **Configuration-Based**: Entire feature is opt-in via environment variables - no breaking changes if not configured

4. **Section Schema Extension**: Added new optional fields to `SongSection` schema:
   - `type_soft`: Heuristic-based section type (from inference)
   - `display_name`: Human-readable name (e.g., "Chorus 1", "Verse 2")
   - `raw_label`: Original Audjust label number

### Detailed Code Changes

#### Backend Changes

**File: `backend/app/core/config.py`**

Added 5 new configuration fields (lines 49-53):
```python
audjust_base_url: Optional[AnyUrl] = Field(default=None, alias="AUDJUST_BASE_URL")
audjust_api_key: Optional[str] = Field(default=None, alias="AUDJUST_API_KEY")
audjust_upload_path: str = Field(default="/upload", alias="AUDJUST_UPLOAD_PATH")
audjust_structure_path: str = Field(default="/structure", alias="AUDJUST_STRUCTURE_PATH")
audjust_timeout_sec: float = Field(default=30.0, alias="AUDJUST_TIMEOUT_SEC")
```

**File: `backend/app/schemas/analysis.py`**

Extended `SongSection` model (lines 25-27):
```python
type_soft: Optional[str] = Field(None, alias="typeSoft")
display_name: Optional[str] = Field(None, alias="displayName")
raw_label: Optional[int] = Field(None, alias="rawLabel")
```

**File: `backend/app/services/audjust_client.py`** (NEW FILE, 161 lines)

Complete new service module for Audjust API integration:

1. **Exception Classes** (lines 14-19):
   ```python
   class AudjustConfigurationError(RuntimeError)
   class AudjustRequestError(RuntimeError)
   ```

2. **Main Function: `fetch_structure_segments()`** (lines 22-142):
   ```python
   def fetch_structure_segments(audio_path: Path) -> List[Dict[str, Any]]:
       """
       Three-step process:
       1. GET /upload -> receives storage_url and retrieval_url
       2. PUT to storage_url -> uploads audio file bytes
       3. POST /structure -> sends retrieval_url, receives sections
       
       Returns: List[{"startMs": int, "endMs": int, "label": int}]
       """
   ```
   
   **Key Implementation Details:**
   - Validates configuration (base_url and api_key must be set)
   - Uses `httpx` for HTTP requests
   - Handles multiple response formats (checks both `sections` and `result.sections`)
   - Comprehensive error handling with specific exception types
   - Uses `X-API-Key` header for authentication
   - Configurable timeout (default 30 seconds)

3. **URL Building Helper** (lines 42-46):
   - Normalizes path strings (ensures leading slash)
   - Combines base_url with path

4. **Response Parsing** (lines 125-137):
   - Handles two possible response structures:
     - Direct: `{"sections": [...]}`
     - Wrapped: `{"result": {"sections": [...]}}`

**File: `backend/app/services/section_inference.py`** (NEW FILE, 210 lines)

New module for inferring section types from Audjust labels:

1. **Type Definitions** (lines 11-18):
   ```python
   SectionSoftType = Literal[
       "intro_like", "verse_like", "chorus_like",
       "bridge_like", "outro_like", "other"
   ]
   ```

2. **Data Structure** (lines 21-31):
   ```python
   @dataclass(slots=True)
   class SectionInference:
       id: str
       index: int
       start_sec: float
       end_sec: float
       duration_sec: float
       label_raw: int
       type_soft: SectionSoftType
       confidence: float
       display_name: str
   ```

3. **Main Function: `infer_section_types()`** (lines 40-210):
   ```python
   def infer_section_types(
       audjust_sections: List[dict],
       energy_per_section: List[float],
       vocals_per_section: Optional[List[float]] = None,
   ) -> List[SectionInference]:
   ```
   
   **Algorithm Overview:**
   - Step 1: Normalize sections (convert ms to seconds, compute durations)
   - Step 2: Group by label, compute stats (occurrence count, total duration, mean energy)
   - Step 3: Find chorus candidate (most repeated + energetic, with early-start penalty)
   - Step 4: Find verse candidates (repeated labels that aren't chorus)
   - Step 5: Classify each segment (chorus/verse/intro/outro/bridge/other based on position + label)
   - Step 6: Assign display names (Verse 1, Chorus 2, etc. with ordinals)
   
   **Heuristic Details:**
   - Chorus: Highest score from `0.5 * occ_norm + 0.2 * dur_norm + 0.3 * energy_norm - early_penalty`
   - Early penalty: 0.3 if first_start < 10.0 seconds
   - Intro: pos_ratio < 0.2
   - Outro: pos_ratio > 0.8
   - Bridge: unique label in middle (0.3 < pos_ratio < 0.8)

4. **Helper: `_normalize()`** (lines 34-42):
   - Normalizes values to 0-1 range for scoring

**File: `backend/app/services/song_analysis.py`**

Major integration point - modified analysis pipeline:

1. **New Imports** (lines 31-38):
   ```python
   from app.services.audjust_client import (
       AudjustConfigurationError,
       AudjustRequestError,
       fetch_structure_segments,
   )
   from app.services.section_inference import infer_section_types
   ```

2. **Pipeline Modification** (lines 186-260):
   ```python
   # BEFORE: Direct call to _detect_sections()
   sections = _detect_sections(y, sr, duration)
   
   # AFTER: Conditional Audjust integration
   sections: List[SongSection]
   audjust_sections_raw: Optional[List[dict]] = None
   
   if settings.audjust_base_url and settings.audjust_api_key:
       try:
           audjust_sections_raw = fetch_structure_segments(audio_path)
           # ... process with inference
       except (AudjustConfigurationError, AudjustRequestError, Exception):
           # ... fallback to _detect_sections()
   
   if audjust_sections_raw:
       energy_per_section = _compute_section_energy(y, sr, audjust_sections_raw)
       inferred_sections = infer_section_types(...)
       sections = _build_song_sections_from_inference(inferred_sections)
   else:
       sections = _detect_sections(y, sr, duration)
   ```

3. **New Helper: `_compute_section_energy()`** (lines 413-440):
   ```python
   def _compute_section_energy(
       y: np.ndarray,
       sr: int,
       audjust_sections: list[dict],
       *,
       frame_length: int = 2048,
       hop_length: int = 512,
   ) -> list[float]:
       """
       Computes RMS energy per section using librosa.
       Returns list of mean energy values, one per section.
       """
   ```

4. **New Helper: `_build_song_sections_from_inference()`** (lines 443-480):
   ```python
   def _build_song_sections_from_inference(
       inferred_sections,
   ) -> list[SongSection]:
       """
       Converts SectionInference objects to SongSection schema objects.
       Maps type_soft to canonical type (intro_like -> intro, etc.)
       Sets repetition_group from label_raw.
       """
   ```

#### Frontend Changes

**File: `frontend/src/types/song.ts`**

Extended `SongSection` interface (lines 96-99):
```typescript
typeSoft?: string | null
displayName?: string | null
rawLabel?: number | null
```

**File: `frontend/src/pages/UploadPage.tsx`**

1. **Enhanced `buildSectionsWithDisplayNames()`** (lines 222-260):
   - Now handles `typeSoft`, `rawLabel`, and `displayName` from backend
   - Falls back to old logic if new fields not present
   - Prioritizes `displayName` from backend over local generation

2. **Polling Logic Simplification** (lines 955-1010):
   - Removed composed video URL checks from polling (unrelated to Audjust, but part of commit)
   - Simplified dependency array

**File: `frontend/src/lib/apiClient.ts`**

Minor formatting change (line 18) - trailing comma fix

**File: `frontend/vite.config.ts`**

Minor formatting change (lines 11-13) - code style consistency

#### Documentation

**File: `docs/ENVIRONMENT_SETUP.md`** (NEW FILE, 57 lines)

Complete guide for configuring Audjust API:
- Required environment variables
- How to obtain API key
- Testing instructions
- Troubleshooting section

**File: `docs/song_sections/audjust_api.md`** (NEW FILE, 273 lines)

Comprehensive documentation on:
- What Audjust provides (segments + similarity labels)
- Why semantic labeling is needed
- Heuristic strategies for chorus/verse detection
- Research references and alternatives

**File: `docs/song_sections/infer_section_type.md`** (NEW FILE, 296 lines)

Detailed implementation guide:
- Data structures
- Algorithm walkthrough
- Code examples
- Integration patterns

### Dependencies

- Requires `httpx` Python package (for HTTP requests)
- Requires Audjust API account and credentials
- Requires `librosa` for energy computation (already in use)
- Frontend changes are backward compatible (optional fields)

### Integration Notes

- **Critical**: The feature is completely opt-in - if `AUDJUST_BASE_URL` and `AUDJUST_API_KEY` are not set, the system behaves exactly as before
- The fallback to `_detect_sections()` must be preserved in any refactoring
- The `_compute_section_energy()` function uses librosa's RMS feature - ensure librosa is available
- The inference algorithm assumes sections are provided in chronological order
- Error handling is comprehensive but non-blocking - failures log warnings and continue with fallback

---

## Commit 3: Song Section Label Logic

**Commit Hash:** `88c6da0e6e32ab81d04e92a13bc8b9580d1e89dc`  
**Date:** Wed Nov 19 18:11:32 2025 -0600  
**Author:** Rasheed Lewis

### High-Level Purpose

Refines and improves the section inference algorithm introduced in commit 2. Adds label clustering (to handle similar but not identical Audjust labels), consecutive section merging, enhanced logging, and UI components for section audio playback.

### Conceptual Changes

1. **Label Clustering**: Groups similar Audjust labels (within threshold distance) into clusters, since Audjust labels are similarity-based (closer numbers = more similar audio)

2. **Section Merging**: Merges consecutive sections of the same type to avoid fragmentation (e.g., "Intro" + "Intro 2" → "Intro")

3. **Improved Heuristics**: Refined thresholds and scoring for better section type detection

4. **UI Enhancement**: Added audio player component for previewing individual sections

5. **Logging Cleanup**: Reduced verbose logging, moved to appropriate log levels

### Detailed Code Changes

#### Backend Changes

**File: `backend/app/services/audjust_client.py`**

Logging cleanup throughout (reduced verbosity):

1. **Log Level Changes**:
   - Changed `logger.warning()` to `logger.debug()` for routine operations (lines 34, 60, 75, 110)
   - Changed `logger.warning()` to `logger.info()` for success messages (line 132)
   - Removed many intermediate log statements
   - Kept `logger.error()` for actual errors

2. **Specific Changes**:
   - Line 34: `logger.warning("[AUDJUST] fetch_structure_segments...")` → `logger.debug("fetch_structure_segments...")`
   - Lines 60-61: Removed base URL and endpoint URL logs
   - Line 75: Combined upload success into single debug log
   - Line 110: Removed detailed request logging
   - Line 132: Changed to `logger.info("Audjust returned %d sections...")`

**File: `backend/app/services/section_inference.py`**

Major algorithm improvements:

1. **New Import** (line 3):
   ```python
   import logging
   logger = logging.getLogger(__name__)
   ```

2. **New Function: `_merge_consecutive_sections()`** (lines 45-100):
   ```python
   def _merge_consecutive_sections(sections: List[SectionInference]) -> List[SectionInference]:
       """
       Merges consecutive sections with same type_soft.
       Example: [Intro, Intro 2] -> [Intro]
                [Chorus 2, Chorus 3] -> [Chorus 2]
       
       Process:
       1. Groups consecutive sections by type_soft
       2. Merges each group (takes earliest start, latest end, averages confidence)
       3. Re-assigns display names with correct ordinals
       """
   ```
   
   **Key Details:**
   - Preserves first section's `id`, `index`, and `label_raw`
   - Computes merged `start_sec` (min), `end_sec` (max), `duration_sec` (difference)
   - Averages confidence across merged sections
   - Re-assigns display names after merging to maintain correct ordinals

3. **New Function: `_merge_section_group()`** (lines 103-125):
   ```python
   def _merge_section_group(group: List[SectionInference]) -> SectionInference:
       """
       Helper that actually performs the merge operation.
       Takes min start, max end, averages confidence.
       """
   ```

4. **New Function: `_cluster_similar_labels()`** (lines 128-161):
   ```python
   def _cluster_similar_labels(
       labels: List[int],
       similarity_threshold: int = 50
   ) -> Dict[int, int]:
       """
       Groups labels within threshold distance into clusters.
       Returns mapping: original_label -> cluster_representative (lowest label in cluster)
       
       Example: labels [100, 105, 110, 500, 510] with threshold=50
                -> clusters: {100: 100, 105: 100, 110: 100, 500: 500, 510: 500}
       """
   ```
   
   **Algorithm:**
   - Greedy clustering: for each label, checks if it's within threshold of existing cluster rep
   - If yes, assigns to that cluster; if no, creates new cluster
   - Cluster representative is always the lowest label value in the cluster

5. **Enhanced `infer_section_types()` Function**:

   a. **Step 2: Label Clustering** (lines 225-240):
      ```python
      # NEW: Cluster similar labels before grouping
      label_clusters = _cluster_similar_labels(
          [s["label"] for s in sections_raw],
          similarity_threshold=50,
      )
      for section in sections_raw:
          section["cluster_label"] = label_clusters[section["label"]]
      ```
   
   b. **Step 3: Group by Cluster** (lines 242-270):
      ```python
      # CHANGED: Group by cluster_label instead of raw label
      by_cluster: Dict[int, List[dict]] = defaultdict(list)
      for seg in sections_raw:
          by_cluster[seg["cluster_label"]].append(seg)
      
      cluster_stats = []  # renamed from label_stats
      for cluster_label, segs in by_cluster.items():
          # ... compute stats per cluster
      ```
   
   c. **Step 4: Chorus Detection Refinements** (lines 275-310):
      ```python
      # CHANGED: Uses cluster_label instead of label
      chorus_cluster = None  # renamed from chorus_label
      # ...
      # CHANGED: Early penalty threshold from 10.0s to 8.0s, penalty from 0.3 to 0.2
      early_penalty = 0.0
      if stat["first_start"] < 8.0:
          early_penalty = 0.2
      
      # CHANGED: Score threshold from 0.2 to 0.15 (more permissive)
      if best_score > 0.15:
          chorus_cluster = best_cluster
      ```
   
   d. **Step 5: Verse Detection** (lines 312-322):
      ```python
      # CHANGED: Uses cluster_label
      verse_clusters = set()  # renamed from verse_labels
      for stat in cluster_stats:
          if stat["label"] == chorus_cluster:
              continue
          if stat["occ"] >= 2:
              verse_clusters.add(stat["label"])
      ```
   
   e. **Step 6: Section Classification** (lines 324-380):
      ```python
      # CHANGED: Uses cluster_label for classification
      cluster_label = segment["cluster_label"]
      
      # CHANGED: Intro threshold from 0.2 to 0.15 (more conservative)
      if base_type == "other" and pos_ratio < 0.15:
          base_type = "intro_like"
      
      # CHANGED: Outro threshold from 0.8 to 0.85 (more conservative)
      if base_type == "other" and pos_ratio > 0.85:
          base_type = "outro_like"
      
      # CHANGED: Bridge region from 0.3-0.8 to 0.35-0.75 (narrower)
      if base_type == "other" and 0.35 < pos_ratio < 0.75:
          # ... bridge detection
      ```
   
   f. **Step 7: Display Name Assignment** (lines 407-430):
      - No algorithm changes, but now happens before merging
   
   g. **Step 8: Section Merging** (lines 432-465):
      ```python
      # NEW: Merge consecutive sections
      merged_sections = _merge_consecutive_sections(inferred_sections)
      
      # NEW: Comprehensive logging
      logger.info("Section inference complete (before merging): %d total sections...")
      logger.info("After merging consecutive sections: %d sections (reduced from %d)...")
      for section in merged_sections:
          logger.info("  [%s] %.1fs-%.1fs (%.1fs) | raw_label=%d | conf=%.2f | %s", ...)
      ```

6. **New Logging Throughout**:
   - Line 195: Logs raw Audjust sections with timing and energy
   - Line 235: Logs label clustering results
   - Line 265: Logs cluster statistics
   - Line 300: Logs chorus detection result
   - Line 320: Logs verse clusters
   - Lines 432-465: Comprehensive section breakdown logging

**File: `backend/app/services/song_analysis.py`**

Logging cleanup:

1. **Removed Verbose Logs** (lines 189-195, 201, 220-225):
   - Removed configuration check logging
   - Removed "Audjust is configured" message
   - Removed "Audjust API not configured" warning
   - Kept essential info logs for successful fetches and fallbacks

#### Frontend Changes

**File: `frontend/src/components/vibecraft/SectionAudioPlayer.tsx`** (NEW FILE, 160 lines)

Complete new React component for section audio playback:

1. **Component Interface** (lines 6-11):
   ```typescript
   export interface SectionAudioPlayerProps {
     audioUrl: string
     startSec: number
     endSec: number
     className?: string
   }
   ```

2. **Core Functionality**:
   - Audio element with ref for programmatic control
   - Play/pause button with visual state
   - Progress bar showing playback within section bounds
   - Time display (current / duration)
   - Automatic stop at `endSec` boundary
   - Resets to `startSec` when stopped

3. **Key Implementation Details**:
   - Uses `setInterval` to monitor playback and enforce boundaries
   - Handles `onTimeUpdate` and `onEnded` events
   - Cleans up intervals on unmount
   - Formats time as MM:SS
   - Styled with Tailwind classes matching design system

**File: `frontend/src/components/vibecraft/SectionCard.tsx`**

1. **New Prop** (line 17):
   ```typescript
   audioUrl?: string
   ```

2. **Component Integration** (lines 58-62):
   ```typescript
   {audioUrl && (
     <div className="mt-3">
       <SectionAudioPlayer audioUrl={audioUrl} startSec={startSec} endSec={endSec} />
     </div>
   )}
   ```

**File: `frontend/src/components/vibecraft/index.ts`**

Added export (line 9):
```typescript
export * from './SectionAudioPlayer'
```

**File: `frontend/src/pages/UploadPage.tsx`**

1. **Section Card Integration** (line 1916):
   ```typescript
   audioUrl={result?.audioUrl}
   ```
   - Passes audio URL to SectionCard, which passes to SectionAudioPlayer

### Dependencies

- No new external dependencies
- Requires all dependencies from commit 2 (Audjust integration)
- Frontend requires audio URL to be available in song result

### Integration Notes

- **Label Clustering**: The `similarity_threshold=50` is a tunable parameter - may need adjustment based on real-world Audjust label distributions
- **Section Merging**: The merging logic assumes sections are sorted chronologically - ensure this is maintained
- **Logging**: The new logging is at INFO level for key decision points - ensure log level configuration allows these through
- **Audio Player**: Requires `result.audioUrl` to be a valid, playable audio URL (typically presigned S3 URL)
- **Heuristic Tuning**: The threshold changes (intro 0.15, outro 0.85, bridge 0.35-0.75) are based on empirical testing - may need further refinement

---

## Cross-Commit Dependencies

### Dependency Graph

```
Commit 1 (Retry Logic)
  └─ Independent (no dependencies on other commits)

Commit 2 (Audjust API)
  └─ Independent (no dependencies on other commits)
  └─ Creates foundation for Commit 3

Commit 3 (Section Label Logic)
  └─ Depends on Commit 2 (extends section_inference.py)
  └─ Depends on Commit 2 (uses audjust_client.py)
  └─ Depends on Commit 2 (extends SongSection schema)
```

### Shared Components

1. **`SongSection` Schema**: Extended in commit 2, used by commit 3
2. **`section_inference.py`**: Created in commit 2, significantly enhanced in commit 3
3. **`audjust_client.py`**: Created in commit 2, logging cleaned up in commit 3
4. **Frontend `SongSection` Type**: Extended in commit 2, used by commit 3 UI components

### Integration Order

If integrating into a refactored branch, the recommended order is:

1. **Commit 1** can be integrated independently at any time
2. **Commit 2** must be integrated before Commit 3
3. **Commit 3** requires all of Commit 2's changes

However, all three commits are on `main` and work together, so if integrating all at once, order doesn't matter.

---

## Integration Considerations

### Critical Dependencies to Preserve

1. **Database Schema**:
   - `SongClip` model must have: `status`, `error`, `video_url`, `rq_job_id`, `duration_sec`, `num_frames`, `fps`
   - No schema migrations in these commits, but assumes existing clip structure

2. **Service Dependencies**:
   - `session_scope()` context manager (from `app.core.database`)
   - `get_settings()` function (from `app.core.config`)
   - Redis/RQ infrastructure for job queues
   - S3 storage functions (for audio upload in Audjust flow)

3. **Analysis Pipeline**:
   - `_detect_sections()` function must exist (fallback)
   - `_execute_analysis_pipeline()` function structure
   - `get_latest_analysis()` function
   - Librosa for audio analysis

4. **Frontend Dependencies**:
   - `apiClient` with `post()` method
   - `fetchClipSummary()` function
   - `result.audioUrl` must be available
   - Section data structure in song analysis response

### Potential Integration Issues

1. **Queue Name Change** (Commit 1):
   - If worker configuration hardcodes queue name, it must be updated
   - Queue name is now `f"{settings.rq_worker_queue}:clip-generation"`
   - Check worker startup code and RQ configuration

2. **Error Handling Changes** (Commit 1):
   - `get_clip_generation_summary()` now raises `ValueError` instead of returning empty dict
   - Any code calling this function must handle the exception
   - API endpoint wraps it in try/except, but direct service calls need updating

3. **Optional Schema Fields** (Commits 2 & 3):
   - New `SongSection` fields are optional, so backward compatible
   - But if refactoring changed schema structure, may need adapter layer
   - Frontend handles missing fields gracefully

4. **Audjust Integration Points** (Commits 2 & 3):
   - Integration happens in `_execute_analysis_pipeline()` function
   - If this function was refactored, need to find equivalent insertion point
   - Look for where `_detect_sections()` is called - that's where Audjust logic should go

5. **New Service Modules** (Commits 2 & 3):
   - `audjust_client.py` and `section_inference.py` are new files
   - If services were reorganized, these may need to move
   - Check import paths in `song_analysis.py`

6. **Frontend Component Structure** (Commit 3):
   - `SectionAudioPlayer` is new component in `components/vibecraft/`
   - If component structure changed, may need to adjust path
   - Component is exported from `components/vibecraft/index.ts`

### Testing Considerations

1. **Commit 1 Tests**:
   - `test_retry_clip_generation_resets_state()` - tests service function
   - `test_retry_clip_generation_endpoint()` - tests HTTP endpoint
   - Both use `DummyQueue` mock - ensure this still works with refactored queue system

2. **Commit 2 & 3**:
   - No new unit tests in these commits
   - Relies on integration testing with actual Audjust API (or mocks)
   - Fallback behavior should be tested (when Audjust not configured)

### Configuration Requirements

1. **Environment Variables** (Commit 2):
   ```
   AUDJUST_BASE_URL=https://api.audjust.com
   AUDJUST_API_KEY=your_key_here
   AUDJUST_UPLOAD_PATH=/upload (optional, has default)
   AUDJUST_STRUCTURE_PATH=/structure (optional, has default)
   AUDJUST_TIMEOUT_SEC=30.0 (optional, has default)
   ```

2. **Existing Config** (Commit 1):
   - `redis_url` - for RQ queue
   - `rq_worker_queue` - base queue name (now used with suffix)
   - S3 configuration - for audio storage

### Migration Strategy

If integrating into a significantly refactored branch:

1. **Start with Commit 1** (isolated, easier to integrate)
   - Identify where clip generation routes are defined
   - Find `get_clip_generation_summary()` function
   - Locate queue creation code
   - Add retry endpoint and service function

2. **Then Commit 2** (foundation for Commit 3)
   - Add configuration fields to settings
   - Create `audjust_client.py` in appropriate services location
   - Create `section_inference.py` in appropriate services location
   - Find analysis pipeline entry point, add Audjust integration
   - Update `SongSection` schema (backend and frontend)
   - Add documentation files

3. **Finally Commit 3** (enhancements)
   - Update `section_inference.py` with clustering and merging
   - Clean up logging in `audjust_client.py`
   - Add `SectionAudioPlayer` component
   - Integrate audio player into section cards
   - Update frontend section display logic

### Code Locations Reference

**Backend:**
- `backend/app/api/v1/routes_songs.py` - API endpoints
- `backend/app/services/clip_generation.py` - Clip generation service
- `backend/app/services/audjust_client.py` - Audjust API client (new)
- `backend/app/services/section_inference.py` - Section type inference (new)
- `backend/app/services/song_analysis.py` - Analysis pipeline integration
- `backend/app/core/config.py` - Configuration
- `backend/app/schemas/analysis.py` - SongSection schema

**Frontend:**
- `frontend/src/pages/UploadPage.tsx` - Main upload/analysis page
- `frontend/src/components/vibecraft/SectionCard.tsx` - Section display card
- `frontend/src/components/vibecraft/SectionAudioPlayer.tsx` - Audio player (new)
- `frontend/src/types/song.ts` - TypeScript types
- `frontend/src/lib/apiClient.ts` - API client

**Documentation:**
- `docs/ENVIRONMENT_SETUP.md` - Audjust configuration guide
- `docs/song_sections/audjust_api.md` - Audjust API documentation
- `docs/song_sections/infer_section_type.md` - Inference algorithm guide

---

## Summary

These three commits add significant functionality:

1. **User-facing**: Retry failed clips, better section detection, section audio preview
2. **Infrastructure**: External API integration with graceful fallback
3. **Algorithm**: Sophisticated section type inference with clustering and merging
4. **UX**: Enhanced section display with audio playback

All changes are designed to be backward compatible (except the queue name change in Commit 1, which requires worker config update). The Audjust integration is completely opt-in via configuration.

When integrating into a refactored branch, pay special attention to:
- Service module locations (may have moved)
- Analysis pipeline structure (may have changed)
- Queue configuration (must match worker setup)
- Schema compatibility (optional fields help, but structure must match)

---

## Appendix: Complete Code Copy-Pastes

This appendix contains complete, copy-paste ready code for all key changes across the three commits.

### Commit 1: Retry Logic Code

#### Backend: Queue Name Change

**File: `backend/app/services/clip_generation.py`**

```python
def _get_clip_queue() -> Queue:
    settings = get_settings()
    connection = redis.from_url(settings.redis_url)
    queue_name = f"{settings.rq_worker_queue}:clip-generation"
    return Queue(queue_name, connection=connection, default_timeout=QUEUE_TIMEOUT_SEC)
```

#### Backend: Retry Service Function

**File: `backend/app/services/clip_generation.py`**

```python
def retry_clip_generation(clip_id: UUID) -> SongClipStatus:
    """Reset clip state and enqueue a new generation job."""
    queue = _get_clip_queue()

    with session_scope() as session:
        clip = session.get(SongClip, clip_id)
        if not clip:
            raise ValueError(f"Clip {clip_id} not found")

        if clip.status in {"processing", "queued"}:
            raise RuntimeError("Clip is already queued or processing")

        song_id = clip.song_id
        clip_index = clip.clip_index
        clip_fps = clip.fps or 8
        num_frames = clip.num_frames
        if num_frames <= 0 and clip.duration_sec:
            num_frames = max(int(round(clip.duration_sec * clip_fps)), 1)

        clip.num_frames = num_frames
        clip.status = "queued"
        clip.error = None
        clip.video_url = None
        clip.replicate_job_id = None
        clip.rq_job_id = None
        session.add(clip)
        session.commit()

    job = queue.enqueue(
        run_clip_generation_job,
        clip_id,
        job_timeout=QUEUE_TIMEOUT_SEC,
        meta={"song_id": str(song_id), "clip_index": clip_index, "retry": True},
    )

    with session_scope() as session:
        clip = session.get(SongClip, clip_id)
        if not clip:
            raise ValueError(f"Clip {clip_id} disappeared after enqueue")
        clip.rq_job_id = job.id
        session.add(clip)
        session.commit()
        return SongClipStatus.model_validate(clip)
```

#### Backend: Summary Function Error Handling Change

**File: `backend/app/services/clip_generation.py`**

```python
def get_clip_generation_summary(song_id: UUID) -> ClipGenerationSummary:
    # ... existing code to fetch clips ...
    
    if not clips:
        raise ValueError("No planned clips found for song.")

    # ... rest of function ...
```

#### Backend: Retry API Endpoint

**File: `backend/app/api/v1/routes_songs.py`**

```python
@router.post(
    "/{song_id}/clips/{clip_id}/retry",
    response_model=SongClipStatus,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Retry generation for a single clip",
)
def retry_clip_generation_route(
    song_id: UUID,
    clip_id: UUID,
    db: Session = Depends(get_db),
) -> SongClipStatus:
    clip = db.get(SongClip, clip_id)
    if not clip or clip.song_id != song_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clip not found for song")

    if clip.status in {"processing", "queued"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Clip is already queued or processing.",
        )

    try:
        refreshed = retry_clip_generation(clip_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    return refreshed
```

#### Backend: Enhanced Error Logging in Upload Endpoint

**File: `backend/app/api/v1/routes_songs.py`**

```python
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Failed to upload audio assets to storage (bucket=%s, song_id=%s, filename=%s)",
            settings.s3_bucket_name,
            song.id,
            sanitized_filename,
        )
        db.delete(song)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to store audio file. Verify storage configuration and try again.",
        ) from exc
```

```python
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Failed to generate presigned URL for uploaded audio (bucket=%s, key=%s)",
            settings.s3_bucket_name,
            original_s3_key,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate access URL for uploaded audio. Verify storage configuration.",
        ) from exc
```

#### Backend: Summary Endpoint Error Handling

**File: `backend/app/api/v1/routes_songs.py`**

```python
def get_clip_generation_status(song_id: UUID, db: Session = Depends(get_db)) -> ClipGenerationSummary:
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    try:
        return get_clip_generation_summary(song_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No clip plans found for this song.",
        ) from exc
```

#### Backend: Service Exports

**File: `backend/app/services/__init__.py`**

```python
from app.services.clip_generation import (
    enqueue_clip_generation_batch,
    get_clip_generation_job_status,
    get_clip_generation_summary,
    retry_clip_generation,  # ADD THIS
    run_clip_generation_job,
    start_clip_generation_job,
)

__all__ = [
    # ... other exports ...
    "retry_clip_generation",  # ADD THIS
    # ... rest of exports ...
]
```

#### Frontend: Retry Handler

**File: `frontend/src/pages/UploadPage.tsx`**

```typescript
const handleRetryClip = useCallback(
  async (clip: SongClipStatus) => {
    if (!result?.songId) return
    try {
      setClipJobError(null)
      setClipJobStatus('queued')
      setClipJobProgress(0)
      setClipJobId(null)
      await apiClient.post<SongClipStatus>(
        `/songs/${result.songId}/clips/${clip.id}/retry`,
      )
      await fetchClipSummary(result.songId)
    } catch (err) {
      setClipJobError(extractErrorMessage(err, 'Unable to retry clip generation.'))
    }
  },
  [result?.songId, fetchClipSummary],
)
```

---

### Commit 2: Audjust API Integration Code

#### Backend: Configuration Fields

**File: `backend/app/core/config.py`**

```python
    audjust_base_url: Optional[AnyUrl] = Field(default=None, alias="AUDJUST_BASE_URL")
    audjust_api_key: Optional[str] = Field(default=None, alias="AUDJUST_API_KEY")
    audjust_upload_path: str = Field(default="/upload", alias="AUDJUST_UPLOAD_PATH")
    audjust_structure_path: str = Field(default="/structure", alias="AUDJUST_STRUCTURE_PATH")
    audjust_timeout_sec: float = Field(default=30.0, alias="AUDJUST_TIMEOUT_SEC")
```

#### Backend: Schema Extension

**File: `backend/app/schemas/analysis.py`**

```python
class SongSection(BaseModel):
    """Represents a structural section of a song."""

    id: str
    type: SongSectionType
    type_soft: Optional[str] = Field(None, alias="typeSoft")
    display_name: Optional[str] = Field(None, alias="displayName")
    raw_label: Optional[int] = Field(None, alias="rawLabel")
    start_sec: float = Field(..., alias="startSec")
    end_sec: float = Field(..., alias="endSec")
    confidence: float
    repetition_group: Optional[str] = Field(None, alias="repetitionGroup")

    model_config = {"populate_by_name": True}
```

#### Backend: Complete Audjust Client

**File: `backend/app/services/audjust_client.py`** (NEW FILE)

```python
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AudjustConfigurationError(RuntimeError):
    """Raised when the Audjust client is not properly configured."""


class AudjustRequestError(RuntimeError):
    """Raised when the Audjust API request fails."""


def fetch_structure_segments(audio_path: Path) -> List[Dict[str, Any]]:
    """
    Upload an audio file to the Audjust structure endpoint and return the sections payload.

    Returns:
        List of dictionaries with keys like {"startMs": int, "endMs": int, "label": int}

    Raises:
        AudjustConfigurationError: If required settings are missing.
        AudjustRequestError: If the request fails or the payload is unexpected.
    """

    logger.debug("fetch_structure_segments called with audio_path=%s", audio_path)

    settings = get_settings()
    if not settings.audjust_base_url or not settings.audjust_api_key:
        raise AudjustConfigurationError("Audjust API credentials are not configured.")

    base_url = str(settings.audjust_base_url).rstrip("/")

    def _build_url(path: str | None, default: str) -> str:
        target = (path or default).strip()
        if not target.startswith("/"):
            target = f"/{target}"
        return f"{base_url}{target}"

    upload_url = _build_url(settings.audjust_upload_path, "/upload")
    structure_url = _build_url(settings.audjust_structure_path, "/structure")

    headers = {"X-API-Key": settings.audjust_api_key}
    timeout = settings.audjust_timeout_sec or 30.0

    try:
        upload_resp = httpx.get(upload_url, headers=headers, timeout=timeout)
        upload_resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise AudjustRequestError(f"Failed to obtain Audjust upload URL: {exc}") from exc

    upload_payload = upload_resp.json()
    storage_url = upload_payload.get("storageUrl")
    retrieval_url = upload_payload.get("retrievalUrl")
    if not storage_url or not retrieval_url:
        raise AudjustRequestError("Audjust upload endpoint did not return storage/retrieval URLs.")

    logger.debug(
        "Audjust upload URL acquired (storage_url=%s, retrieval_url=%s)",
        storage_url,
        retrieval_url,
    )

    try:
        with audio_path.open("rb") as fh:
            file_bytes = fh.read()
        put_resp = httpx.put(
            storage_url,
            content=file_bytes,
            timeout=timeout,
        )
        put_resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise AudjustRequestError(f"Failed to upload audio to Audjust storage: {exc}") from exc

    logger.debug("Audjust storage upload succeeded")

    payload = {
        "sourceFileUrl": retrieval_url,
    }
    
    try:
        response = httpx.post(
            structure_url,
            headers={**headers, "Content-Type": "application/json"},
            json=payload,
            timeout=timeout,
        )
    except httpx.HTTPError as exc:
        raise AudjustRequestError(f"Failed to call Audjust structure endpoint: {exc}") from exc

    if response.status_code >= 400:
        logger.error(
            "Audjust API returned error %s: %s",
            response.status_code,
            response.text[:500],
        )
        raise AudjustRequestError(
            f"Audjust API request failed with status {response.status_code}"
        )

    logger.debug(
        "Audjust API response status=%s length=%s body_preview=%s",
        response.status_code,
        len(response.text),
        response.text[:750],
    )

    try:
        structure_payload = response.json()
    except ValueError as exc:  # noqa: B902
        raise AudjustRequestError("Audjust API response was not valid JSON") from exc

    sections = None
    if isinstance(structure_payload, dict):
        if isinstance(structure_payload.get("sections"), list):
            sections = structure_payload["sections"]
        elif isinstance(structure_payload.get("result"), dict) and isinstance(
            structure_payload["result"].get("sections"), list
        ):
            sections = structure_payload["result"]["sections"]

    if not sections:
        raise AudjustRequestError("Audjust API response did not include sections.")

    logger.info(
        "Audjust returned %d sections (status=%s)",
        len(sections),
        response.status_code,
    )

    return sections
```

#### Backend: Complete Section Inference Module (Initial Version)

**File: `backend/app/services/section_inference.py`** (NEW FILE - Initial version from Commit 2)

Note: This is the initial version. Commit 3 adds clustering and merging. See next section for final version.

```python
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional


SectionSoftType = Literal[
    "intro_like",
    "verse_like",
    "chorus_like",
    "bridge_like",
    "outro_like",
    "other",
]


@dataclass(slots=True)
class SectionInference:
    id: str
    index: int
    start_sec: float
    end_sec: float
    duration_sec: float
    label_raw: int
    type_soft: SectionSoftType
    confidence: float
    display_name: str


def _normalize(values: Iterable[float]) -> List[float]:
    values = list(values)
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if abs(vmin - vmax) < 1e-9:
        return [0.5 for _ in values]
    return [(value - vmin) / (vmax - vmin) for value in values]


def infer_section_types(
    audjust_sections: List[dict],
    energy_per_section: List[float],
    vocals_per_section: Optional[List[float]] = None,
) -> List[SectionInference]:
    """
    Infer soft section types from Audjust segments and per-segment features.

    Args:
        audjust_sections: List of dicts with at least startMs, endMs, label.
        energy_per_section: Average energy value per section, aligned with audjust_sections.
        vocals_per_section: Optional vocal activity metrics per section.
    """

    n = len(audjust_sections)
    if n == 0:
        return []

    if len(energy_per_section) != n:
        raise ValueError("energy_per_section length must match audjust_sections length")
    if vocals_per_section is not None and len(vocals_per_section) != n:
        raise ValueError("vocals_per_section length must match audjust_sections length")

    # Step 1: Basic section payload
    sections_raw: List[dict] = []
    total_duration_sec = 0.0
    for i, section in enumerate(audjust_sections):
        start_ms = float(section.get("startMs", 0))
        end_ms = float(section.get("endMs", start_ms))
        label = int(section.get("label", -1))
        start_sec = max(0.0, start_ms / 1000.0)
        end_sec = max(start_sec, end_ms / 1000.0)
        duration_sec = max(0.0, end_sec - start_sec)
        total_duration_sec = max(total_duration_sec, end_sec)
        sections_raw.append(
            {
                "index": i,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": duration_sec,
                "label": label,
                "energy": float(energy_per_section[i]),
                "vocals": (
                    float(vocals_per_section[i]) if vocals_per_section is not None else None
                ),
            }
        )

    if total_duration_sec <= 0:
        total_duration_sec = sum(section["duration_sec"] for section in sections_raw)

    # Step 2: stats per label
    by_label: Dict[int, List[dict]] = defaultdict(list)
    for seg in sections_raw:
        by_label[seg["label"]].append(seg)

    label_stats = []
    for label, slices in by_label.items():
        occ = len(slices)
        total_dur = sum(s["duration_sec"] for s in slices)
        mean_energy = (
            sum(s["energy"] for s in slices) / occ if occ else 0.0
        )
        first_start = min(s["start_sec"] for s in slices)
        label_stats.append(
            {
                "label": label,
                "occ": occ,
                "total_dur": total_dur,
                "mean_energy": mean_energy,
                "first_start": first_start,
            }
        )

    # Step 3: chorus label heuristics
    chorus_label = None
    chorus_candidates = [stat for stat in label_stats if stat["occ"] >= 2]
    if chorus_candidates:
        occ_norm = _normalize(stat["occ"] for stat in chorus_candidates)
        dur_norm = _normalize(stat["total_dur"] for stat in chorus_candidates)
        energy_norm = _normalize(stat["mean_energy"] for stat in chorus_candidates)

        best_score = -1.0
        best_label = None
        for idx, stat in enumerate(chorus_candidates):
            early_penalty = 0.3 if stat["first_start"] < 10.0 else 0.0
            score = (
                0.5 * occ_norm[idx]
                + 0.2 * dur_norm[idx]
                + 0.3 * energy_norm[idx]
                - early_penalty
            )
            if score > best_score:
                best_score = score
                best_label = stat["label"]

        if best_score > 0.2:
            chorus_label = best_label

    # Step 4: verse-like label set
    verse_labels = {
        stat["label"]
        for stat in label_stats
        if stat["label"] != chorus_label and stat["occ"] >= 2
    }

    # Step 5: section typing
    inferred_sections: List[SectionInference] = []
    for segment in sections_raw:
        idx = segment["index"]
        label = segment["label"]
        center = (segment["start_sec"] + segment["end_sec"]) / 2.0
        pos_ratio = center / max(total_duration_sec, 1e-6)
        base_type: SectionSoftType = "other"
        conf = 0.45

        if chorus_label is not None and label == chorus_label:
            base_type = "chorus_like"
            conf = 0.7
        elif label in verse_labels:
            base_type = "verse_like"
            conf = 0.6
        elif pos_ratio < 0.2:
            base_type = "intro_like"
            conf = 0.6
        elif pos_ratio > 0.8:
            base_type = "outro_like"
            conf = 0.6
        elif 0.3 < pos_ratio < 0.8 and next(
            stat["occ"] for stat in label_stats if stat["label"] == label
        ) == 1:
            base_type = "bridge_like"
            conf = 0.55

        inferred_sections.append(
            SectionInference(
                id=f"sec-{idx}",
                index=idx,
                start_sec=segment["start_sec"],
                end_sec=segment["end_sec"],
                duration_sec=segment["duration_sec"],
                label_raw=label,
                type_soft=base_type,
                confidence=conf,
                display_name="",  # filled later
            )
        )

    # Step 6: assign display names
    counters: Dict[SectionSoftType, int] = Counter()
    for section in inferred_sections:
        counters[section.type_soft] += 1
        ordinal = counters[section.type_soft]
        if section.type_soft == "chorus_like":
            section.display_name = f"Chorus {ordinal}"
        elif section.type_soft == "verse_like":
            section.display_name = f"Verse {ordinal}"
        elif section.type_soft == "intro_like":
            section.display_name = "Intro" if ordinal == 1 else f"Intro {ordinal}"
        elif section.type_soft == "outro_like":
            section.display_name = "Outro" if ordinal == 1 else f"Outro {ordinal}"
        elif section.type_soft == "bridge_like":
            section.display_name = "Bridge" if ordinal == 1 else f"Bridge {ordinal}"
        else:
            section.display_name = f"Section {chr(ord('A') + section.index)}"

    inferred_sections.sort(key=lambda s: s.start_sec)
    return inferred_sections
```

#### Backend: Song Analysis Integration

**File: `backend/app/services/song_analysis.py`**

Add imports at top:
```python
from app.services.audjust_client import (
    AudjustConfigurationError,
    AudjustRequestError,
    fetch_structure_segments,
)
from app.services.section_inference import infer_section_types
```

Replace section detection code in `_execute_analysis_pipeline()`:
```python
        sections: List[SongSection]
        audjust_sections_raw: Optional[List[dict]] = None

        if settings.audjust_base_url and settings.audjust_api_key:
            try:
                audjust_sections_raw = fetch_structure_segments(audio_path)
                logger.info(
                    "Fetched %d sections from Audjust for song %s",
                    len(audjust_sections_raw),
                    song_id,
                )
            except AudjustConfigurationError as exc:
                logger.warning("Audjust configuration invalid: %s", exc)
            except AudjustRequestError as exc:
                logger.warning(
                    "Audjust section request failed for song %s: %s. Falling back to internal segmentation.",
                    song_id,
                    exc,
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Unexpected error while calling Audjust for song %s: %s",
                    song_id,
                    exc,
                )

        if audjust_sections_raw:
            try:
                energy_per_section = _compute_section_energy(
                    y, sr, audjust_sections_raw
                )
                inferred_sections = infer_section_types(
                    audjust_sections=audjust_sections_raw,
                    energy_per_section=energy_per_section,
                )
                if inferred_sections:
                    sections = _build_song_sections_from_inference(inferred_sections)
                else:
                    logger.warning(
                        "Audjust returned no usable sections for song %s. Falling back to internal segmentation.",
                        song_id,
                    )
                    sections = _detect_sections(y, sr, duration)
            except Exception as exc:  # noqa: BLE001
                logger.exception(
                    "Failed to build sections from Audjust response for song %s: %s. Falling back to internal segmentation.",
                    song_id,
                    exc,
                )
                sections = _detect_sections(y, sr, duration)
        else:
            sections = _detect_sections(y, sr, duration)
```

Add helper functions:
```python
def _compute_section_energy(
    y: np.ndarray,
    sr: int,
    audjust_sections: list[dict],
    *,
    frame_length: int = 2048,
    hop_length: int = 512,
) -> list[float]:
    rms = librosa.feature.rms(
        y=y, frame_length=frame_length, hop_length=hop_length, center=True
    )[0]
    times = librosa.frames_to_time(
        np.arange(len(rms)), sr=sr, hop_length=hop_length, n_fft=frame_length
    )
    global_mean = float(np.mean(rms)) if len(rms) else 0.0

    energies: list[float] = []
    for section in audjust_sections:
        start = float(section.get("startMs", 0)) / 1000.0
        end = float(section.get("endMs", start)) / 1000.0
        if end <= start:
            energies.append(global_mean)
            continue
        mask = (times >= start) & (times < end)
        segment_rms = rms[mask]
        if segment_rms.size == 0:
            energies.append(global_mean)
        else:
            energies.append(float(segment_rms.mean()))
    return energies


def _build_song_sections_from_inference(
    inferred_sections,
) -> list[SongSection]:
    type_map = {
        "intro_like": "intro",
        "verse_like": "verse",
        "chorus_like": "chorus",
        "bridge_like": "bridge",
        "outro_like": "outro",
        "other": "other",
    }

    sections: list[SongSection] = []
    for entry in inferred_sections:
        type_value = type_map.get(entry.type_soft, "other")
        repetition_group = (
            f"label-{entry.label_raw}" if entry.label_raw is not None else None
        )
        sections.append(
            SongSection(
                id=entry.id,
                type=type_value,  # type: ignore[arg-type]
                type_soft=entry.type_soft,
                display_name=entry.display_name,
                raw_label=entry.label_raw,
                start_sec=round(entry.start_sec, 3),
                end_sec=round(entry.end_sec, 3),
                confidence=round(entry.confidence, 3),
                repetition_group=repetition_group,
            )
        )

    return sections
```

#### Frontend: Type Extensions

**File: `frontend/src/types/song.ts`**

```typescript
export interface SongSection {
  id: string
  type: SongSectionType
  typeSoft?: string | null
  displayName?: string | null
  rawLabel?: number | null
  startSec: number
  endSec: number
  confidence: number
  repetitionGroup?: string | null
}
```

#### Frontend: Enhanced Section Display Logic

**File: `frontend/src/pages/UploadPage.tsx`**

```typescript
const buildSectionsWithDisplayNames = (
  sections: SongSection[],
): Array<
  SongSection & {
    displayName: string
    typeSoft: string | null
    rawLabel: number | null
  }
> => {
  const counts: Record<string, number> = {}
  return sections.map((section) => {
    const baseType = section.typeSoft ?? section.type

    const label =
      (section.displayName && section.displayName.split(' ')[0]) ??
      SECTION_TYPE_LABELS[section.type] ??
      'Section'

    const key = baseType ?? section.type
    const nextCount = (counts[key] ?? 0) + 1
    counts[key] = nextCount

    const displayName =
      section.displayName ??
      (key === 'intro_like' || key === 'intro'
        ? 'Intro'
        : key === 'outro_like' || key === 'outro'
          ? 'Outro'
          : key === 'bridge_like' || key === 'bridge'
            ? 'Bridge'
            : `${label} ${nextCount}`)

    return {
      ...section,
      typeSoft: section.typeSoft ?? null,
      rawLabel: section.rawLabel ?? null,
      displayName,
    }
  })
}
```

---

### Commit 3: Section Label Logic Enhancements

#### Backend: Complete Section Inference Module (Final Version)

**File: `backend/app/services/section_inference.py`** (FINAL VERSION with clustering and merging)

This is the complete file with all enhancements from Commit 3:

```python
from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Optional

logger = logging.getLogger(__name__)


SectionSoftType = Literal[
    "intro_like",
    "verse_like",
    "chorus_like",
    "bridge_like",
    "outro_like",
    "other",
]


@dataclass(slots=True)
class SectionInference:
    id: str
    index: int
    start_sec: float
    end_sec: float
    duration_sec: float
    label_raw: int
    type_soft: SectionSoftType
    confidence: float
    display_name: str


def _normalize(values: Iterable[float]) -> List[float]:
    values = list(values)
    if not values:
        return []
    vmin = min(values)
    vmax = max(values)
    if abs(vmin - vmax) < 1e-9:
        return [0.5 for _ in values]
    return [(value - vmin) / (vmax - vmin) for value in values]


def _merge_consecutive_sections(sections: List[SectionInference]) -> List[SectionInference]:
    """
    Merge consecutive sections that have the same type_soft.
    
    For example: [Intro, Intro 2] -> [Intro]
                [Chorus 2, Chorus 3] -> [Chorus 2]
    
    Args:
        sections: List of SectionInference objects, assumed to be sorted by start_sec
    
    Returns:
        New list with consecutive same-type sections merged
    """
    if len(sections) <= 1:
        return sections
    
    merged: List[SectionInference] = []
    current_group: List[SectionInference] = [sections[0]]
    
    for section in sections[1:]:
        # If same type as current group, add to group
        if section.type_soft == current_group[0].type_soft:
            current_group.append(section)
        else:
            # Different type, merge current group and start new one
            merged.append(_merge_section_group(current_group))
            current_group = [section]
    
    # Don't forget the last group
    if current_group:
        merged.append(_merge_section_group(current_group))
    
    # Re-assign display names with correct ordinals
    counters: Dict[SectionSoftType, int] = {}
    for section in merged:
        if section.type_soft not in counters:
            counters[section.type_soft] = 0
        counters[section.type_soft] += 1
        ordinal = counters[section.type_soft]
        
        if section.type_soft == "chorus_like":
            section.display_name = f"Chorus {ordinal}"
        elif section.type_soft == "verse_like":
            section.display_name = f"Verse {ordinal}"
        elif section.type_soft == "intro_like":
            section.display_name = "Intro" if ordinal == 1 else f"Intro {ordinal}"
        elif section.type_soft == "outro_like":
            section.display_name = "Outro" if ordinal == 1 else f"Outro {ordinal}"
        elif section.type_soft == "bridge_like":
            section.display_name = "Bridge" if ordinal == 1 else f"Bridge {ordinal}"
        else:
            letter = chr(ord("A") + section.index)
            section.display_name = f"Section {letter}"
    
    return merged


def _merge_section_group(group: List[SectionInference]) -> SectionInference:
    """
    Merge a group of consecutive sections with the same type into a single section.
    
    Takes the earliest start_sec, latest end_sec, and averages confidence.
    Uses the first section's label_raw and index.
    """
    if len(group) == 1:
        return group[0]
    
    start_sec = min(s.start_sec for s in group)
    end_sec = max(s.end_sec for s in group)
    duration_sec = end_sec - start_sec
    avg_confidence = sum(s.confidence for s in group) / len(group)
    
    return SectionInference(
        id=group[0].id,  # Keep the first section's ID
        index=group[0].index,  # Keep the first section's index
        start_sec=start_sec,
        end_sec=end_sec,
        duration_sec=duration_sec,
        label_raw=group[0].label_raw,  # Keep the first section's raw label
        type_soft=group[0].type_soft,
        confidence=round(avg_confidence, 3),
        display_name=group[0].display_name,  # Will be reassigned later
    )


def _cluster_similar_labels(labels: List[int], similarity_threshold: int) -> Dict[int, int]:
    """
    Cluster labels that are within similarity_threshold distance.
    
    Returns a mapping from original label to cluster representative (lowest label in cluster).
    
    Args:
        labels: List of Audjust label values (0-1000)
        similarity_threshold: Max distance between labels to be considered similar
    
    Returns:
        Dict mapping each label to its cluster representative
    """
    unique_labels = sorted(set(labels))
    if not unique_labels:
        return {}
    
    # Group labels into clusters using a simple greedy approach
    clusters: Dict[int, int] = {}  # label -> cluster_representative
    
    for label in unique_labels:
        # Check if this label is close to any existing cluster representative
        assigned = False
        for cluster_rep in sorted(set(clusters.values())):
            if abs(label - cluster_rep) <= similarity_threshold:
                clusters[label] = cluster_rep
                assigned = True
                break
        
        # If not close to any existing cluster, create a new cluster
        if not assigned:
            clusters[label] = label
    
    return clusters


def infer_section_types(
    audjust_sections: List[dict],
    energy_per_section: List[float],
    vocals_per_section: Optional[List[float]] = None,
) -> List[SectionInference]:
    """
    Infer soft section types (intro/verse/chorus/bridge/outro/other) from:
      - Audjust structure segments: [{'startMs', 'endMs', 'label'}, ...]
      - Per-section average energy (e.g. RMS)
      - Optional per-section vocal activity (0.0–1.0)

    Returns a list of SectionInference objects with type_soft + display_name.

    Args:
        audjust_sections: List of dicts with at least startMs, endMs, label.
        energy_per_section: Average energy value per section, aligned with audjust_sections.
        vocals_per_section: Optional vocal activity metrics per section.

    Returns:
        List of SectionInference objects with inferred section types.
    """

    n = len(audjust_sections)
    if n == 0:
        return []

    if len(energy_per_section) != n:
        raise ValueError("energy_per_section length must match audjust_sections length")
    if vocals_per_section is not None and len(vocals_per_section) != n:
        raise ValueError("vocals_per_section length must match audjust_sections length")

    # Step 1: construct basic sections with durations & positions
    sections_raw: List[dict] = []
    total_duration_sec = 0.0
    for i, section in enumerate(audjust_sections):
        start_ms = float(section.get("startMs", 0))
        end_ms = float(section.get("endMs", start_ms))
        label = int(section.get("label", -1))
        start_sec = max(0.0, start_ms / 1000.0)
        end_sec = max(start_sec, end_ms / 1000.0)
        duration_sec = max(0.0, end_sec - start_sec)
        total_duration_sec = max(total_duration_sec, end_sec)
        sections_raw.append(
            {
                "index": i,
                "start_sec": start_sec,
                "end_sec": end_sec,
                "duration_sec": duration_sec,
                "label": label,
                "energy": float(energy_per_section[i]),
                "vocals": (
                    float(vocals_per_section[i]) if vocals_per_section is not None else None
                ),
            }
        )

    if total_duration_sec <= 0:
        total_duration_sec = sum(section["duration_sec"] for section in sections_raw)

    # Log raw sections from Audjust
    logger.info("Raw Audjust sections (%d total, %.1fs duration):", len(sections_raw), total_duration_sec)
    for seg in sections_raw:
        logger.info(
            "  %.1fs-%.1fs (%.1fs) | label=%d | energy=%.3f",
            seg["start_sec"],
            seg["end_sec"],
            seg["duration_sec"],
            seg["label"],
            seg["energy"],
        )

    # Step 2: cluster similar labels together
    # Audjust labels are 0-1000, closer numbers = more similar sections
    # We'll group labels within a threshold distance into the same cluster
    label_clusters = _cluster_similar_labels(
        [s["label"] for s in sections_raw],
        similarity_threshold=50,  # labels within 50 points are considered similar
    )
    
    # Map each section to its cluster representative
    for section in sections_raw:
        section["cluster_label"] = label_clusters[section["label"]]
    
    logger.info(
        "Label clustering: %d unique labels → %d clusters. Mapping: %s",
        len(set(s["label"] for s in sections_raw)),
        len(set(label_clusters.values())),
        {k: v for k, v in label_clusters.items() if k != v},  # show non-trivial mappings
    )

    # Step 3: group by cluster label and compute stats
    by_cluster: Dict[int, List[dict]] = defaultdict(list)
    for seg in sections_raw:
        by_cluster[seg["cluster_label"]].append(seg)

    cluster_stats = []
    for cluster_label, segs in by_cluster.items():
        occ = len(segs)
        total_dur = sum(s["duration_sec"] for s in segs)
        mean_energy = sum(s["energy"] for s in segs) / occ if occ else 0.0
        first_start = min(s["start_sec"] for s in segs)
        cluster_stats.append(
            {
                "label": cluster_label,
                "occ": occ,
                "total_dur": total_dur,
                "mean_energy": mean_energy,
                "first_start": first_start,
            }
        )

    # Log cluster statistics for debugging
    logger.info(
        "Cluster statistics: %d unique clusters, repetitions: %s",
        len(cluster_stats),
        {stat["label"]: stat["occ"] for stat in cluster_stats},
    )

    # Step 4: find chorus candidate (most repeated & energetic)
    # Only consider clusters that occur at least twice
    chorus_candidates = [stat for stat in cluster_stats if stat["occ"] >= 2]

    chorus_cluster = None
    if chorus_candidates:
        occ_norm = _normalize(stat["occ"] for stat in chorus_candidates)
        dur_norm = _normalize(stat["total_dur"] for stat in chorus_candidates)
        energy_norm = _normalize(stat["mean_energy"] for stat in chorus_candidates)

        best_score = -1.0
        best_cluster = None
        for idx, stat in enumerate(chorus_candidates):
            # Penalize sections whose first start is extremely early (< 8s)
            # but make it less aggressive
            early_penalty = 0.0
            if stat["first_start"] < 8.0:
                early_penalty = 0.2

            score = (
                0.5 * occ_norm[idx] +
                0.2 * dur_norm[idx] +
                0.3 * energy_norm[idx] -
                early_penalty
            )
            if score > best_score:
                best_score = score
                best_cluster = stat["label"]

        # Only accept if the score is reasonably high and occ >= 2
        # Lowered threshold from 0.2 to 0.15 to be more permissive
        if best_score > 0.15:
            chorus_cluster = best_cluster
            logger.info(
                "Detected chorus: cluster=%s, score=%.2f, occurrences=%d",
                best_cluster,
                best_score,
                next(s["occ"] for s in cluster_stats if s["label"] == best_cluster),
            )
        else:
            logger.warning(
                "No chorus detected. Best candidate score=%.2f (threshold=0.15), candidates=%d",
                best_score if best_score > -1 else 0.0,
                len(chorus_candidates),
            )
    else:
        logger.warning("No chorus candidates found (no clusters with ≥2 occurrences)")

    # Step 5: find verse-like clusters
    # verse-like: repeated clusters that are not chorus
    verse_clusters = set()
    for stat in cluster_stats:
        if stat["label"] == chorus_cluster:
            continue
        if stat["occ"] >= 2:
            verse_clusters.add(stat["label"])

    if verse_clusters:
        logger.info("Detected verse clusters: %s", verse_clusters)
    else:
        logger.warning("No verse clusters detected (no repeated non-chorus sections)")

    # Step 6: classify each segment with soft type
    inferred_sections: List[SectionInference] = []
    for segment in sections_raw:
        idx = segment["index"]
        label = segment["label"]
        cluster_label = segment["cluster_label"]
        center = (segment["start_sec"] + segment["end_sec"]) / 2.0
        pos_ratio = center / max(1e-6, total_duration_sec)
        base_type: SectionSoftType = "other"
        conf = 0.4  # baseline

        # chorus-like: most repeated & energetic section
        if chorus_cluster is not None and cluster_label == chorus_cluster:
            base_type = "chorus_like"
            conf = 0.7

        # verse-like: repeated sections that are not chorus
        elif cluster_label in verse_clusters:
            base_type = "verse_like"
            conf = 0.6

        # intro-like: early in song & not already classified as chorus/verse
        # Reduced from 0.2 to 0.15 to be more conservative with intro classification
        if base_type == "other" and pos_ratio < 0.15:
            base_type = "intro_like"
            conf = 0.6

        # outro-like: late in song & not already classified as chorus/verse
        # Increased from 0.8 to 0.85 to be more conservative with outro classification
        if base_type == "other" and pos_ratio > 0.85:
            base_type = "outro_like"
            conf = 0.6

        # bridge-like: unique cluster in middle region, not chorus/verse
        # Made the middle region narrower (0.35-0.75 instead of 0.3-0.8)
        # to reduce over-classification of bridges
        if (
            base_type == "other"
            and 0.35 < pos_ratio < 0.75
            and next(stat["occ"] for stat in cluster_stats if stat["label"] == cluster_label) == 1
        ):
            base_type = "bridge_like"
            conf = 0.5

        # if nothing fit, leave as "other" with baseline confidence
        # you could bump confidence using energy/vocals if desired

        inferred_sections.append(
            SectionInference(
                id=f"sec_{idx}",
                index=idx,
                start_sec=segment["start_sec"],
                end_sec=segment["end_sec"],
                duration_sec=segment["duration_sec"],
                label_raw=label,
                type_soft=base_type,
                confidence=conf,
                display_name="",  # filled later
            )
        )

    # Step 7: assign initial display names (Verse 1, Chorus 2, etc.)
    # Note: These will be reassigned after merging consecutive sections
    counters: Dict[SectionSoftType, int] = Counter()
    for section in inferred_sections:
        counters[section.type_soft] += 1
        ordinal = counters[section.type_soft]

        if section.type_soft == "chorus_like":
            section.display_name = f"Chorus {ordinal}"
        elif section.type_soft == "verse_like":
            section.display_name = f"Verse {ordinal}"
        elif section.type_soft == "intro_like":
            section.display_name = "Intro" if ordinal == 1 else f"Intro {ordinal}"
        elif section.type_soft == "outro_like":
            section.display_name = "Outro" if ordinal == 1 else f"Outro {ordinal}"
        elif section.type_soft == "bridge_like":
            section.display_name = "Bridge" if ordinal == 1 else f"Bridge {ordinal}"
        else:
            # fallback for "other": Section A/B/C...
            letter = chr(ord("A") + section.index)
            section.display_name = f"Section {letter}"

    # Sort back in chronological order
    inferred_sections.sort(key=lambda s: s.start_sec)

    # Log summary of inferred sections (before merging)
    type_counts = dict(counters)
    logger.info(
        "Section inference complete (before merging): %d total sections, types: %s",
        len(inferred_sections),
        type_counts,
    )

    # Step 8: Merge consecutive sections of the same type
    merged_sections = _merge_consecutive_sections(inferred_sections)

    # Log merged sections
    logger.info(
        "After merging consecutive sections: %d sections (reduced from %d)",
        len(merged_sections),
        len(inferred_sections),
    )

    # Log detailed section breakdown
    for section in merged_sections:
        logger.info(
            "  [%s] %.1fs-%.1fs (%.1fs) | raw_label=%d | conf=%.2f | %s",
            section.type_soft,
            section.start_sec,
            section.end_sec,
            section.duration_sec,
            section.label_raw,
            section.confidence,
            section.display_name,
        )

    return merged_sections
```

#### Frontend: Complete Section Audio Player Component

**File: `frontend/src/components/vibecraft/SectionAudioPlayer.tsx`** (NEW FILE)

```typescript
import React, { useRef, useEffect, useState } from 'react'
import clsx from 'clsx'

export interface SectionAudioPlayerProps {
  audioUrl: string
  startSec: number
  endSec: number
  className?: string
}

export const SectionAudioPlayer: React.FC<SectionAudioPlayerProps> = ({
  audioUrl,
  startSec,
  endSec,
  className,
}) => {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const intervalRef = useRef<number | null>(null)

  const duration = endSec - startSec

  // Clean up interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
      }
    }
  }, [])

  const handlePlayPause = () => {
    if (!audioRef.current) return

    if (isPlaying) {
      audioRef.current.pause()
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      setIsPlaying(false)
    } else {
      // Set to start time if not already in range
      if (
        audioRef.current.currentTime < startSec ||
        audioRef.current.currentTime >= endSec
      ) {
        audioRef.current.currentTime = startSec
      }

      audioRef.current.play()
      setIsPlaying(true)

      // Monitor playback and stop at end
      intervalRef.current = window.setInterval(() => {
        if (audioRef.current) {
          const time = audioRef.current.currentTime
          setCurrentTime(time - startSec)

          if (time >= endSec) {
            audioRef.current.pause()
            audioRef.current.currentTime = startSec
            setIsPlaying(false)
            setCurrentTime(0)
            if (intervalRef.current !== null) {
              clearInterval(intervalRef.current)
              intervalRef.current = null
            }
          }
        }
      }, 100)
    }
  }

  const handleTimeUpdate = () => {
    if (!audioRef.current || !isPlaying) return
    const time = audioRef.current.currentTime

    // Stop if we've gone past the end
    if (time >= endSec) {
      audioRef.current.pause()
      audioRef.current.currentTime = startSec
      setIsPlaying(false)
      setCurrentTime(0)
      if (intervalRef.current !== null) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }

  const handleEnded = () => {
    setIsPlaying(false)
    setCurrentTime(0)
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  const formatTime = (sec: number) => {
    const minutes = Math.floor(sec / 60)
    const seconds = Math.floor(sec % 60)
      .toString()
      .padStart(2, '0')
    return `${minutes}:${seconds}`
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div className={clsx('flex items-center gap-3', className)}>
      <audio
        ref={audioRef}
        src={audioUrl}
        onTimeUpdate={handleTimeUpdate}
        onEnded={handleEnded}
        preload="metadata"
      />

      <button
        onClick={handlePlayPause}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-vc-accent-primary/20 hover:bg-vc-accent-primary/30 transition-colors"
        aria-label={isPlaying ? 'Pause' : 'Play'}
      >
        {isPlaying ? (
          <svg
            className="h-4 w-4 text-vc-accent-primary"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
          </svg>
        ) : (
          <svg
            className="h-4 w-4 text-vc-accent-primary"
            fill="currentColor"
            viewBox="0 0 24 24"
          >
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </button>

      <div className="flex-1">
        <div className="h-1.5 w-full rounded-full bg-vc-surface-tertiary overflow-hidden">
          <div
            className="h-full bg-vc-accent-primary transition-all duration-100"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <span className="text-xs text-vc-text-secondary tabular-nums">
        {formatTime(currentTime)} / {formatTime(duration)}
      </span>
    </div>
  )
}
```

#### Frontend: Section Card Integration

**File: `frontend/src/components/vibecraft/SectionCard.tsx`**

Add prop to interface:
```typescript
export interface SectionCardProps {
  // ... existing props ...
  audioUrl?: string
  // ... rest of props ...
}
```

Add component usage:
```typescript
{audioUrl && (
  <div className="mt-3">
    <SectionAudioPlayer audioUrl={audioUrl} startSec={startSec} endSec={endSec} />
  </div>
)}
```

#### Frontend: Component Export

**File: `frontend/src/components/vibecraft/index.ts`**

```typescript
export * from './SectionAudioPlayer'
```

#### Frontend: UploadPage Integration

**File: `frontend/src/pages/UploadPage.tsx`**

In the section card rendering:
```typescript
<SectionCard
  // ... other props ...
  audioUrl={result?.audioUrl}
  // ... rest of props ...
/>
```

---

### Summary of All Files Changed

**Backend Files:**
- `backend/app/api/v1/routes_songs.py` - Retry endpoint, error handling
- `backend/app/services/clip_generation.py` - Retry function, queue name, summary error
- `backend/app/services/__init__.py` - Export retry function
- `backend/app/core/config.py` - Audjust configuration
- `backend/app/schemas/analysis.py` - SongSection schema extension
- `backend/app/services/audjust_client.py` - NEW FILE
- `backend/app/services/section_inference.py` - NEW FILE (enhanced in commit 3)
- `backend/app/services/song_analysis.py` - Audjust integration, helper functions

**Frontend Files:**
- `frontend/src/pages/UploadPage.tsx` - Retry handler, section display logic
- `frontend/src/types/song.ts` - SongSection type extension
- `frontend/src/components/vibecraft/SectionAudioPlayer.tsx` - NEW FILE
- `frontend/src/components/vibecraft/SectionCard.tsx` - Audio player integration
- `frontend/src/components/vibecraft/index.ts` - Export audio player

**Documentation Files:**
- `docs/ENVIRONMENT_SETUP.md` - NEW FILE
- `docs/song_sections/audjust_api.md` - NEW FILE
- `docs/song_sections/infer_section_type.md` - NEW FILE

---

This appendix provides complete, copy-paste ready code for all changes. Use this as a reference when integrating into the refactored branch.

