"""Integration and contract tests for Phase 3 implemented endpoints.

Verifies:
- POST /api/v1/health-records
- POST /api/v1/symptoms
- POST /api/v1/predictions (with deterministic safety precedence)
- GET /api/v1/alerts
- PATCH /api/v1/alerts/{id}/status
- POST /api/v1/visits
- POST /api/v1/followups
- GET /api/v1/mothers/{id}/risk-timeline
Enforcing authentication (401), authorization & patient isolation (403), validation (422),
and ASHA assignment boundaries.
"""

from datetime import date, datetime, timezone
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from backend.app.db.repositories import (
    TEST_ADMIN_ID,
    TEST_ASHA_ID,
    TEST_MOTHER_B_ID,
    TEST_MOTHER_ID,
    get_repository,
)
from backend.app.safety.evaluator import SafetyResult, get_safety_engine
from backend.app.safety.states import SafetyStatus
from backend.app.schemas.alert import AlertResponse, AlertSeverity, AlertStatus


@pytest.fixture(autouse=True)
def reset_repo():
    """Reset repository store before each test run."""
    repo = get_repository()
    repo.reset()
    yield
    repo.reset()


# ------------------------------------------------------------------------------
# 1. Health Records (POST /api/v1/health-records)
# ------------------------------------------------------------------------------
def test_create_health_record_happy_path(mother_client: TestClient):
    """Mother successfully records valid maternal vitals."""
    payload = {
        "pregnancy_week": 24,
        "systolic_bp": 120.0,
        "diastolic_bp": 80.0,
        "blood_sugar": 95.0,
        "hemoglobin": 11.5,
        "weight_kg": 62.0,
        "body_temperature": 36.6,
        "heart_rate": 78.0,
    }
    response = mother_client.post("/api/v1/health-records", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["mother_id"] == str(TEST_MOTHER_ID)
    assert data["pregnancy_week"] == 24
    assert data["systolic_bp"] == 120.0
    assert "id" in data
    assert "created_at" in data

    # Verify persistence
    repo = get_repository()
    rec_id = UUID(data["id"])
    persisted = repo.get_health_record(rec_id)
    assert persisted is not None
    assert persisted.pregnancy_week == 24

    # Verify audit log recorded
    assert any(log["resource_type"] == "health_records" and log["action"] == "CREATE" for log in repo.audit_logs)


def test_create_health_record_unauthenticated(client: TestClient):
    """Missing auth header returns 401."""
    payload = {"systolic_bp": 120.0}
    response = client.post("/api/v1/health-records", json=payload)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_create_health_record_validation_error(mother_client: TestClient):
    """Invalid vital values fail data-integrity validation with 422."""
    payload = {
        "systolic_bp": 999.0,  # Max allowed is 250.0
    }
    response = mother_client.post("/api/v1/health-records", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ------------------------------------------------------------------------------
# 2. Symptoms (POST /api/v1/symptoms)
# ------------------------------------------------------------------------------
def test_record_symptoms_happy_path(mother_client: TestClient):
    """Mother successfully records symptoms list."""
    payload = {
        "symptoms": [
            {"symptom_code": "headache", "severity": 2, "notes": "Mild morning headache"},
            {"symptom_code": "swelling_feet", "severity": 1},
        ]
    }
    response = mother_client.post("/api/v1/symptoms", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert data[0]["symptom_code"] == "headache"
    assert data[0]["severity"] == 2
    assert data[1]["symptom_code"] == "swelling_feet"

    # Verify persistence & audit
    repo = get_repository()
    assert len(repo.symptoms) == 2
    assert any(log["resource_type"] == "symptoms" and log["action"] == "CREATE" for log in repo.audit_logs)


def test_record_symptoms_empty_rejected(mother_client: TestClient):
    """Empty symptoms list is rejected with 422."""
    payload = {"symptoms": []}
    response = mother_client.post("/api/v1/symptoms", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ------------------------------------------------------------------------------
# 3. Predictions (POST /api/v1/predictions) & Safety Precedence
# ------------------------------------------------------------------------------
def test_create_prediction_happy_path(mother_client: TestClient):
    """Evaluate screening prediction from features payload."""
    payload = {
        "features": {
            "pregnancy_week": 26,
            "systolic_bp": 120.0,
            "diastolic_bp": 80.0,
            "blood_sugar": 90.0,
            "hemoglobin": 12.0,
            "body_temperature": 36.8,
            "heart_rate": 72.0,
        }
    }
    response = mother_client.post("/api/v1/predictions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["mother_id"] == str(TEST_MOTHER_ID)
    assert data["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "model_score" in data
    assert "contributing_factors" in data
    assert data["model_version"] is not None


def test_safety_precedence_overrides_prediction(mother_client: TestClient):
    """Deterministic safety rule takes precedence and overrides baseline ML prediction."""
    engine = get_safety_engine()

    # Register temporary test clinical emergency rule
    def emergency_rule(vitals, symptoms):
        if vitals and vitals.get("systolic_bp") and vitals["systolic_bp"] >= 160.0:
            return SafetyResult(
                status=SafetyStatus.EMERGENCY,
                triggered_rules=["Severe maternal hypertension emergency"],
                action_required="Emergency hospital transfer",
                is_emergency=True,
            )
        return None

    engine.register_rule(emergency_rule)

    payload = {
        "features": {
            "systolic_bp": 170.0,   # Triggers emergency safety rule
            "blood_sugar": 90.0,
        }
    }
    response = mother_client.post("/api/v1/predictions", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Safety precedence forces final risk to HIGH
    assert data["risk_level"] == "HIGH"

    # Emergency alert generated
    repo = get_repository()
    assert any(a.severity == AlertSeverity.CRITICAL for a in repo.alerts.values())


# ------------------------------------------------------------------------------
# 4. Alerts (GET /api/v1/alerts and PATCH /api/v1/alerts/{id}/status)
# ------------------------------------------------------------------------------
def _seed_sample_alerts(repo):
    alert_a = AlertResponse(
        id=uuid4(),
        mother_id=TEST_MOTHER_ID,
        mother_name="Test Mother",
        asha_id=TEST_ASHA_ID,
        severity=AlertSeverity.HIGH,
        status=AlertStatus.NEW,
        trigger_reason="High risk screening",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    alert_b = AlertResponse(
        id=uuid4(),
        mother_id=TEST_MOTHER_B_ID,
        mother_name="Mother B",
        asha_id=None,
        severity=AlertSeverity.LOW,
        status=AlertStatus.NEW,
        trigger_reason="Routine check",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repo.add_alert(alert_a)
    repo.add_alert(alert_b)
    return alert_a, alert_b


def test_list_alerts_mother_sees_only_own(mother_client: TestClient):
    """Mother A sees only alerts for herself."""
    repo = get_repository()
    alert_a, _ = _seed_sample_alerts(repo)

    res_m = mother_client.get("/api/v1/alerts")
    assert res_m.status_code == 200
    data_m = res_m.json()
    assert data_m["total"] == 1
    assert data_m["items"][0]["id"] == str(alert_a.id)


def test_list_alerts_asha_sees_assigned_only(asha_client: TestClient):
    """ASHA sees only alerts for assigned mothers."""
    repo = get_repository()
    alert_a, _ = _seed_sample_alerts(repo)

    res_a = asha_client.get("/api/v1/alerts")
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["total"] == 1
    assert data_a["items"][0]["id"] == str(alert_a.id)


def test_list_alerts_admin_sees_all(admin_client: TestClient):
    """Admin sees all alerts across system."""
    repo = get_repository()
    _seed_sample_alerts(repo)

    res_admin = admin_client.get("/api/v1/alerts")
    assert res_admin.status_code == 200
    assert res_admin.json()["total"] == 2



def test_update_alert_status_assigned_asha(asha_client: TestClient):
    """Assigned ASHA updates alert workflow status."""
    repo = get_repository()
    alert = AlertResponse(
        id=uuid4(),
        mother_id=TEST_MOTHER_ID,
        mother_name="Test Mother",
        asha_id=TEST_ASHA_ID,
        severity=AlertSeverity.HIGH,
        status=AlertStatus.NEW,
        trigger_reason="High BP",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repo.add_alert(alert)

    payload = {"status": "CONTACTED", "notes": "Called mother, scheduled home visit"}
    response = asha_client.patch(f"/api/v1/alerts/{alert.id}/status", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CONTACTED"

    # Verify audit trail
    assert any(log["resource_type"] == "alerts" and log["action"] == "UPDATE" for log in repo.audit_logs)


def test_update_alert_status_unassigned_asha_forbidden(asha_client: TestClient):
    """Unassigned ASHA cannot update alert for another mother."""
    repo = get_repository()
    alert_b = AlertResponse(
        id=uuid4(),
        mother_id=TEST_MOTHER_B_ID,  # Not assigned to TEST_ASHA_ID
        mother_name="Mother B",
        asha_id=None,
        severity=AlertSeverity.HIGH,
        status=AlertStatus.NEW,
        trigger_reason="High risk",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repo.add_alert(alert_b)

    payload = {"status": "ACKNOWLEDGED"}
    response = asha_client.patch(f"/api/v1/alerts/{alert_b.id}/status", json=payload)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


# ------------------------------------------------------------------------------
# 5. Visits (POST /api/v1/visits)
# ------------------------------------------------------------------------------
def test_create_visit_assigned_asha(asha_client: TestClient):
    """Assigned ASHA creates visit for assigned mother."""
    payload = {
        "mother_id": str(TEST_MOTHER_ID),
        "visit_date": "2026-10-15T10:00:00Z",
        "notes": "Routine home vitals check",
        "findings": {"blood_pressure": "normal"},
    }
    response = asha_client.post("/api/v1/visits", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["mother_id"] == str(TEST_MOTHER_ID)
    assert data["asha_id"] == str(TEST_ASHA_ID)
    assert data["status"] == "SCHEDULED"


def test_create_visit_unassigned_asha_forbidden(asha_client: TestClient):
    """ASHA attempting to create visit for unassigned mother is forbidden."""
    payload = {
        "mother_id": str(TEST_MOTHER_B_ID),
        "visit_date": "2026-10-15T10:00:00Z",
    }
    response = asha_client.post("/api/v1/visits", json=payload)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


# ------------------------------------------------------------------------------
# 6. Follow-ups (POST /api/v1/followups)
# ------------------------------------------------------------------------------
def test_create_followup_assigned_asha(asha_client: TestClient):
    """Assigned ASHA schedules follow-up task."""
    payload = {
        "mother_id": str(TEST_MOTHER_ID),
        "due_date": "2026-10-20",
        "notes": "Follow up on blood sugar adherence",
    }
    response = asha_client.post("/api/v1/followups", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["mother_id"] == str(TEST_MOTHER_ID)
    assert data["status"] == "PENDING"


def test_create_followup_unassigned_asha_forbidden(asha_client: TestClient):
    """ASHA scheduling follow-up for unassigned mother is rejected with 403."""
    payload = {
        "mother_id": str(TEST_MOTHER_B_ID),
        "due_date": "2026-10-20",
    }
    response = asha_client.post("/api/v1/followups", json=payload)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


# ------------------------------------------------------------------------------
# 7. Risk Timeline (GET /api/v1/mothers/{id}/risk-timeline)
# ------------------------------------------------------------------------------
def test_risk_timeline_mother_own_allowed(mother_client: TestClient):
    """Mother can access her own risk timeline."""
    response = mother_client.get(f"/api/v1/mothers/{TEST_MOTHER_ID}/risk-timeline")
    assert response.status_code == 200
    data = response.json()
    assert data["mother_id"] == str(TEST_MOTHER_ID)
    assert "assessments" in data


def test_risk_timeline_mother_another_forbidden(mother_client: TestClient):
    """Mother A attempting to access Mother B's timeline returns 403."""
    response = mother_client.get(f"/api/v1/mothers/{TEST_MOTHER_B_ID}/risk-timeline")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_risk_timeline_assigned_asha_allowed(asha_client: TestClient):
    """Assigned ASHA can view assigned mother's timeline."""
    response = asha_client.get(f"/api/v1/mothers/{TEST_MOTHER_ID}/risk-timeline")
    assert response.status_code == 200
    assert response.json()["mother_id"] == str(TEST_MOTHER_ID)


def test_risk_timeline_unassigned_asha_forbidden(asha_client: TestClient):
    """Unassigned ASHA viewing unassigned mother's timeline returns 403."""
    response = asha_client.get(f"/api/v1/mothers/{TEST_MOTHER_B_ID}/risk-timeline")
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_risk_timeline_admin_allowed(admin_client: TestClient):
    """Admin can view any mother's risk timeline."""
    response = admin_client.get(f"/api/v1/mothers/{TEST_MOTHER_B_ID}/risk-timeline")
    assert response.status_code == 200
    assert response.json()["mother_id"] == str(TEST_MOTHER_B_ID)
