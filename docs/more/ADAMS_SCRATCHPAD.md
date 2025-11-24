# Adam's Scratchpad

## Latest Notes

- Update video player to also be portrait mode (for short-form)
- Tweak it to not play audio during clip previews (because it's starting from the beginning)
- Fix the clip-planning logic to allow 1-2 clips, or just set min of 18s
- We still don't really have beat-aligned number-of-frames requested - if we technically do, it won't make any difference for a model that only gives us 8fps we probably need 24+ to see that matter
- Still would love to test various prompt thingies, ideally rigorously with like library & guidelines
- Should we at least use the Veo model?!
- oh also the first_frame_image should probably be cut out in post-processing since the generated video was so different and then it was weird

## Would-Be-Nice

- CloudFront for video URLs (at least for /public endpoints) and template character-images
- Smooth out transition timing (sub-frame precision cuts, beat verification, audio sync
  correction, tempo-aware alignment); and better frame interpolation, e.g.advanced algorithms, smoother motion, reduce artifacts and ghosting, maintain temporal consistency, preserve video quality during upscaling (if API
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
- Demo gallery page in frontend demonstrating one or more of (high-energy, slow emotional,
  complex transitions)
- Can we transition to actual beats instead of a pre-computed list based on BPM?

