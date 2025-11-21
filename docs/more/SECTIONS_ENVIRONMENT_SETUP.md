# Environment Configuration Guide

## Required Environment Variables for Audjust Integration

To enable song section analysis using the Audjust API, you need to configure the following
environment variables in your `backend/.env` file:

### Audjust API Configuration

```bash
# Audjust API Base URL (production endpoint)
AUDJUST_BASE_URL=https://api.audjust.com

# Your Audjust API Key
# Get this from: https://www.audjust.com/console
AUDJUST_API_KEY=your_api_key_here

# API endpoints (default values, usually don't need to change)
AUDJUST_UPLOAD_PATH=/upload
AUDJUST_STRUCTURE_PATH=/structure
AUDJUST_TIMEOUT_SEC=30.0
```

### How to Get an Audjust API Key

1. Visit the [Audjust API Console](https://www.audjust.com/console)
2. Sign up or log in
3. Generate a new API key
4. Copy the key and add it to your `.env` file

### Testing Your Configuration

After setting up the environment variables, restart your backend server and check the logs when
uploading a song for analysis. You should see:

```text
INFO: Checking Audjust configuration: base_url=https://api.audjust.com, api_key=***
INFO: Audjust is configured, attempting to fetch structure segments for song <song_id>
INFO: fetch_structure_segments called with audio_path=<path>
INFO: Calling Audjust structure API: url=https://api.audjust.com/structure, payload={'sourceFileUrl': '...'}
INFO: Fetched N sections from Audjust for song <song_id>
```

### Troubleshooting

**If you see:** `WARNING: Audjust API not configured`

- Check that both `AUDJUST_BASE_URL` and `AUDJUST_API_KEY` are set in your `.env` file
- Verify there are no extra spaces or quotes in the values
- Make sure the `.env` file is in the `backend/` directory

**If the API call fails:**

- Check that your API key is valid
- Verify you have sufficient API credits
- Check the logs for specific error messages

**If no logs appear at all:**

- Check that your log level is set to `info` or `debug`: `API_LOG_LEVEL=info`
- Ensure the song analysis job is actually running (check Redis/RQ worker logs)
