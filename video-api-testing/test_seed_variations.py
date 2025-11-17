#!/usr/bin/env python3
"""
Test the same prompt with multiple seeds to see variations.
Useful for understanding how seed affects output and finding good seeds.
LOWER PRIORITY THAN GOOD PROMPTS / MODELS COMBOS
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
        description="Test the same prompt with multiple seeds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_seed_variations.py "Abstract shapes floating" --seeds 1,2,3,4,5
  python test_seed_variations.py "Neon cityscape" --count 5 --start-seed 10
        """
    )
    
    parser.add_argument("prompt", help="Text prompt to test with different seeds")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Replicate model (default: {DEFAULT_MODEL})")
    parser.add_argument("--num-frames", type=int, default=24, help="Number of frames (default: 24)")
    parser.add_argument("--fps", type=int, default=8, help="Frames per second (default: 8)")
    parser.add_argument("--width", type=int, default=576, help="Video width (default: 576)")
    parser.add_argument("--height", type=int, default=320, help="Video height (default: 320)")
    parser.add_argument(
        "--seeds",
        help="Comma-separated list of seeds (e.g., '1,2,3,4,5')"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="Number of seeds to test (if --seeds not provided, generates random seeds)"
    )
    parser.add_argument(
        "--start-seed",
        type=int,
        default=1,
        help="Starting seed number (if --seeds not provided, uses start-seed, start-seed+1, ...)"
    )
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between generations (default: 2.0)")
    
    args = parser.parse_args()
    
    # Determine seeds to test
    if args.seeds:
        seeds = [int(s.strip()) for s in args.seeds.split(",")]
    else:
        seeds = list(range(args.start_seed, args.start_seed + args.count))
    
    print(f"🧪 Testing prompt with {len(seeds)} different seeds")
    print(f"📝 Prompt: {args.prompt}")
    print(f"🎬 Model: {args.model}")
    print(f"⚙️  Frames: {args.num_frames} @ {args.fps} fps")
    print(f"📐 Resolution: {args.width}x{args.height}")
    print(f"🌱 Seeds: {seeds}")
    print()
    
    results = []
    
    for i, seed in enumerate(seeds, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}/{len(seeds)} - Seed: {seed}")
        print(f"{'=' * 60}")
        
        video_url = generate_video(
            prompt=args.prompt,
            model=args.model,
            num_frames=args.num_frames,
            fps=args.fps,
            width=args.width,
            height=args.height,
            seed=seed,
        )
        
        results.append({
            "seed": seed,
            "success": video_url is not None,
            "url": video_url,
        })
        
        if i < len(seeds):
            print(f"\n⏸️  Waiting {args.delay}s before next generation...")
            import time
            time.sleep(args.delay)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("📊 Summary")
    print(f"{'=' * 60}")
    successful = sum(1 for r in results if r["success"])
    print(f"✅ Successful: {successful}/{len(results)}")
    
    if successful > 0:
        print(f"\n✅ Generated videos (same prompt, different seeds):")
        for result in results:
            if result["success"]:
                print(f"  Seed {result['seed']:3d}: {result['url']}")
        
        print(f"\n💡 Tip: Compare these videos to see how seed affects variation.")
        print(f"   If they look similar, seed provides consistency.")
        print(f"   If they look different, seed provides variety.")
    else:
        print(f"\n❌ All generations failed")


if __name__ == "__main__":
    main()
