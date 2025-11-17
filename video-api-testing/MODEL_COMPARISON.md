# Video Generation Model Comparison: Prompt Adherence & Quality

Research summary on which models best capture prompts accurately and produce high-quality videos.

## Key Findings

### Top Recommendations for Prompt Adherence & Quality

**1. Minimax Hailuo 2.3** (`minimax/hailuo-2.3`) ⭐ **RECOMMENDED**
- **Prompt Adherence:** Excellent - Built-in prompt optimizer helps ensure accurate interpretation
- **Quality:** High-quality, realistic videos with smooth motion and temporal consistency
- **Strengths:**
  - Built-in prompt optimization feature (can be enabled/disabled)
  - Supports reference images for better context
  - Multiple style options (realism, anime, CG cinematic, water-ink)
  - Stable motion and balanced lighting
  - Higher resolution support (768p, 1080p)
- **Duration:** 6 seconds (768p) or 10 seconds (768p only)
- **Cost:** ~$0.10-$0.15 per video
- **Best For:** Realistic scenes, detailed prompts, when prompt accuracy is critical
- **Note:** Uses duration-based control (not frame-based), which can be more intuitive

**2. Wan2.1** (`wavespeedai/wan-2.1-t2v-720p` or `wavespeedai/wan-2.1-t2v-480p`)
- **Prompt Adherence:** Very good - Known for real-world accuracy
- **Quality:** High-quality, realistic videos
- **Strengths:**
  - Open-source model with good documentation
  - Fast generation (~39 seconds for 5-second video at 480p)
  - Tunable parameters (`guide_scale`, `shift`, `steps`) for fine-tuning prompt adherence
  - Supports both text-to-video and image-to-video
- **Duration:** 5 seconds
- **Cost:** Lower cost (open-source)
- **Best For:** Realistic videos, when you need fast iteration
- **Parameters:** `guide_scale` around 4 and `shift` around 2 recommended for realism

**3. Leonardo AI Motion 2.0** (`leonardoai/motion-2.0`)
- **Prompt Adherence:** Good - Multiple style controls help guide output
- **Quality:** High-quality with frame interpolation for smooth motion
- **Strengths:**
  - Multiple aspect ratios supported
  - Style controls for better prompt matching
  - Frame interpolation for smoother videos
- **Duration:** 5 seconds
- **Best For:** When you need style control and smooth motion

### Other Notable Models

**4. Luma Ray** (`luma/ray`)
- **Prompt Adherence:** Good
- **Quality:** Cinematic, smooth camera movements
- **Duration:** 5 seconds
- **Cost:** ~$0.10 per video
- **Best For:** Cinematic shots, smooth camera movements

**5. Zeroscope v2 XL** (`anotherjesse/zeroscope-v2-xl`)
- **Prompt Adherence:** Moderate - Can be inconsistent with complex prompts
- **Quality:** Good but lower resolution (576x320 default)
- **Strengths:**
  - Very affordable (~$0.035 per video)
  - Fast generation
  - Good for testing and iteration
- **Duration:** Up to 6 seconds (48 frames at 8 fps)
- **Best For:** Quick testing, budget-conscious projects, simple prompts
- **Limitations:** Lower resolution, less reliable with complex prompts

**6. Tencent Hunyuan Video** (`tencent/hunyuan-video` or similar)
- **Prompt Adherence:** Good
- **Quality:** State-of-the-art, smooth motion
- **Strengths:**
  - Configurable resolution, duration, steps, guidance scale
  - Excellent temporal consistency
- **Duration:** 5+ seconds (configurable)
- **Best For:** When you need fine-grained control over generation parameters

## Prompt Adherence Best Practices

Regardless of model choice, these practices improve prompt adherence:

1. **Detailed Prompts:** Include specific details about:
   - Motion and actions
   - Mood and atmosphere
   - Camera angles and movement
   - Lighting conditions
   - Style and aesthetic

2. **Use Reference Images:** Models like Minimax Hailuo 2.3 support reference images, which significantly improve accuracy

3. **Enable Prompt Optimization:** When available (e.g., Minimax Hailuo), use the built-in prompt optimizer

4. **Fine-tune Parameters:**
   - **Guide Scale:** Higher values = more prompt adherence (but may reduce creativity)
   - **Sampling Steps:** More steps = better quality but slower generation
   - **Seed:** Use same seed for consistent style across videos

5. **Iterate and Refine:** Test different phrasings and structures to find what works best for each model

## Recommendations by Use Case

### For Maximum Prompt Accuracy:
**Use: Minimax Hailuo 2.3** with prompt optimizer enabled
- Best built-in prompt optimization
- Reference image support
- Multiple style options

### For Budget-Conscious Testing:
**Use: Zeroscope v2 XL**
- Lowest cost
- Fast generation
- Good enough for initial testing

### For Realistic, High-Quality Output:
**Use: Wan2.1 (720p)** or **Minimax Hailuo 2.3 (1080p)**
- Both produce realistic, high-quality videos
- Wan2.1 is faster and cheaper
- Minimax Hailuo has better prompt optimization

### For Fast Iteration:
**Use: Wan2.1 (480p)**
- Fastest generation time (~39 seconds)
- Good quality-to-speed ratio

## Testing Strategy

1. **Start with Minimax Hailuo 2.3** - Best prompt adherence out of the box
2. **Test with your specific prompts** - Different models excel at different types of content
3. **Compare outputs** - Generate the same prompt with 2-3 models and compare
4. **Use `check_model_schema.py`** - Always verify what parameters each model accepts
5. **Log results** - Use `log_to_experiment.py` to track which models work best for your use case

## Model Availability on Replicate

To find and verify models:
- **Explore:** https://replicate.com/explore?query=text+to+video
- **Collections:** https://replicate.com/collections/homepage-generate-videos
- **Check Schema:** Use `python check_model_schema.py <model-name>` to see parameters

## Notes

- Model quality and availability change frequently - always verify current status
- Prompt adherence can vary significantly based on prompt complexity and style
- What works for one type of content may not work for another
- Consider cost vs. quality trade-offs based on your use case
- Some models may not be available on Replicate (e.g., Runway Gen-3, Kling AI) - check availability

