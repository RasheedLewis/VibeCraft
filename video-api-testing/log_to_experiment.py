#!/usr/bin/env python3
"""
Parse the last non-empty line from api_calls.log and append it to experiments/README.md
using the template format.
"""

import json
import re
from datetime import datetime
from pathlib import Path

LOG_FILE = "api_calls.log"
EXPERIMENTS_README = "experiments/README.md"


def get_last_log_entry(log_file: str) -> dict:
    """Get the last non-empty line from the log file."""
    if not Path(log_file).exists():
        raise FileNotFoundError(f"Log file not found: {log_file}")
    
    with open(log_file, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    if not lines:
        raise ValueError("No entries found in log file")
    
    last_line = lines[-1]
    
    # Parse format: timestamp | model | prompt | params | result | duration
    parts = last_line.split(" | ")
    if len(parts) < 6:
        raise ValueError(f"Invalid log format: {last_line}")
    
    timestamp_str = parts[0]
    model = parts[1]
    prompt = parts[2]
    params_str = parts[3]
    result = parts[4]
    duration_str = parts[5].rstrip("s")
    
    # Parse parameters JSON
    try:
        params = json.loads(params_str)
    except json.JSONDecodeError:
        params = {}
    
    # Parse duration
    try:
        duration = float(duration_str)
    except ValueError:
        duration = None
    
    # Parse timestamp
    try:
        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        timestamp = None
    
    return {
        "timestamp": timestamp,
        "timestamp_str": timestamp_str,
        "model": model,
        "prompt": prompt,
        "params": params,
        "result": result,
        "duration": duration,
    }


def format_experiment_entry(data: dict) -> str:
    """Format the log entry as an experiment entry using the simplified template."""
    # Generate experiment name from timestamp
    if data["timestamp"]:
        exp_name = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
    else:
        exp_name = data["timestamp_str"]
    
    # Extract parameters
    num_frames = data["params"].get("num_frames", "N/A")
    fps = data["params"].get("fps", "N/A")
    width = data["params"].get("width", "N/A")
    height = data["params"].get("height", "N/A")
    seed = data["params"].get("seed")
    
    # Format parameters line
    params_parts = []
    if num_frames != "N/A" and fps != "N/A":
        params_parts.append(f"{num_frames} frames @ {fps}fps")
    resolution = f"{width}x{height}" if width != "N/A" and height != "N/A" else None
    if resolution:
        params_parts.append(resolution)
    if seed is not None:
        params_parts.append(f"seed: {seed}")
    params_str = ", ".join(params_parts) if params_parts else "N/A"
    
    # Calculate video duration from num_frames / fps
    if num_frames != "N/A" and fps != "N/A":
        try:
            video_duration = float(num_frames) / float(fps)
            video_duration_str = f"{video_duration:.1f}s"
        except (ValueError, TypeError):
            video_duration_str = "N/A"
    else:
        video_duration_str = "N/A"
    
    # Format API call duration
    if data["duration"]:
        api_duration_str = f"{data['duration']:.1f}s"
    else:
        api_duration_str = "N/A"
    
    # Get video URL or error
    is_success = data["result"].startswith("http")
    if is_success:
        video_url = data["result"]
    else:
        video_url = f"[Failed: {data['result']}]"
    
    entry = f"""## Experiment: {exp_name}

**Prompt:** {data['prompt']}  
**Model:** {data['model']}  
**Parameters:** {params_str}  
**Video URL:** {video_url}  
**Video Duration:** {video_duration_str} (calculated from frames/fps)  
**API Call Duration:** {api_duration_str}  
**Observations:** [Your notes about quality, style, what worked/didn't work]

"""
    
    return entry


def append_to_experiments_readme(entry: str, readme_file: str):
    """Append the experiment entry to the experiments README."""
    Path(readme_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing content
    if Path(readme_file).exists():
        with open(readme_file, "r") as f:
            content = f.read()
    else:
        content = "# Experiment Logs\n\n"
    
    # Append new entry
    content += entry
    
    # Write back
    with open(readme_file, "w") as f:
        f.write(content)


def main():
    try:
        # Get last log entry
        data = get_last_log_entry(LOG_FILE)
        
        # Format as experiment entry
        entry = format_experiment_entry(data)
        
        # Append to experiments README
        append_to_experiments_readme(entry, EXPERIMENTS_README)
        
        print(f"✅ Added experiment entry to {EXPERIMENTS_README}")
        print(f"   Timestamp: {data['timestamp_str']}")
        print(f"   Model: {data['model']}")
        print(f"   Prompt: {data['prompt'][:50]}...")
        print(f"   Result: {'Success' if data['result'].startswith('http') else 'Failed'}")
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("   Make sure you've run at least one video generation.")
    except ValueError as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

