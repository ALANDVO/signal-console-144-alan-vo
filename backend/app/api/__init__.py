from fastapi import APIRouter

from app.api.routes import health, skills, drift, auth


api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(skills.router)
api_router.include_router(drift.router)