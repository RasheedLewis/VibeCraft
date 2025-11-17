#!/usr/bin/env python3
"""
Estimate video generation time based on model and parameters.
Uses historical data from api_calls.log if available, otherwise uses known model estimates.
"""

import argparse
import json
import re
from pathlib import Path
from statistics import mean, median

LOG_FILE = "api_calls.log"


def parse_log_file(log_file: str) -> dict:
    """Parse api_calls.log to extract timing data by model."""
    if not Path(log_file).exists():
        return {}
    
    model_times = {}
    
    with open(log_file, "r") as f:
        for line in f:
            # Format: timestamp | model | prompt | params | result | duration
            parts = line.strip().split(" | ")
            if len(parts) >= 6:
                model = parts[1]
                duration_str = parts[5].rstrip("s")
                try:
                    duration = float(duration_str)
                    if model not in model_times:
                        model_times[model] = []
                    model_times[model].append(duration)
                except ValueError:
                    continue
    
    return model_times


def get_model_estimates() -> dict:
    """Get known time estimates for different models (in seconds)."""
    return {
        "anotherjesse/zeroscope-v2-xl": {
            "typical": 45,  # 30-60 seconds typical, use 45 as median
            "fast": 20,
            "slow": 120,
            "factors": {
                "resolution": 1.0,  # Base
                "num_frames": 1.0,  # Linear with frames
            }
        },
        "luma/ray": {
            "typical": 40,
            "fast": 30,
            "slow": 60,
            "factors": {
                "resolution": 1.0,
                "num_frames": 1.0,
            }
        },
        "lightricks/ltx-video": {
            "typical": 10,
            "fast": 5,
            "slow": 20,
            "factors": {
                "resolution": 1.0,
                "num_frames": 1.0,
            }
        },
        # Default estimate for unknown models
        "default": {
            "typical": 45,
            "fast": 30,
            "slow": 90,
            "factors": {
                "resolution": 1.0,
                "num_frames": 1.0,
            }
        }
    }


def estimate_time(
    model: str,
    num_frames: int = 24,
    width: int = 576,
    height: int = 320,
    use_log_data: bool = True,
) -> dict:
    """
    Estimate generation time for given parameters.
    
    Returns dict with: typical, fast, slow (in seconds)
    """
    # Try to get historical data from log
    log_data = parse_log_file(LOG_FILE) if use_log_data else {}
    
    # Get model-specific estimates
    estimates = get_model_estimates()
    model_estimate = estimates.get(model, estimates["default"])
    
    # Calculate base time
    if model in log_data and len(log_data[model]) > 0:
        # Use historical data if available
        times = log_data[model]
        base_typical = median(times)
        base_fast = min(times)
        base_slow = max(times)
    else:
        # Use known estimates
        base_typical = model_estimate["typical"]
        base_fast = model_estimate["fast"]
        base_slow = model_estimate["slow"]
    
    # Adjust for parameters (simple linear scaling)
    factors = model_estimate["factors"]
    
    # Resolution factor (higher resolution = longer time)
    resolution_factor = (width * height) / (576 * 320)  # Normalize to default
    
    # Frames factor (more frames = longer time, roughly linear)
    frames_factor = num_frames / 24  # Normalize to default 24 frames
    
    # Apply factors
    typical = base_typical * resolution_factor * frames_factor
    fast = base_fast * resolution_factor * frames_factor
    slow = base_slow * resolution_factor * frames_factor
    
    return {
        "typical": round(typical, 1),
        "fast": round(fast, 1),
        "slow": round(slow, 1),
        "model": model,
        "num_frames": num_frames,
        "resolution": f"{width}x{height}",
        "based_on": "log_data" if model in log_data else "known_estimates",
        "sample_count": len(log_data.get(model, [])),
    }


def format_time(seconds: float) -> str:
    """Format seconds into human-readable time."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def main():
    parser = argparse.ArgumentParser(
        description="Estimate video generation time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python estimate_time.py --model anotherjesse/zeroscope-v2-xl
  python estimate_time.py --model luma/ray --num-frames 48 --width 1024
  python estimate_time.py --model anotherjesse/zeroscope-v2-xl --no-log-data
        """
    )
    
    parser.add_argument("--model", default="anotherjesse/zeroscope-v2-xl", help="Replicate model")
    parser.add_argument("--num-frames", type=int, default=24, help="Number of frames")
    parser.add_argument("--width", type=int, default=576, help="Video width")
    parser.add_argument("--height", type=int, default=320, help="Video height")
    parser.add_argument("--no-log-data", action="store_true", help="Don't use historical log data")
    
    args = parser.parse_args()
    
    estimate = estimate_time(
        model=args.model,
        num_frames=args.num_frames,
        width=args.width,
        height=args.height,
        use_log_data=not args.no_log_data,
    )
    
    print(f"\n⏱️  Time Estimate for {estimate['model']}")
    print(f"   Parameters: {estimate['num_frames']} frames @ {estimate['resolution']}")
    print()
    print(f"   Typical: {format_time(estimate['typical'])} ({estimate['typical']:.1f}s)")
    print(f"   Fast:    {format_time(estimate['fast'])} ({estimate['fast']:.1f}s)")
    print(f"   Slow:    {format_time(estimate['slow'])} ({estimate['slow']:.1f}s)")
    print()
    
    if estimate['based_on'] == 'log_data':
        print(f"   📊 Based on {estimate['sample_count']} historical runs from api_calls.log")
    else:
        print(f"   📊 Based on known model estimates (no log data available)")
        print(f"   💡 Tip: Run some generations to build up historical data for better estimates")


if __name__ == "__main__":
    main()

