# Trigger.dev Resource Configuration for Video Composition

## Current Architecture

**Important:** The actual FFmpeg work runs in your **Python backend** (FastAPI), NOT in Trigger.dev.

- **Trigger.dev task**: Just orchestrates (calls API endpoint, polls for status)
- **Python backend**: Does the actual work (downloads, normalizes, stitches, uploads)

So memory limits are determined by **where your Python backend is deployed** (Railway, Render, EC2, etc.), not Trigger.dev.

## Trigger.dev Configuration

### Machine Types (if running work IN Trigger.dev)

If you wanted to run the work directly in Trigger.dev (not just orchestrate), you can specify machine types:

```typescript
// In task definition
export const composeVideoTask = task({
  id: "trigger-compose-video",
  machine: "large-1x",  // Configure machine preset
  // ... rest of config
});

// Or when triggering
await composeVideoTask.trigger(payload, { 
  machine: "large-1x" 
});
```

**Machine presets** (from Trigger.dev docs):
- `small-1x` - Default, basic resources
- `medium-1x` - More CPU/RAM
- `large-1x` - High CPU/RAM for intensive tasks
- `xlarge-1x` - Maximum resources

### Current Setup

Your current task doesn't specify a machine type, so it uses the default. But since the work runs in Python, this doesn't matter much.

## Python Backend Memory Configuration

Since the actual work runs in your Python backend, you need to configure resources there:

### 1. Check Current Deployment Resources

**Railway:**
- Check your service settings → Resources
- Default: 512MB RAM
- Upgrade to 2GB+ for video processing

**Render:**
- Check service settings → Plan
- Free tier: 512MB RAM
- Paid tiers: 2GB+ available

**EC2/Fargate:**
- Configure in task definition or instance type
- Recommended: 4GB+ RAM for 60 clips

### 2. Monitor Memory Usage

Add memory monitoring to your composition execution:

```python
import psutil
import os

# In composition_execution.py
process = psutil.Process(os.getpid())
memory_mb = process.memory_info().rss / 1024 / 1024
logger.info(f"Current memory usage: {memory_mb:.2f} MB")
```

### 3. Estimate Memory Requirements

For 60 clips:
- **Input clips**: 60 × ~10MB (original) = 600MB
- **Normalized clips**: 60 × ~50MB (1080p) = 3GB
- **FFmpeg working memory**: ~500MB-1GB during concat
- **Python overhead**: ~200MB
- **Total**: ~4-5GB recommended

## Recommended Configuration

### For 10-20 clips:
- **RAM**: 2GB minimum
- **Current setup**: Should work on most platforms

### For 60 clips:
- **RAM**: 4-8GB recommended
- **Platform**: EC2/Fargate or upgraded Railway/Render
- **Consider**: Stream processing or chunked normalization

## Trigger.dev Documentation Links

1. **Machine Configuration**: https://trigger.dev/docs/triggering
   - How to specify machine types
   - Machine preset options

2. **Task Configuration**: https://trigger.dev/docs/v3
   - Task definition options
   - maxDuration, retries, etc.

3. **Build Configuration**: https://trigger.dev/docs/config/config-file
   - Adding system packages (FFmpeg)
   - Custom build steps

4. **Main Docs**: https://trigger.dev/docs/v3
   - Complete API reference

## Next Steps

1. **Test with 10 clips** on current setup
2. **Monitor memory usage** during test
3. **Scale up deployment** if needed for 60 clips
4. **Consider alternatives**:
   - Stream processing (don't load all clips at once)
   - Chunked normalization (process in batches)
   - Move to EC2/Fargate for more control

