# MaternAI System Architecture — Phase 0

This document outlines the system architecture for **MaternAI** (Multilingual Maternal-Health Risk Prediction and Emergency Care Coordination System).

---

## 1. System Overview

```text
React / TypeScript (Frontend)
        ↓
FastAPI (Backend)
        ↓
Authentication / Authorization (Supabase Auth & Role Validation)
        ↓
Validation (Pydantic)
        ↓
Safety Engine (Deterministic Rules)
        ↓
ML Risk Model (Structured Screening)
        ↓
Decision Layer (Workflow & Escalation)
        ↓
Alerts / Workflow (Case Management)
        ↓
Supabase PostgreSQL (RLS & Audit Logs)
```

Supporting Systems:
- **AI4Bharat Voice**: Multilingual speech-to-text (IndicWhisper) and text-to-speech (Indic-TTS).
- **Local LLM**: Ollama-based local language model for explanation, summarization, and translation assistance.
- **AI Agent**: Tool execution and decision-support reasoning under strict authorization.
- **Audit Logs**: Tamper-evident logging of all sensitive access and workflow transitions.

---

## 2. Component Boundaries and Implementation Status

### 2.1 Frontend Boundary
- **Status**: [PLANNED - Developer 2 Phase 0/1]
- **Technology**: React, TypeScript, responsive mobile-first UI.
- **Portals**: Mother Portal, ASHA Portal.
- **Environment Boundary**: Accesses only public client variables (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL`). Under no circumstances is `SUPABASE_SERVICE_ROLE_KEY` included or accessible in frontend code.

### 2.2 Backend Boundary
- **Status**: [IMPLEMENTED - Phase 3 API Execution Layer]
- **Technology**: Python 3.13, FastAPI, Pydantic v2, Pydantic-Settings, Uvicorn.
- **Entry Point**: `backend/app/main.py`.
- **API Base**: `/api/v1`.
- **Architecture**: Strict modular layer separation:
  - `backend/app/api/`: Versioned API routers (`v1/router.py`).
  - `backend/app/core/`: Safe configuration loading and constants.
  - `backend/app/schemas/`: Frozen request/response models and DTOs.
  - `backend/app/safety/`: Safety state definitions, deterministic `SafetyEngine`, and `DecisionEngine`.
  - `backend/app/services/`: Business logic services (`health_service`, `prediction_service`, `coordination_service`).
  - `backend/app/auth/`: Fail-closed production authentication boundary and role dependencies.
  - `backend/app/db/`: Persistence repositories (`RepositoryStore`) enforcing relational mapping and audit trails.
  - `backend/app/ml/`: Machine learning inference orchestration (`MLPredictionService`, `ModelProvider` interface).
  - `backend/app/llm/`: Local LLM integration [PLANNED - Phase 6].
  - `backend/app/agent/`: AI Agent workflow tools [PLANNED - Phase 6].
  - `backend/app/voice/`: Voice STT/TTS pipeline [PLANNED - Phase 7].

### 2.3 Database & Persistence Boundary
- **Status**: [IMPLEMENTED - Phase 4 Persistent Database & Repository Layer]
- **Target Production Architecture**: `FastAPI -> Authentication -> Service -> Repository -> Supabase/PostgreSQL`.
- **Deterministic Repository Selection**:
  - **Production Environment (`ENVIRONMENT=production`)**: Strictly requires and instantiates `SupabasePostgresRepository` (configured via `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` or `DATABASE_URL`). If Supabase credentials are missing or unconfigured, the application fails closed at startup with `RuntimeError`. The local disk-backed repository is prohibited from silently becoming the production backend.
  - **Development / Test Environment**: Explicitly falls back to `RepositoryStore` providing disk-backed relational SQL persistence (`data/maternai.db`) or in-memory storage (`:memory:`), ensuring complete schema parity across all 17 entities and verifying that application data survives process restarts.
- **Supabase Client Scoping & Identity Propagation**:
  - **User-Scoped Operations**: Authenticated operations propagate the caller's verified JWT Bearer token via `get_authenticated_client(access_token)` to PostgREST, ensuring PostgreSQL executes queries under `auth.uid()` and enforces Row Level Security (RLS) policies.
  - **Privileged Operations**: `get_service_client()` uses `SUPABASE_SERVICE_ROLE_KEY` strictly guarded for server-side privileged tasks (immutable audit logging in `audit_logs`, model registry updates in `model_versions`, safety event records in `safety_events`, and initial profile bootstrapping). Service-role keys are never exposed to frontend code.
- **Entities**: All 17 documented entities (`profiles`, `mother_profiles`, `asha_profiles`, `health_records`, `symptoms`, `model_versions`, `predictions`, `safety_events`, `asha_assignments`, `alerts`, `visits`, `follow_ups`, `appointments`, `medication_reminders`, `chat_sessions`, `chat_messages`, `audit_logs`).

### 2.4 Authentication Boundary
- **Status**: [IMPLEMENTED - Phase 4 Cryptographic JWT Verification & Role Integrity]
- **Architecture**: Production dependency `get_current_user` cryptographically verifies Supabase access tokens (HMAC-SHA256 signature against `SUPABASE_JWT_SECRET`, token structure, expiration, subject claim extraction). Fails closed if token is invalid, expired, malformed, or unconfigured.
- **Authoritative Role Resolution**: Role is resolved strictly from the database `profiles` table. Client-submitted roles, request body role fields, and arbitrary JWT `user_metadata.role` claims are never trusted for authorization.
- **Role Integrity**: `POST /api/v1/auth/profile` prevents non-admin users from self-promoting to `ASHA` or `ADMIN`, or mutating existing roles (`403 Forbidden`).
- **Roles**: `MOTHER`, `ASHA`, `ADMIN`.

### 2.5 Machine Learning Boundary
- **Status**: [IMPLEMENTED - Service Boundary & ModelProvider Interface]
- **Documented Input Contract**: `MLRiskInput` schema defined in `backend/app/schemas/ml.py`.
- **Model Provider**: `ModelProvider` abstract base class with `BaselineScreeningModel` provider deployed in Phase 3; pluggable trained ML models in Phase 5.
- **Purpose**: Structured risk screening (`LOW`, `MEDIUM`, `HIGH`). `model_score` is an internal model metric (0.0 to 1.0), NOT a clinical probability.

### 2.6 Safety Engine Boundary
- **Status**: [IMPLEMENTED - Deterministic Safety Engine & Precedence Layer]
- **Safety States**: `CLEAR`, `CONCERNING`, `EMERGENCY` (`backend/app/safety/states.py`).
- **Processing Order**: Validation -> Deterministic Safety Rules -> ML Risk Model -> Decision Layer -> Alerts / Workflow.
- **Deterministic Precedence**: `DecisionEngine` strictly prioritizes safety: decision state resolves to `EMERGENCY`, `CONCERNING`, or ML screening classification (`LOW`, `MEDIUM`, `HIGH`). Deterministic safety events are authoritatively logged in `safety_events`. Non-authoritative clinical mappings (such as `EMERGENCY -> HIGH` risk or `EMERGENCY -> CRITICAL` alert) remain explicitly deferred pending approved clinical safety specifications.

### 2.7 LLM & Agent Boundary
- **Status**: [IMPLEMENTED - Phase 6 Chat & Agent Contracts Frozen]
- **Technology**: Local inference (e.g. Ollama with open weights) & deterministic agent tool orchestration.
- **Scope**: Chat sessions, conversational message handling, natural language explanations of structured risk, translation, and authorized agent queries. LLM never independently determines clinical risk.
- **Safety Precedence**: Deterministic safety rules strictly take precedence over LLM/agent responses. Safety state is categorized as `CLEAR`, `CONCERNING`, or `EMERGENCY`.
- **Authorized Tool Allowlist**: Constrained strictly to `get_health_summary`, `get_recent_vitals`, `get_recent_symptoms`, `check_safety_alerts`, `get_upcoming_visits`, and `explain_risk_factors`.

### 2.8 Voice Boundary
- **Status**: [PLANNED - Phase 7]
- **Technology**: AI4Bharat IndicWhisper (ASR) + Indic-TTS.
- **Safety Guardrail**: Critical voice-transcribed medical information must be confirmed by the user before entering the risk or alert workflow.

