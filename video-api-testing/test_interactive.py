#!/usr/bin/env python3
"""
Interactive script for testing video generation prompts.
Quick iteration on prompts without typing command-line arguments each time.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Import the generation function from test_video
sys.path.insert(0, str(Path(__file__).parent))
from test_video import generate_video, DEFAULT_MODEL

load_dotenv()


def main():
    print("=" * 60)
    print("🎬 Interactive Video Generation Tester")
    print("=" * 60)
    print()
    print("Enter prompts to test. Commands:")
    print("  'quit' or 'exit' - Exit")
    print("  'model <name>' - Change model (default: minimax/hailuo-2.3)")
    print("  'frames <n>' - Change num_frames (default: 144 for 6s @ 24fps)")
    print("  'fps <n>' - Change fps (default: 24)")
    print("  'width <n>' - Change video width (default: 576)")
    print("  'height <n>' - Change video height (default: 320)")
    print("  'seed <n>' - Set seed (default: random)")
    print("  'clear' - Clear seed")
    print("  'show' - Show current settings")
    print()
    
    current_model = DEFAULT_MODEL
    current_frames = 144
    current_fps = 24
    current_width = 576
    current_height = 320
    current_seed = None
    
    while True:
        try:
            user_input = input(f"\n[{current_model} | {current_width}x{current_height} | {current_frames}f@{current_fps}fps] Prompt: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break
                
            if user_input.lower().startswith("model "):
                current_model = user_input[6:].strip()
                print(f"✅ Model set to: {current_model}")
                continue
                
            if user_input.lower().startswith("frames "):
                try:
                    current_frames = int(user_input[7:].strip())
                    print(f"✅ Frames set to: {current_frames}")
                except ValueError:
                    print("❌ Invalid number")
                continue
                
            if user_input.lower().startswith("fps "):
                try:
                    current_fps = int(user_input[4:].strip())
                    print(f"✅ FPS set to: {current_fps}")
                except ValueError:
                    print("❌ Invalid number")
                continue
                
            if user_input.lower().startswith("width "):
                try:
                    current_width = int(user_input[6:].strip())
                    print(f"✅ Width set to: {current_width}")
                except ValueError:
                    print("❌ Invalid number")
                continue
                
            if user_input.lower().startswith("height "):
                try:
                    current_height = int(user_input[7:].strip())
                    print(f"✅ Height set to: {current_height}")
                except ValueError:
                    print("❌ Invalid number")
                continue
                
            if user_input.lower().startswith("seed "):
                try:
                    current_seed = int(user_input[5:].strip())
                    print(f"✅ Seed set to: {current_seed}")
                except ValueError:
                    print("❌ Invalid seed (must be integer)")
                continue
                
            if user_input.lower() == "clear":
                current_seed = None
                print("✅ Seed cleared")
                continue
                
            if user_input.lower() == "show":
                print(f"\n📋 Current Settings:")
                print(f"  Model: {current_model}")
                print(f"  Frames: {current_frames}")
                print(f"  FPS: {current_fps}")
                print(f"  Resolution: {current_width}x{current_height}")
                print(f"  Seed: {current_seed if current_seed is not None else 'random'}")
                continue
            
            # Generate video with current settings
            print()
            video_url = generate_video(
                prompt=user_input,
                model=current_model,
                num_frames=current_frames,
                fps=current_fps,
                width=current_width,
                height=current_height,
                seed=current_seed,
            )
            
            if video_url:
                print(f"\n✅ Generated! URL: {video_url}")
            else:
                print(f"\n❌ Generation failed")
                
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except EOFError:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

