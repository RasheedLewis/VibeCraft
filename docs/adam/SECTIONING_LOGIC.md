# Section Detection Logic - Issues & Improvements

## Current Problems

1. **Tiny sections**: Sections can be fractions of a second (e.g., 0.1s, 0.3s)
2. **Last section gets everything**: Most of the song gets lumped into the final section labeled "outro"
3. **Naive labeling**: Section types are assigned sequentially by index (`template_types[min(idx, len(template_types) - 1)]`), not based on actual musical structure
4. **No minimum duration enforcement**: No post-processing to merge or filter out sections that are too short
5. **Poor boundary detection**: Agglomerative clustering with `k = min(6, max(2, n_frames // 32))` can create too many boundaries early, leaving the rest for the last section

## Current Implementation

**Location:** `backend/app/services/song_analysis.py::_detect_sections()`

**Algorithm:**
1. Extract chroma features from audio
2. Use agglomerative clustering to find `k` boundaries (where `k = min(6, max(2, n_frames // 32))`)
3. Convert frame boundaries to time boundaries
4. Assign section types sequentially: `["intro", "verse", "pre_chorus", "chorus", "bridge", "outro"]`
5. No minimum duration check or post-processing

## Proposed Improvements

### 1. Minimum Section Duration

**Requirement:** Enforce a minimum section duration (e.g., 5-10 seconds)

**Implementation:**
- After boundary detection, merge sections that are below minimum duration
- Merge small sections with adjacent sections (prefer merging with longer adjacent section)
- If a section is too small, merge it with the previous section (unless it's the first, then merge with next)

### 2. Better Boundary Detection

**Issues:**
- Current `k` calculation (`n_frames // 32`) can create too many boundaries for short songs
- No consideration of song structure (e.g., typical verse/chorus patterns)

**Proposed:**
- Use song duration to estimate reasonable number of sections (e.g., 1 section per 15-30 seconds)
- Consider using beat-aligned boundaries as constraints (sections should align with beats)
- Use onset detection to find actual structural changes, not just chroma similarity

### 3. Post-Processing: Merge Small Sections

**Algorithm:**
1. After initial boundary detection, calculate section durations
2. Identify sections below minimum duration threshold
3. Merge small sections with adjacent sections:
   - If first section is too small → merge with next
   - If last section is too small → merge with previous
   - If middle section is too small → merge with shorter adjacent section (to balance sizes)
4. Recalculate boundaries after merging

### 4. Better Section Labeling

**Current:** Sequential assignment by index (completely arbitrary)

**Proposed Approaches:**

**Option A: Duration-based heuristics**
- First section → "intro" (if < 30s) or "verse"
- Longest sections → "chorus" (typically longest and most repetitive)
- Short sections between long ones → "pre_chorus" or "bridge"
- Last section → "outro" (if < 30s and near end) or continue pattern

**Option B: Repetition-based**
- Use existing `repetitionGroup` to identify repeated sections
- Most repeated section type → "chorus"
- Sections before chorus → "verse" or "pre_chorus"
- Unique sections → "bridge" or "solo"

**Option C: Energy/Intensity-based**
- Analyze energy/intensity per section
- High energy sections → "chorus" or "drop"
- Low energy sections → "verse" or "bridge"
- Rising energy → "pre_chorus"

**Option D: Hybrid approach**
- Combine repetition groups + duration + position in song
- Use heuristics to assign most likely labels

### 5. Maximum Section Count

**Requirement:** Limit maximum number of sections to prevent over-segmentation

**Implementation:**
- Cap at reasonable number (e.g., 8-10 sections max for typical song)
- If too many boundaries detected, merge smallest adjacent sections first

### 6. Beat-Aligned Boundaries (Future)

**Consideration:** Use beat-aligned boundaries from MVP-02 as constraints
- Sections should start/end near beats (within tolerance)
- This ensures sections align with musical structure
- Can use beat grid to validate section boundaries

## Recommended Minimum Section Duration

**Suggested:** 8-10 seconds minimum
- Shorter sections are hard to work with for video generation
- Typical song sections (verse, chorus) are usually 15-30+ seconds
- Allows for meaningful visual content per section

**Alternative:** Make it configurable based on song duration
- Short songs (< 60s): 5 seconds minimum
- Medium songs (60-180s): 8 seconds minimum  
- Long songs (> 180s): 10 seconds minimum

## Implementation Priority

1. **High Priority:**
   - Minimum section duration enforcement
   - Post-processing to merge small sections
   - Better `k` calculation for boundary detection

2. **Medium Priority:**
   - Improved section labeling (at least duration + position based)
   - Maximum section count limit

3. **Low Priority (Future):**
   - Beat-aligned section boundaries
   - Energy/intensity-based labeling
   - ML-based section type classification

## Testing Considerations

- Test with songs of different lengths (30s, 60s, 180s, 300s)
- Verify no sections are below minimum duration
- Verify last section isn't disproportionately large
- Verify section labels make sense (at least positionally)
- Test edge cases: very short songs, very long songs, songs with minimal structure

