# Auto-Generated Captions Plan

## Overview

Add automatic caption/subtitle generation for Short Form videos using existing Whisper transcription, with social media-optimized styling.

---

## Current State

**What exists:**
- ✅ Whisper transcription via `extract_lyrics_with_whisper()` in `lyric_extraction.py`
- ✅ Returns segments with `start`, `end`, `text` timestamps
- ✅ Used for lyric extraction and alignment to song sections

**What's missing:**
- ❌ SRT/VTT subtitle file generation
- ❌ Subtitle styling (large, bold, white text with black outline)
- ❌ Burning subtitles into video using FFmpeg
- ❌ UI toggle to enable/disable captions

---

## Implementation Plan

### Phase 1: SRT Generation

**Create:** `backend/app/services/subtitle_generation.py`

**Functions:**
```python
def segments_to_srt(segments: List[dict]) -> str:
    """
    Convert Whisper segments to SRT format.
    
    Args:
        segments: List of dicts with 'start', 'end', 'text' keys
    
    Returns:
        SRT file content as string
    """
    # Format:
    # 1
    # 00:00:00,000 --> 00:00:03,500
    # Text content here
    # 
    # 2
    # ...
```

**Key details:**
- Convert seconds to SRT timestamp format: `HH:MM:SS,mmm`
- Handle overlapping segments
- Split long text into multiple subtitle entries if needed
- Max characters per line: ~42 (safe for vertical format)

---

### Phase 2: Subtitle Styling

**Social Media Requirements:**
- Large, bold font (24-32px equivalent)
- White text with black outline (2px) for visibility
- Positioned in center-bottom (safe area, avoids platform UI)
- Works for 9:16 vertical format

**FFmpeg Subtitle Filter:**
```python
subtitle_filter = (
    f"subtitles={srt_path}:"
    f"force_style='"
    f"Fontsize=28,"
    f"PrimaryColour=&Hffffff,"
    f"OutlineColour=&H000000,"
    f"Outline=2,"
    f"Alignment=2,"
    f"MarginV=100"
    f"'"
)
```

**Style parameters:**
- `Fontsize=28`: Large text for mobile viewing
- `PrimaryColour=&Hffffff`: White text (BGR format)
- `OutlineColour=&H000000`: Black outline
- `Outline=2`: 2px outline thickness
- `Alignment=2`: Center-bottom alignment
- `MarginV=100`: 100px margin from bottom (safe area)

---

### Phase 3: Integration with Composition

**Update:** `backend/app/services/video_composition.py`

**Add to `concatenate_clips()`:**
```python
def concatenate_clips(
    ...,
    enable_captions: bool = False,
    caption_segments: Optional[List[dict]] = None,
) -> CompositionResult:
    """
    If enable_captions and caption_segments provided:
    1. Generate SRT file from segments
    2. Apply subtitle filter during final encoding
    3. Burn captions into video
    """
```

**FFmpeg integration:**
- Add subtitle filter to video filter chain
- Apply before final encoding
- Works with both 16:9 and 9:16 formats

---

### Phase 4: Transcription Reuse vs. Re-run

**Option A: Reuse existing transcription**
- Pros: Faster, no extra API cost
- Cons: May not match selected audio segment (if user selected 30s from 3min song)

**Option B: Re-run Whisper on selected segment**
- Pros: Accurate captions for selected portion
- Cons: Slower, extra API cost

**Recommendation:** 
- If `selected_start_sec` and `selected_end_sec` exist, re-run Whisper on that segment
- Otherwise, reuse existing transcription and filter segments by time range

---

### Phase 5: UI Integration

**Frontend changes:**
- Add checkbox: "Add Captions" in video generation/composition UI
- Show caption status in video completion panel
- Display caption toggle in `ClipGenerationPanel.tsx` or composition modal

**Backend API:**
- Add `enable_captions: bool` to composition request
- Return caption status in composition response

---

## Technical Considerations

### File Size Impact
- Burning subtitles adds minimal file size (~few KB)
- No significant encoding overhead

### Performance
- SRT generation: < 1ms (simple string formatting)
- Subtitle filter: Minimal encoding overhead (~5-10% slower)
- Whisper re-run (if needed): ~10-30 seconds for 60s audio

### Error Handling
- If Whisper fails, continue without captions (log warning)
- If SRT generation fails, continue without captions
- If subtitle filter fails, continue without captions (fallback to no captions)

---

## Testing Plan

1. **Unit tests:**
   - `segments_to_srt()` with various segment formats
   - Edge cases: overlapping segments, long text, empty segments

2. **Integration tests:**
   - Full composition with captions enabled
   - Verify captions appear in output video
   - Verify caption positioning and styling

3. **Manual testing:**
   - Test with 9:16 Short Form videos
   - Test with 16:9 Full Length videos
   - Test with selected audio segments
   - Verify captions are readable on mobile devices

---

## Future Enhancements

- **Multiple languages:** Support translation of captions
- **Custom styling:** Allow users to customize font, size, position
- **Caption file download:** Provide SRT file for manual editing
- **Auto-timing adjustments:** Fine-tune timing to match beats/music

---

**Status:** Planning phase - not implemented
**Priority:** Medium (Phase 1 feature, but polish)
**Estimated effort:** 4-6 hours

