# MaternAI --- End-to-End Project Documentation

## 1. Document Purpose

MaternAI is a maternal-health screening and care-coordination prototype
designed to help mothers and ASHA/community health workers organize
maternal health information, identify potentially higher-risk cases,
support follow-up, and improve communication through multilingual voice
and AI-assisted explanations.

MaternAI is a **decision-support and workflow system**, not a diagnostic
or treatment system. Clinical rules, thresholds, recommendations, and
claims must be validated against authoritative clinical sources before
release.

------------------------------------------------------------------------

## 2. Product Vision

MaternAI connects the complete workflow:

**Mother → Health Data → Validation → Safety Rules → ML Risk Assessment
→ Decision Layer → Alert → ASHA → Follow-up → New Health Data → Risk
Timeline**

The system combines deterministic safety logic, a structured ML model, a
local LLM, multilingual voice, secure relational data, and human ASHA
follow-up.

### Core principles

1.  Safety rules are deterministic and take precedence over generated
    text.
2.  ML predicts structured risk; it does not diagnose.
3.  The LLM explains, summarizes, translates, and assists with
    conversation; it does not decide clinical risk.
4.  Important voice-derived information is confirmed before entering
    risk or alert workflows.
5.  ASHAs remain part of the human follow-up loop.
6.  Every sensitive workflow action should be auditable.
7.  Access is enforced through authentication and database-level
    authorization/RLS.
8.  The initial voice stack uses open-source AI4Bharat technologies;
    hosted voice providers such as Sarvam AI remain future options.
9.  Dataset limitations and model uncertainty must be visible in project
    documentation.
10. The MVP stays focused on the central maternal monitoring and
    escalation workflow.

------------------------------------------------------------------------

# 3. Problem Statement

Maternal-health information may be distributed across conversations,
measurements, symptoms, visits, and follow-up records. A system that
centralizes structured information and supports risk screening can help
organize this information for mothers and ASHAs.

The challenge is not simply to build a chatbot or prediction model. The
system must connect:

-   structured maternal health data
-   symptom information
-   risk assessment
-   safety checks
-   alerts
-   ASHA assignment
-   follow-up
-   visit history
-   risk trends
-   multilingual communication
-   secure access

The project therefore emphasizes a complete workflow rather than
isolated AI features.

------------------------------------------------------------------------

# 4. Target Users

## 4.1 Mother

The mother can:

-   create and manage her account
-   maintain a maternal profile
-   enter health measurements
-   record symptoms
-   view risk assessments
-   understand contributing factors
-   view alerts relevant to her
-   view health history and risk trends
-   interact with the system using text or voice
-   view appointments and follow-ups
-   receive reminders
-   communicate through supported multilingual interfaces

## 4.2 ASHA / Community Health Worker

The ASHA can:

-   sign in securely
-   view assigned mothers
-   monitor risk assessments
-   review alerts
-   acknowledge and manage cases
-   record contact and visit information
-   schedule or track follow-ups
-   review maternal history
-   use agent-assisted workflow queries for assigned mothers

## 4.3 Administrator

An administrator is an optional future role for controlled operational
management, configuration, auditing, and system administration.

The client must never allow a normal user to self-assign the ADMIN role.

------------------------------------------------------------------------

# 5. Scope

## 5.1 MVP

The MVP contains:

-   Mother authentication
-   ASHA authentication
-   Mother profile
-   ASHA profile
-   Maternal health records
-   Symptom records
-   ML risk prediction
-   Risk explanation
-   Deterministic safety engine
-   Decision layer
-   ASHA assignment
-   Alert generation
-   ASHA alert workflow
-   Visits
-   Follow-ups
-   Risk timeline
-   Multilingual voice using AI4Bharat technologies
-   Local LLM for explanation/conversation
-   Basic AI agent tools
-   Supabase PostgreSQL
-   Supabase Auth
-   Row Level Security
-   Audit logging
-   Automated tests for security and workflows

## 5.2 Phase 2

-   richer conversational agent
-   more advanced trend intelligence
-   advanced reminders
-   visit analytics
-   richer multilingual coverage
-   network-aware/offline queue improvements
-   improved agent workflows

## 5.3 Future

-   Sarvam AI hosted voice layer
-   broader Indian-language coverage
-   advanced voice interaction
-   integrations
-   administrative portal
-   advanced analytics
-   larger-scale deployment
-   additional healthcare workflows after validation

------------------------------------------------------------------------

# 6. High-Level Architecture

``` text
                    ┌─────────────────────┐
                    │      Mother UI      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │      ASHA UI        │
                    └──────────┬──────────┘
                               │
                         HTTPS / JSON
                               │
                    ┌──────────▼──────────┐
                    │       FastAPI       │
                    │  Authentication     │
                    │  API Orchestration  │
                    └──────────┬──────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
 ┌────────▼────────┐  ┌────────▼────────┐  ┌──────▼─────────┐
 │  Safety Engine  │  │   ML Predictor  │  │ Local LLM /    │
 │ deterministic   │  │ structured risk │  │ AI Agent       │
 └────────┬────────┘  └────────┬────────┘  └──────┬─────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Decision Layer    │
                    │ alert/workflow rules│
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Supabase PostgreSQL │
                    │ Auth + RLS + Audit  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │ ASHA Case Workflow  │
                    │ Alert → Visit →     │
                    │ Follow-up → Resolve │
                    └─────────────────────┘

Voice:
Mother → IndicWhisper STT → confirmation → safety/intent processing
→ ML/Agent → response → Indic-TTS
```

------------------------------------------------------------------------

# 7. Technology Stack

## Frontend

-   React
-   TypeScript
-   responsive web UI

## Backend

-   Python
-   FastAPI
-   Pydantic
-   service-layer architecture

## Database and Authentication

-   Supabase
-   PostgreSQL
-   Supabase Auth
-   PostgreSQL Row Level Security

## Machine Learning

Candidate models:

-   Logistic Regression
-   Decision Tree
-   Random Forest
-   Gradient Boosting

The final model must be selected using documented evaluation rather than
assumed superiority.

Evaluation should include:

-   accuracy
-   precision
-   recall
-   F1
-   ROC-AUC where appropriate
-   confusion matrix
-   calibration where probabilities are used

For a health screening workflow, recall and false-negative behavior
require particular attention, but no model should be presented as
clinically validated without appropriate evidence.

## Explainability

Use feature-level explanations appropriate to the selected model. SHAP
may be used where technically appropriate.

## LLM

A locally hosted model through Ollama or an equivalent local inference
layer.

The LLM handles:

-   explanations
-   summarization
-   conversation
-   language assistance
-   symptom structuring
-   agent reasoning around authorized tools

The LLM does not independently determine medical risk.

## Voice

Initial:

-   AI4Bharat IndicWhisper for speech-to-text
-   AI4Bharat Indic-TTS for text-to-speech

Future:

-   hosted voice APIs such as Sarvam AI

------------------------------------------------------------------------

# 8. End-to-End User Flow

## 8.1 Mother Registration

1.  Mother opens the application.
2.  Mother creates an account through Supabase Auth.
3.  Backend verifies the authenticated identity.
4.  Profile is created.
5.  Mother profile information is collected.
6.  RLS ensures the mother can only access her own records.

## 8.2 Health Data Submission

1.  Mother enters health measurements.
2.  Frontend performs basic validation.
3.  Request is sent to FastAPI.
4.  Backend validates again.
5.  Health record is stored.
6.  Symptoms may be stored separately.
7.  Safety engine evaluates validated inputs.
8.  ML model evaluates the structured feature set if appropriate.
9.  Decision layer combines the safety state and ML output.
10. Prediction and relevant workflow records are stored.
11. An alert is created when workflow rules require it.
12. ASHA dashboard reflects the new case.

------------------------------------------------------------------------

# 9. Safety Architecture

The mandatory processing order is:

``` text
Input
  ↓
Validation
  ↓
Safety Rules
  ↓
ML Risk Model
  ↓
Decision Layer
  ↓
LLM / Agent
```

## Safety states

-   CLEAR
-   CONCERNING
-   EMERGENCY

## Decision hierarchy

``` text
if validation fails:
    VALIDATION_ERROR
else if emergency rule:
    EMERGENCY
else if concerning rule:
    CONCERNING
else:
    use ML classification
```

The exact clinical conditions and thresholds must come from validated
sources. The project documentation must not invent them.

## Safety invariant

The LLM cannot:

-   downgrade an emergency state
-   override a concerning safety state
-   invent a clinical threshold
-   convert uncertain generated text into a verified clinical fact

------------------------------------------------------------------------

# 10. Safety Rule Specification

Every production safety rule must contain:

-   rule code
-   rule version
-   rule name
-   description
-   category
-   input fields
-   exact condition
-   priority
-   action
-   clinical/source reference
-   enabled state
-   confirmation requirement
-   tests
-   reviewer/approval status

Example metadata:

``` json
{
  "rule_code": "RULE_001",
  "version": "1.0",
  "name": "Documented concerning condition",
  "description": "Triggers when a validated project rule is satisfied.",
  "category": "SYMPTOM",
  "priority": "HIGH",
  "enabled": true,
  "requires_confirmation": true,
  "clinical_source": "REQUIRED_BEFORE_RELEASE"
}
```

Rule categories:

-   data integrity
-   concerning symptoms
-   emergency
-   trend

------------------------------------------------------------------------

# 11. ML Pipeline

## Training pipeline

``` text
Dataset
  ↓
Data audit
  ↓
Cleaning
  ↓
Missing-value analysis
  ↓
Feature engineering
  ↓
Train/test methodology
  ↓
Candidate models
  ↓
Evaluation
  ↓
Calibration / threshold analysis
  ↓
Explainability
  ↓
Model selection
  ↓
Versioning
  ↓
Prediction API
```

## Dataset documentation requirements

Record:

-   dataset source
-   number of samples
-   features
-   target definition
-   missing values
-   class distribution
-   represented population
-   limitations
-   potential bias
-   train/test split
-   preprocessing
-   model version
-   feature schema version

Do not fabricate model metrics or clinical claims.

------------------------------------------------------------------------

# 12. ML Input Contract

``` python
class MLRiskInput(BaseModel):
    age_years: float | None
    hemoglobin: float | None
    systolic_bp: float | None
    diastolic_bp: float | None
    blood_sugar: float | None
    weight_kg: float | None
    pregnancy_week: int | None
    symptom_features: dict[str, int | float | bool]
```

The actual feature list must be finalized according to the selected
dataset and trained model.

------------------------------------------------------------------------

# 13. ML Output Contract

``` python
class ContributingFactor(BaseModel):
    feature: str
    direction: str
    value: float | int | str | bool | None

class MLRiskOutput(BaseModel):
    model_version: str
    feature_schema_version: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    model_score: float | None
    contributing_factors: list[ContributingFactor]
```

The `model_score` must not be described as a clinical probability unless
it has been appropriately validated and calibrated.

------------------------------------------------------------------------

# 14. Risk Representation

MaternAI should use understandable categories:

-   LOW
-   MEDIUM
-   HIGH

A numeric model score may exist internally, but the UI should avoid
implying unsupported medical precision.

Example timeline:

``` text
Assessment 1 → LOW
Assessment 2 → LOW
Assessment 3 → MEDIUM
Assessment 4 → HIGH
ASHA intervention
Assessment 5 → MEDIUM
```

Trend intelligence can describe:

-   current risk
-   direction of change
-   recent measurement changes
-   symptom changes
-   overdue follow-up
-   recent ASHA intervention

The system should not simply render a chart and call that intelligence.

------------------------------------------------------------------------

# 15. ASHA Case Management

Core workflow:

``` text
Alert Created
    ↓
ASHA Notified
    ↓
Acknowledged
    ↓
Contacted
    ↓
Visit Scheduled
    ↓
Visit Recorded
    ↓
Follow-up Scheduled
    ↓
Resolved / Escalated
```

Supported alert statuses:

-   NEW
-   ACKNOWLEDGED
-   CONTACTED
-   VISIT_SCHEDULED
-   FOLLOW_UP_PENDING
-   RESOLVED
-   ESCALATED

The ASHA should only access mothers assigned to that ASHA.

------------------------------------------------------------------------

# 16. Voice Workflow

``` text
Mother speaks
    ↓
AI4Bharat IndicWhisper
    ↓
Transcribed text
    ↓
Language / intent processing
    ↓
Symptom extraction
    ↓
Confirmation for important information
    ↓
Safety engine
    ↓
ML / Agent
    ↓
Response
    ↓
AI4Bharat Indic-TTS
    ↓
Mother hears response
```

Important extracted health information should be confirmed before it
changes a risk or alert workflow.

------------------------------------------------------------------------

# 17. LLM Responsibilities

The local LLM can:

-   explain a prediction in simple language
-   summarize health history
-   structure free-form symptom descriptions
-   support multilingual communication
-   answer questions using authorized context
-   prepare summaries for ASHA workflows

The LLM cannot:

-   independently diagnose
-   create unsupported clinical thresholds
-   override safety rules
-   directly access unauthorized patient data
-   fabricate records
-   invent test results
-   create false medical certainty

------------------------------------------------------------------------

# 18. AI Agent

The agent is a tool-using workflow component, not merely a chatbot.

## Example ASHA request

> "Show mothers who need follow-up today."

Agent flow:

``` text
User request
  ↓
Permission check
  ↓
Identify ASHA
  ↓
Query assigned mothers
  ↓
Retrieve relevant risk records
  ↓
Retrieve alerts
  ↓
Retrieve follow-up dates
  ↓
Prioritize using deterministic workflow logic
  ↓
Return structured result
```

## Example mother request

> "What happened to my last assessment?"

Agent flow:

``` text
Authenticate mother
  ↓
Retrieve latest assessment
  ↓
Retrieve previous assessment if needed
  ↓
Compare authorized records
  ↓
Generate explanation
```

Every agent tool must enforce the same authorization boundary as normal
APIs.

------------------------------------------------------------------------

# 19. Database Design

Core entities:

-   profiles
-   mother_profiles
-   asha_profiles
-   health_records
-   symptoms
-   model_versions
-   predictions
-   safety_events
-   asha_assignments
-   alerts
-   visits
-   follow_ups
-   appointments
-   medication_reminders
-   chat_sessions
-   chat_messages
-   audit_logs

Important relationships:

``` text
profiles
  ├── mother_profiles
  │      ├── health_records
  │      │      ├── symptoms
  │      │      └── predictions
  │      ├── alerts
  │      ├── visits
  │      ├── follow_ups
  │      ├── appointments
  │      └── chat_sessions
  │
  └── asha_profiles
         └── asha_assignments
                 └── assigned mother
```

------------------------------------------------------------------------

# 20. Authentication

Supabase Auth owns authentication.

Frontend sends:

``` text
Authorization: Bearer <supabase_access_token>
```

FastAPI validates the authenticated identity and role.

Roles:

-   MOTHER
-   ASHA
-   ADMIN

Role assignment must be controlled server-side.

------------------------------------------------------------------------

# 21. RLS and Authorization

RLS is enabled on application tables.

Security invariants:

1.  unauthenticated users cannot access protected data
2.  Mother A cannot access Mother B
3.  an ASHA cannot access an unassigned mother
4.  mothers cannot access ASHA-only operations
5.  service-role keys never appear in browser code
6.  client cannot directly insert authoritative predictions
7.  agent tools cannot bypass authorization
8.  major workflow actions are auditable

Conceptual helper functions:

``` sql
current_user_id()
current_user_role()
is_assigned_asha(p_mother_id)
```

------------------------------------------------------------------------

# 22. API Architecture

Base URL:

``` text
/api/v1
```

Authentication:

``` text
Authorization: Bearer <supabase_access_token>
```

Response format:

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid health record",
    "details": {}
  }
}
```

## Core endpoints

### Authentication

``` text
POST /api/v1/auth/profile
```

### Mother

``` text
GET   /api/v1/mothers/me
PATCH /api/v1/mothers/me
```

### Health

``` text
POST /api/v1/health-records
POST /api/v1/symptoms
POST /api/v1/predictions
```

### Alerts

``` text
GET   /api/v1/alerts
PATCH /api/v1/alerts/{alert_id}/status
```

### Visits

``` text
POST  /api/v1/visits
PATCH /api/v1/visits/{visit_id}
```

### Follow-ups

``` text
POST  /api/v1/followups
PATCH /api/v1/followups/{id}
```

### Risk timeline

``` text
GET /api/v1/mothers/{mother_id}/risk-timeline
```

### Chat

``` text
POST /api/v1/chat/sessions
POST /api/v1/chat/sessions/{session_id}/messages
```

### Voice

``` text
POST /api/v1/voice/transcribe
POST /api/v1/voice/confirm
```

### Agent

``` text
POST /api/v1/agent/query
```

------------------------------------------------------------------------

# 23. Folder Structure

``` text
MaternAI/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       │   ├── auth/
│       │   ├── mother/
│       │   └── asha/
│       ├── layouts/
│       ├── hooks/
│       ├── services/
│       ├── auth/
│       ├── types/
│       └── utils/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   ├── auth/
│   │   ├── db/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── safety/
│   │   ├── ml/
│   │   ├── llm/
│   │   ├── agent/
│   │   ├── voice/
│   │   └── core/
│   └── tests/
│       ├── unit/
│       ├── api/
│       ├── security/
│       ├── safety/
│       └── integration/
│
├── ml/
├── supabase/
│   └── migrations/
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

------------------------------------------------------------------------

# 24. Environment Configuration

Frontend:

``` text
VITE_SUPABASE_URL
VITE_SUPABASE_ANON_KEY
VITE_API_BASE_URL
```

Backend:

``` text
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
MODEL_PATH
MODEL_VERSION
OLLAMA_BASE_URL
OLLAMA_MODEL
```

Secrets must never be committed to Git or bundled into frontend code.

------------------------------------------------------------------------

# 25. Security Model

Security is part of the product rather than a final cleanup task.

Required tests:

### Mother isolation

Mother A requests Mother B's record → denied.

### ASHA assignment isolation

ASHA A requests an unassigned mother's record → denied.

### Role isolation

Mother attempts an ASHA-only operation → denied.

### Secret protection

Frontend bundle contains no service-role key.

### Agent isolation

Agent asks for unrelated patient data → denied.

### Auditability

Important actions create audit records.

------------------------------------------------------------------------

# 26. Testing Strategy

## Unit tests

-   validation
-   safety rules
-   ML preprocessing
-   permission checks
-   service functions

## API tests

-   authentication
-   validation
-   status codes
-   response schemas
-   authorization

## Security tests

-   mother-to-mother isolation
-   ASHA assignment isolation
-   role isolation
-   agent isolation
-   secret exposure

## Integration tests

``` text
Login
→ health record
→ safety + ML
→ prediction
→ alert
→ ASHA login
→ acknowledge
→ contact
→ visit
→ follow-up
```

## System metrics

Track where appropriate:

-   ML recall/F1
-   API latency
-   authentication test results
-   authorization test results
-   prediction API tests
-   alert workflow tests
-   end-to-end test results

------------------------------------------------------------------------

# 27. UX Requirements

## Mother interface

-   simple navigation
-   large primary actions
-   minimal typing
-   local-language support
-   voice-first interaction where useful
-   clear risk explanations
-   obvious next actions
-   accessible alert presentation

## ASHA interface

-   denser dashboard
-   patient list
-   alert queue
-   risk history
-   follow-up status
-   visit recording
-   case-management controls

------------------------------------------------------------------------

# 28. Network-Aware Design

The initial system does not require full offline operation.

However, the architecture should allow:

-   temporary local draft storage
-   retryable requests
-   clear connection status
-   safe synchronization
-   prevention of duplicate submissions

Critical clinical/workflow actions should not silently appear successful
when the backend has not confirmed them.

------------------------------------------------------------------------

# 29. Observability

Log operational events without unnecessarily exposing sensitive health
information.

Monitor:

-   API failures
-   latency
-   model errors
-   voice failures
-   LLM failures
-   database errors
-   alert creation failures
-   workflow transitions

Audit logs should capture important sensitive actions.

------------------------------------------------------------------------

# 30. Data and Clinical Limitations

MaternAI must clearly document that:

-   the model depends on the quality and representativeness of its
    training data
-   datasets may not represent the target population
-   missing data can affect predictions
-   model performance may change across populations
-   a prototype model is not equivalent to clinical validation
-   generated explanations are not independent clinical evidence
-   clinical thresholds and recommendations require authoritative
    validation

The product should be positioned as **maternal-health screening and
decision support**, not autonomous diagnosis.

------------------------------------------------------------------------

# 31. Implementation Roadmap

## Stage 1 --- Foundation

-   React frontend
-   FastAPI backend
-   Supabase project
-   PostgreSQL schema
-   authentication
-   Git/GitHub
-   environment configuration

## Stage 2 --- Core Health

-   mother profile
-   ASHA profile
-   health records
-   symptoms
-   assignments
-   alerts
-   visits
-   follow-ups

## Stage 3 --- ML

-   dataset analysis
-   preprocessing
-   candidate models
-   evaluation
-   explainability
-   versioning
-   prediction API

## Stage 4 --- Safety

-   validation
-   safety registry
-   concerning rules
-   emergency rules
-   decision layer
-   audit logging
-   LLM guardrails

## Stage 5 --- UX

-   mother dashboard
-   ASHA dashboard
-   patient detail
-   alert queue
-   risk timeline
-   follow-up workflow

## Stage 6 --- Voice

-   IndicWhisper integration
-   confirmation layer
-   language processing
-   Indic-TTS integration

## Stage 7 --- Agent

-   history tool
-   prediction tool
-   alert tool
-   appointment tool
-   reminder tool
-   ASHA-patient tool
-   authorization policy

## Stage 8 --- Hardening

-   RLS tests
-   API tests
-   security tests
-   end-to-end tests
-   error handling
-   logging
-   performance
-   deployment preparation

------------------------------------------------------------------------

# 32. Definition of Done

The MVP is complete when:

-   Mother and ASHA authentication works.
-   RLS blocks unauthorized access.
-   Mother health records can be created and retrieved securely.
-   Symptoms can be recorded.
-   Safety rules run before ML classification.
-   ML prediction is versioned and documented.
-   Prediction explanations identify contributing factors.
-   Alerts are generated according to deterministic workflow rules.
-   ASHAs can only see assigned mothers.
-   ASHA case workflow can progress from alert to follow-up.
-   Risk timeline is available.
-   Voice can capture and confirm supported inputs.
-   Local LLM can explain and summarize authorized information.
-   Agent tools enforce permissions.
-   Audit logs capture important actions.
-   Security and integration tests pass.
-   Dataset/model limitations are documented.
-   No unsupported clinical thresholds or claims are presented as facts.

------------------------------------------------------------------------

# 33. Recommended Project Positioning

MaternAI should be presented as:

> **A multilingual maternal-health screening and care-coordination
> platform that combines structured ML risk assessment, deterministic
> safety rules, AI-assisted explanations, voice interaction, and ASHA
> follow-up workflows.**

This positioning is stronger than presenting it as simply an "AI
chatbot" or "pregnancy prediction app" because the core value is the
complete workflow.

------------------------------------------------------------------------

# 34. Non-Goals

MaternAI should not attempt to:

-   replace doctors or ASHAs
-   autonomously diagnose disease
-   prescribe medication
-   invent medical thresholds
-   use an LLM as the primary risk engine
-   expose unrestricted patient data to agents
-   claim clinical validation without evidence
-   build unnecessary blockchain/Web3 infrastructure
-   train custom speech models in the MVP
-   implement every possible healthcare feature

------------------------------------------------------------------------

# 35. Final Architecture

``` text
Mother
  ↓
React / TypeScript
  ↓
FastAPI
  ↓
Authentication + Authorization
  ↓
Input Validation
  ↓
Safety Engine
  ↓
ML Risk Model
  ↓
Decision Layer
  ├── Prediction
  ├── Alert
  └── Monitoring
  ↓
ASHA Workflow
  ├── Acknowledge
  ├── Contact
  ├── Visit
  ├── Follow-up
  └── Resolve / Escalate
  ↓
New Health Data
  ↓
Risk Timeline

Supporting intelligence:
- AI4Bharat Voice
- Local LLM
- AI Agent

Foundation:
- Supabase Auth
- PostgreSQL
- RLS
- Audit Logs
```

------------------------------------------------------------------------

# 36. Antigravity Implementation Protocol

Do not give Antigravity one giant implementation request.

Implement in isolated increments:

1.  Database migration
2.  Authentication
3.  RLS
4.  Backend foundation
5.  Health records
6.  ML pipeline
7.  Safety engine
8.  Alerts
9.  ASHA workflow
10. Frontend dashboards
11. Voice
12. LLM
13. Agent
14. Testing
15. Hardening

After every subsystem:

-   inspect generated code
-   run tests
-   verify security boundaries
-   check environment variables
-   commit a working checkpoint

------------------------------------------------------------------------

# 37. Git Strategy

Use small, meaningful commits.

Example:

``` text
feat: add initial Supabase schema
feat: add Supabase authentication
feat: add RLS policies
feat: add health record APIs
feat: add ML prediction service
feat: add safety engine
feat: add alert workflow
feat: add ASHA dashboard
feat: add multilingual voice pipeline
feat: add agent tools
test: add authorization isolation tests
```

Avoid committing secrets, model credentials, or local environment files.
