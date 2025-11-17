# Deployed URLs

This document tracks the production deployment URLs for VibeCraft services on Railway.

## Production URLs

### Backend API
- **Service:** `backend-api`
- **URL:** `https://backend-api-production.up.railway.app`
- **Health Check:** `https://backend-api-production.up.railway.app/healthz`
- **API Base:** `https://backend-api-production.up.railway.app/api/v1`

### RQ Worker
- **Service:** `rq-worker`
- **URL:** `https://rq-worker-production.up.railway.app`
- **Note:** Worker service (no HTTP endpoints, processes background jobs)

### Frontend
- **Service:** `frontend`
- **URL:** `https://frontend-production.up.railway.app` (or your custom domain)
- **Status:** Not yet deployed

## Environment Variables Reference

### Frontend Needs
When deploying frontend, set:
```bash
VITE_API_BASE_URL=https://backend-api-production.up.railway.app
```

### Backend CORS Configuration
Update `backend/app/main.py` to allow frontend domain:
```python
allow_origins=[
    "https://frontend-production.up.railway.app",
    "http://localhost:5173",  # Keep for local dev
]
```

## Railway Project
- **Project Name:** `vibe-craft-music-videos`
- **Project ID:** `9d147533-96b0-4aeb-ab3a-502138d87ae7`
- **Environment:** `production`

## Quick Links
- [Railway Dashboard](https://railway.app/project/9d147533-96b0-4aeb-ab3a-502138d87ae7)
- Backend Health: https://backend-api-production.up.railway.app/healthz

## Notes
- URLs may change if services are redeployed or domains are updated
- Update this file when URLs change
- Health check endpoint returns: `{"status":"ok"}`

