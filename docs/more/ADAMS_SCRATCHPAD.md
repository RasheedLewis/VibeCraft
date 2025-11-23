# Adam's Scratchpad

## Process

- I like what I did in v2/ testing-wise: have it write a test shell-script, and give UI tips

## Tiny fixes noticed late Friday night

- Cache character templates on Cloudfront
- dev/start script shouldn't say "No backend unit tests found"
- 'Compose when done' button, I just remembered that's silly wording unless you can actually click it before clips are done
- Not a fix but Reena suggested wow imagine if I could provide video for ref (like screenshots), ooh Murad told her there are also models that take video directly
- the playback in audio selection timeline leaves much to be desired. right now the start and end times are wrong, see screenshot, but also and more important it's a drag (lol) to drag the markers, and also the playhead should be draggable too, and snap to the beginning-marker. ok actually it is draggable but sometimes it's hard especially going backwards and near the start-marker
- add back button for templates/image-upload
- ok so start/end definitely need to be draggable as a group...ah it is, but has annoying "Max: 30s"
- oh also pretty sure it only sends the first pose so lol what's the point of two, let user pick?
- also when the figure is spinning, the head doesn't look so good
- ?

## New Future Work For Sure

- User must select max 30 seconds, UI should let them drag start/end like you can on freebeat.ai

## Potential Future Work Identified At End Of MVP

Do-first:

- Ooh, Reena's tip, ask Murad what he did to have user provide a YouTube link and it downloads it
- Crazy: the clips are currently generated with concurrency limit 2, that's low!
- Uhh if you refresh page all state is lost... terrible UX
- *MOST* important! — Transition beat-sync logic to use actual beat times from analysis (not
  calculated from fixed BPM), which includes handling tempo changes mid-song
- Update Song Profile UI for clip-based workflow, e.g. allow user to approve/reject generated
  clips, and regenerate individual clips
- Prompt experimentation and style consistency: test different templates/models, catalog
  prompt→video mappings, implement shared style seeds/tokens across clips, create prompt
  library and guidelines
- Async: Convert blocking I/O to async, parallelize operations
- Concurrency: Tune limits, parallelize S3 operations
- DB queries: Found N+1 issue in get_clip_generation_summary (queries song then clips
  separately), missing indexes, no eager loading

Nice-to-haves:

- CDN for static assets (CloudFront for videos and frontend assets)
- Rate limiting (per-user, per-IP, per-endpoint) as isolated module
- Enforce max file size for upload
- Update copy on the website, e.g. it mentions "7 minutes" before song upload
- Documentation: update readme, developer guide, architecture, and maybe create a user guide,
  maybe create a testing guide
- Smooth out transition timing (sub-frame precision cuts, beat verification, audio sync
  correction, tempo-aware alignment)
- Better frame interpolation, e.g.advanced algorithms, smoother motion, reduce artifacts and
  ghosting, maintain temporal consistency, preserve video quality during upscaling (if API
  doesn't support 24fps+)
- Audio sync improvements: periodically check audio/video sync to help ensure no audio drift,
  maybe insert small gaps or speed adjustments to maintain sync, maybe use FFmpeg's -itsoffset or
  -af atempo for fine-tuning, maybe handle variable tempo songs, beat-sync accuracy improvements
  (sub-frame precision), and handle beat alignment drift and frame rounding errors (e.g. 35
  frames at 8 FPS = 4.375 seconds, but beat might be at 4.364 seconds, and then small drifts
  may accumulate across multiple clips)
- Enhanced transitions: light flares, zoom effects, crossfades, wipes, beat-synced effects,
  motion blur during transitions, color flash effects (currently hard cuts only)
- Additional video effects: motion stabilization, slow motion / speed ramping, particle
  effects, lens flares and light leaks, chromatic aberration effects, vignetting, film grain
  texture
- Add shell scripts for E2E integration tests
- Take and edit demo video of using the app
- Per-video cost tracking utilities
- User authentication
- Demo gallery page in frontend demonstrating one or more of (high-energy, slow emotional,
  complex transitions)
- Orchestration endpoint for one-button generation (`POST /api/v1/songs/{song_id}/generate-full-video`
  that handles plan → generate → compose automatically)
- Error toast notifications with retry buttons along with improved retry logic for AI inference
  failures (automatic retry with exponential backoff, distinguish retryable vs non-retryable
  errors)
- Handle songs with no vocals/instrumental tracks
