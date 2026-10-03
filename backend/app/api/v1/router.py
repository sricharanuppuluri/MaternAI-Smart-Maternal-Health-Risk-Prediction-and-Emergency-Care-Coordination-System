"""API v1 router definition and frozen contract endpoints.

Phase 2 establishes the frozen technical contracts for all frontend-critical endpoints.
Endpoints scheduled for subsequent phases are explicitly marked with 501 Not Implemented
while fully exposing their Pydantic request/response schemas in the OpenAPI specification.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status

from backend.app.auth.dependencies import (
    get_current_user,
    require_asha,
    require_mother,
)
from backend.app.core.config import Settings, get_settings
from backend.app.core.errors import ForbiddenError
from backend.app.db.repositories import get_repository
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
from backend.app.services.coordination_service import coordination_service
from backend.app.services.health_service import health_record_service, symptom_service
from backend.app.services.prediction_service import prediction_service

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
# 2. Auth & Profile Bootstrapping [IMPLEMENTED]
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
    """Bootstrap user profile enforcing role authorization."""
    if payload.role == UserRole.ADMIN and current_user.role != UserRole.ADMIN:
        raise ForbiddenError(message="Unauthorized: Regular users cannot bootstrap with ADMIN role.")

    repo = get_repository()
    now = datetime.now(timezone.utc)
    profile_data = {
        "id": current_user.id,
        "role": payload.role,
        "full_name": payload.full_name,
        "phone": payload.phone,
        "created_at": now,
        "updated_at": now,
    }
    repo.profiles[current_user.id] = profile_data
    if payload.role == UserRole.MOTHER:
        repo.resolve_mother_id(current_user.id)
    repo.log_audit(
        user_id=current_user.id,
        action="BOOTSTRAP_PROFILE",
        resource_type="profiles",
        resource_id=current_user.id,
        details={"role": payload.role.value},
    )
    return ProfileResponse(
        id=current_user.id,
        role=payload.role,
        full_name=payload.full_name,
        phone=payload.phone,
        created_at=now,
        updated_at=now,
    )


# ------------------------------------------------------------------------------
# 3. Mother Profile [IMPLEMENTED]
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
    """Return profile information for the currently authenticated mother."""
    repo = get_repository()
    mother_id = repo.resolve_mother_id(current_user.id)
    profile = repo.mother_profiles.get(mother_id, {})
    return MotherProfileResponse(
        id=mother_id,
        user_id=current_user.id,
        full_name=profile.get("full_name", current_user.full_name or "Mother"),
        date_of_birth=profile.get("date_of_birth"),
        age_years=profile.get("age_years"),
        gestational_age_weeks=profile.get("gestational_age_weeks"),
        expected_due_date=profile.get("expected_due_date"),
        assigned_asha_id=profile.get("assigned_asha_id"),
        last_risk_level=profile.get("last_risk_level"),
        phone=profile.get("phone"),
        created_at=profile.get("created_at", datetime.now(timezone.utc)),
    )


# ------------------------------------------------------------------------------
# 4. Health Records [IMPLEMENTED]
# ------------------------------------------------------------------------------
@api_router.post(
    "/health-records",
    response_model=HealthRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Maternal Health Measurements",
    description="Accepts vital measurements, evaluates safety boundary, and stores a new health record.",
)
async def create_health_record(
    payload: HealthRecordCreate,
    current_user: AuthUser = Depends(require_mother),
) -> HealthRecordResponse:
    """Create and persist new maternal vital sign measurements."""
    return health_record_service.create_health_record(payload, current_user)


# ------------------------------------------------------------------------------
# 5. Symptoms [IMPLEMENTED]
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
    """Record and persist maternal symptoms."""
    return symptom_service.record_symptoms(payload, current_user)


# ------------------------------------------------------------------------------
# 6. ML Predictions [IMPLEMENTED]
# ------------------------------------------------------------------------------
@api_router.post(
    "/predictions",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate Maternal Risk Screening",
    description="Evaluates vital and symptom inputs through deterministic safety engine and ML risk model.",
)
async def create_prediction(
    payload: PredictionRequest,
    current_user: AuthUser = Depends(require_mother),
) -> PredictionResponse:
    """Evaluate maternal risk screening enforcing deterministic safety precedence."""
    return prediction_service.evaluate_risk(payload, current_user)


# ------------------------------------------------------------------------------
# 7. Alerts Queue [IMPLEMENTED]
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
    """List alerts filtered by role and assignment scope."""
    return coordination_service.list_alerts(current_user, page=page, size=size)


@api_router.patch(
    "/alerts/{alert_id}/status",
    response_model=AlertResponse,
    summary="Update Alert Status",
    description="Updates workflow status of an alert (ASHA assigned or Admin only).",
)
async def update_alert_status(
    alert_id: UUID,
    payload: AlertStatusUpdate,
    current_user: AuthUser = Depends(require_asha),
) -> AlertResponse:
    """Update workflow status of an alert."""
    return coordination_service.update_alert_status(alert_id, payload, current_user)


# ------------------------------------------------------------------------------
# 8. Visits [IMPLEMENTED]
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
    """Record an in-person or home visit performed by an assigned ASHA."""
    return coordination_service.create_visit(payload, current_user)


# ------------------------------------------------------------------------------
# 9. Follow-ups [IMPLEMENTED]
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
    """Schedule a follow-up action for an assigned mother."""
    return coordination_service.create_followup(payload, current_user)


# ------------------------------------------------------------------------------
# 10. Risk Timeline [IMPLEMENTED]
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
    """Return longitudinal risk timeline enforcing patient isolation and ASHA assignment boundaries."""
    return coordination_service.get_risk_timeline(mother_id, current_user)

