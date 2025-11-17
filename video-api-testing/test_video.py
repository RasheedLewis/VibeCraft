#!/usr/bin/env python3
"""
Simple script to test Replicate video generation API with a prompt.
Completely independent of the main VibeCraft codebase.
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
DEFAULT_MODEL = "anotherjesse/zeroscope-v2-xl"

# Log file path
LOG_FILE = "api_calls.log"


def log_api_call(
    model: str,
    prompt: str,
    params: dict,
    result: str,
    duration_sec: float,
    log_file: str = LOG_FILE,
):
    """
    Log an API call to a log file.
    
    Format: timestamp | model | prompt | params | result | duration_sec
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format params as compact string
    params_str = json.dumps(params, sort_keys=True, separators=(',', ':'))
    
    # Truncate long prompts for readability
    prompt_short = prompt[:100] + "..." if len(prompt) > 100 else prompt
    
    log_line = f"{timestamp} | {model} | {prompt_short} | {params_str} | {result} | {duration_sec:.2f}s"
    
    try:
        with open(log_file, "a") as f:
            f.write(log_line + "\n")
    except Exception as e:
        print(f"⚠️  Warning: Could not write to log file: {e}")


def generate_video(
    prompt: str,
    model: str = DEFAULT_MODEL,
    num_frames: int = 24,
    fps: int = 8,
    width: int = 576,
    height: int = 320,
    seed: int = None,
    output_dir: str = "output",
    # Minimax/Hailuo parameters
    duration: int = None,
    resolution: str = None,
    prompt_optimizer: bool = None,
    first_frame_image: str = None,
):
    """
    Generate a video using Replicate API.
    
    Args:
        prompt: Text prompt for video generation
        model: Replicate model identifier (e.g., "anotherjesse/zeroscope-v2-xl")
        num_frames: Number of frames to generate
        fps: Frames per second
        width: Video width
        height: Video height
        seed: Optional seed for reproducibility
        output_dir: Directory to save metadata (videos are hosted by Replicate)
    
    Returns:
        Video URL if successful, None otherwise
    """
    api_token = os.getenv("REPLICATE_API_TOKEN")
    if not api_token:
        print("ERROR: REPLICATE_API_TOKEN not found in environment")
        print("Create a .env file with your token or export it:")
        print("  export REPLICATE_API_TOKEN=your_token_here")
        return None

    print(f"\n🎬 Generating video with model: {model}")
    print(f"📝 Prompt: {prompt}")
    
    # Start timing
    start_time = time.time()
    
    # Prepare input parameters based on model type
    input_params = {"prompt": prompt}
    
    # Check if this is a minimax/hailuo model
    if "minimax" in model.lower() or "hailuo" in model.lower():
        # Minimax/Hailuo schema: duration, resolution, prompt_optimizer
        # Use defaults if not specified (model defaults: duration=6, resolution=768p, prompt_optimizer=True)
        input_params["duration"] = duration if duration is not None else 6
        input_params["resolution"] = resolution if resolution is not None else "768p"
        input_params["prompt_optimizer"] = prompt_optimizer if prompt_optimizer is not None else True
        if first_frame_image is not None:
            input_params["first_frame_image"] = first_frame_image
        
        params_str = f"duration: {input_params['duration']}s, resolution: {input_params['resolution']}"
        params_str += f", prompt_optimizer: {input_params['prompt_optimizer']}"
        print(f"⚙️  Parameters: {params_str}")
    else:
        # Standard schema: num_frames, fps, width, height, seed
        input_params["num_frames"] = num_frames
        input_params["width"] = width
        input_params["height"] = height
        input_params["fps"] = fps
        if seed is not None:
            input_params["seed"] = seed
        
        params_str = f"{num_frames} frames @ {fps} fps, {width}x{height}"
        if seed:
            params_str += f", seed: {seed}"
        print(f"⚙️  Parameters: {params_str}")
    print()

    try:
        client = replicate.Client(api_token=api_token)
        
        # Get model version
        model_obj = client.models.get(model)
        version = model_obj.latest_version
        
        print("🚀 Starting generation...")
        prediction = client.predictions.create(
            version=version,
            input=input_params,
        )

        job_id = prediction.id
        print(f"📋 Job ID: {job_id}")
        print("⏳ Waiting for completion...")

        # Poll for completion
        max_attempts = 180
        poll_interval = 5.0
        
        for attempt in range(max_attempts):
            prediction = client.predictions.get(job_id)
            
            if prediction.status == "succeeded":
                # Extract video URL
                video_url = None
                if prediction.output:
                    if isinstance(prediction.output, str):
                        video_url = prediction.output
                    elif isinstance(prediction.output, list) and len(prediction.output) > 0:
                        video_url = prediction.output[0]
                    elif isinstance(prediction.output, dict) and "video" in prediction.output:
                        video_url = prediction.output["video"]
                
                # Calculate duration
                duration_sec = time.time() - start_time
                
                if video_url:
                    print(f"\n✅ Success! Video URL: {video_url}")
                    print(f"⏱️  Duration: {duration_sec:.2f} seconds")
                    
                    # Save metadata
                    save_metadata(
                        output_dir,
                        prompt,
                        model,
                        video_url,
                        input_params,
                        job_id,
                    )
                    
                    # Log successful call
                    log_api_call(model, prompt, input_params, video_url, duration_sec)
                    
                    return video_url
                else:
                    print(f"\n❌ Generation succeeded but no video URL in output")
                    print(f"Output: {prediction.output}")
                    duration_sec = time.time() - start_time
                    log_api_call(model, prompt, input_params, f"ERROR: No video URL in output", duration_sec)
                    return None
                    
            elif prediction.status == "failed":
                error = getattr(prediction, "error", "Unknown error")
                duration_sec = time.time() - start_time
                print(f"\n❌ Generation failed: {error}")
                print(f"⏱️  Duration: {duration_sec:.2f} seconds")
                log_api_call(model, prompt, input_params, f"FAILED: {error}", duration_sec)
                return None
                
            elif prediction.status in ["starting", "processing"]:
                elapsed = (attempt + 1) * poll_interval
                print(f"⏳ Status: {prediction.status} (~{elapsed:.0f}s elapsed)", end="\r")
                time.sleep(poll_interval)
            else:
                print(f"⚠️  Unknown status: {prediction.status}")
                time.sleep(poll_interval)

        # Timeout
        duration_sec = time.time() - start_time
        print(f"\n⏱️  Timeout after {max_attempts * poll_interval / 60:.1f} minutes")
        final_prediction = client.predictions.get(job_id)
        print(f"Final status: {final_prediction.status}")
        print(f"⏱️  Duration: {duration_sec:.2f} seconds")
        log_api_call(model, prompt, input_params, f"TIMEOUT: {final_prediction.status}", duration_sec)
        return None

    except Exception as e:
        duration_sec = time.time() - start_time
        print(f"\n❌ Error: {e}")
        print(f"⏱️  Duration: {duration_sec:.2f} seconds")
        log_api_call(model, prompt, input_params, f"EXCEPTION: {str(e)}", duration_sec)
        import traceback
        traceback.print_exc()
        return None


def save_metadata(output_dir: str, prompt: str, model: str, video_url: str, params: dict, job_id: str):
    """Save experiment metadata to a file."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/experiment_{timestamp}.txt"
    
    with open(filename, "w") as f:
        f.write(f"Experiment: {timestamp}\n")
        f.write(f"Model: {model}\n")
        f.write(f"Job ID: {job_id}\n")
        f.write(f"Video URL: {video_url}\n")
        f.write(f"\nPrompt:\n{prompt}\n")
        f.write(f"\nParameters:\n")
        for key, value in params.items():
            f.write(f"  {key}: {value}\n")
    
    print(f"💾 Metadata saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Test Replicate video generation API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_video.py "A futuristic cityscape at sunset"
  python test_video.py "Neon lights in Tokyo" --model anotherjesse/zeroscope-v2-xl --num-frames 48
  python test_video.py "Abstract shapes floating" --seed 42 --width 1024 --height 576
  python test_video.py "Neon cityscape" --model minimax/hailuo-2.3 --duration 6 --resolution 768p
        """
    )
    
    parser.add_argument("prompt", help="Text prompt for video generation")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Replicate model (default: {DEFAULT_MODEL})")
    
    # Standard parameters (for zeroscope, etc.)
    parser.add_argument("--num-frames", type=int, default=24, help="Number of frames (default: 24, for standard models)")
    parser.add_argument("--fps", type=int, default=8, help="Frames per second (default: 8, for standard models)")
    parser.add_argument("--width", type=int, default=576, help="Video width (default: 576, for standard models)")
    parser.add_argument("--height", type=int, default=320, help="Video height (default: 320, for standard models)")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility (for standard models)")
    
    # Minimax/Hailuo parameters
    parser.add_argument("--duration", type=int, help="Video duration in seconds (for minimax/hailuo models, default: 6)")
    parser.add_argument("--resolution", type=str, help="Resolution: 768p or 1080p (for minimax/hailuo models, default: 768p)")
    parser.add_argument("--prompt-optimizer", action="store_true", default=None, help="Enable prompt optimizer (for minimax/hailuo models)")
    parser.add_argument("--no-prompt-optimizer", dest="prompt_optimizer", action="store_false", help="Disable prompt optimizer (for minimax/hailuo models)")
    parser.add_argument("--first-frame-image", type=str, help="First frame image URL (for minimax/hailuo models)")
    
    parser.add_argument("--output-dir", default="output", help="Output directory for metadata (default: output)")
    
    args = parser.parse_args()
    
    # prompt_optimizer will be True, False, or None
    prompt_optimizer = args.prompt_optimizer
    
    video_url = generate_video(
        prompt=args.prompt,
        model=args.model,
        num_frames=args.num_frames,
        fps=args.fps,
        width=args.width,
        height=args.height,
        seed=args.seed,
        output_dir=args.output_dir,
        duration=args.duration,
        resolution=args.resolution,
        prompt_optimizer=prompt_optimizer,
        first_frame_image=args.first_frame_image,
    )
    
    if video_url:
        print(f"\n🎉 Done! Open the video URL in your browser to view it.")
        sys.exit(0)
    else:
        print(f"\n💥 Failed to generate video")
        sys.exit(1)


if __name__ == "__main__":
    main()

