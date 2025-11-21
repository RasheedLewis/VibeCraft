from fastapi import APIRouter
from app.api.v1 import routes_config, routes_health, routes_jobs, routes_scenes, routes_songs, routes_videos

api_router = APIRouter()
api_router.include_router(routes_health.router, prefix="/health", tags=["health"])
api_router.include_router(routes_songs.router, prefix="/songs", tags=["songs"])
api_router.include_router(routes_jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(routes_scenes.router, tags=["scenes"])
api_router.include_router(routes_videos.router, tags=["videos"])
api_router.include_router(routes_config.router, tags=["config"])
