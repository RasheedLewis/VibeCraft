#!/usr/bin/env python3
"""Generate 4 test video clips in parallel using Replicate.

Usage:
    export REPLICATE_API_TOKEN="your_token_here"
    python scripts/generate_test_clips.py
"""

import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import replicate

# Based on actual prompts from the database - 4 distinct variants (only one abstract visualizer)
prompts = [
    "Abstract visual style, vibrant color palette with #FF6B9D, #FFD93D, and #6BCF7F, energetic, upbeat, danceable mood, Electronic aesthetic, close_up_to_wide with fast pacing, fast_zoom camera motion (fast speed), dynamic and energetic, inspired by: Dance, with, tonight",
    "Neon cityscape at night, cyberpunk aesthetic, vibrant color palette with #00FFFF, #FF00FF, and #FFFF00, energetic, upbeat, rhythmic mood, Electronic aesthetic, wide_to_close with fast pacing, fast_pan camera motion (fast speed), dynamic and energetic, inspired by: Move, feel, rhythm",
    "Flowing water and nature scene, peaceful yet energetic, color palette with #4A90E2, #7B68EE, and #87CEEB, upbeat, pulsating mood, Electronic aesthetic, medium_shot with fast pacing, fast_zoom camera motion (fast speed), dynamic and energetic, inspired by: Beat, pulse, energy",
    "Geometric patterns and abstract art, vibrant color palette with #FF7BA3, #FFE085, and #6DD4A0, energetic, upbeat, driving mood, Electronic aesthetic, wide_shot with fast pacing, fast_tilt camera motion (fast speed), dynamic and energetic, inspired by: Flow, groove, motion",
]


def generate_clip(client, clip_num, prompt):
    """Generate a single clip and return the URL."""
    print(f"Generating clip {clip_num}/4...")
    try:
        # Use the same pattern as production code: get model, get version, create prediction
        model = client.models.get("anotherjesse/zeroscope-v2-xl")
        version = model.latest_version
        
        input_params = {
            "prompt": prompt,
            "num_frames": 32,  # 4 seconds at 8fps
            "width": 576,
            "height": 320,
            "fps": 8,
        }
        
        prediction = client.predictions.create(
            version=version,
            input=input_params,
        )
        
        # Poll for completion (similar to production code)
        max_attempts = 180  # 15 minutes max
        poll_interval = 5.0
        
        for attempt in range(max_attempts):
            prediction = client.predictions.get(prediction.id)
            
            if prediction.status == "succeeded":
                # Get video URL from output
                if prediction.output:
                    if isinstance(prediction.output, str):
                        video_url = prediction.output
                    elif isinstance(prediction.output, list) and len(prediction.output) > 0:
                        video_url = prediction.output[0]
                    else:
                        video_url = str(prediction.output)
                    print(f"✓ Clip {clip_num} ready: {video_url}")
                    return video_url
                else:
                    raise Exception(f"Clip {clip_num} succeeded but no output URL")
            elif prediction.status == "failed":
                error_msg = getattr(prediction, "error", "Unknown error")
                raise Exception(f"Clip {clip_num} failed: {error_msg}")
            
            # Still processing, wait and continue
            if attempt < max_attempts - 1:
                time.sleep(poll_interval)
        
        raise Exception(f"Clip {clip_num} timed out after {max_attempts * poll_interval / 60:.1f} minutes")
        
    except Exception as e:
        print(f"✗ Clip {clip_num} failed: {e}")
        raise


def download_clip(url, output_path):
    """Download a clip from URL to output path."""
    try:
        subprocess.run(["curl", "-L", "-o", str(output_path), url], check=True, capture_output=True)
        print(f"✓ Downloaded {output_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to download {output_path.name}: {e}")
        return False


def main():
    """Generate and download 4 test clips."""
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("Error: REPLICATE_API_TOKEN environment variable not set")
        print("Set it with: export REPLICATE_API_TOKEN='your_token_here'")
        sys.exit(1)

    client = replicate.Client(api_token=api_token)

    print("=" * 60)
    print("Generating 4 test clips in parallel...")
    print("=" * 60)

    # Generate all clips in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        urls = list(executor.map(lambda x: generate_clip(client, x[0] + 1, x[1]), enumerate(prompts)))

    print("\n" + "=" * 60)
    print("Downloading clips...")
    print("=" * 60)

    # Download all clips
    desktop = Path.home() / "Desktop"
    desktop.mkdir(exist_ok=True)

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(
            executor.map(
                lambda x: download_clip(x[1], desktop / f"clip{x[0] + 1}.mp4"),
                enumerate(urls),
            )
        )

    print("\n" + "=" * 60)
    if all(results):
        print("✓ All clips generated and downloaded successfully!")
        print(f"  Location: {desktop}")
        print(f"  Files: clip1.mp4, clip2.mp4, clip3.mp4, clip4.mp4")
    else:
        print("⚠ Some clips failed to download. Check errors above.")
    print("=" * 60)


if __name__ == "__main__":
    main()

