# Video Generation API Testing

Standalone testing environment for experimenting with video generation APIs and prompts.

**Goal:** Generate cool-looking videos by testing different APIs, models, and prompts.

## Features

Multiple testing modes (single video, batch, interactive). Full parameter control for model, resolution, frames, and FPS. Automatic timing and logging of all API calls to `api_calls.log` with timestamps, parameters, results, and duration. Completely independent from the main VibeCraft codebase. Setup instructions near the end.

## Usage

### Quick Test
```bash
# Uses default model (anotherjesse/zeroscope-v2-xl) with default parameters
python test_video.py "A futuristic cityscape at sunset with neon lights"

# Or specify a different model
python test_video.py "A futuristic cityscape at sunset with neon lights" --model minimax/hailuo-2.3
```

### Test with Custom Parameters
```bash
# Zeroscope-style model
python test_video.py "Your prompt here" --model anotherjesse/zeroscope-v2-xl --num-frames 24 --width 1024 --height 576

# Minimax model
python test_video.py "Your prompt here" --model minimax/hailuo-2.3 --duration 6 --resolution 768p
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

**Important:** Different models use different parameter schemas. The script automatically detects the model type and uses the appropriate parameters. Always check a model's schema with `check_model_schema.py` to see what parameters it accepts.

### test_video.py

Generate a single video with a prompt.

**Positional Arguments:**
- `prompt` - Text prompt for video generation (required)

**Model Selection:**
- `--model` - Replicate model identifier (default: `anotherjesse/zeroscope-v2-xl`)

**Zeroscope/Luma-style Parameters** (for models like `anotherjesse/zeroscope-v2-xl`, `luma/ray`, etc.):
- `--num-frames` - Number of frames to generate (default: 24)
- `--fps` - Frames per second (default: 8)
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

Zeroscope-style model:
```bash
python test_video.py "Neon cityscape" --model anotherjesse/zeroscope-v2-xl --num-frames 48 --width 1024 --height 576 --seed 42
```

Minimax model:
```bash
python test_video.py "Neon cityscape" --model minimax/hailuo-2.3 --duration 6 --resolution 768p
python test_video.py "Neon cityscape" --model minimax/hailuo-2.3 --duration 10 --resolution 768p --no-prompt-optimizer
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
# Zeroscope-style model
python test_batch.py prompts.txt --model anotherjesse/zeroscope-v2-xl --num-frames 24 --width 1024 --height 576

# Minimax model
python test_batch.py prompts.txt --model minimax/hailuo-2.3 --duration 6 --resolution 768p
```

### test_interactive.py

Interactive prompt testing mode. No command-line flags. Use commands within the interactive session:

- `model <name>` - Change model
- `frames <n>` - Change num_frames
- `fps <n>` - Change fps
- `width <n>` - Change video width
- `height <n>` - Change video height
- `seed <n>` - Set seed
- `clear` - Clear seed
- `show` - Show current settings
- `quit` or `exit` - Exit

### test_seed_variations.py

Test the same prompt with multiple seeds. Note: Only works with models that support the `seed` parameter (Zeroscope/Luma-style models, not minimax/hailuo).

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

### API Parameters

Different models use different parameter schemas. The script automatically maps command-line flags to the appropriate API parameters based on the model.

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
- **Zeroscope/Luma-style models** use frame-based control (`num_frames`, `fps`) and pixel dimensions (`width`, `height`)
- **Minimax/Hailuo models** use duration-based control (`duration` in seconds) and preset resolutions (`768p`, `1080p`)
- **Zeroscope/Luma-style models** support `seed` for reproducibility; **Minimax/Hailuo models** do not

**Always check a model's schema:**
```bash
python check_model_schema.py <model-name>
```

## File Structure

- `test_video.py` - Single video generation script
- `test_batch.py` - Batch testing from file
- `test_interactive.py` - Interactive prompt testing
- `estimate_time.py` - Estimate generation time before starting
- `check_model_schema.py` - Check model parameters and defaults
- `experiments/` - Experiment logs and notes
- `output/` - Generated videos (gitignored)
- `api_calls.log` - Automatic log of all API calls with timing (gitignored)

## Time Estimation

Estimate how long a video generation will take before starting:

```bash
python estimate_time.py --model anotherjesse/zeroscope-v2-xl --num-frames 24
python estimate_time.py --model luma/ray --num-frames 48 --width 1024 --height 576
```

The estimator uses:
- Historical data from `api_calls.log` (if available) for more accurate estimates
- Known model estimates for models without historical data
- Parameter adjustments (resolution and frame count affect generation time)

**Typical generation times:**
- `anotherjesse/zeroscope-v2-xl`: 30-60 seconds
- `minimax/hailuo-2.3`: 30-90 seconds
- `luma/ray`: ~40 seconds
- `lightricks/ltx-video`: ~10 seconds (very fast, lower quality)
- Other models: 30-90 seconds (varies by model and parameters)

**Factors that affect generation time:**
- Model choice (biggest factor)
- Resolution (higher = longer)
- Number of frames (more frames = longer)
- Server load (can vary)

## Logging

All API calls are automatically logged to `api_calls.log` with:
- Timestamp
- Model used
- Prompt (truncated to 100 chars)
- Parameters (JSON format)
- Result (video URL or error message)
- Duration in seconds

Example log entry:
```
2024-01-15 14:30:25 | anotherjesse/zeroscope-v2-xl | A futuristic cityscape at sunset... | {"fps":8,"height":320,"num_frames":24,"prompt":"A futuristic cityscape at sunset","width":576} | https://replicate.delivery/... | 45.23s
```

The log file is automatically created and appended to. You can analyze it to track:
- Which prompts/models work best
- Average generation times
- Success/failure rates
- Parameter combinations that produce good results

## Experimentation

Document your experiments in `experiments/` folder. Track:
- Prompts that work well
- Models and their capabilities
- Parameter combinations
- Visual results and notes

## Models to Test

### Models to Test

**Zeroscope/Luma-style Schema Models** (use `num_frames`, `fps`, `width`, `height`):

- **`anotherjesse/zeroscope-v2-xl`** - Script default
  - Max Duration: 6 seconds (48 frames at 8 fps)
  - Cost: ~$0.035 per run
  - Resolution: Up to 1024x576
  - FPS: 8 fps
  - Parameters: `num_frames`, `fps`, `width`, `height`, `seed`
  - Good for: Cost-effective testing, abstract visuals

### Model Comparison & Recommendations

**📊 See [MODEL_COMPARISON.md](MODEL_COMPARISON.md) for detailed research on prompt adherence and quality.**

Quick summary: **Minimax Hailuo 2.3** is recommended for best prompt adherence and quality, with built-in prompt optimization and reference image support.

### Recommended Models to Try

**1. Luma Ray** (`luma/ray`)
- Max Duration: 5 seconds
- Cost: ~$0.10 per video
- Resolution: 720p
- FPS: 24 fps
- Quality: Cinematic, smooth camera movements
- Features: Fast generation (~40s), supports start/end frames, interpolation
- Good for: Cinematic visuals, smooth motion

**2. Haiper 2.0** (check `haiper/haiper-2.0` or similar)
- Max Duration: 4-6 seconds
- Cost: ~$0.10-$0.15 per video
- Resolution: 720p (4K coming)
- Quality: High quality, versatile
- Good for: General purpose, high quality

**3. Tencent Hunyuan Video** (check `tencent/hunyuan-video` or similar)
- Max Duration: 5+ seconds (configurable)
- Cost: ~$0.08-$0.12 per video
- Resolution: 720p
- Quality: State-of-the-art, smooth motion
- Features: Configurable resolution, duration, steps, guidance scale
- Good for: Realistic motion, fine-tunable

**Minimax/Hailuo Schema Models** (use `duration`, `resolution`, `prompt_optimizer`):

**4. Minimax Hailuo 2.3** (`minimax/hailuo-2.3`)
- Max Duration: 6 seconds (768p) or 10 seconds (768p only)
- Cost: ~$0.10-$0.15 per video
- Resolution: 768p or 1080p (1080p limited to 6s)
- Quality: Excellent realism and coherence
- Parameters: `duration`, `resolution`, `prompt_optimizer`, `first_frame_image` (optional)
- Good for: Realistic scenes, smooth videos
- Note: Uses duration-based control, not frame-based

**5. Genmo Mochi 1** (check `genmo/mochi-1` or similar)
- Quality: High-fidelity motion, strong prompt adherence
- Good for: Detailed, accurate outputs

**6. Lightricks LTX-Video** (check `lightricks/ltx-video` or similar)
- Max Duration: 3 seconds
- Speed: Very fast (~10 seconds generation)
- Quality: Lower quality but extremely fast
- Good for: Quick iterations, testing

### How to Find More Models

**1. Replicate Explore Page**
- Visit: https://replicate.com/explore?query=text+to+video
- Filter by "Video Generation" category
- Browse models and check their documentation

**2. Replicate Collections**
- Video Generation Collection: https://replicate.com/collections/homepage-generate-videos
- Curated list of video models with examples

**3. Check Model Schema Programmatically**
```bash
# Use the helper script to see model parameters and defaults
python check_model_schema.py minimax/hailuo-2.3
python check_model_schema.py anotherjesse/zeroscope-v2-xl
```

Or programmatically:
```python
import replicate
client = replicate.Client(api_token=YOUR_TOKEN)
model = client.models.get("owner/model-name")
version = model.latest_version
print(version.openapi_schema)  # See all available parameters
```

**4. Test Model Availability**
Models may have different names on Replicate. Try variations like:
- `owner/model-name`
- `owner/model-name-v2`
- `owner/model`

## Documentation & Resources

### Getting Started
- **Replicate Docs**: https://replicate.com/docs
  - Complete API reference
  - Python client guide
  - Model schema documentation

### Video Generation Guides
- **Replicate Blog - AI Video**: https://replicate.com/blog/ai-video-is-having-its-stable-diffusion-moment
  - Overview of current video models
  - Comparison of different approaches
  - Latest developments

- **Generate Videos with Playground**: https://replicate.com/blog/generate-videos-with-playground
  - Tutorial on using Replicate for video generation
  - Best practices

- **Compare AI Video Models**: https://replicate.com/blog/compare-ai-video-models
  - Side-by-side comparisons
  - Quality assessments

### Advanced Topics
- **Fine-tuning Video Models**: https://replicate.com/blog/fine-tune-video
  - How to fine-tune models for specific styles
  - Custom training workflows

### Finding Models
1. **Replicate Explore**: https://replicate.com/explore
   - Search for "text to video", "video generation", etc.
   - Filter by category
   - Sort by popularity or recency

2. **Model Pages**: Each model page shows:
   - Input/output schemas
   - Example prompts
   - Cost estimates
   - User examples

3. **Community**: Check Replicate's Discord/community for:
   - New model announcements
   - User recommendations
   - Troubleshooting tips

## Tips for Model Testing

1. **Check model schema first** - Use `check_model_schema.py` to see what parameters each model accepts
2. **Test one model at a time** with the same prompts to compare quality
3. **Check model schemas** - different models use different parameter schemas:
   - Zeroscope/Luma-style: `num_frames`, `fps`, `width`, `height`, `seed`
   - Minimax/Hailuo-style: `duration`, `resolution`, `prompt_optimizer`
   - Always check with `check_model_schema.py` before using a new model
4. **Document costs** - track which models give best quality per dollar
5. **Check generation time** - some models are faster but lower quality

## Usage Guide

### Quick Start Workflow

1. **Check model parameters:**
   ```bash
   python check_model_schema.py <model-name>
   ```

2. **Estimate time before generating:**
   ```bash
   python estimate_time.py --model <model-name>
   ```

3. **Generate your first video:**
   ```bash
   python test_video.py "A futuristic cityscape at sunset with neon lights" --model <model-name>
   ```

3. **Check the result:**
   - Video URL will be printed in the console
   - Open the URL in your browser to view
   - Metadata saved to `output/` folder
   - Call logged to `api_calls.log`

4. **Iterate and experiment:**
   - Try different prompts
   - Test different models
   - Adjust resolution and frame count
   - Use interactive mode for quick iterations

### Workflow Patterns

**Pattern 1: Quick Exploration**
```bash
# Use interactive mode for rapid iteration
python test_interactive.py
# Then type prompts directly, adjust settings on the fly
```

**Pattern 2: Systematic Testing**
```bash
# Create a prompts file
echo "Neon cityscape at night" > my_prompts.txt
echo "Abstract shapes floating" >> my_prompts.txt
echo "Cinematic landscape with dramatic clouds" >> my_prompts.txt

# Test all prompts with same settings (Zeroscope-style model)
python test_batch.py my_prompts.txt --model anotherjesse/zeroscope-v2-xl --num-frames 24

# Or with minimax model
python test_batch.py my_prompts.txt --model minimax/hailuo-2.3 --duration 6 --resolution 768p
```

**Pattern 3: Model Comparison**
```bash
# Test same prompt with different models (note: different parameter schemas)
python test_video.py "Neon cityscape" --model anotherjesse/zeroscope-v2-xl --num-frames 24
python test_video.py "Neon cityscape" --model minimax/hailuo-2.3 --duration 6 --resolution 768p
python test_video.py "Neon cityscape" --model luma/ray --num-frames 24
```

**Pattern 4: Parameter Tuning**
```bash
# Test same prompt with different resolutions
python test_video.py "Abstract shapes" --width 576 --height 320
python test_video.py "Abstract shapes" --width 1024 --height 576
python test_video.py "Abstract shapes" --width 1280 --height 720
```

### Analyzing Results

**Check your log file:**
```bash
cat api_calls.log
# or
tail -f api_calls.log  # Watch in real-time
```

**Review timing data:**
```bash
# Get estimates based on your historical data
python estimate_time.py --model <model-name>
```

**Check saved metadata:**
```bash
ls output/  # See all experiment metadata files
cat output/experiment_*.txt  # View details
```

### Tips for Effective Testing

- Start simple: Use default parameters first, then adjust
- Document what works: Note successful prompts/models in `experiments/` folder
- Build historical data: More generations = better time estimates
- Compare systematically: Test one variable at a time (model, prompt, or parameters)
- Check costs: Monitor your Replicate usage dashboard
- Save good results: Note video URLs and parameters that produce cool videos

## Setup

1. Create and activate a virtual environment (recommended):
```bash
cd video-api-testing
python3.12 -m venv venv  # Use Python 3.10-3.13 (3.14+ not compatible)
# or: python3.11 -m venv venv
# or: python3.10 -m venv venv
source venv/bin/activate  # On macOS/Linux
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API token:
```bash
# Create a .env file with your Replicate API token:
echo "REPLICATE_API_TOKEN=your_token_here" > .env
# Or manually create .env and add: REPLICATE_API_TOKEN=your_token_here
```

## Understanding the `seed` Parameter

The `seed` is a number that initializes the model's random number generator, controlling randomness in video generation.

### How It Works
- **Same prompt + same seed + same parameters** = Same (or very similar) output
- **Same prompt + different seed** = Different variations of the same concept
- **No seed** = Random output each time

### When to Use Seed

**1. For Style Consistency (Main Use Case)**
If generating multiple clips for the same song/video, use the same seed across all clips to maintain visual coherence:
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

### Best Practice for Testing

**Start without seeds** to explore freely and see the full range of possibilities. Once you find prompts you like, **test with seeds** to:
- Verify seed actually works for style consistency
- See how much variation you get with different seeds
- Determine if seed is reliable for your use case

### Test Seed Variations

Test the same prompt with multiple seeds to see how seed affects output:
```bash
python test_seed_variations.py "Abstract shapes floating" --seeds 1,2,3,4,5
python test_seed_variations.py "Neon cityscape" --count 5 --start-seed 10
```

Note: `test_seed_variations.py` is available for seed testing, but seed experimentation is lower priority than finding good prompt/model combinations.
