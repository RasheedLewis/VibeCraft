# Video Generation API Testing

Standalone testing environment for experimenting with video generation APIs and prompts.

**Goal:** Generate cool-looking videos by testing different APIs, models, and prompts.

## Features

Multiple testing modes (single video, batch, interactive). Full parameter control for model,
resolution, frames, and FPS. Automatic timing and logging of all API calls to `api_calls.log`
with timestamps, parameters, results, and duration. Completely independent from the main
VibeCraft codebase.

## Usage

### Quick Test

```bash
# Uses default model (minimax/hailuo-2.3) with default parameters
python test_video.py "A futuristic cityscape at sunset with neon lights"

# Or specify a different model
python test_video.py "A futuristic cityscape at sunset with neon lights" --model anotherjesse/zeroscope-v2-xl
```

### Test with Custom Parameters

```bash
# Minimax model (default)
python test_video.py "Your prompt here" --model minimax/hailuo-2.3 --duration 6 --resolution 768p

# Zeroscope-style model
python test_video.py "Your prompt here" --model anotherjesse/zeroscope-v2-xl --num-frames 144 --width 1024 --height 576
```

### Test Multiple Prompts

```bash
python test_batch.py prompts.txt
```

### Interactive Mode

```bash
python test_interactive.py
```

## Script Flags & API Parameters Reference

**Important:** Different models use different parameter schemas. The script automatically detects
the model type and uses the appropriate parameters. Always check a model's schema with
`check_model_schema.py` to see what parameters it accepts.

### test_video.py

Generate a single video with a prompt.

**Positional Arguments:**

- `prompt` - Text prompt for video generation (required)

**Model Selection:**

- `--model` - Replicate model identifier (default: `minimax/hailuo-2.3`)

**Zeroscope/Luma-style Parameters** (for models like `anotherjesse/zeroscope-v2-xl`, `luma/ray`, etc.):

- `--num-frames` - Number of frames to generate (default: 144 for 6s @ 24fps)
- `--fps` - Frames per second (default: 24)
- `--width` - Video width in pixels (default: 576)
- `--height` - Video height in pixels (default: 320)
- `--seed` - Random seed for reproducibility (optional)

**Minimax/Hailuo Model Parameters** (for models like `minimax/hailuo-2.3`):

- `--duration` - Video duration in seconds (default: 6, model default)
- `--resolution` - Resolution: `768p` or `1080p` (default: 768p, model default)
- `--prompt-optimizer` - Enable prompt optimizer (default: True, model default)
- `--no-prompt-optimizer` - Disable prompt optimizer
- `--first-frame-image` - First frame image URL (optional)

**Common Flags:**

- `--output-dir` - Directory to save metadata (default: `output`)

**Examples:**

Minimax model (default):

```bash
python test_video.py "Neon cityscape" --model minimax/hailuo-2.3 --duration 6 --resolution 768p
python test_video.py "Neon cityscape" --model minimax/hailuo-2.3 --duration 10 --resolution 768p --no-prompt-optimizer
```

Zeroscope-style model:

```bash
python test_video.py "Neon cityscape" --model anotherjesse/zeroscope-v2-xl --num-frames 144 --width 1024 --height 576 --seed 42
```

### test_batch.py

Test multiple prompts from a file.

**Positional Arguments:**

- `file` - Text file with one prompt per line (required)

**Optional Flags:**

- `--model` - Replicate model identifier
- Zeroscope/Luma-style parameters: `--num-frames`, `--fps`, `--width`, `--height`, `--seed`
- Minimax/Hailuo parameters: `--duration`, `--resolution`, `--prompt-optimizer`, `--no-prompt-optimizer`
- `--delay` - Delay between generations in seconds (default: 2.0)

**Examples:**

```bash
# Minimax model (default)
python test_batch.py prompts.txt --model minimax/hailuo-2.3 --duration 6 --resolution 768p

# Zeroscope-style model
python test_batch.py prompts.txt --model anotherjesse/zeroscope-v2-xl --num-frames 144 --width 1024 --height 576
```

### test_interactive.py

Interactive prompt testing mode. No command-line flags. Use commands within the interactive session:

- `model <name>` - Change model
- `frames <n>` - Change num_frames (for Zeroscope/Luma-style models)
- `fps <n>` - Change fps (for Zeroscope/Luma-style models)
- `width <n>` - Change video width (for Zeroscope/Luma-style models)
- `height <n>` - Change video height (for Zeroscope/Luma-style models)
- `seed <n>` - Set seed (for Zeroscope/Luma-style models)
- `clear` - Clear seed
- `show` - Show current settings
- `quit` or `exit` - Exit

### test_seed_variations.py

Test the same prompt with multiple seeds. Note: Only works with models that support the `seed`
parameter (Zeroscope/Luma-style models, not minimax/hailuo).

**Positional Arguments:**

- `prompt` - Text prompt to test with different seeds (required)

**Optional Flags:**

- `--model` - Replicate model identifier
- Zeroscope/Luma-style parameters: `--num-frames`, `--fps`, `--width`, `--height`
- `--seeds` - Comma-separated list of seeds (e.g., `1,2,3,4,5`)
- `--count` - Number of seeds to test if `--seeds` not provided (default: 3)
- `--start-seed` - Starting seed number if `--seeds` not provided (default: 1)
- `--delay` - Delay between generations in seconds (default: 2.0)

**Example:**

```bash
python test_seed_variations.py "Abstract shapes" --seeds 1,2,3,4,5 --width 1024 --height 576
python test_seed_variations.py "Neon cityscape" --count 5 --start-seed 10
```

## API Parameters

Different models use different parameter schemas. The script automatically maps command-line
flags to the appropriate API parameters based on the model.

**Zeroscope/Luma-style Models** (e.g., `anotherjesse/zeroscope-v2-xl`, `luma/ray`):

- `prompt` (string, required) - Text description of the video to generate
- `num_frames` (integer) - Number of frames in the video
- `fps` (integer) - Frames per second (typically 8, 24, or 30)
- `width` (integer) - Video width in pixels
- `height` (integer) - Video height in pixels
- `seed` (integer, optional) - Random seed for reproducibility

**Minimax/Hailuo Models** (e.g., `minimax/hailuo-2.3`):

- `prompt` (string, required) - Text description of the video to generate
- `duration` (integer) - Video duration in seconds (default: 6)
- `resolution` (string) - Resolution: `768p` or `1080p` (default: `768p`)
- `prompt_optimizer` (boolean) - Use prompt optimizer (default: `true`)
- `first_frame_image` (string, optional) - First frame image URL

**Key Differences:**

- **Zeroscope/Luma-style models** use frame-based control (`num_frames`, `fps`) and pixel
  dimensions (`width`, `height`)
- **Minimax/Hailuo models** use duration-based control (`duration` in seconds) and preset
  resolutions (`768p`, `1080p`)
- **Zeroscope/Luma-style models** support `seed` for reproducibility; **Minimax/Hailuo models**
  do not

**Always check a model's schema:**

```bash
python check_model_schema.py <model-name>
```

## Setup

These scripts use the root project's `.venv` (no separate virtual environment needed).

**Dependencies:**

- `replicate>=0.25.0`
- `python-dotenv>=1.0.0`

Both are already installed in the root `.venv`.

**Environment:**
Create a `.env` file in this directory (or use the root `.env`) with:

```env
REPLICATE_API_TOKEN=your_token_here
```

## Logging

All API calls are automatically logged to `api_calls.log` with:

- Timestamp
- Model used
- Prompt (truncated to 100 chars)
- Parameters (JSON format)
- Result (video URL or error message)
- Duration in seconds

Example log entry:

```text
2024-01-15 14:30:25 | minimax/hailuo-2.3 | A futuristic cityscape at sunset... | {"duration":6,"prompt":"A futuristic cityscape at sunset","resolution":"768p"} | https://replicate.delivery/... | 45.23s
```

The log file is automatically created and appended to. You can analyze it to track:

- Which prompts/models work best
- Average generation times
- Success/failure rates
- Parameter combinations that produce good results

## Understanding the `seed` Parameter

The `seed` is a number that initializes the model's random number generator, controlling
randomness in video generation.

### How It Works

- **Same prompt + same seed + same parameters** = Same (or very similar) output
- **Same prompt + different seed** = Different variations of the same concept
- **No seed** = Random output each time

### When to Use Seed

**1. For Style Consistency (Main Use Case)**
If generating multiple clips for the same song/video, use the same seed across all clips to
maintain visual coherence:

```bash
python test_video.py "Neon cityscape" --seed 42
python test_video.py "Neon cityscape at night" --seed 42
python test_video.py "Neon cityscape with rain" --seed 42
```

**2. For Experimentation**
Try different seeds with the same prompt to see variations:

```bash
python test_video.py "Abstract shapes floating" --seed 1
python test_video.py "Abstract shapes floating" --seed 2
python test_video.py "Abstract shapes floating" --seed 3
```

**3. For Reproducibility**
If you find a result you like, save the seed to regenerate it later.

**Note:** Seed only works with Zeroscope/Luma-style models. Minimax/Hailuo models do not
support seed parameters.

### test_rapid_iteration.py

Interactive rapid iteration testing for prompt experimentation. Generate 4-second videos on demand.

**Positional Arguments:**

- `prompt` - Base prompt for video generation (optional, can be set interactively)

**Optional Flags:**

- `--model` - Replicate model identifier (default: `minimax/hailuo-2.3`)

**Features:**

- Interactive mode: Press ENTER to generate another video
- Generates 4-second clips for fast iteration
- Logs full prompts (not truncated) to `rapid_iteration.log` in JSON format
- Tracks success/failure rates
- Optimized for speed (uses 768p resolution for minimax models)
- Change prompt/model on the fly

**Commands:**

- Press **ENTER** - Generate another video
- `prompt <text>` - Change the prompt
- `model <name>` - Change the model
- `show` - Show current settings
- `quit` or `exit` - Exit

**Example:**

```bash
# Start with a prompt
python test_rapid_iteration.py "A futuristic cityscape"

# Or start without a prompt (will prompt you)
python test_rapid_iteration.py

# Then interactively:
> [Press ENTER to generate]
> prompt A neon-lit Tokyo street at night
> [Press ENTER to generate with new prompt]
> show
> quit
```

**Log Format:**

Each iteration is logged as a JSON object with:

- `iteration`: Iteration number
- `timestamp`: ISO timestamp
- `model`: Model used
- `prompt`: Full prompt (not truncated)
- `parameters`: Full parameter dict
- `result`: Video URL or error message
- `duration_sec`: Generation duration

## File Structure

- `test_video.py` - Single video generation script
- `test_batch.py` - Batch testing from file
- `test_interactive.py` - Interactive prompt testing
- `test_seed_variations.py` - Test same prompt with multiple seeds
- `test_rapid_iteration.py` - Rapid iteration testing (50 iterations, 4s clips, full prompt logging)
- `requirements.txt` - Python dependencies
- `output/` - Generated videos metadata (gitignored)
- `api_calls.log` - Automatic log of all API calls with timing (gitignored)
- `rapid_iteration.log` - Full prompt logs for rapid iteration testing (gitignored)
