"""Unit tests for Phase 2 Pydantic request and response schemas."""

from datetime import date, datetime
from uuid import UUID, uuid4
import pytest
from pydantic import ValidationError

from backend.app.schemas.alert import AlertResponse, AlertSeverity, AlertStatus, AlertStatusUpdate
from backend.app.schemas.asha import AshaProfileCreate, AshaProfileResponse
from backend.app.schemas.auth import ProfileCreate, ProfileResponse, UserRole
from backend.app.schemas.common import ApiErrorDetail, ApiErrorResponse, PaginatedResponse
from backend.app.schemas.followup import FollowUpCreate, FollowUpResponse, FollowUpStatus
from backend.app.schemas.health_record import HealthRecordCreate, HealthRecordResponse
from backend.app.schemas.mother import (
    MaternalRiskLevel,
    MotherProfileCreate,
    MotherProfileResponse,
    MotherProfileUpdate,
)
from backend.app.schemas.prediction import (
    ContributingFactor,
    PredictionRequest,
    PredictionResponse,
)
from backend.app.schemas.symptom import SymptomItem, SymptomResponse, SymptomSubmission
from backend.app.schemas.timeline import RiskTimelinePoint, RiskTimelineResponse
from backend.app.schemas.visit import VisitCreate, VisitResponse, VisitStatus


# ------------------------------------------------------------------------------
# 1. Common & Error Envelope Tests
# ------------------------------------------------------------------------------
def test_error_envelope_structure():
    """Verify standard error response contract structure."""
    detail = ApiErrorDetail(
        code="VALIDATION_ERROR",
        message="Required field missing",
        details={"field": "pregnancy_week"},
    )
    envelope = ApiErrorResponse(error=detail)
    data = envelope.model_dump()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert data["error"]["message"] == "Required field missing"
    assert data["error"]["details"]["field"] == "pregnancy_week"


def test_paginated_response():
    """Verify paginated response wrapper format."""
    paginated = PaginatedResponse[str](
        items=["item1", "item2"],
        total=2,
        page=1,
        size=20,
        total_pages=1,
    )
    assert paginated.total == 2
    assert len(paginated.items) == 2


# ------------------------------------------------------------------------------
# 2. Auth & Profile Schema Tests
# ------------------------------------------------------------------------------
def test_profile_create_validation():
    """Verify ProfileCreate constraints."""
    profile = ProfileCreate(full_name="Ananya Sharma", role=UserRole.MOTHER)
    assert profile.full_name == "Ananya Sharma"
    assert profile.role == UserRole.MOTHER

    # Empty name should fail
    with pytest.raises(ValidationError):
        ProfileCreate(full_name="")


# ------------------------------------------------------------------------------
# 3. Health Record Schema Tests
# ------------------------------------------------------------------------------
def test_health_record_create_valid():
    """Verify HealthRecordCreate with realistic clinical inputs."""
    record = HealthRecordCreate(
        pregnancy_week=24,
        systolic_bp=120.0,
        diastolic_bp=80.0,
        blood_sugar=95.0,
        hemoglobin=11.5,
        weight_kg=60.0,
        heart_rate=78.0,
        body_temperature=36.8,
    )
    data = record.model_dump()
    assert data["pregnancy_week"] == 24
    assert data["systolic_bp"] == 120.0
    # Confirm snake_case JSON keys
    assert "blood_sugar" in data
    assert "systolic_bp" in data


def test_health_record_create_out_of_bounds():
    """Verify HealthRecordCreate boundaries reject impossible values."""
    with pytest.raises(ValidationError):
        HealthRecordCreate(pregnancy_week=50)  # max 45

    with pytest.raises(ValidationError):
        HealthRecordCreate(systolic_bp=300.0)  # max 250


# ------------------------------------------------------------------------------
# 4. Symptom Schema Tests
# ------------------------------------------------------------------------------
def test_symptom_submission_valid():
    """Verify SymptomSubmission accepts structured list of symptom items."""
    submission = SymptomSubmission(
        symptoms=[
            SymptomItem(symptom_code="headache", severity=2, notes="Mild morning headache"),
            SymptomItem(symptom_code="swelling_feet", severity=1),
        ]
    )
    assert len(submission.symptoms) == 2
    assert submission.symptoms[0].symptom_code == "headache"
    assert submission.symptoms[0].severity == 2


def test_symptom_submission_empty_rejected():
    """Verify empty symptoms list is rejected."""
    with pytest.raises(ValidationError):
        SymptomSubmission(symptoms=[])


# ------------------------------------------------------------------------------
# 5. Prediction & Decision Contract Tests
# ------------------------------------------------------------------------------
def test_prediction_response_contract():
    """Verify PredictionResponse structure and contributing factors."""
    factor = ContributingFactor(
        feature="systolic_bp",
        direction="INCREASES_RISK",
        value=145.0,
    )
    pred = PredictionResponse(
        id=uuid4(),
        mother_id=uuid4(),
        risk_level=MaternalRiskLevel.HIGH,
        model_score=0.82,
        model_version="v0.1.0",
        feature_schema_version="v1.0",
        contributing_factors=[factor],
        created_at=datetime.utcnow(),
    )
    assert pred.risk_level == MaternalRiskLevel.HIGH
    assert pred.model_score == 0.82
    assert len(pred.contributing_factors) == 1
    assert pred.contributing_factors[0].feature == "systolic_bp"


# ------------------------------------------------------------------------------
# 6. Alert Schema Tests
# ------------------------------------------------------------------------------
def test_alert_enums_and_update():
    """Verify alert severity and status enums."""
    assert AlertSeverity.CRITICAL == "CRITICAL"
    assert AlertStatus.VISIT_SCHEDULED == "VISIT_SCHEDULED"

    update = AlertStatusUpdate(
        status=AlertStatus.ACKNOWLEDGED,
        notes="ASHA contacted mother via phone",
    )
    assert update.status == AlertStatus.ACKNOWLEDGED
    assert update.notes == "ASHA contacted mother via phone"


# ------------------------------------------------------------------------------
# 7. Visit & Follow-up Schema Tests
# ------------------------------------------------------------------------------
def test_visit_and_followup_schemas():
    """Verify visit and follow-up contract creation."""
    visit = VisitCreate(
        mother_id=uuid4(),
        visit_date=datetime.utcnow(),
        notes="Home visit completed. BP checked.",
        findings={"bp_stable": True},
    )
    assert visit.findings["bp_stable"] is True

    followup = FollowUpCreate(
        mother_id=uuid4(),
        due_date=date.today(),
        notes="Check hemoglobin levels again",
    )
    assert followup.due_date == date.today()


# ------------------------------------------------------------------------------
# 8. Longitudinal Risk Timeline Tests
# ------------------------------------------------------------------------------
def test_risk_timeline_response():
    """Verify longitudinal risk timeline structure."""
    point = RiskTimelinePoint(
        timestamp=datetime.utcnow(),
        risk_level=MaternalRiskLevel.MEDIUM,
        assessment_type="PREDICTION",
        systolic_bp=130.0,
        diastolic_bp=85.0,
    )
    timeline = RiskTimelineResponse(
        mother_id=uuid4(),
        current_risk_level=MaternalRiskLevel.MEDIUM,
        assessments=[point],
    )
    assert len(timeline.assessments) == 1
    assert timeline.current_risk_level == MaternalRiskLevel.MEDIUM
