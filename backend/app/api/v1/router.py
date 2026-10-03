"""API v1 router definition and frozen contract endpoints.

Phase 2 establishes the frozen technical contracts for all frontend-critical endpoints.
Endpoints scheduled for subsequent phases are explicitly marked with 501 Not Implemented
while fully exposing their Pydantic request/response schemas in the OpenAPI specification.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from backend.app.auth.dependencies import (
    get_current_user,
    require_asha,
    require_mother,
)
from backend.app.core.config import Settings, get_settings
from backend.app.core.errors import AppError
from backend.app.schemas.alert import AlertResponse, AlertStatusUpdate
from backend.app.schemas.auth import AuthUser, ProfileCreate, ProfileResponse, UserRole
from backend.app.schemas.common import PaginatedResponse
from backend.app.schemas.followup import FollowUpCreate, FollowUpResponse
from backend.app.schemas.health import HealthStatus
from backend.app.schemas.health_record import HealthRecordCreate, HealthRecordResponse
from backend.app.schemas.mother import MotherProfileResponse
from backend.app.schemas.prediction import PredictionRequest, PredictionResponse
from backend.app.schemas.symptom import SymptomResponse, SymptomSubmission
from backend.app.schemas.timeline import RiskTimelineResponse
from backend.app.schemas.visit import VisitCreate, VisitResponse

api_router = APIRouter()


# ------------------------------------------------------------------------------
# 1. Health Status [IMPLEMENTED]
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# 2. Auth & Profile Bootstrapping [CONTRACT FROZEN]
# ------------------------------------------------------------------------------
@api_router.post(
    "/auth/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or Bootstrap User Profile",
    description="Bootstraps profile for an authenticated Supabase user. Role elevation to ADMIN is prohibited.",
)
async def bootstrap_profile(
    payload: ProfileCreate,
    current_user: AuthUser = Depends(get_current_user),
) -> ProfileResponse:
    """Contract stub for profile creation."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 3 (Authentication). Contract is frozen.",
    )


# ------------------------------------------------------------------------------
# 3. Mother Profile [CONTRACT FROZEN]
# ------------------------------------------------------------------------------
@api_router.get(
    "/mothers/me",
    response_model=MotherProfileResponse,
    summary="Get Current Mother Profile",
    description="Returns profile information for the currently authenticated mother.",
)
async def get_current_mother(
    current_user: AuthUser = Depends(require_mother),
) -> MotherProfileResponse:
    """Contract stub for fetching current mother profile."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 3/4. Contract is frozen.",
    )


# ------------------------------------------------------------------------------
# 4. Health Records [CONTRACT FROZEN]
# ------------------------------------------------------------------------------
@api_router.post(
    "/health-records",
    response_model=HealthRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Maternal Health Measurements",
    description="Accepts vital measurements and stores a new health record.",
)
async def create_health_record(
    payload: HealthRecordCreate,
    current_user: AuthUser = Depends(require_mother),
) -> HealthRecordResponse:
    """Contract stub for creating health records."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 4 (Health API). Contract is frozen.",
    )


# ------------------------------------------------------------------------------
# 5. Symptoms [CONTRACT FROZEN]
# ------------------------------------------------------------------------------
@api_router.post(
    "/symptoms",
    response_model=List[SymptomResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Record Maternal Symptoms",
    description="Records maternal symptom occurrences mapped to standardized symptom codes.",
)
async def record_symptoms(
    payload: SymptomSubmission,
    current_user: AuthUser = Depends(require_mother),
) -> List[SymptomResponse]:
    """Contract stub for recording symptoms."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 4 (Health API). Contract is frozen.",
    )


# ------------------------------------------------------------------------------
# 6. ML Predictions [CONTRACT FROZEN]
# ------------------------------------------------------------------------------
@api_router.post(
    "/predictions",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate Maternal Risk Screening",
    description="Evaluates vital and symptom inputs against the ML risk model and decision layer.",
)
async def create_prediction(
    payload: PredictionRequest,
    current_user: AuthUser = Depends(require_mother),
) -> PredictionResponse:
    """Contract stub for ML risk prediction."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 5 (ML Pipeline). Contract is frozen.",
    )


# ------------------------------------------------------------------------------
# 7. Alerts Queue [CONTRACT FROZEN]
# ------------------------------------------------------------------------------
@api_router.get(
    "/alerts",
    response_model=PaginatedResponse[AlertResponse],
    summary="List Alerts Queue",
    description="Returns paginated list of alerts for the authenticated ASHA or Mother.",
)
async def list_alerts(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AuthUser = Depends(get_current_user),
) -> PaginatedResponse[AlertResponse]:
    """Contract stub for listing alerts."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 4 (Alerts API). Contract is frozen.",
    )


@api_router.patch(
    "/alerts/{alert_id}/status",
    response_model=AlertResponse,
    summary="Update Alert Status",
    description="Updates workflow status of an alert (ASHA only).",
)
async def update_alert_status(
    alert_id: UUID,
    payload: AlertStatusUpdate,
    current_user: AuthUser = Depends(require_asha),
) -> AlertResponse:
    """Contract stub for updating alert status."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 4 (Alerts API). Contract is frozen.",
    )


# ------------------------------------------------------------------------------
# 8. Visits [CONTRACT FROZEN]
# ------------------------------------------------------------------------------
@api_router.post(
    "/visits",
    response_model=VisitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule or Record ASHA Visit",
    description="Records an in-person or home visit performed by an ASHA worker.",
)
async def create_visit(
    payload: VisitCreate,
    current_user: AuthUser = Depends(require_asha),
) -> VisitResponse:
    """Contract stub for creating a visit."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 4 (Visits API). Contract is frozen.",
    )


# ------------------------------------------------------------------------------
# 9. Follow-ups [CONTRACT FROZEN]
# ------------------------------------------------------------------------------
@api_router.post(
    "/followups",
    response_model=FollowUpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Schedule Follow-up Task",
    description="Schedules a follow-up action for an assigned mother.",
)
async def create_followup(
    payload: FollowUpCreate,
    current_user: AuthUser = Depends(require_asha),
) -> FollowUpResponse:
    """Contract stub for creating a follow-up."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 4 (Follow-ups API). Contract is frozen.",
    )


# ------------------------------------------------------------------------------
# 10. Risk Timeline [CONTRACT FROZEN]
# ------------------------------------------------------------------------------
@api_router.get(
    "/mothers/{mother_id}/risk-timeline",
    response_model=RiskTimelineResponse,
    summary="Get Mother Longitudinal Risk Timeline",
    description="Returns chronological assessments and vital trends for a mother.",
)
async def get_risk_timeline(
    mother_id: UUID,
    current_user: AuthUser = Depends(get_current_user),
) -> RiskTimelineResponse:
    """Contract stub for fetching risk timeline."""
    raise AppError(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        code="NOT_IMPLEMENTED",
        message="Endpoint implementation scheduled for Phase 4/5. Contract is frozen.",
    )
