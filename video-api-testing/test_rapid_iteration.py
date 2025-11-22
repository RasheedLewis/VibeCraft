#!/usr/bin/env python3
"""
Rapid iteration testing script for prompt experimentation.
Generates 50 videos with 4-second clips for fast iteration.
Logs full prompts for analysis.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import replicate
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Default model
DEFAULT_MODEL = "minimax/hailuo-2.3"

# Log file path
LOG_FILE = "rapid_iteration.log"


def log_full_prompt(
    iteration: int,
    model: str,
    prompt: str,
    params: dict,
    result: str,
    duration_sec: float,
    log_file: str = LOG_FILE,
):
    """
    Log a full prompt iteration with all details.
    
    Format: JSON with full prompt, parameters, and results.
    """
    log_entry = {
        "iteration": iteration,
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "prompt": prompt,  # Full prompt, not truncated
        "parameters": params,
        "result": result,
        "duration_sec": round(duration_sec, 2),
    }
    
    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"⚠️  Warning: Could not write to log file: {e}")


def generate_video_4s(
    prompt: str,
    model: str = DEFAULT_MODEL,
    iteration: int = 1,
):
    """
    Generate a 4-second video for rapid iteration.
    
    Args:
        prompt: Text prompt for video generation
        model: Replicate model identifier
        iteration: Iteration number for logging
    
    Returns:
        Video URL if successful, None otherwise
    """
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("ERROR: REPLICATE_API_TOKEN not found in environment")
        return None

    print(f"\n[{iteration}/50] 🎬 Generating 4s video")
    print(f"📝 Prompt: {prompt}")
    print(f"🤖 Model: {model}")

    # Start timing
    start_time = time.time()
    
    try:
        client = replicate.Client(api_token=api_token)
        model_obj = client.models.get(model)
        version = model_obj.latest_version
        
        # Build input parameters for 4-second generation
        # Minimax/Hailuo models use duration parameter
        if "minimax" in model.lower() or "hailuo" in model.lower():
            input_params = {
                "prompt": prompt,
                "duration": 4,  # 4 seconds for rapid iteration
                "resolution": "768p",  # Use 768p for faster generation
                "prompt_optimizer": True,
            }
        else:
            # Zeroscope/Luma-style models use num_frames
            # 4 seconds @ 24fps = 96 frames
            input_params = {
                "prompt": prompt,
                "num_frames": 96,
                "fps": 24,
                "width": 768,
                "height": 432,
            }
        
        print(f"⚙️  Parameters: {json.dumps(input_params, indent=2)}")
        
        prediction = client.predictions.create(
            version=version,
            input=input_params,
        )
        
        print(f"🔄 Job ID: {prediction.id}")
        print("⏳ Waiting for generation...", end="", flush=True)
        
        # Poll for completion
        max_attempts = 180  # 15 minutes max
        for attempt in range(max_attempts):
            time.sleep(5)
            prediction = client.predictions.get(prediction.id)
            
            if prediction.status == "succeeded":
                print(" ✅")
                video_url = None
                if prediction.output:
                    if isinstance(prediction.output, str):
                        video_url = prediction.output
                    elif isinstance(prediction.output, list) and len(prediction.output) > 0:
                        video_url = prediction.output[0]
                    elif isinstance(prediction.output, dict) and "video" in prediction.output:
                        video_url = prediction.output["video"]
                
                duration_sec = time.time() - start_time
                print(f"✅ Success! Duration: {duration_sec:.2f}s")
                if video_url:
                    print(f"🎥 Video: {video_url}")
                
                log_full_prompt(
                    iteration=iteration,
                    model=model,
                    prompt=prompt,
                    params=input_params,
                    result=video_url or "No video URL",
                    duration_sec=duration_sec,
                )
                return video_url
            elif prediction.status == "failed":
                print(" ❌")
                error = getattr(prediction, "error", "Unknown error")
                print(f"❌ Failed: {error}")
                duration_sec = time.time() - start_time
                log_full_prompt(
                    iteration=iteration,
                    model=model,
                    prompt=prompt,
                    params=input_params,
                    result=f"FAILED: {error}",
                    duration_sec=duration_sec,
                )
                return None
            else:
                print(".", end="", flush=True)
        
        # Timeout
        print(" ⏱️")
        print(f"⏱️  Timeout after {max_attempts * 5} seconds")
        duration_sec = time.time() - start_time
        log_full_prompt(
            iteration=iteration,
            model=model,
            prompt=prompt,
            params=input_params,
            result=f"TIMEOUT: {prediction.status}",
            duration_sec=duration_sec,
        )
        return None
        
    except Exception as e:
        duration_sec = time.time() - start_time
        print(f"\n❌ Exception: {e}")
        log_full_prompt(
            iteration=iteration,
            model=model,
            prompt=prompt,
            params={},
            result=f"EXCEPTION: {str(e)}",
            duration_sec=duration_sec,
        )
        return None


def main():
    """Run 50 iterations of video generation."""
    parser = argparse.ArgumentParser(
        description="Rapid iteration testing: Generate 50 videos with 4-second clips"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Base prompt for video generation (can be modified per iteration)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Replicate model identifier (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=50,
        help="Number of iterations to run (default: 50)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between iterations in seconds (default: 2.0)",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 RAPID ITERATION TESTING")
    print("=" * 80)
    print(f"📝 Base Prompt: {args.prompt}")
    print(f"🤖 Model: {args.model}")
    print(f"⏱️  Duration: 4 seconds per clip")
    print(f"🔄 Iterations: {args.iterations}")
    print(f"⏸️  Delay: {args.delay}s between iterations")
    print(f"📊 Log File: {LOG_FILE}")
    print("=" * 80)
    
    # Clear or create log file
    if Path(LOG_FILE).exists():
        print(f"\n⚠️  Log file {LOG_FILE} already exists. Appending to it.")
    else:
        print(f"\n📝 Creating new log file: {LOG_FILE}")
    
    # Run iterations
    successful = 0
    failed = 0
    
    for i in range(1, args.iterations + 1):
        # Use the same prompt for all iterations (can be modified later)
        result = generate_video_4s(
            prompt=args.prompt,
            model=args.model,
            iteration=i,
        )
        
        if result:
            successful += 1
        else:
            failed += 1
        
        # Delay between iterations (except after last one)
        if i < args.iterations:
            print(f"⏸️  Waiting {args.delay}s before next iteration...")
            time.sleep(args.delay)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {successful}/{args.iterations}")
    print(f"❌ Failed: {failed}/{args.iterations}")
    print(f"📊 Success Rate: {(successful/args.iterations)*100:.1f}%")
    print(f"📝 Full logs saved to: {LOG_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    main()

