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

**Missing Infrastructure:**

- **CloudFront/CDN Setup** (Line 96, Phase 7.6) - Currently using presigned S3 URLs directly. Need CloudFront distribution for character images and final videos. No detailed implementation plan found.

**User Experience Enhancements:**

- **Transition Effects** (Line 118, Phase 7.1) - No crossfades/dissolves between clips (only fadeout for trim/extend). Listed as future spike.
- **Multiple Reference Images UX** (Line 106, Phase 7.4) - Code supports pose-a/pose-b, but no UX to choose "pose 2" from templates.

**Advanced Features (Future Spikes):**

- **Advanced Dancing Sync** (Line 100, Phase 7.2) - OpenCV motion detection + time stretching approach
- **Veo Model Testing** (Line 102, Phase 7.3) - Spike on Veo/Veo3 model

**Needs Verification:**

- **Performance Optimizations** (Line 92, Phase 7.5) - Check for N+1 queries, missing indexes, eager loading opportunities, sync processes that should be async

**Already Implemented ✅:**

- Concurrent clip generation (4 clips) - `DEFAULT_MAX_CONCURRENCY = 4`
- Actual beat detection - Using `librosa.beat.beat_track()` for real beats
- BPM-aware prompting - `TEMPO_DESCRIPTORS` in `prompt_enhancement.py`
- State persistence - URL params
- Auth + project listing - `AuthModal.tsx` and `ProjectsModal.tsx` exist
- Rate limiting, cost tracking, max file size validation

---

## 🎯 What's Left

**Completed:**

- ✅ Phase 3: Verification & Testing (beat-sync effects, image upload, rapid iteration)
- ✅ Phase 4: Product Polish (state persistence, auth + project listing, cost tracking)
- ✅ Phase 5.1: Rate Limiting
- ✅ Phase 5.3: Documentation updates

**Remaining:**

- ⏳ Phase 5.2: Deploy to Prod (manual deployment step)
- ⏳ Phase 6: Demo & User Testing Prep (manual tasks - demo video, user testing)
- ⏳ Phase 7: Future Spikes (lower priority - transitions, advanced dancing sync, Veo testing, etc.)

**Status:** Core features complete. Ready for deployment and user testing.

---

Here's what's on my mind, I don't have an organized plan yet.
Note: Some referenced documents (Temp-Troubleshooting-Log.md, BEAT-SYNC-IMPLEMENTATION-PLAN.md, MANUAL_TESTING_GUIDE.md) no longer exist.

- Beat-synced visual effects - I'd like to verify it's happening - maybe temporarily exaggerating its effect and duration for manual inspection
- Beat-synced visual effects - why on earth is this only applying for the first 50 beats? we need to do it for the whole duration - when the clip is short-form
- Dancing, one of my poses, the video I got back it was barely dancing. We can try prompt-engineering to make it dance a lot. May swap out poses, too.
- Can we transition to actual beats instead of a pre-computed list based on BPM?
- Why not generate more than 2 clips concurrently?
- Is there anything else we can parallelize?
- Is there any (long-running) process that's sync that we can and should make async?
- Is there still an N+1 in get_clip_generation_summary, or anywhere else? For any db ops should we add an index? Do we want to add eager loading in some places?
- Let's persist state on page refresh!
- Can we also add auth, and a simple page listing projects, with 5 max
- And maybe after that, Rate limiting (per-user, per-IP, per-endpoint) (make a module)
- What can we serve with CloudFront? What's in S3 afaik: character images, final video
- Can we add more visual effects with ffmpeg post-processing?
- We still need per-video cost-tracking
- Get a slick demo vid not just for Sunday but also for twtr, LinkedIn, project README
- Try further approaches for actual dancing sync, as outlined in Technical-Exploration, possibly starting with a spike on using python OpenCV to detect motion peaks and apply subtle time stretching (and then trim/loop video length, as well as the flow of when audio is added namely make sure it's after that)
- Easy win, check max file size
- Easy win but also a spike, try Veo (Veo3?)
- General spike work on prompts — this is probably most important, just so open-ended
- Gotta actually deploy all these changes to prod - oh, and update Architecture (Architecture.md in root)
- Oh uh I need to test actually uploading an image, like the use case could be brand avatar!
- I want to see if I can pass multiple (e.g. two) reference images - and if not, alter UX to let user choose 'pose 2' from the templates
- Wait a sec, if an image is supplied, is that used *instead* of the text prompt?! No no no let's check that logic and make sure it's both
- What's this "glitch effect"? How can I test that (perhaps exaggerate the effect while testing)?
- In fact, I want to get a summary of all the beat-sync and all the visual effects and a list of how to test/observe them. See `beat-sync-effects-guide.md` for effects documentation.
- Trim/extend functionality - I'm unfamiliar with testing that, I guess this is a special case of my request on the line above
- I do need user testing. I'd love to get Arial to try it out, but that might not happen. I don't know who else...Nick? I want to know whether, or how close, this is to something useful. I can also get, from anyone, their impression of both "overall fun" and "beat sync", plus their suggestions.
- Is there really no good source on how rhythmic prompts affect generated video? If I had time, I'd love to gather findings and write a brief report
- To analyze prompts, I need to go back to my setup and testing facilities in the video-api-testing/ branch — which I abandoned too soon! Certainly I want to iterate rapidly on short clips (like 4 seconds - to generate just 1 clip, for speed) and log the full prompt passed. And do that 50 times!!
- Is `interrogate_reference_image` actually used (and how would I know)? Oh and, uh, do I need to get an OpenAI key if I want to try using the Vision model?
- I think I probably want to add a lot more comments to code, not for niggling details but for important foundational, character-consistency, or beat-sync logic, and probably update CODE_ANALYSIS_REPORT as well for a high-level overview of all the code.
- Yeah seeing prompts passed, transparently, as easily as possible, for a high-iteration flow, is a top priority to nail down asap.
- Although today is manual-heavy, when I do identify chunks of work, I want to break it into parallel groups that two agents can work simultaneously.
- Hmm so do we have any transition effects at all? I'm reading adv-features-technical-exploration.md line 553 that would add them, but it's an Approach that we didn't implement
- And-oh my god-same doc line 898, do we currently pass any bpm-aware prompting, other than literal bpm? because this is low-hanging fruit!
- Also, same doc line 1837, did we implement all those effects/filters? Probably, or at least we should've.
- Let's apply an approach in Temp-TODO-FIX-THIS-POLLING just a one-commit thing but test E2E flow as polling has proven tricky.
- I still like the idea of calling it BeatDrop, maybe I'll wait on that though
- Haha for prompts let's first try alternatives to anything hardcoded (although we could turn out to like it and stick with it).
- You know one more thing I'd like? I'd like to finish today. I don't need to estimate time on any of this, but for the 1-3 highest-effort things maybe I could see if I feel like tackling them tomorrow. If I could wrap up in the next 9 hours (3:20pm-12:20am) I'd be overjoyed. And just sync w/R tomorrow.
