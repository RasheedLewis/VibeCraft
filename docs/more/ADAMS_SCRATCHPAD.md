# Adam's Scratchpad

## Latest Notes

- We still don't really have beat-aligned number-of-frames requested - if we technically do, it won't make any difference for a model that only gives us 8fps we probably need 24+ to see that matter
- Still would love to test various prompt thingies, ideally rigorously with like library & guidelines
- 

## Would-Be-Nice

- CloudFront for video URLs (at least for /public endpoints) and template character-images
- Try 


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
