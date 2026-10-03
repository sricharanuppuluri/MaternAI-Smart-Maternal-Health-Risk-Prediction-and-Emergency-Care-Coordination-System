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
- **Status**: [IMPLEMENTED - Baseline Foundation]
- **Technology**: Python 3.13, FastAPI, Pydantic v2, Pydantic-Settings, Uvicorn.
- **Entry Point**: `backend/app/main.py`.
- **API Base**: `/api/v1` (with `/api/v1/health` and root `/` health check).
- **Architecture**: Strict modular layer separation:
  - `backend/app/api/`: Versioned API routers (`v1/`).
  - `backend/app/core/`: Safe configuration loading and constants.
  - `backend/app/schemas/`: Data transfer objects and request/response models.
  - `backend/app/safety/`: Safety state definitions (`SafetyStatus`).
  - `backend/app/services/`: Business logic service layer [PLANNED].
  - `backend/app/auth/`: Backend identity & authorization checks [PLANNED].
  - `backend/app/db/`: Database clients and query layer [PLANNED].
  - `backend/app/ml/`: Machine learning inference orchestration [PLANNED].
  - `backend/app/llm/`: Local LLM integration [PLANNED].
  - `backend/app/agent/`: AI Agent workflow tools [PLANNED].
  - `backend/app/voice/`: Voice STT/TTS pipeline [PLANNED].

### 2.3 Database Boundary
- **Status**: [PLANNED - Phase 2]
- **Technology**: Supabase PostgreSQL.
- **Access Control**: PostgreSQL Row Level Security (RLS) policies enforcing patient isolation and ASHA assignment boundaries.
- **Planned Entities**: `profiles`, `mother_profiles`, `asha_profiles`, `health_records`, `symptoms`, `model_versions`, `predictions`, `safety_events`, `asha_assignments`, `alerts`, `visits`, `follow_ups`, `appointments`, `medication_reminders`, `chat_sessions`, `chat_messages`, `audit_logs`.

### 2.4 Authentication Boundary
- **Status**: [PLANNED - Phase 3]
- **Architecture**: Supabase Auth tokens verified server-side in FastAPI; PostgreSQL RLS and assignment tables enforce tenant and record isolation.
- **Roles**: `MOTHER`, `ASHA`, `ADMIN` (future). Client cannot self-assign roles.

### 2.5 Machine Learning Boundary
- **Status**: [PLANNED - Phase 5] / [IMPLEMENTED - Input Contract]
- **Documented Input Contract**: `MLRiskInput` schema defined in `backend/app/schemas/ml.py`.
- **Candidate Models**: Logistic Regression, Decision Tree, Random Forest, Gradient Boosting.
- **Purpose**: Structured risk screening (`LOW`, `MEDIUM`, `HIGH`). It does not diagnose. Model selection will be strictly based on empirical comparative metrics.

### 2.6 Safety Engine Boundary
- **Status**: [PLANNED - Phase 6] / [IMPLEMENTED - States Definition]
- **Safety States**: `CLEAR`, `CONCERNING`, `EMERGENCY` (`backend/app/safety/states.py`).
- **Processing Order**: Validation -> Safety Rules -> ML -> Decision Layer -> LLM / Agent.
- **Deterministic Precedence**: Explicit deterministic safety rules always override ML risk assessments and LLM output. No clinical thresholds are implemented in Phase 0.

### 2.7 LLM & Agent Boundary
- **Status**: [PLANNED - Phase 6]
- **Technology**: Local inference (e.g. Ollama with open weights).
- **Scope**: Natural language explanations of structured risk, translation, and authorized agent queries. LLM never independently determines clinical risk.

### 2.8 Voice Boundary
- **Status**: [PLANNED - Phase 7]
- **Technology**: AI4Bharat IndicWhisper (ASR) + Indic-TTS.
- **Safety Guardrail**: Critical voice-transcribed medical information must be confirmed by the user before entering the risk or alert workflow.
