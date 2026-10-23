from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import get_db_session
from app.api.schemas import HealthResponse


router = APIRouter(prefix="/health", tags=["health"])
settings = get_settings()


@router.get("", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db_session)) -> HealthResponse:
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db_session)) -> dict:
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "not ready", "database": "disconnected", "error": str(e)}


@router.get("/live")
async def liveness_check() -> dict:
    return {"status": "alive"}