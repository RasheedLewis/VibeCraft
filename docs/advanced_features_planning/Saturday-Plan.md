# Saturday Plan

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
If I say (TTL) refer to Temp-Troubleshooting-Log.md, if I say (BSIP) refer to BEAT-SYNC-IMPLEMENTATION-PLAN.md, if I say (MTG) refer to MANUAL_TESTING_GUIDE.md

- Beat-synced visual effects, (TTL) line 132 - I'd like to verify it's happening - maybe temporarily exaggerating its effect and duration for manual inspection
- Beat-synced visual effects, (TTL) line 136 - why on earth is this only applying for the first 50 beats? we need to do it for the whole duration - when the clip is short-form
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
- Gotta actually deploy all these changes to prod - oh, and update Architecture (ARCH.md in root)
- Oh uh I need to test actually uploading an image, like the use case could be brand avatar!
- I want to see if I can pass multiple (e.g. two) reference images - and if not, alter UX to let user choose 'pose 2' from the templates
- Wait a sec, if an image is supplied, is that used *instead* of the text prompt?! No no no let's check that logic and make sure it's both
- Hmm in (MTG) line 496, what's this "glitch effect"? How can I test that (perhaps exaggerate the effect while testing)?
- In fact, I want to get a summary of all the beat-sync and all the visual effects and a list of how to test/observe them. You could start by reading BEAT-SYNC-IMPLEMENTATION-PLAN.md which lists effects—that whole doc was (supposedly) implemented
- (MTG) lines 542-554 mentions trim/extend but I'm unfamiliar with testing that, I guess this is a special case of my request on the line above
- I do need user testing. I'd love to get Arial to try it out, but that might not happen. I don't know who else...Nick? I want to know whether, or how close, this is to something useful. I can also get, from anyone, their impression of both "overall fun" and "beat sync", plus their suggestions.
- Is there really no good source on how rhythmic prompts affect generated video? If I had time, I'd love to gather findings and write a brief report
- To analyze prompts, I need to go back to my setup and testing facilities in the video-api-testing/ branch — which I abandoned too soon! Certainly I want to iterate rapidly on short clips (like 4 seconds - to generate just 1 clip, for speed) and log the full prompt passed. And do that 50 times!!
- Is `interrogate_reference_image` mentioned in CHARACTER_CONSISTENCY_IMPLEMENTATION.md actually used (and how would I know)? Oh and, uh, do I need to get an OpenAI key if I want to try using the Vision model?
- I think I probably want to add a lot more comments to code, not for niggling details but for important foundational, character-consistency, or beat-sync logic, and probably update CODE_ANALYSIS_REPORT as well for a high-level overview of all the code.
- Yeah seeing prompts passed, transparently, as easily as possible, for a high-iteration flow, is a top priority to nail down asap.
- Although today is manual-heavy, when I do identify chunks of work, I want to break it into parallel groups that two agents can work simultaneously.
- Hmm so do we have any transition effects at all? I'm reading Technical-Exploration.md line 553 that would add them, but it's an Approach that we didn't implement
- And-oh my god-same doc line 898, do we currently pass any bpm-aware prompting, other than literal bpm? because this is low-hanging fruit!
- Also, same doc line 1837, did we implement all those effects/filters? Probably, or at least we should've.
- Let's apply an approach in Temp-TODO-FIX-THIS-POLLING just a one-commit thing but test E2E flow as polling has proven tricky.
- I still like the idea of calling it BeatDrop, maybe I'll wait on that though
- Haha for prompts let's first try alternatives to anything hardcoded (although we could turn out to like it and stick with it).
- You know one more thing I'd like? I'd like to finish today. I don't need to estimate time on any of this, but for the 1-3 highest-effort things maybe I could see if I feel like tackling them tomorrow. If I could wrap up in the next 9 hours (3:20pm-12:20am) I'd be overjoyed. And just sync w/R tomorrow.

---

# Organized Plan - Prioritized & Focused

**Goal:** Maximize value delivered in ~9 hours (3:30pm-11:30pm). Focus on critical fixes, high-value quick wins, and enabling rapid iteration.

**Reference Docs:**

- (TTL) = Temp-Troubleshooting-Log.md
- (BSIP) = BEAT-SYNC-IMPLEMENTATION-PLAN.md  
- (MTG) = MANUAL_TESTING_GUIDE.md
- (TE) = Technical-Exploration.md

---

## 🚨 PHASE 1: Critical Bug Fixes (Do First - 1-2 hours)

**These block core functionality and must be fixed before anything else.**

### 1.1 Fix 50-Beat Limitation in Beat Filters ⚠️ CRITICAL

- **Issue:** (TTL line 136) Beat filters only apply to first 50 beats in `video_composition.py:445`
- **Fix:** Remove `[:50]` limit, use `generate_beat_filter_complex()` for all beats, or chunk processing
- **Test:** Generate short-form video, verify effects throughout entire duration
- **Files:** `backend/app/services/video_composition.py:445`

### 1.2 Verify Reference Image Logic

- **Issue:** (Line 27) Need to confirm: if image supplied, is it used *instead* of text prompt?
- **Fix:** Ensure both image AND text prompt are used together (not replacement)
- **Test:** Upload image + provide text prompt, verify both influence generation
- **Files:** `backend/app/services/character_consistency.py`, `video_generation.py`

### 1.3 Fix Polling (One-Commit Approach)

- **Issue:** (Line 41) Polling has proven tricky, need E2E test
- **Action:** Apply approach from `Temp-TODO-FIX-THIS-POLLING_ANALYSIS_REPORT.md`
- **Test:** Full E2E flow with polling

---

## ⚡ PHASE 2: High-Value Quick Wins (2-3 hours)

**Low effort, high impact. Enable better iteration and product quality.**

### 2.1 Enable Prompt Visibility & Logging 🔥 TOP PRIORITY

- **Why:** (Line 36) "Seeing prompts passed, transparently, as easily as possible, for a high-iteration flow, is a top priority"
- **Action:**
  - Add prompt logging to worker logs (full final prompt)
  - Consider adding prompt to API response or frontend display
  - Set up rapid iteration: 4-second clips, single clip generation, log full prompt
- **Files:** `video_generation.py`, worker logs, potentially frontend

### 2.2 Add BPM-Aware Prompting (Beyond Literal BPM) 🎯 LOW-HANGING FRUIT

- **Issue:** (TE line 898) Currently only passes literal BPM, missing tempo-aware descriptors
- **Action:** Enhance `prompt_enhancement.py` with tempo descriptors (slow/flowing, fast/energetic based on BPM ranges)
- **Files:** `backend/app/services/prompt_enhancement.py`

### 2.3 Create Beat-Sync Effects Summary & Testing Guide

- **Action:**
  - Document all implemented effects (flash, color_burst, zoom_pulse, glitch, brightness_pulse)
  - Create testing checklist with how to observe each effect
  - Temporarily exaggerate effects for manual inspection (increase intensity/duration)
- **Output:** New doc or section in MANUAL_TESTING_GUIDE.md

### 2.4 Improve Dancing Prompts

- **Issue:** (Line 7) Videos barely dancing, need stronger prompts
- **Action:**
  - Enhance motion descriptors for dancing poses
  - Try alternatives to hardcoded prompts (Line 43)
  - Consider swapping poses if needed
- **Files:** `prompt_enhancement.py`, `scene_planner.py`

### 2.5 Parallelize Clip Generation

- **Issue:** (Line 9) Why not generate more than 2 clips concurrently?
- **Action:** Increase concurrent clip generation limit (check current config)
- **Files:** `video_generation.py`, worker configuration

---

## 🔍 PHASE 3: Verification & Testing (1-2 hours)

**Verify what's working, identify gaps, prepare for user testing.**

### 3.1 Verify Beat-Sync Effects Are Working

- **Action:**
  - Temporarily exaggerate flash effect (increase RGB boost, extend duration)
  - Generate test video, manually inspect for beat-synced flashes
  - Verify effects trigger on beats (not just first 50)
- **Files:** `video_composition.py`, `beat_filters.py`

### 3.2 Test All Visual Effects

- **Action:**
  - Test glitch effect (MTG line 496) - verify it's implemented and working
  - Test trim/extend functionality (MTG lines 542-554)
  - Verify all effects from (BSIP) are actually implemented
- **Files:** Various effect implementations

### 3.3 Test Image Upload Flow

- **Action:**
  - Test uploading custom image (brand avatar use case - Line 25)
  - Verify `interrogate_reference_image` is actually used (Line 34)
  - Check if OpenAI Vision key needed (Line 34)
- **Files:** `image_interrogation.py`, `character_consistency.py`

### 3.4 Set Up Rapid Iteration Testing

- **Action:**
  - Revive `video-api-testing/` setup (Line 33)
  - Enable 4-second single-clip generation for speed
  - Log full prompts for 50 iterations
- **Files:** `video-api-testing/` directory

---

## 🚀 PHASE 4: Product Polish (2-3 hours)

**Make product actually usable and ready for users.**

### 4.1 Persist State on Page Refresh

- **Action:** Save current project state to localStorage or backend
- **Files:** Frontend state management

### 4.2 Add Auth + Project Listing (5 max)

- **Action:**
  - Simple auth (JWT or session-based)
  - Projects page listing user's projects (max 5)
- **Files:** New auth endpoints, frontend auth flow, projects page

### 4.3 Easy Wins

- **Action:**
  - Check max file size validation (Line 21)
  - Add per-video cost tracking (Line 18)
- **Files:** Upload validation, cost tracking service

---

## 📊 PHASE 5: Infrastructure & Deployment (1-2 hours)

**Prepare for production and documentation.**

### 5.1 Rate Limiting

- **Action:** Create rate limiting module (per-user, per-IP, per-endpoint)
- **Files:** New `rate_limiting.py` module, middleware

### 5.2 Deploy to Prod

- **Action:** Deploy all changes, verify production works
- **Files:** Deployment scripts, production config

### 5.3 Update Documentation

- **Action:**
  - Update ARCH.md with current architecture
  - Add code comments for important beat-sync/character-consistency logic (Line 35)
  - Update CODE_ANALYSIS_REPORT.md (Line 35)
- **Files:** `docs/ARCH.md`, `docs/more/CODE_ANALYSIS_REPORT.md`, code files

---

## 🎬 PHASE 6: Demo & User Testing Prep (1 hour)

**Prepare for external validation.**

### 6.1 Create Demo Video

- **Action:** Record slick demo for Sunday, Twitter, LinkedIn, README
- **Output:** Demo video file

### 6.2 Prepare User Testing

- **Action:**
  - Identify testers (Arial, Nick, others)
  - Prepare feedback form/questions:
    - Overall fun rating
    - Beat sync perception
    - Suggestions
- **Output:** Testing guide/checklist

---

## 🔮 PHASE 7: Future Spikes (If Time Permits)

**Lower priority, can defer to tomorrow.**

### 7.1 Transition Effects

- **Issue:** (Line 38) No transition effects implemented (TE line 553)
- **Action:** Research and implement basic transition effects

### 7.2 Advanced Dancing Sync

- **Issue:** (Line 20) OpenCV motion detection + time stretching approach
- **Action:** Spike on motion peak detection, time stretching, trim/loop
- **Files:** New service for motion analysis

### 7.3 Veo Model Testing

- **Action:** Spike on Veo/Veo3 model (Line 22)
- **Files:** Video generation service

### 7.4 Multiple Reference Images

- **Issue:** (Line 26) Want to pass 2 reference images, or let user choose pose 2 from templates
- **Action:** Research API support, implement if possible

### 7.5 Performance Optimizations

- **Action:**
  - Check for N+1 queries in `get_clip_generation_summary` (Line 12)
  - Add database indexes where needed
  - Add eager loading where appropriate
  - Identify sync processes that should be async (Line 11)
- **Files:** Various services, database models

### 7.6 CloudFront Setup

- **Action:** Determine what to serve via CloudFront (character images, final videos from S3)
- **Files:** S3/CloudFront configuration

---

## 📋 Execution Strategy

### Parallel Work Streams

When breaking into chunks, consider these parallel groups:

**Stream A (Backend):**

- Fix 50-beat limitation
- BPM-aware prompting
- Rate limiting
- Cost tracking

**Stream B (Testing/Verification):**

- Beat-sync effects verification
- Image upload testing
- Rapid iteration setup
- Effects summary doc

**Stream C (Frontend/UX):**

- State persistence
- Auth + project listing
- Prompt visibility in UI

### Time Management

- **Must Finish Today:** Phases 1-3 (Critical fixes + Quick wins + Verification)
- **Nice to Have:** Phase 4 (Product polish)
- **Can Defer:** Phases 5-7 (Infrastructure, demo, spikes)

### Success Metrics

- ✅ Beat filters work for full video duration
- ✅ Prompts visible/logged for rapid iteration
- ✅ BPM-aware prompting enhanced
- ✅ All effects verified and testable
- ✅ Product ready for user testing

---

## 🎯 Focus Areas for Maximum Value

1. **Enable Rapid Iteration** - Prompt visibility is #1 priority
2. **Fix Critical Bugs** - 50-beat limit blocks core feature
3. **Verify What Exists** - Don't build new if current doesn't work
4. **Low-Hanging Fruit** - BPM-aware prompting, parallelization
5. **User-Ready** - State persistence, basic auth, demo video
