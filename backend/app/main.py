"""Main application entry point for MaternAI FastAPI Backend.

Establishes the baseline application, CORS, error handling, root health check,
and /api/v1 router foundation.
"""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.errors import AppError
from backend.app.schemas.common import ApiErrorResponse
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

    # --------------------------------------------------------------------------
    # Standardized Error Handlers (Conforms to MaternAI standard error envelope)
    # --------------------------------------------------------------------------
    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request payload validation failed",
                    "details": {"errors": exc.errors()},
                }
            },
        )

    @app.exception_handler(HTTPException)
    async def generic_http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "error" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": "HTTP_ERROR",
                    "message": str(exc.detail),
                    "details": {},
                }
            },
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
