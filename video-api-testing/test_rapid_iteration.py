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
    """Interactive rapid iteration testing - manually trigger each video."""
    parser = argparse.ArgumentParser(
        description="Interactive rapid iteration testing: Generate 4-second videos on demand"
    )
    parser.add_argument(
        "prompt",
        type=str,
        nargs="?",
        default=None,
        help="Base prompt for video generation (optional, can be set interactively)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Replicate model identifier (default: {DEFAULT_MODEL})",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 INTERACTIVE RAPID ITERATION TESTING")
    print("=" * 80)
    print(f"🤖 Model: {args.model}")
    print(f"⏱️  Duration: 4 seconds per clip")
    print(f"📊 Log File: {LOG_FILE}")
    print("=" * 80)
    print("\n📖 Commands:")
    print("  - Press ENTER to generate another video")
    print("  - Type 'prompt <text>' to change the prompt")
    print("  - Type 'model <name>' to change the model")
    print("  - Type 'show' to show current settings")
    print("  - Type 'quit' or 'exit' to exit")
    print("=" * 80)
    
    # Initialize settings
    current_prompt = args.prompt
    current_model = args.model
    iteration = 0
    successful = 0
    failed = 0
    
    # Get initial prompt if not provided
    if not current_prompt:
        current_prompt = input("\n📝 Enter initial prompt: ").strip()
        if not current_prompt:
            print("❌ Prompt is required. Exiting.")
            return
    
    # Clear or create log file
    if Path(LOG_FILE).exists():
        print(f"\n⚠️  Log file {LOG_FILE} already exists. Appending to it.")
    else:
        print(f"\n📝 Creating new log file: {LOG_FILE}")
    
    print(f"\n✅ Ready! Current prompt: {current_prompt}")
    print("Press ENTER to generate a video, or type a command.\n")
    
    # Interactive loop
    while True:
        try:
            user_input = input("> ").strip()
            
            if not user_input:
                # Empty input = generate video
                iteration += 1
                result = generate_video_4s(
                    prompt=current_prompt,
                    model=current_model,
                    iteration=iteration,
                )
                
                if result:
                    successful += 1
                else:
                    failed += 1
                
                print(f"\n📊 Stats: {successful} successful, {failed} failed (iteration {iteration})")
                print("Press ENTER for another video, or type a command.\n")
                
            elif user_input.lower() in ["quit", "exit", "q"]:
                break
                
            elif user_input.lower().startswith("prompt "):
                new_prompt = user_input[7:].strip()
                if new_prompt:
                    current_prompt = new_prompt
                    print(f"✅ Prompt updated: {current_prompt}\n")
                else:
                    print("❌ Please provide a prompt: 'prompt <text>'\n")
                    
            elif user_input.lower().startswith("model "):
                new_model = user_input[6:].strip()
                if new_model:
                    current_model = new_model
                    print(f"✅ Model updated: {current_model}\n")
                else:
                    print("❌ Please provide a model: 'model <name>'\n")
                    
            elif user_input.lower() == "show":
                print(f"\n📋 Current Settings:")
                print(f"  Prompt: {current_prompt}")
                print(f"  Model: {current_model}")
                print(f"  Iteration: {iteration}")
                print(f"  Successful: {successful}")
                print(f"  Failed: {failed}")
                print()
                
            else:
                print("❌ Unknown command. Press ENTER to generate, or type 'quit' to exit.\n")
                
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except EOFError:
            print("\n\n⚠️  End of input")
            break
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    total = successful + failed
    if total > 0:
        print(f"✅ Successful: {successful}/{total}")
        print(f"❌ Failed: {failed}/{total}")
        print(f"📊 Success Rate: {(successful/total)*100:.1f}%")
    print(f"📝 Full logs saved to: {LOG_FILE}")
    print("=" * 80)


if __name__ == "__main__":
    main()

