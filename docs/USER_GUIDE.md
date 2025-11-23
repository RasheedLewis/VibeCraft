# VibeCraft User Guide

## Video Composition

### Overview

VibeCraft composes multiple video clips into a single music video with synchronized audio. All clips are normalized to 1080p at 24 FPS, stitched together, and synced with your original song audio.

### Limitations

- **Maximum song duration**: 5 minutes
- **Processing time**: 5-15 minutes depending on number of clips

### Usage

#### 1. Enqueue a Composition Job

```bash
POST /api/songs/{song_id}/compose
Content-Type: application/json

{
  "clipIds": ["uuid1", "uuid2", "uuid3"],
  "clipMetadata": [
    {"clipId": "uuid1", "startFrame": 0, "endFrame": 240},
    {"clipId": "uuid2", "startFrame": 0, "endFrame": 240},
    {"clipId": "uuid3", "startFrame": 0, "endFrame": 240}
  ]
}
```

**Response:**
```json
{
  "jobId": "composition-...",
  "status": "queued",
  "songId": "..."
}
```

#### 2. Check Job Status

```bash
GET /api/songs/{song_id}/compose/{job_id}/status
```

**Status values:**
- `queued`: Waiting to start
- `processing`: In progress
- `completed`: Success
- `failed`: Failed (check `error` field)
- `cancelled`: Cancelled

**Progress milestones:**
- 0-10%: Validation
- 10-30%: Downloading clips
- 30-80%: Normalizing clips
- 80-90%: Stitching clips
- 90-95%: Uploading
- 95-100%: Verification

#### 3. Get Composed Video

```bash
GET /api/songs/{song_id}/composed-videos/{composed_video_id}
```

Returns video URL (presigned, expires in 1 hour) and metadata.

#### 4. Cancel a Job (Optional)

```bash
POST /api/songs/{song_id}/compose/{job_id}/cancel
```

### Error Handling

Common errors:
- **Clip not found**: Clip ID doesn't exist
- **Clip not ready**: Clip not completed or missing video URL
- **Song duration exceeded**: Song longer than 5 minutes
- **Download/Normalization/Stitching failed**: Processing error

Retry by creating a new composition job.

### Best Practices

1. Ensure all clips are completed before composing
2. Songs longer than 5 minutes will be rejected
3. Monitor progress by polling status every 10-30 seconds
4. Download video promptly (URLs expire after 1 hour)

### Output Specifications

- **Format**: MP4 (H.264 video, AAC audio)
- **Resolution**: 1920x1080 (1080p)
- **Frame rate**: 24 FPS
- **Audio bitrate**: 192 kbps

