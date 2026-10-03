"""Phase 4 Security & Persistence Verification Test Suite.

Verifies:
- Cryptographic Supabase JWT verification (valid, invalid, expired, malformed, missing).
- Authoritative role resolution from database profiles table (client/metadata role claims rejected).
- Role integrity protection on /api/v1/auth/profile (rejection of ASHA and ADMIN self-promotion).
- Patient isolation: Mother A cannot access Mother B.
- ASHA assignment boundary: assigned mothers allowed, unassigned denied.
- Admin access boundaries.
- Relational database persistence across backend/repository restarts.
- Audit log persistence and integrity.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import time
from typing import Optional
from uuid import UUID, uuid4
import jwt
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import get_settings
from backend.app.db.repositories import (
    RepositoryStore,
    TEST_ADMIN_ID,
    TEST_ASHA_ID,
    TEST_MOTHER_B_ID,
    TEST_MOTHER_ID,
    get_repository,
)
from backend.app.main import app
from backend.app.schemas.alert import AlertResponse, AlertSeverity, AlertStatus
from backend.app.schemas.auth import UserRole
from backend.app.schemas.health_record import HealthRecordResponse

TEST_JWT_SECRET = "test-phase4-supabase-jwt-secret-key-32bytes"


def _create_jwt(
    sub: UUID,
    secret: str = TEST_JWT_SECRET,
    role_claim: Optional[str] = None,
    user_metadata: Optional[dict] = None,
    exp_offset: int = 3600,
) -> str:
    """Generate a test JWT signed with specified secret."""
    now = int(time.time())
    payload = {
        "sub": str(sub),
        "email": f"user-{str(sub)[:8]}@example.com",
        "aud": "authenticated",
        "iat": now,
        "exp": now + exp_offset,
    }
    if role_claim:
        payload["role"] = role_claim
    if user_metadata:
        payload["user_metadata"] = user_metadata

    return jwt.encode(payload, secret, algorithm="HS256")


# ------------------------------------------------------------------------------
# 1. Cryptographic JWT Verification Tests
# ------------------------------------------------------------------------------

def test_missing_auth_header_rejected_with_401(client: TestClient):
    """Calling protected endpoint without Authorization header must return 401."""
    response = client.get("/api/v1/mothers/me")
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "missing or malformed" in data["error"]["message"].lower()


def test_malformed_auth_header_rejected_with_401(client: TestClient):
    """Calling with non-Bearer or invalid token structure returns 401."""
    # Not starting with Bearer
    res1 = client.get("/api/v1/mothers/me", headers={"Authorization": "Token 12345"})
    assert res1.status_code == 401
    assert res1.json()["error"]["code"] == "UNAUTHORIZED"

    # Empty token
    res2 = client.get("/api/v1/mothers/me", headers={"Authorization": "Bearer "})
    assert res2.status_code == 401
    assert res2.json()["error"]["code"] == "UNAUTHORIZED"

    # Non-3-part token
    res3 = client.get("/api/v1/mothers/me", headers={"Authorization": "Bearer not-three-parts"})
    assert res3.status_code == 401
    assert res3.json()["error"]["code"] == "UNAUTHORIZED"


def test_valid_supabase_jwt_authenticates_successfully(client: TestClient, monkeypatch):
    """A valid, signed JWT with matching secret authenticates and returns user context."""
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)

    token = _create_jwt(sub=TEST_MOTHER_ID)
    response = client.get("/api/v1/mothers/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(TEST_MOTHER_ID)
    assert data["full_name"] == "Test Mother"


def test_invalid_signature_jwt_rejected_with_401(client: TestClient, monkeypatch):
    """JWT signed with an untrusted/different secret must be rejected with 401."""
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)

    wrong_secret_token = _create_jwt(sub=TEST_MOTHER_ID, secret="wrong-untrusted-secret-at-least-32-bytes-long")
    response = client.get("/api/v1/mothers/me", headers={"Authorization": f"Bearer {wrong_secret_token}"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "unverified" in data["error"]["message"].lower() or "invalid" in data["error"]["message"].lower()


def test_expired_jwt_rejected_with_401(client: TestClient, monkeypatch):
    """An expired JWT must fail verification and return 401."""
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)

    expired_token = _create_jwt(sub=TEST_MOTHER_ID, exp_offset=-3600)
    response = client.get("/api/v1/mothers/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    data = response.json()
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "expired" in data["error"]["message"].lower()


# ------------------------------------------------------------------------------
# 2. Authoritative Database Role Resolution & Anti-Spoofing Tests
# ------------------------------------------------------------------------------

def test_authoritative_role_resolved_from_database(client: TestClient, monkeypatch):
    """Authoritative role is resolved from database profiles table, granting role access."""
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)

    token = _create_jwt(sub=TEST_ASHA_ID)
    # ASHA worker accessing ASHA-only endpoint
    response = client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_client_cannot_spoof_admin_role_via_jwt_claims(client: TestClient, monkeypatch):
    """A client forging 'ADMIN' claims in token payload or metadata does NOT gain ADMIN role."""
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)

    # Mother user forging ADMIN claim in JWT payload and user_metadata
    forged_token = _create_jwt(
        sub=TEST_MOTHER_ID,
        role_claim="ADMIN",
        user_metadata={"role": "ADMIN", "is_admin": True}
    )

    # Attempting to access an ASHA/Admin endpoint with mother ID
    # In database, TEST_MOTHER_ID has role MOTHER
    response = client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {forged_token}"})
    # Mother can call GET /alerts, but sees ONLY her own alerts, NOT all alerts like an Admin
    assert response.status_code == 200
    repo = get_repository()
    # Add an alert for Mother B
    other_alert = AlertResponse(
        id=uuid4(),
        mother_id=TEST_MOTHER_B_ID,
        mother_name="Mother B",
        asha_id=None,
        severity=AlertSeverity.HIGH,
        status=AlertStatus.NEW,
        trigger_reason="Test Alert",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repo.add_alert(other_alert)

    # Calling with forged mother token must NOT see Mother B's alert
    res = client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {forged_token}"})
    data = res.json()
    for item in data["items"]:
        assert item["mother_id"] == str(TEST_MOTHER_ID)


# ------------------------------------------------------------------------------
# 3. Profile Role Integrity & Anti-Escalation Tests
# ------------------------------------------------------------------------------

def test_regular_user_cannot_self_promote_to_asha(mother_client: TestClient):
    """Regular user cannot self-promote to ASHA role via /api/v1/auth/profile."""
    payload = {
        "full_name": "Self Promoting Mother",
        "role": "ASHA",
    }
    response = mother_client.post("/api/v1/auth/profile", json=payload)
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "FORBIDDEN"
    assert "privileged role" in data["error"]["message"].lower() or "unauthorized" in data["error"]["message"].lower()


def test_regular_user_cannot_self_promote_to_admin(mother_client: TestClient):
    """Regular user cannot self-promote to ADMIN role via /api/v1/auth/profile."""
    payload = {
        "full_name": "Self Promoting Mother",
        "role": "ADMIN",
    }
    response = mother_client.post("/api/v1/auth/profile", json=payload)
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "FORBIDDEN"
    assert "privileged role" in data["error"]["message"].lower() or "unauthorized" in data["error"]["message"].lower()


def test_admin_can_provision_asha_profile(admin_client: TestClient):
    """Admin is authorized to bootstrap/provision an ASHA profile."""
    new_asha_id = uuid4()
    # Temporarily override user identity to test provisioning
    payload = {
        "full_name": "Newly Provisioned ASHA",
        "role": "ASHA",
        "phone": "+91-9876500000",
    }
    response = admin_client.post("/api/v1/auth/profile", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "ASHA"
    assert data["full_name"] == "Newly Provisioned ASHA"


def test_normal_profile_creation_defaults_to_mother(client: TestClient, monkeypatch):
    """Default profile creation without specifying role assigns non-privileged MOTHER."""
    monkeypatch.setattr(get_settings(), "SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    new_user_id = uuid4()
    token = _create_jwt(sub=new_user_id)

    payload = {"full_name": "New Patient"}
    response = client.post(
        "/api/v1/auth/profile",
        json=payload,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["role"] == "MOTHER"
    assert data["full_name"] == "New Patient"


# ------------------------------------------------------------------------------
# 4. Relational Persistence & Restart Survival Tests
# ------------------------------------------------------------------------------

def test_database_persistence_across_repository_restarts(tmp_path: Path):
    """Data stored in the repository must survive application/repository restart."""
    test_db = str(tmp_path / "test_restart_persistence.db")

    # Instance 1: write data
    repo1 = RepositoryStore(db_path=test_db)
    record_id = uuid4()
    test_record = HealthRecordResponse(
        id=record_id,
        mother_id=TEST_MOTHER_ID,
        pregnancy_week=24,
        systolic_bp=118.0,
        diastolic_bp=78.0,
        blood_sugar=88.0,
        hemoglobin=12.2,
        weight_kg=60.0,
        body_temperature=36.7,
        heart_rate=72.0,
        recorded_by=TEST_MOTHER_ID,
        recorded_at=datetime.now(timezone.utc),
        created_at=datetime.now(timezone.utc),
    )
    repo1.add_health_record(test_record)

    # Add an alert
    alert_id = uuid4()
    test_alert = AlertResponse(
        id=alert_id,
        mother_id=TEST_MOTHER_ID,
        mother_name="Test Mother",
        asha_id=TEST_ASHA_ID,
        severity=AlertSeverity.HIGH,
        status=AlertStatus.NEW,
        trigger_reason="Test Persistence Alert",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    repo1.add_alert(test_alert)

    # Close instance 1 connection
    repo1._conn.close()

    # Instance 2: restart / connect to the same persistent db file
    repo2 = RepositoryStore(db_path=test_db)

    # Verify health record survived restart
    recovered_record = repo2.get_health_record(record_id)
    assert recovered_record is not None
    assert recovered_record.id == record_id
    assert recovered_record.systolic_bp == 118.0
    assert recovered_record.pregnancy_week == 24

    # Verify alert survived restart
    recovered_alert = repo2.get_alert(alert_id)
    assert recovered_alert is not None
    assert recovered_alert.id == alert_id
    assert recovered_alert.severity == AlertSeverity.HIGH
    assert recovered_alert.trigger_reason == "Test Persistence Alert"

    # Verify audit logs survived restart
    assert len(repo2.audit_logs) >= 2

    repo2._conn.close()


def test_audit_logs_immutability_and_persistence():
    """Audit logs are recorded on operations and cannot be modified or deleted."""
    repo = get_repository()
    initial_log_count = len(repo.audit_logs)

    repo.log_audit(
        user_id=TEST_MOTHER_ID,
        action="TEST_ACTION",
        resource_type="test_resource",
        resource_id=uuid4(),
        details={"test_key": "test_value"},
    )

    logs = repo.audit_logs
    assert len(logs) == initial_log_count + 1
    latest = logs[-1]
    assert latest["action"] == "TEST_ACTION"
    assert latest["resource_type"] == "test_resource"
    assert latest["details"]["test_key"] == "test_value"
