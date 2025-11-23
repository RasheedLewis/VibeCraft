# Finding Test Clips for Video Composition

## Current Model
- **Model:** `anotherjesse/zeroscope-v2-xl` on Replicate
- **Specs:** 576x320 resolution, 8 FPS, typically 3-6 seconds
- **Cost:** ~$0.035 per generation

## Quick Options

### 1. **Generate Your Own (Recommended)**
Fastest way to get clips matching your exact specs:

```bash
# Install Replicate CLI (if not already installed)
pip install replicate

# Set your API token
export REPLICATE_API_TOKEN="your_token_here"

# Generate a few test clips (3-5 seconds each)
replicate run anotherjesse/zeroscope-v2-xl \
  --prompt "abstract colorful waves, cinematic, 4k" \
  --num_frames 32 \
  --width 576 \
  --height 320 \
  --fps 8

# Save the output URL and download:
curl -O <video_url_from_output>
```

**Quick test prompts:**
- `"abstract colorful waves, cinematic, 4k"`
- `"neon cityscape at night, cyberpunk style"`
- `"flowing water, nature scene, peaceful"`
- `"geometric patterns, abstract art, vibrant colors"`
- `"space nebula, stars, cosmic"`

### 2. **Use Replicate Model Page**
- Visit: https://replicate.com/anotherjesse/zeroscope-v2-xl
- Browse example outputs in the "Examples" section
- Right-click example videos → "Save video as..."
- Note: These may vary in resolution/FPS, but should work for testing

### 3. **Replicate API Script**
Create a quick script to generate multiple clips:

```python
import replicate
import os

client = replicate.Client(api_token=os.getenv("REPLICATE_API_TOKEN"))

prompts = [
    "abstract colorful waves, cinematic",
    "neon cityscape at night, cyberpunk",
    "flowing water, nature scene",
]

for i, prompt in enumerate(prompts):
    output = client.run(
        "anotherjesse/zeroscope-v2-xl",
        input={
            "prompt": prompt,
            "num_frames": 32,  # 4 seconds at 8fps
            "width": 576,
            "height": 320,
            "fps": 8,
        }
    )
    print(f"Clip {i+1}: {output}")
    # Download with: curl -O <output>
```

### 4. **Use Existing SectionVideos**
If you have any songs with generated videos in your database:

```bash
# Get SectionVideo URLs from your database
docker exec ai-music-video-postgres psql -U postgres -d ai_music_video \
  -c "SELECT id, video_url, duration_sec FROM section_videos WHERE video_url IS NOT NULL LIMIT 5;"

# Download them:
curl -O <video_url_1>
curl -O <video_url_2>
# etc.
```

### 5. **Public Zeroscope Outputs**
- Search Twitter/X for `#zeroscope` or `zeroscope v2 xl`
- Check Replicate community examples
- Note: May need to verify resolution/FPS matches your needs

## Recommended Workflow

1. **Generate 3-5 clips** using option #1 or #3 above
2. **Save to Desktop** for easy access: `~/Desktop/clip1.mp4`, `clip2.mp4`, etc.
3. **Use with local script:**
   ```bash
   python scripts/compose_local.py \
     --clips ~/Desktop/clip1.mp4 ~/Desktop/clip2.mp4 ~/Desktop/clip3.mp4 \
     --audio ~/Desktop/song.mp3 \
     --output ~/Desktop/composed.mp4
   ```

## Tips

- **Keep clips short:** 3-5 seconds each (24-40 frames at 8fps) for faster testing
- **Use varied prompts:** Different styles/colors help verify composition works with diverse content
- **Match specs:** Ensure clips are 576x320 @ 8fps to match production (or let normalization handle it)
- **Save URLs:** Keep Replicate job URLs in case you need to regenerate

## Cost Estimate

- 3 clips × $0.035 = **~$0.10** for a full test set
- Very affordable for testing!

