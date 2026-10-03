"""Security and authorization contract tests.

Verifies:
- 401 Unauthorized semantics when authentication is missing or invalid.
- 403 Forbidden semantics when authenticated role lacks permission.
- Patient isolation: Mother A cannot access Mother B.
- Assignment boundary: ASHA cannot access unassigned mother.
- Standard error envelope returned on 401, 403, and 422 errors.
"""

from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from backend.app.auth.dependencies import verify_patient_access
from backend.app.core.errors import ForbiddenError
from backend.app.schemas.auth import AuthUser, UserRole


# ------------------------------------------------------------------------------
# 1. 401 Unauthorized API Semantics
# ------------------------------------------------------------------------------
def test_missing_auth_returns_401_standard_error(client: TestClient):
    """Calling protected endpoint without Authorization header must return 401."""
    response = client.get("/api/v1/mothers/me")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "message" in data["error"]


def test_malformed_auth_header_returns_401(client: TestClient):
    """Calling with non-Bearer Authorization header must return 401."""
    response = client.get("/api/v1/mothers/me", headers={"Authorization": "Basic 12345"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"


# ------------------------------------------------------------------------------
# 2. 403 Forbidden API Semantics
# ------------------------------------------------------------------------------
def test_role_mismatch_returns_403_standard_error(client: TestClient):
    """Mother role attempting ASHA-only operation (PATCH /alerts/{id}/status) must return 403."""
    alert_id = uuid4()
    # Mother token provided
    headers = {"Authorization": "Bearer test-mother-token"}
    payload = {"status": "ACKNOWLEDGED", "notes": "Test notes"}

    response = client.patch(f"/api/v1/alerts/{alert_id}/status", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FORBIDDEN"
    assert "forbidden" in data["error"]["message"].lower()


def test_mother_cannot_schedule_asha_visit(client: TestClient):
    """Mother role attempting to create ASHA visit must return 403."""
    headers = {"Authorization": "Bearer test-mother-token"}
    payload = {
        "mother_id": str(uuid4()),
        "visit_date": "2026-10-10T10:00:00Z",
    }
    response = client.post("/api/v1/visits", json=payload, headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


# ------------------------------------------------------------------------------
# 3. 422 Validation Error Standard Envelope
# ------------------------------------------------------------------------------
def test_validation_error_returns_standard_envelope(client: TestClient):
    """Payload failing validation must return 422 with standard error envelope."""
    headers = {"Authorization": "Bearer test-mother-token"}
    invalid_payload = {
        "pregnancy_week": 99,  # Invalid: max 45
        "systolic_bp": "not-a-number",
    }
    response = client.post("/api/v1/health-records", json=invalid_payload, headers=headers)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in data["error"]


# ------------------------------------------------------------------------------
# 4. Patient Isolation & Assignment Authorization Boundaries
# ------------------------------------------------------------------------------
def test_mother_accessing_own_records_allowed():
    """Mother accessing her own records is permitted."""
    mother_id = uuid4()
    user = AuthUser(
        id=mother_id,
        role=UserRole.MOTHER,
        full_name="Mother A",
    )
    assert verify_patient_access(user, target_mother_id=mother_id) is True


def test_mother_accessing_another_mother_forbidden():
    """Mother A attempting to access Mother B must raise ForbiddenError."""
    mother_a_id = uuid4()
    mother_b_id = uuid4()
    user_a = AuthUser(
        id=mother_a_id,
        role=UserRole.MOTHER,
        full_name="Mother A",
    )
    with pytest.raises(ForbiddenError) as exc_info:
        verify_patient_access(user_a, target_mother_id=mother_b_id)
    assert exc_info.value.code == "FORBIDDEN"


def test_asha_accessing_assigned_mother_allowed():
    """ASHA accessing an assigned mother is permitted."""
    asha_user_id = uuid4()
    assigned_mother_id = uuid4()
    asha_user = AuthUser(
        id=asha_user_id,
        role=UserRole.ASHA,
        full_name="ASHA Worker",
    )
    assert verify_patient_access(
        asha_user,
        target_mother_id=assigned_mother_id,
        assigned_mother_ids=[assigned_mother_id],
    ) is True


def test_asha_accessing_unassigned_mother_forbidden():
    """ASHA accessing an unassigned mother must raise ForbiddenError."""
    asha_user_id = uuid4()
    unassigned_mother_id = uuid4()
    other_mother_id = uuid4()
    asha_user = AuthUser(
        id=asha_user_id,
        role=UserRole.ASHA,
        full_name="ASHA Worker",
    )
    with pytest.raises(ForbiddenError) as exc_info:
        verify_patient_access(
            asha_user,
            target_mother_id=unassigned_mother_id,
            assigned_mother_ids=[other_mother_id],
        )
    assert exc_info.value.code == "FORBIDDEN"


def test_admin_has_operational_access():
    """Admin role has operational access to records."""
    admin_id = uuid4()
    any_mother_id = uuid4()
    admin_user = AuthUser(
        id=admin_id,
        role=UserRole.ADMIN,
        full_name="System Administrator",
    )
    assert verify_patient_access(admin_user, target_mother_id=any_mother_id) is True
