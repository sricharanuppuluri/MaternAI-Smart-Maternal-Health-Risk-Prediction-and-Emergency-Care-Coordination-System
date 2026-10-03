"""Main application entry point for MaternAI FastAPI Backend.

Phase 0 establishes the baseline application, CORS, root health check,
and /api/v1 router foundation.
"""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings
from backend.app.schemas.health import HealthStatus

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("maternai.backend")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown events."""
    settings = get_settings()
    logger.info("Starting %s backend (version: %s, env: %s)", settings.PROJECT_NAME, settings.VERSION, settings.ENVIRONMENT)
    yield
    logger.info("Shutting down %s backend", settings.PROJECT_NAME)


def create_application() -> FastAPI:
    """Application factory for FastAPI instance."""
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.PROJECT_NAME} API",
        version=settings.VERSION,
        description="MaternAI - Smart Maternal Health Risk Prediction & Care Coordination System Backend API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Root health/status endpoint
    @app.get(
        "/",
        response_model=HealthStatus,
        summary="Application Root & Health Check",
        description="Returns the status of the MaternAI Backend service.",
    )
    async def root_health() -> HealthStatus:
        """Root endpoint returning basic service status."""
        return HealthStatus(
            status="ok",
            app=settings.PROJECT_NAME,
            version=settings.VERSION,
            environment=settings.ENVIRONMENT,
        )

    # Mount Versioned API Routes (/api/v1)
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_application()
