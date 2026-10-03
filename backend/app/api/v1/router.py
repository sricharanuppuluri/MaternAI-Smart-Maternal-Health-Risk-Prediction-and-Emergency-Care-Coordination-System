"""API v1 router definition.

This module defines the /api/v1 routes for MaternAI.
In Phase 0, only baseline health checks and structural boundaries are established.
Future phases will introduce authentication, health records, predictions, alerts, visits, and follow-ups.
"""

from fastapi import APIRouter, Depends
from backend.app.core.config import Settings, get_settings
from backend.app.schemas.health import HealthStatus

api_router = APIRouter()


@api_router.get(
    "/health",
    response_model=HealthStatus,
    summary="API v1 Health Check",
    description="Returns the health status of the MaternAI v1 API.",
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthStatus:
    """Return health status of API v1."""
    return HealthStatus(
        status="healthy",
        app=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )
