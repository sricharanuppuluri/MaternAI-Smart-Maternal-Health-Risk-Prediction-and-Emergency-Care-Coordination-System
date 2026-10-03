# MaternAI Backend API Contracts & Schema Specification

This document defines the frozen API request/response contracts, data types, authentication/authorization boundaries, JSON naming conventions, and standard error envelopes established in **Developer 1 Phase 2**.

> **Note for Developer 2**: All data models in this document are frozen. TypeScript interfaces on the frontend should align directly with these specifications.

---

## 1. General API Conventions

### 1.1 Base URL
All version 1 API endpoints are mounted under:
```text
/api/v1
```

### 1.2 JSON Naming Convention
- **Naming Style**: `snake_case` is strictly enforced for all JSON request bodies and response payloads.
- **Example**: `pregnancy_week`, `systolic_bp`, `blood_sugar`, `model_score`, `contributing_factors`.

### 1.3 Authentication Header
Protected endpoints require a valid Supabase Auth Bearer token:
```text
Authorization: Bearer <supabase_access_token>
```

### 1.4 Authorization Semantics
- **401 Unauthorized**: Returned when the `Authorization` header is missing, malformed, or the token is expired/invalid.
- **403 Forbidden**: Returned when the authenticated user lacks the required role, attempts cross-patient access, or an ASHA attempts access to an unassigned mother.

### 1.5 Standard Error Envelope
All error responses adhere to the standard envelope:
```json
{
  "error": {
    "code": "UNAUTHORIZED | FORBIDDEN | VALIDATION_ERROR | NOT_FOUND | NOT_IMPLEMENTED",
    "message": "Human-readable description of the error",
    "details": {}
  }
}
```

### 1.6 Pagination Convention
List endpoints requiring pagination use `page` and `size` query parameters:
- **`page`**: 1-indexed integer, default `1`, minimum `1`.
- **`size`**: Integer, default `20`, minimum `1`, maximum `100`.

**Response Format**:
```json
{
  "items": [],
  "total": 45,
  "page": 1,
  "size": 20,
  "total_pages": 3
}
```

---

## 2. Core Enums

### 2.1 User Roles (`UserRole`)
- `MOTHER`: Expecting or post-partum mother accessing maternal tracking.
- `ASHA`: Community health worker managing assigned maternal cases.
- `ADMIN`: System administrator (server-controlled; client cannot self-assign).

### 2.2 Maternal Risk Levels (`MaternalRiskLevel`)
- `LOW`: Baseline standard monitoring.
- `MEDIUM`: Elevated risk factors requiring ASHA monitoring.
- `HIGH`: Significant clinical risk screening tier requiring urgent evaluation.

### 2.3 Deterministic Safety States (`SafetyStatus`)
- `CLEAR`: No emergency or concerning deterministic rules triggered.
- `CONCERNING`: Explicit clinical rule triggered; flagged for proactive care.
- `EMERGENCY`: Immediate escalation condition triggered; overrides ML risk output.

### 2.4 Alert Severity (`AlertSeverity`)
- `LOW`
- `MEDIUM`
- `HIGH`
- `CRITICAL`

### 2.5 Alert Workflow Status (`AlertStatus`)
- `NEW`: Newly generated alert awaiting review.
- `ACKNOWLEDGED`: ASHA has viewed the alert.
- `CONTACTED`: ASHA has reached out to the mother (call/SMS).
- `VISIT_SCHEDULED`: A home or clinic visit has been scheduled.
- `FOLLOW_UP_PENDING`: Visit completed; pending next check.
- `RESOLVED`: Case closed after clinical intervention or stabilization.
- `ESCALATED`: Case escalated to Medical Officer or higher facility.

### 2.6 Visit Status (`VisitStatus`)
- `SCHEDULED`
- `COMPLETED`
- `CANCELLED`
- `RESCHEDULED`

### 2.7 Follow-up Status (`FollowUpStatus`)
- `PENDING`
- `COMPLETED`
- `OVERDUE`
- `CANCELLED`

---

## 3. Endpoints Inventory & Contract Status

| HTTP Method | Path | Required Role | Implementation Status | Description |
|---|---|---|---|---|
| `GET` | `/` | Public | **IMPLEMENTED** | Root application health check |
| `GET` | `/api/v1/health` | Public | **IMPLEMENTED** | API v1 service health status |
| `POST` | `/api/v1/auth/profile` | Authenticated | **IMPLEMENTED** (Phase 3) | Profile onboarding & role bootstrapping |
| `GET` | `/api/v1/mothers/me` | `MOTHER`, `ADMIN` | **IMPLEMENTED** (Phase 3) | Fetch current mother's profile |
| `POST` | `/api/v1/health-records` | `MOTHER`, `ADMIN` | **IMPLEMENTED** (Phase 3) | Record maternal vital signs |
| `POST` | `/api/v1/symptoms` | `MOTHER`, `ADMIN` | **IMPLEMENTED** (Phase 3) | Submit structured maternal symptoms |
| `POST` | `/api/v1/predictions` | `MOTHER`, `ADMIN` | **IMPLEMENTED** (Phase 3) | Trigger ML risk screening & deterministic safety |
| `GET` | `/api/v1/alerts` | Authenticated | **IMPLEMENTED** (Phase 3) | Paginated alerts queue |
| `PATCH` | `/api/v1/alerts/{id}/status` | `ASHA`, `ADMIN` | **IMPLEMENTED** (Phase 3) | Update alert workflow status |
| `POST` | `/api/v1/visits` | `ASHA`, `ADMIN` | **IMPLEMENTED** (Phase 3) | Record/schedule ASHA visit |
| `POST` | `/api/v1/followups` | `ASHA`, `ADMIN` | **IMPLEMENTED** (Phase 3) | Schedule ASHA follow-up task |
| `GET` | `/api/v1/mothers/{id}/risk-timeline` | Authenticated | **IMPLEMENTED** (Phase 3) | Longitudinal risk & vitals timeline |


---

## 4. Detailed Request & Response Schemas

### 4.1 Health Check (`GET /api/v1/health`)
- **Status**: `IMPLEMENTED`
- **Response**:
```json
{
  "status": "healthy",
  "app": "MaternAI",
  "version": "0.1.0",
  "environment": "development"
}
```

### 4.2 Profile Bootstrapping (`POST /api/v1/auth/profile`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 3)
- **Request Body**:
```json
{
  "full_name": "Pooja Devi",
  "role": "MOTHER",
  "phone": "+91-9876543210"
}
```
- **Response Body** (`201 Created`):
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "role": "MOTHER",
  "full_name": "Pooja Devi",
  "phone": "+91-9876543210",
  "created_at": "2026-10-03T10:00:00Z",
  "updated_at": "2026-10-03T10:00:00Z"
}
```

### 4.3 Mother Profile (`GET /api/v1/mothers/me`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 4)
- **Response Body**:
```json
{
  "id": "223e4567-e89b-12d3-a456-426614174001",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "full_name": "Pooja Devi",
  "date_of_birth": "1998-05-14",
  "age_years": 28,
  "gestational_age_weeks": 26,
  "expected_due_date": "2027-01-10",
  "assigned_asha_id": "323e4567-e89b-12d3-a456-426614174002",
  "last_risk_level": "LOW",
  "phone": "+91-9876543210",
  "created_at": "2026-10-03T10:00:00Z"
}
```

### 4.4 Health Records (`POST /api/v1/health-records`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 4)
- **Request Body**:
```json
{
  "pregnancy_week": 26,
  "systolic_bp": 120.0,
  "diastolic_bp": 80.0,
  "blood_sugar": 92.0,
  "hemoglobin": 11.2,
  "weight_kg": 62.5,
  "body_temperature": 36.6,
  "heart_rate": 76.0,
  "recorded_at": "2026-10-03T10:30:00Z"
}
```
- **Response Body** (`201 Created`):
```json
{
  "id": "423e4567-e89b-12d3-a456-426614174003",
  "mother_id": "223e4567-e89b-12d3-a456-426614174001",
  "pregnancy_week": 26,
  "systolic_bp": 120.0,
  "diastolic_bp": 80.0,
  "blood_sugar": 92.0,
  "hemoglobin": 11.2,
  "weight_kg": 62.5,
  "body_temperature": 36.6,
  "heart_rate": 76.0,
  "recorded_by": "123e4567-e89b-12d3-a456-426614174000",
  "recorded_at": "2026-10-03T10:30:00Z",
  "created_at": "2026-10-03T10:30:00Z"
}
```

### 4.5 Symptoms (`POST /api/v1/symptoms`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 4)
- **Request Body**:
```json
{
  "health_record_id": "423e4567-e89b-12d3-a456-426614174003",
  "symptoms": [
    {
      "symptom_code": "headache",
      "severity": 2,
      "notes": "Mild frontal headache in the morning"
    },
    {
      "symptom_code": "swelling_feet",
      "severity": 1,
      "notes": "Mild pedal swelling after walking"
    }
  ]
}
```
- **Response Body** (`201 Created`):
```json
[
  {
    "id": "523e4567-e89b-12d3-a456-426614174004",
    "mother_id": "223e4567-e89b-12d3-a456-426614174001",
    "health_record_id": "423e4567-e89b-12d3-a456-426614174003",
    "symptom_code": "headache",
    "severity": 2,
    "notes": "Mild frontal headache in the morning",
    "recorded_at": "2026-10-03T10:35:00Z",
    "created_at": "2026-10-03T10:35:00Z"
  }
]
```

### 4.6 Predictions (`POST /api/v1/predictions`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 5)
- **Request Body**:
```json
{
  "health_record_id": "423e4567-e89b-12d3-a456-426614174003"
}
```
- **Response Body** (`201 Created`):
```json
{
  "id": "623e4567-e89b-12d3-a456-426614174005",
  "mother_id": "223e4567-e89b-12d3-a456-426614174001",
  "health_record_id": "423e4567-e89b-12d3-a456-426614174003",
  "risk_level": "LOW",
  "model_score": 0.18,
  "model_version": "v0.1.0",
  "feature_schema_version": "v1.0",
  "contributing_factors": [
    {
      "feature": "hemoglobin",
      "direction": "DECREASES_RISK",
      "value": 11.2
    }
  ],
  "created_at": "2026-10-03T10:35:05Z"
}
```

### 4.7 Alerts Queue (`GET /api/v1/alerts`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 4)
- **Query Params**: `page=1&size=20`
- **Response Body**:
```json
{
  "items": [
    {
      "id": "723e4567-e89b-12d3-a456-426614174006",
      "mother_id": "223e4567-e89b-12d3-a456-426614174001",
      "mother_name": "Pooja Devi",
      "asha_id": "323e4567-e89b-12d3-a456-426614174002",
      "severity": "HIGH",
      "status": "NEW",
      "trigger_reason": "High systolic blood pressure reading (145 mmHg)",
      "safety_event_id": null,
      "prediction_id": "623e4567-e89b-12d3-a456-426614174005",
      "created_at": "2026-10-03T10:40:00Z",
      "updated_at": "2026-10-03T10:40:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20,
  "total_pages": 1
}
```

### 4.8 Update Alert Status (`PATCH /api/v1/alerts/{id}/status`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 4)
- **Request Body**:
```json
{
  "status": "ACKNOWLEDGED",
  "notes": "Reviewed vital alert; contacting mother"
}
```
- **Response Body**: Updated `AlertResponse` object.

### 4.9 Visits (`POST /api/v1/visits`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 4)
- **Request Body**:
```json
{
  "mother_id": "223e4567-e89b-12d3-a456-426614174001",
  "alert_id": "723e4567-e89b-12d3-a456-426614174006",
  "visit_date": "2026-10-04T09:00:00Z",
  "notes": "Scheduled home visit to repeat blood pressure check",
  "findings": {}
}
```

### 4.10 Follow-ups (`POST /api/v1/followups`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 4)
- **Request Body**:
```json
{
  "mother_id": "223e4567-e89b-12d3-a456-426614174001",
  "alert_id": "723e4567-e89b-12d3-a456-426614174006",
  "due_date": "2026-10-07",
  "notes": "Follow up on iron supplement intake and headaches"
}
```

### 4.11 Longitudinal Risk Timeline (`GET /api/v1/mothers/{id}/risk-timeline`)
- **Status**: `CONTRACT FROZEN` (Implementation scheduled for Phase 4/5)
- **Response Body**:
```json
{
  "mother_id": "223e4567-e89b-12d3-a456-426614174001",
  "current_risk_level": "LOW",
  "assessments": [
    {
      "timestamp": "2026-10-03T10:35:05Z",
      "risk_level": "LOW",
      "assessment_type": "PREDICTION",
      "trigger_reason": null,
      "systolic_bp": 120.0,
      "diastolic_bp": 80.0,
      "hemoglobin": 11.2,
      "blood_sugar": 92.0
    }
  ]
}
```

---

## 5. Developer Authorization Matrix & Security Boundaries

The following matrix documents the database Row Level Security (RLS) and backend API access boundaries for all 17 entities:

| Entity | Mother Access | Assigned ASHA Access | Unassigned ASHA Access | Admin Access | Client Direct Write? | Notes / Anti-Escalation Safeguards |
|---|---|---|---|---|---|---|
| `profiles` | SELECT (own), UPDATE (own) | SELECT (assigned mothers) | DENIED | ALL (SELECT, INSERT, UPDATE, DELETE) | Restricted | **Trigger `trg_prevent_role_escalation`** strictly prohibits users from changing `role` column. |
| `mother_profiles` | SELECT (own), INSERT (own), UPDATE (own) | SELECT (assigned), UPDATE (assigned) | DENIED | ALL | Restricted | **Trigger `trg_prevent_mother_authoritative_update`** prevents Mother from updating `last_risk_level` or self-reassigning `assigned_asha_id`. |
| `asha_profiles` | SELECT (all authenticated) | SELECT (all), UPDATE (own) | SELECT (all), UPDATE (own) | ALL | Restricted | ASHA profile identity; worker code and village assignment. |
| `asha_assignments` | SELECT (own assignment) | SELECT (own assignments), INSERT, UPDATE | DENIED | ALL | Restricted | Authoritative mapping table for assignment-based authorization. Only ASHA/Admin can insert/update assignments. |
| `health_records` | SELECT (own), INSERT (own) | SELECT (assigned), INSERT (assigned) | DENIED | ALL | Insert Only | **Immutable**: UPDATE and DELETE are restricted to ADMIN to protect medical record integrity. |
| `symptoms` | SELECT (own), INSERT (own) | SELECT (assigned), INSERT (assigned) | DENIED | ALL | Insert Only | **Immutable**: UPDATE and DELETE are restricted to ADMIN once logged. |
| `model_versions` | SELECT (all authenticated) | SELECT (all authenticated) | SELECT (all authenticated) | ALL | DENIED (Read Only) | Public model registry; model artifacts and metrics managed server-side. |
| `predictions` | SELECT (own) | SELECT (assigned) | DENIED | ALL | **DENIED** (Server Only) | Authoritative ML screening output; direct client INSERT/UPDATE is strictly prohibited by RLS. |
| `safety_events` | SELECT (own) | SELECT (assigned) | DENIED | ALL | **DENIED** (Server Only) | Deterministic safety escalation output; direct client INSERT/UPDATE is strictly prohibited by RLS. |
| `alerts` | SELECT (own) | SELECT (assigned), UPDATE (status, notes) | DENIED | ALL | Restricted | Generated by decision engine. ASHA can only update workflow `status` and `notes`. |
| `visits` | SELECT (own) | SELECT (assigned), INSERT (assigned), UPDATE (assigned) | DENIED | ALL | ASHA Only | In-person and home visits scheduled and conducted by assigned ASHA. |
| `follow_ups` | SELECT (own) | SELECT (assigned), INSERT (assigned), UPDATE (assigned) | DENIED | ALL | ASHA Only | Follow-up tracking and status updates by assigned ASHA. |
| `appointments` | SELECT (own), INSERT (own), UPDATE (own) | SELECT (assigned), INSERT (assigned), UPDATE (assigned) | DENIED | ALL | Yes | Scheduled clinical appointments. |
| `medication_reminders` | SELECT (own), INSERT (own), UPDATE (own) | SELECT (assigned), INSERT (assigned), UPDATE (assigned) | DENIED | ALL | Yes | Prescribed medication reminders and adherence. |
| `chat_sessions` | SELECT (own), INSERT (own), UPDATE (own), DELETE (own) | DENIED | DENIED | ALL | Mother Only | Private maternal conversation sessions. |
| `chat_messages` | SELECT (own session), INSERT (own session) | DENIED | DENIED | ALL | Mother Only | Chat transcript; UPDATE/DELETE restricted. |
| `audit_logs` | **DENIED** (No read) | **DENIED** (No read) | **DENIED** (No read) | SELECT (Admin Only) | **DENIED** (Server Only) | Immutable system audit log. UPDATE and DELETE are strictly denied for all roles including Admin. |

---

## 6. Clinical & Domain Clarifications & Deferred Mappings

### 6.1 `model_score` Interpretation
- `model_score` is defined as a floating-point number between `0.0` and `1.0`.
- Per project documentation, `model_score` is an **internal screening metric**, NOT a calibrated clinical probability.
- Developer 2's frontend must NOT present `model_score` as a medical certainty or probability percentage. User-facing UI must display only the categorical risk classification: `LOW`, `MEDIUM`, or `HIGH`.

### 6.2 Safety Status vs. Alert Severity Mapping (Deferred to Phase 4/6)
- The documentation establishes two independent enum taxonomies:
  - `SafetyStatus`: `CLEAR`, `CONCERNING`, `EMERGENCY`
  - `AlertSeverity`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
  - `MaternalRiskLevel`: `LOW`, `MEDIUM`, `HIGH`
- While a future mapping is anticipated (e.g., `EMERGENCY` -> `CRITICAL` alert, `CONCERNING` -> `HIGH` alert), **no authoritative mapping is hardcoded in Phase 2**. Any mapping between these domain concepts remains deferred to Phase 4 (Decision Layer) and Phase 6 (Safety Engine) upon clinical validation.

### 6.3 Technical Validation Bounds vs. Clinical Diagnostic Thresholds
- Pydantic fields in `HealthRecordCreate` specify technical boundary constraints for input sanitization (e.g., `systolic_bp` between 50 and 250 mmHg, `pregnancy_week` between 1 and 45).
- These boundaries are **data integrity filters**, not diagnostic criteria or clinical decision thresholds.

### 6.4 Production Authentication Boundary & Cryptographic Verification Status
- **Cryptographic Verification (IMPLEMENTED - Phase 4)**: Production authentication uses PyJWT to cryptographically verify Supabase Auth access tokens:
  - Missing token or non-Bearer scheme -> `401 Unauthorized`
  - Malformed or non-3-part token -> `401 Unauthorized`
  - Unsigned or invalid signature -> `401 Unauthorized`
  - Expired token (`exp` claim) -> `401 Unauthorized`
  - Unconfigured JWT verification secret -> fails closed with `401 Unauthorized`
- **Authoritative Identity & Role Resolution**: Authenticated user identity is extracted from `sub`. The user's application role is resolved strictly from the authoritative database `profiles` table. Client claims, request body role fields, and arbitrary JWT `user_metadata.role` claims are **never trusted** for authorization. Fresh signups without an existing database profile default strictly to the unprivileged `MOTHER` role.
- **Profile Role Integrity (`POST /api/v1/auth/profile`)**: Prohibits non-admin users from self-promoting to `ASHA` or `ADMIN`, and disallows mutation of existing user roles without administrative authorization.
- **Test Authentication Isolation**: Deterministic test identities (`mother_client`, `asha_client`, `admin_client`) bypass the production verification boundary strictly via explicit FastAPI `app.dependency_overrides` in testing fixtures (`backend/tests/conftest.py`). The production dependency contains zero test-token parsing logic.

### 6.5 Row Level Security (RLS) Verification Status
- **Static Migration & Policy Analysis**: **PASSED**. All 17 entities, explicit `search_path = public, auth` on security definer functions, anti-escalation triggers (`trg_prevent_role_escalation`, `trg_prevent_mother_authoritative_update`), and audit log immutability are verified via static regex and AST analysis (`backend/tests/security/test_database_rls_contracts.py`).
- **Runtime PostgreSQL / Supabase RLS Execution**: **BLOCKED / DEFERRED**. Live execution of SQL role-switching and RLS queries against an active database could not be executed locally because neither Docker, the Supabase CLI, nor local PostgreSQL (`psql`) are installed on the local host machine. A dedicated live integration test runner (`backend/tests/integration/test_supabase_rls_live.py`) detects environment availability and cleanly defers execution until a running PostgreSQL / Supabase instance is provided.
