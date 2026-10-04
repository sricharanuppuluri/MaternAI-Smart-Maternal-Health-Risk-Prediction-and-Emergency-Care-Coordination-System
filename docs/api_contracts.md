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
- **Status**: `CONTRACT FROZEN - IMPLEMENTED`
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

### 4.12 Create Chat Session (`POST /api/v1/chat/sessions`)
- **Status**: `CONTRACT FROZEN - IMPLEMENTED (Phase 6)`
- **Authentication**: Required (`Bearer <supabase_access_token>`).
- **Authorization & Ownership**:
  - `MOTHER`: Defaults to authenticated mother's ID. If `mother_id` is supplied, must match authenticated user, otherwise `403 Forbidden`.
  - `ASHA`: `mother_id` is required; must be an actively assigned mother, otherwise `403 Forbidden`.
  - `ADMIN`: Permitted for all mothers.
- **Request Body (`ChatSessionCreate`)**:
```json
{
  "mother_id": "223e4567-e89b-12d3-a456-426614174001",
  "title": "First Trimester Nutrition and Symptoms",
  "language": "en"
}
```
- **Response Body (`ChatSessionResponse`)** (HTTP 201 Created):
```json
{
  "id": "823e4567-e89b-12d3-a456-426614174010",
  "mother_id": "223e4567-e89b-12d3-a456-426614174001",
  "title": "First Trimester Nutrition and Symptoms",
  "language": "en",
  "created_at": "2026-10-04T10:00:00Z"
}
```
- **Error Responses**:
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `403 Forbidden`: Patient isolation violation or unassigned ASHA access.
  - `422 Unprocessable Entity`: Validation failure.
- **Audit Behavior**: Emits `CREATE_CHAT_SESSION` in `audit_logs`.

### 4.13 Submit Chat Message (`POST /api/v1/chat/sessions/{session_id}/messages`)
- **Status**: `CONTRACT FROZEN - IMPLEMENTED (Phase 6)`
- **Authentication**: Required (`Bearer <supabase_access_token>`).
- **Authorization & Ownership**:
  - `MOTHER`: Can submit messages only to sessions belonging to the authenticated mother.
  - `ASHA`: Can submit messages only to sessions belonging to assigned mothers.
  - `ADMIN`: Permitted for all sessions.
  - Cross-patient / unassigned access returns `403 Forbidden`.
- **Request Body (`ChatMessageCreate`)**:
```json
{
  "content": "Can you explain what maternal health records are currently tracked?",
  "language": "en"
}
```
  *(Note: Request schema enforces `extra='forbid'`. Any attempt by client to inject `safety_state`, `sender_role`, or safety policy overrides is rejected with 422 Unprocessable Entity).*
- **Response Body (`ChatTurnResponse`)** (HTTP 201 Created):
```json
{
  "session_id": "823e4567-e89b-12d3-a456-426614174010",
  "user_message": {
    "id": "923e4567-e89b-12d3-a456-426614174011",
    "session_id": "823e4567-e89b-12d3-a456-426614174010",
    "sender_role": "USER",
    "content": "Can you explain what maternal health records are currently tracked?",
    "metadata": {
      "language": "en",
      "authoritative_safety_state": "CLEAR"
    },
    "created_at": "2026-10-04T10:05:00Z"
  },
  "assistant_message": {
    "id": "923e4567-e89b-12d3-a456-426614174012",
    "session_id": "823e4567-e89b-12d3-a456-426614174010",
    "sender_role": "ASSISTANT",
    "content": "Authoritative safety state: CLEAR. Message received and logged in care session. Detailed clinical safety policy is pending authoritative specification.",
    "metadata": {
      "safety_state": "CLEAR",
      "language": "en"
    },
    "created_at": "2026-10-04T10:05:01Z"
  },
  "safety_state": "CLEAR",
  "safety_events": [],
  "disclaimer": "MaternAI provides maternal decision support and educational guidance only. It does not replace professional medical diagnosis, advice, or treatment."
}
```
- **Authoritative Safety Evaluation & Policy Boundary**:
  - `SafetyStatus`: `CLEAR | CONCERNING | EMERGENCY` is the authoritative safety-state contract.
  - Clinical criteria for assigning those states must come exclusively from the authoritative safety policy engine (`SafetyEngine`).
  - No speculative symptom keyword mappings (e.g. fever -> CONCERNING, bleeding -> EMERGENCY) or invented clinical escalation rules are hardcoded.
  - Where clinical policy is pending authoritative specification, the backend deterministically maintains an explicit service boundary returning `CLEAR`.
  - Assistant content remains neutral decision-support / informational output and must not invent treatment instructions, referral requirements, urgency rules, monitoring schedules, or diagnosis claims.
  - `SafetyStatus` (`CLEAR | CONCERNING | EMERGENCY`) and `MaternalRiskLevel` (`LOW | MEDIUM | HIGH`) remain strictly separate; the assistant/agent cannot derive or override either state.
  - When an authoritative safety policy rule triggers `EMERGENCY` or `CONCERNING`, the backend immutably records an authoritative row in `safety_events`.
- **Error Responses**:
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `403 Forbidden`: Cross-patient / unassigned session access.
  - `404 Not Found`: Session ID does not exist.
  - `422 Unprocessable Entity`: Validation failure or attempted client field injection.
- **Audit Behavior**: Emits `CREATE_CHAT_MESSAGE` in `audit_logs`.

### 4.14 Query Decision-Support Agent (`POST /api/v1/agent/query`)
- **Status**: `CONTRACT FROZEN - IMPLEMENTED (Phase 6)`
- **Authentication**: Required (`Bearer <supabase_access_token>`).
- **Authorization & Ownership**:
  - `MOTHER`: Can query agent only for herself.
  - `ASHA`: Can query agent only for assigned mothers.
  - `ADMIN`: Permitted for all mothers.
  - Cross-patient / unassigned access returns `403 Forbidden`.
- **Authorized Tools Explicit Allowlist (`AgentToolName`)**:
  1. `get_health_summary`: Reads maternal profile, baseline gestational age, and assigned ASHA.
  2. `get_recent_vitals`: Reads recent maternal vital recordings within patient boundary.
  3. `get_recent_symptoms`: Reads reported maternal symptoms within patient boundary.
  4. `check_safety_alerts`: Reads active safety events and coordination alerts.
  5. `get_upcoming_visits`: Reads scheduled visits and follow-up tasks.
  6. `explain_risk_factors`: Explains contributing risk factors from latest ML screening prediction.
  *Any requested tool outside this allowlist is strictly rejected with `422 Unprocessable Entity`.*
- **Request Body (`AgentQueryRequest`)**:
```json
{
  "mother_id": "223e4567-e89b-12d3-a456-426614174001",
  "query": "What are my upcoming visits and risk factors?",
  "requested_tools": [
    "get_upcoming_visits",
    "explain_risk_factors"
  ],
  "language": "en"
}
```
- **Response Body (`AgentQueryResponse`)** (HTTP 200 OK):
```json
{
  "mother_id": "223e4567-e89b-12d3-a456-426614174001",
  "query": "What are my upcoming visits and risk factors?",
  "response": "Authoritative Safety State: CLEAR.\n\nAuthorized Context Evaluated:\n- get_upcoming_visits: Retrieved 1 visit(s) and 1 follow-up task(s).\n- explain_risk_factors: Latest screening tier: LOW. 2 contributing factor(s).",
  "safety_state": "CLEAR",
  "tools_invoked": [
    {
      "tool_name": "get_upcoming_visits",
      "status": "SUCCESS",
      "summary": "Retrieved 1 visit(s) and 1 follow-up task(s).",
      "data": {
        "visits_count": 1,
        "followups_count": 1
      }
    },
    {
      "tool_name": "explain_risk_factors",
      "status": "SUCCESS",
      "summary": "Latest screening tier: LOW. 2 contributing factor(s).",
      "data": {
        "risk_level": "LOW",
        "factors": [
          {"feature": "systolic_bp", "impact": 0.45},
          {"feature": "blood_sugar", "impact": 0.32}
        ]
      }
    }
  ],
  "disclaimer": "MaternAI Agent provides maternal decision support and informational coordination only. It does not replace professional medical diagnosis, advice, or treatment.",
  "created_at": "2026-10-04T10:10:00Z"
}
```
- **Authoritative Safety Precedence & Policy Boundary**:
  - `safety_state` is determined exclusively by the backend `SafetyEngine` policy boundary.
  - The agent reasoning or LLM cannot override, infer, or fabricate the safety state.
  - The agent output reports factual data from authorized tools without independent clinical reinterpretation or invented care recommendations.
  - `SafetyStatus` (`CLEAR | CONCERNING | EMERGENCY`) and `MaternalRiskLevel` (`LOW | MEDIUM | HIGH`) remain strictly separate; the agent cannot derive or override either state.
- **Error Responses**:
  - `401 Unauthorized`: Missing or invalid Bearer token.
  - `403 Forbidden`: Cross-patient / unassigned access.
  - `422 Unprocessable Entity`: Validation error, unapproved tool requested, or attempted client field injection.
- **Audit Behavior**: Emits `AGENT_QUERY` in `audit_logs`.


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
| `chat_sessions` | SELECT (own), INSERT (own), UPDATE (own), DELETE (own) | SELECT (assigned), INSERT (assigned) | DENIED | ALL | Mother & Assigned ASHA | Private maternal conversation sessions. Mothers can access own; ASHAs can access assigned. |
| `chat_messages` | SELECT (own session), INSERT (own session) | SELECT (assigned session), INSERT (assigned session) | DENIED | ALL | Mother & Assigned ASHA | Chat transcript; UPDATE/DELETE restricted to protect conversation integrity. |
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

### 6.6 Authorized Agent Tools Allowlist & Safety Precedence (Phase 6)
- **Explicit Authorized Tool Allowlist (`AgentToolName`)**:
  - `get_health_summary`: Retrieves maternal profile baseline (gestational week, assigned ASHA, last risk level).
  - `get_recent_vitals`: Retrieves recorded vital measurements for the authorized mother.
  - `get_recent_symptoms`: Retrieves reported symptoms within the authorized mother scope.
  - `check_safety_alerts`: Retrieves recorded safety events and workflow alerts.
  - `get_upcoming_visits`: Retrieves scheduled in-person visits and follow-up tracking tasks.
  - `explain_risk_factors`: Retrieves structured explanation of contributing risk factors from latest ML prediction without autonomous diagnosis.
- **Strict Allowlist Enforcement**: Any tool requested outside `AgentToolName` is rejected with HTTP `422 Unprocessable Entity`.
- **Deterministic Safety Precedence**:
  - Queries describing acute emergency red flags immediately trigger `safety_state = EMERGENCY` and authoritatively record a safety event in the database.
  - The decision-support agent NEVER overrides, alters, or downgrades a deterministic safety decision.
  - Safety state is strictly categorical (`CLEAR`, `CONCERNING`, `EMERGENCY`) and must never be converted or mapped to clinical risk levels (`LOW`, `MEDIUM`, `HIGH`).

