# MaternAI --- Product Requirements Document (PRD)

## 1. Product Overview

**Product:** MaternAI\
**Category:** Maternal-health screening and care coordination\
**Primary users:** Mothers and ASHA/community health workers\
**Platform:** Web application\
**Initial geography/context:** India-focused prototype\
**Primary objective:** Connect maternal health data, risk screening,
safety escalation, and ASHA follow-up in one secure workflow.

MaternAI is not intended to replace clinical professionals or provide
autonomous diagnosis or treatment.

------------------------------------------------------------------------

# 2. Product Vision

Create a multilingual, AI-assisted maternal-health platform where a
mother can record health information naturally, receive understandable
screening feedback, and remain connected to a structured ASHA follow-up
workflow.

The product's central loop is:

**Mother → Data → Risk/Safety Assessment → Alert → ASHA → Follow-up →
New Data**

------------------------------------------------------------------------

# 3. Problem

A maternal-health workflow can involve measurements, symptoms,
appointments, visits, reminders, and follow-up actions. Without a
connected workflow, important information can be fragmented.

Existing AI prototypes can also over-focus on chat or prediction while
neglecting:

-   deterministic safety handling
-   human follow-up
-   secure patient isolation
-   auditability
-   multilingual interaction
-   model limitations

MaternAI addresses the workflow as a complete system.

------------------------------------------------------------------------

# 4. Product Goals

## Goal 1 --- Centralize maternal health information

Provide a structured place for:

-   maternal profile
-   health measurements
-   symptoms
-   predictions
-   alerts
-   visits
-   follow-ups
-   appointments

## Goal 2 --- Provide structured risk screening

Use a documented ML model to classify risk into:

-   LOW
-   MEDIUM
-   HIGH

The model is a screening/decision-support component.

## Goal 3 --- Add deterministic safety escalation

Concerning and emergency conditions must be evaluated through explicit
rules rather than relying on generated language.

## Goal 4 --- Connect mothers to ASHAs

Risk and workflow events should create actionable case-management tasks
for assigned ASHAs.

## Goal 5 --- Make interaction multilingual

Support voice and language interaction using AI4Bharat open-source
technologies in the initial implementation.

## Goal 6 --- Provide understandable explanations

Use a local LLM to explain structured results and summarize authorized
information.

## Goal 7 --- Maintain strong privacy boundaries

Use Supabase Auth, PostgreSQL RLS, backend authorization, and audit
logging.

------------------------------------------------------------------------

# 5. Non-Goals

The MVP will not:

-   autonomously diagnose conditions
-   prescribe medication
-   replace doctors or ASHAs
-   allow an LLM to override safety rules
-   claim clinical validation without evidence
-   invent clinical thresholds
-   expose cross-patient information
-   build a large healthcare infrastructure platform
-   train custom speech models
-   implement every possible maternal-health feature

------------------------------------------------------------------------

# 6. User Personas

## Persona A --- Mother

Needs:

-   simple interface
-   minimal typing
-   local language support
-   voice interaction
-   understandable health information
-   clear next steps
-   visibility into history and follow-ups

## Persona B --- ASHA

Needs:

-   assigned mother list
-   risk overview
-   alert queue
-   patient history
-   follow-up tracking
-   visit recording
-   efficient case prioritization

## Persona C --- Administrator

Future user responsible for:

-   controlled operational configuration
-   user management
-   audit review
-   system administration

------------------------------------------------------------------------

# 7. Core User Journeys

## Journey 1 --- Mother records health data

``` text
Login
→ Open health form
→ Enter measurements
→ Submit
→ Validation
→ Save record
→ Safety evaluation
→ ML evaluation
→ Decision
→ Show result
```

## Journey 2 --- Concerning case

``` text
Mother enters data
→ Validation
→ Safety rule triggered
→ Concerning state
→ Priority alert
→ Assigned ASHA sees alert
→ ASHA acknowledges
→ Contacts mother
→ Visit/follow-up
→ Resolution or escalation
```

## Journey 3 --- Normal monitoring

``` text
Mother submits data
→ No concerning safety rule
→ ML classification
→ LOW/MEDIUM/HIGH
→ Store prediction
→ Show explanation
→ Continue monitoring
```

## Journey 4 --- Voice interaction

``` text
Mother speaks
→ IndicWhisper
→ Transcript
→ Extract information
→ Confirm important information
→ Safety/ML/agent workflow
→ Response
→ Indic-TTS
```

## Journey 5 --- ASHA agent query

``` text
ASHA asks:
"Who needs follow-up today?"
→ permission check
→ assigned mothers only
→ retrieve alerts/predictions/follow-ups
→ structured prioritized response
```

------------------------------------------------------------------------

# 8. Functional Requirements

## FR-001 Authentication

The system shall allow:

-   Mother sign-up/sign-in
-   ASHA sign-in
-   controlled role assignment
-   secure session handling

## FR-002 Mother Profile

The system shall allow mothers to:

-   view profile
-   update permitted profile fields
-   view their own pregnancy-related profile information

## FR-003 Health Records

The system shall allow authorized users to:

-   create health records
-   retrieve health history
-   associate records with the correct mother
-   track record source

## FR-004 Symptoms

The system shall allow symptoms to be captured through:

-   manual entry
-   voice
-   chat
-   ASHA entry

Each symptom record should preserve its source.

## FR-005 ML Prediction

The system shall:

-   validate model input
-   run the selected model
-   return risk category
-   return model version
-   return feature schema version
-   provide contributing factors where supported

## FR-006 Safety Engine

The system shall:

-   evaluate validated safety rules
-   produce CLEAR/CONCERNING/EMERGENCY state
-   record triggered rules
-   determine workflow priority
-   prevent LLM override

## FR-007 Decision Layer

The decision layer shall combine safety and ML outputs according to
deterministic precedence.

Emergency and concerning states shall not be downgraded by generated
content.

## FR-008 Alerts

The system shall:

-   create alerts according to configured workflow rules
-   associate alerts with the correct mother
-   associate alerts with an assigned ASHA where applicable
-   track alert status
-   audit important transitions

## FR-009 ASHA Assignment

The system shall:

-   associate mothers with ASHAs
-   support active/inactive assignments
-   enforce assignment-based access
-   prevent access to unassigned mothers

## FR-010 Visits

The system shall allow authorized ASHAs to:

-   schedule visits
-   record visits
-   update visit status

## FR-011 Follow-ups

The system shall allow:

-   follow-up creation
-   follow-up scheduling
-   completion
-   overdue state
-   cancellation

## FR-012 Risk Timeline

The system shall display:

-   previous predictions
-   risk categories
-   relevant dates
-   contributing factors where available
-   major workflow interventions

## FR-013 Chat

The system shall support:

-   chat sessions
-   messages
-   authorized health context
-   explanation and summarization

## FR-014 Voice

The system shall support:

-   speech-to-text
-   confirmation of important extracted information
-   text-to-speech

Initial voice stack:

-   AI4Bharat IndicWhisper
-   AI4Bharat Indic-TTS

## FR-015 AI Agent

The agent shall use authorized tools for:

-   health history
-   predictions
-   alerts
-   appointments
-   reminders
-   ASHA-patient workflows

## FR-016 Audit

The system shall record important sensitive workflow actions.

------------------------------------------------------------------------

# 9. ML Requirements

The ML system should compare candidate algorithms such as:

-   Logistic Regression
-   Decision Tree
-   Random Forest
-   Gradient Boosting

Evaluation should document:

-   accuracy
-   precision
-   recall
-   F1
-   ROC-AUC where applicable
-   confusion matrix
-   calibration where applicable

The final model must be selected based on documented evidence from the
project dataset and evaluation methodology.

------------------------------------------------------------------------

# 10. ML Input

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

The final feature schema must match the selected dataset and trained
model.

------------------------------------------------------------------------

# 11. ML Output

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

The product shall not label an unvalidated model score as a clinical
probability.

------------------------------------------------------------------------

# 12. Safety Requirements

## Safety precedence

``` text
Validation
↓
Safety Rules
↓
ML
↓
Decision Layer
↓
LLM/Agent
```

## Required safety states

-   CLEAR
-   CONCERNING
-   EMERGENCY

## Required rule metadata

Every rule must define:

-   rule code
-   version
-   name
-   description
-   category
-   inputs
-   exact condition
-   priority
-   action
-   clinical/source reference
-   tests
-   approval/reviewer status

The project must not invent medical thresholds.

------------------------------------------------------------------------

# 13. Alert Requirements

Alert statuses:

-   NEW
-   ACKNOWLEDGED
-   CONTACTED
-   VISIT_SCHEDULED
-   FOLLOW_UP_PENDING
-   RESOLVED
-   ESCALATED

The system should make the current state and next action visible to the
ASHA.

------------------------------------------------------------------------

# 14. ASHA Dashboard Requirements

The dashboard should provide:

-   assigned mother list
-   risk summary
-   alert queue
-   follow-up due list
-   recent assessments
-   patient detail
-   visit history
-   action controls

The ASHA should never receive data for unassigned mothers.

------------------------------------------------------------------------

# 15. Mother Dashboard Requirements

The dashboard should provide:

-   current health overview
-   recent measurements
-   latest risk assessment
-   explanation
-   alerts relevant to the mother
-   risk timeline
-   appointments
-   reminders
-   voice interaction
-   chat access

The UI should avoid unnecessarily alarming language and should make
clear when the result is a screening/decision-support output.

------------------------------------------------------------------------

# 16. AI/LLM Requirements

The LLM may:

-   explain results
-   summarize history
-   structure symptoms
-   translate/support language interaction
-   assist with authorized agent tasks

The LLM shall not:

-   diagnose independently
-   override safety
-   fabricate medical information
-   access unauthorized data
-   invent thresholds
-   fabricate patient records
-   fabricate model metrics

------------------------------------------------------------------------

# 17. Agent Requirements

The agent must be tool-based.

### Mother tools

-   own health history
-   own predictions
-   own alerts where permitted
-   own reminders
-   own appointments

### ASHA tools

-   assigned mother history
-   assigned mother predictions
-   assigned alerts
-   assigned appointments
-   assigned reminders
-   follow-up workflow

The agent must enforce authorization before every tool operation.

------------------------------------------------------------------------

# 18. Database Requirements

Required core entities:

``` text
profiles
mother_profiles
asha_profiles
health_records
symptoms
model_versions
predictions
safety_events
asha_assignments
alerts
visits
follow_ups
appointments
medication_reminders
chat_sessions
chat_messages
audit_logs
```

Primary relationship:

``` text
Mother
→ Health Records
→ Symptoms
→ Predictions
→ Alerts
→ Visits
→ Follow-ups
```

ASHA relationship:

``` text
ASHA
→ Active Assignments
→ Assigned Mothers
→ Alerts / Visits / Follow-ups
```

------------------------------------------------------------------------

# 19. Authentication and Authorization Requirements

Authentication:

-   Supabase Auth

Authorization:

-   FastAPI permission checks
-   PostgreSQL RLS
-   assignment checks

Mandatory rules:

1.  Mother A cannot access Mother B.
2.  ASHA A cannot access unassigned Mother B.
3.  Mother cannot perform ASHA-only operations.
4.  Service-role key cannot be exposed to the frontend.
5.  Agent cannot bypass RLS/authorization.
6.  Predictions cannot be freely inserted by clients.
7.  Sensitive workflow actions are auditable.

------------------------------------------------------------------------

# 20. API Requirements

Base path:

``` text
/api/v1
```

### Endpoints

``` text
POST /auth/profile

GET /mothers/me
PATCH /mothers/me

POST /health-records
POST /symptoms
POST /predictions

GET /alerts
PATCH /alerts/{alert_id}/status

POST /visits
PATCH /visits/{visit_id}

POST /followups
PATCH /followups/{id}

GET /mothers/{mother_id}/risk-timeline

POST /chat/sessions
POST /chat/sessions/{session_id}/messages

POST /voice/transcribe
POST /voice/confirm

POST /agent/query
```

Authentication header:

``` text
Authorization: Bearer <supabase_access_token>
```

------------------------------------------------------------------------

# 21. Non-Functional Requirements

## Security

-   RLS enabled
-   role-based authorization
-   assignment-based access
-   no secrets in frontend
-   audit logging

## Reliability

-   backend validation
-   error handling
-   retry-safe requests where appropriate
-   no false success when backend confirmation is absent

## Performance

The system should define and measure API latency targets during
implementation rather than claiming unmeasured performance.

## Maintainability

-   modular backend
-   isolated safety engine
-   isolated ML module
-   isolated agent tools
-   versioned model
-   versioned safety rules

## Explainability

Risk results should provide understandable contributing factors where
supported by the model.

## Privacy

Only necessary health information should be collected and exposed to
each role.

------------------------------------------------------------------------

# 22. UX Requirements

### Mother

-   mobile-friendly
-   large buttons
-   simple wording
-   minimal typing
-   multilingual
-   voice-first where useful
-   clear action hierarchy

### ASHA

-   information-dense
-   alert prioritization
-   searchable assigned mothers
-   clear case status
-   fast follow-up recording

------------------------------------------------------------------------

# 23. Success Metrics

## ML

-   recall
-   precision
-   F1
-   confusion matrix
-   ROC-AUC where appropriate
-   calibration where applicable

## System

-   API latency
-   API error rate
-   authentication test pass rate
-   authorization test pass rate
-   prediction workflow test pass rate
-   alert workflow test pass rate
-   end-to-end test pass rate

## Product workflow

Measure during prototype testing:

-   successful health-record submissions
-   successful risk assessment completion
-   alert acknowledgement completion
-   follow-up completion
-   voice transcription confirmation rate

These are engineering/product metrics, not clinical effectiveness
claims.

------------------------------------------------------------------------

# 24. Risks and Mitigations

  -----------------------------------------------------------------------
  Risk                                Mitigation
  ----------------------------------- -----------------------------------
  Weak or biased dataset              Document source, population,
                                      missingness, limitations

  False reassurance                   Safety rules and human ASHA
                                      workflow

  False alarms                        Validate rules and document
                                      workflow thresholds

  LLM hallucination                   Guardrails, structured context, no
                                      clinical override

  Unauthorized data access            RLS + backend authorization +
                                      security tests

  Voice transcription errors          Confirmation before important
                                      actions

  Model drift                         Versioning and future monitoring

  Network interruption                Retryable operations and clear
                                      status

  Overly broad scope                  MVP/Phase 2/future separation

  Unsupported clinical claims         Source every clinical rule and
                                      recommendation
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# 25. Release Requirements

Before MVP release:

-   authentication tested
-   RLS tested
-   mother isolation tested
-   ASHA assignment isolation tested
-   prediction pipeline tested
-   safety engine tested
-   alert workflow tested
-   visit/follow-up workflow tested
-   agent authorization tested
-   voice confirmation tested
-   audit logging verified
-   model documentation complete
-   dataset limitations documented
-   no secrets committed
-   no unsupported clinical thresholds used

------------------------------------------------------------------------

# 26. MVP Acceptance Criteria

The MVP passes acceptance when:

1.  A mother can authenticate.
2.  An ASHA can authenticate.
3.  A mother can create health data.
4.  Symptoms can be recorded.
5.  Safety validation runs before ML.
6.  ML returns a documented risk category.
7.  Contributing factors are shown where supported.
8.  Alerts are generated when configured workflow conditions are met.
9.  An assigned ASHA can see the relevant alert.
10. An unassigned ASHA cannot access the mother.
11. Another mother cannot access the record.
12. ASHA can acknowledge and manage the case.
13. Visits and follow-ups can be recorded.
14. Risk history can be viewed.
15. Voice input can be transcribed and confirmed.
16. Local LLM can explain authorized information.
17. Agent tools enforce permissions.
18. Important actions are auditable.
19. Security and integration tests pass.
20. Documentation clearly states that the system is a
    screening/decision-support prototype.

------------------------------------------------------------------------

# 27. Product Roadmap

## Phase 1 --- Foundation

-   React
-   FastAPI
-   Supabase
-   PostgreSQL
-   Auth
-   RLS

## Phase 2 --- Core Workflow

-   health records
-   symptoms
-   assignments
-   predictions
-   alerts
-   visits
-   follow-ups

## Phase 3 --- Intelligence

-   ML comparison
-   explainability
-   safety engine
-   decision layer
-   local LLM

## Phase 4 --- Experience

-   mother dashboard
-   ASHA dashboard
-   risk timeline
-   multilingual voice

## Phase 5 --- Agent

-   authorized tool calling
-   ASHA workflow queries
-   mother history queries

## Phase 6 --- Hardening

-   security tests
-   integration tests
-   observability
-   deployment
-   documentation

## Future

-   Sarvam hosted voice
-   broader language coverage
-   advanced analytics
-   integrations
-   offline-first enhancements

------------------------------------------------------------------------

# 28. Product Architecture Summary

``` text
                 MaternAI
                    │
        ┌───────────┴───────────┐
        │                       │
     Mother                    ASHA
        │                       │
        └───────────┬───────────┘
                    ↓
                FastAPI
                    ↓
        Authentication / RLS
                    ↓
              Input Validation
                    ↓
              Safety Engine
                    ↓
               ML Predictor
                    ↓
              Decision Layer
             /              \
         Prediction         Alert
                              ↓
                         ASHA Workflow
                              ↓
                     Visit / Follow-up
                              ↓
                         New Data
                              ↓
                         Risk Timeline

Supporting layers:
AI4Bharat Voice
Local LLM
AI Agent
Supabase PostgreSQL
Audit Logs
```

------------------------------------------------------------------------

# 29. Final Product Statement

MaternAI is a multilingual maternal-health screening and
care-coordination platform that combines structured ML risk assessment,
deterministic safety rules, AI-assisted explanations, voice interaction,
secure patient data management, and ASHA follow-up workflows.

The product's defining characteristic is the connection between **risk
detection and real-world follow-up**, rather than prediction or
conversation alone.
