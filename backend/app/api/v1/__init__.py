from fastapi import APIRouter

from app.api.v1 import routes_health, routes_jobs, routes_songs

api_router = APIRouter()
api_router.include_router(routes_health.router, prefix="/health", tags=["health"])
api_router.include_router(routes_songs.router, prefix="/songs", tags=["songs"])
api_router.include_router(routes_jobs.router, prefix="/jobs", tags=["jobs"])

