# Saturday Plan

## 📊 Testing Findings

### Prompt Over-Engineering: Motion Descriptors May Be Reducing Dance Quality

**Issue:** Analysis of prompt logs shows we may have gone overboard with "rhythmic motion" and motion descriptors generally. The figures are dancing less than they used to.

**Evidence from Prompt Logs:**

- Heavy emphasis on motion descriptors: 67+ occurrences of "dance/dancing" across 19 prompts
- Multiple overlapping rhythmic phrases: "rhythmic motion matching the beat", "synchronized to tempo", "dynamic dancing synchronized to BPM"
- All prompts include extensive motion descriptors: "energetic, driving, dynamic, upbeat energetic dancing, rapid rhythmic dance motion, quick dance steps synchronized to tempo"

**Hypothesis:**

- Too many motion descriptors may be confusing the model or diluting the core "dancing" instruction
- The model might be interpreting the complex prompt as abstract motion rather than clear dancing
- Simpler, more direct prompts may produce better dancing results

**Action Items:**

- Consider simplifying prompts to focus on clear, direct dancing instructions
- Test with fewer motion descriptors to see if dance quality improves
- Compare current prompts with earlier versions that produced better dancing
- May need to reduce or remove some of the overlapping rhythmic phrases

---

## 💭 My Thoughts During Testing

### Beat-Sync Limitations with 8fps Model

**Issue:** With an 8fps model, we can't do much to beat-sync unless we actually trim the clips. However, we can't trim clips if there's no slack — i.e., if the total clip duration isn't greater than the video duration.

**Implications:**

- Need to ensure clips have extra duration (slack) to allow trimming for beat alignment
- May need to generate clips slightly longer than needed, then trim to align with beats
- This requires careful planning in clip generation to account for trimming overhead

### Visual Effects Not Visible

**Observation:** Visual effects (beat-sync effects) are not visible in the final composed video.

**Possible causes:**

- Effects may be too subtle at 8fps
- Effects may not be applying correctly
- May need to increase effect intensity or duration
- Test mode (`BEAT_EFFECT_TEST_MODE=true`) should make effects more visible but may still need adjustment

### Dancing Figure During Silence

**New Feature Idea:** The dancing figure should stop dancing if the music stops (or effectively stops). During silence, we should post-process to keep the frame still.

**Initial thoughts:**

- Need to detect silence/quiet sections in audio
- Apply post-processing to freeze/hold frames during silence
- This would make the video more natural and responsive to the music
- Requires audio analysis to detect silence vs. quiet but still present music
- May need to integrate with existing beat detection or add separate silence detection

**Note:** This is a new feature needing breakdown — will flesh out in another chat.

---

## 📋 Summary: What's Not Implemented (Excluding Beat-Sync Effects & Prompt Engineering)

**User Experience Enhancements:**

- **Transition Effects** (Line 118, Phase 7.1) - No crossfades/dissolves between clips (only fadeout for trim/extend). Listed as future spike.
- **Multiple Reference Images UX** (Line 106, Phase 7.4) - Code supports pose-a/pose-b, but no UX to choose "pose 2" from templates.

**Advanced Features (Future Spikes):**

- **Advanced Dancing Sync** (Line 100, Phase 7.2) - OpenCV motion detection + time stretching approach
- **Veo Model Testing** (Line 102, Phase 7.3) - Spike on Veo/Veo3 model
