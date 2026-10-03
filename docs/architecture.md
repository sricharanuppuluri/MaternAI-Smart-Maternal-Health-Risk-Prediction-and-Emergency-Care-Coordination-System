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

### 2.3 Database Boundary
- **Status**: [IMPLEMENTED - Phase 4 Persistent Database & Repository Layer]
- **Technology**: Supabase PostgreSQL / Relational Persistent `RepositoryStore` (17-Entity Schema Parity).
- **Persistence**: Application data is persisted relationally to disk, surviving backend process restarts.
- **Access Control**: PostgreSQL Row Level Security (RLS) policies enforcing patient isolation and ASHA assignment boundaries across all 17 schema entities.
- **Entities**: `profiles`, `mother_profiles`, `asha_profiles`, `health_records`, `symptoms`, `model_versions`, `predictions`, `safety_events`, `asha_assignments`, `alerts`, `visits`, `follow_ups`, `appointments`, `medication_reminders`, `chat_sessions`, `chat_messages`, `audit_logs`.

### 2.4 Authentication Boundary
- **Status**: [IMPLEMENTED - Phase 4 Cryptographic JWT Verification & Role Integrity]
- **Architecture**: Production dependency cryptographically verifies Supabase access tokens (signature, expiration, structure). Identity is extracted from `sub`.
- **Authoritative Role Resolution**: Role is resolved strictly from the database `profiles` table. Client-submitted roles, request body role fields, and arbitrary JWT `user_metadata.role` claims are never trusted for authorization.
- **Role Integrity**: `/api/v1/auth/profile` prevents regular users from self-promoting to `ASHA` or `ADMIN`.
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
- **Status**: [PLANNED - Phase 6]
- **Technology**: Local inference (e.g. Ollama with open weights).
- **Scope**: Natural language explanations of structured risk, translation, and authorized agent queries. LLM never independently determines clinical risk.

### 2.8 Voice Boundary
- **Status**: [PLANNED - Phase 7]
- **Technology**: AI4Bharat IndicWhisper (ASR) + Indic-TTS.
- **Safety Guardrail**: Critical voice-transcribed medical information must be confirmed by the user before entering the risk or alert workflow.

