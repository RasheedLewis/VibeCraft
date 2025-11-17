#!/usr/bin/env python3
"""
Batch test multiple prompts from a file.
Each line in the file is treated as a separate prompt.
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
from test_video import generate_video, DEFAULT_MODEL

load_dotenv()


def main():
    parser = argparse.ArgumentParser(
        description="Batch test prompts from a file",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example prompts.txt:
  A futuristic cityscape at sunset with neon lights
  Abstract shapes floating in space
  Neon lights in Tokyo at night
        """
    )
    
    parser.add_argument("file", help="Text file with one prompt per line")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Replicate model (default: {DEFAULT_MODEL})")
    parser.add_argument("--num-frames", type=int, default=24, help="Number of frames (default: 24)")
    parser.add_argument("--fps", type=int, default=8, help="Frames per second (default: 8)")
    parser.add_argument("--width", type=int, default=576, help="Video width (default: 576)")
    parser.add_argument("--height", type=int, default=320, help="Video height (default: 320)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between generations in seconds (default: 2.0)")
    
    args = parser.parse_args()
    
    # Read prompts from file
    prompt_file = Path(args.file)
    if not prompt_file.exists():
        print(f"❌ File not found: {args.file}")
        sys.exit(1)
    
    with open(prompt_file, "r") as f:
        prompts = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    
    if not prompts:
        print(f"❌ No prompts found in {args.file}")
        sys.exit(1)
    
    print(f"📋 Found {len(prompts)} prompts")
    print(f"🎬 Model: {args.model}")
    print(f"⚙️  Frames: {args.num_frames} @ {args.fps} fps")
    print(f"📐 Resolution: {args.width}x{args.height}")
    if args.seed:
        print(f"🌱 Seed: {args.seed}")
    print()
    
    results = []
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}/{len(prompts)}: {prompt[:50]}...")
        print(f"{'=' * 60}")
        
        video_url = generate_video(
            prompt=prompt,
            model=args.model,
            num_frames=args.num_frames,
            fps=args.fps,
            width=args.width,
            height=args.height,
            seed=args.seed,
        )
        
        results.append({
            "prompt": prompt,
            "success": video_url is not None,
            "url": video_url,
        })
        
        if i < len(prompts):
            print(f"\n⏸️  Waiting {args.delay}s before next generation...")
            import time
            time.sleep(args.delay)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("📊 Summary")
    print(f"{'=' * 60}")
    successful = sum(1 for r in results if r["success"])
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")
    
    if successful > 0:
        print(f"\n✅ Successful videos:")
        for i, result in enumerate(results, 1):
            if result["success"]:
                print(f"  {i}. {result['url']}")
                print(f"     Prompt: {result['prompt'][:60]}...")


if __name__ == "__main__":
    main()

