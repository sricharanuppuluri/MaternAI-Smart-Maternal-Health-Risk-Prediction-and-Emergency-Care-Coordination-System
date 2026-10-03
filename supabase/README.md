# Supabase Database & Migrations

This directory contains Supabase PostgreSQL migrations and database scripts for MaternAI.

## Migrations

- `20261003000001_initial_schema.sql`: Baseline relational schema establishing all 17 documented entities, indexes, security functions (`current_user_id()`, `current_user_role()`, `is_assigned_asha()`), and Row Level Security (RLS) policies.

## Documented Relational Entities

1. `profiles`: Central user profile linked to Supabase Auth `auth.users`, holding server-enforced role (`MOTHER`, `ASHA`, `ADMIN`).
2. `mother_profiles`: Maternal demographics, gestational age, assigned ASHA, last risk level.
3. `asha_profiles`: ASHA worker identity, worker code, assigned village, phone.
4. `asha_assignments`: Active assignment mapping linking an ASHA worker to a mother for assignment-based authorization.
5. `health_records`: Maternal vital measurements (pregnancy week, systolic/diastolic BP, blood sugar, hemoglobin, weight, temperature, heart rate).
6. `symptoms`: Reported maternal symptoms mapped to standardized codes and severity levels.
7. `model_versions`: Registry of trained ML screening models and feature schema versions.
8. `predictions`: Structured screening risk classification (`LOW`, `MEDIUM`, `HIGH`), screening model score, and contributing factors.
9. `safety_events`: Deterministic escalation events (`CLEAR`, `CONCERNING`, `EMERGENCY`) evaluated by deterministic safety rules.
10. `alerts`: ASHA workflow queue items (`NEW`, `ACKNOWLEDGED`, `CONTACTED`, `VISIT_SCHEDULED`, `FOLLOW_UP_PENDING`, `RESOLVED`, `ESCALATED`) with severity levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
11. `visits`: In-person and home visit records scheduled and completed by ASHAs.
12. `follow_ups`: Scheduled follow-up dates and status tracking.
13. `appointments`: Clinic and health facility scheduled appointments.
14. `medication_reminders`: Prescribed maternal medication reminders and schedules.
15. `chat_sessions`: Multilingual conversation sessions for explanation and care assistance.
16. `chat_messages`: Structured message transcript within a chat session.
17. `audit_logs`: Immutable audit trails recording critical workflow transitions and data access.

## Row Level Security (RLS) Principles

- Unauthenticated access is blocked across all protected tables.
- Mothers can only access records associated with their own `mother_profile`.
- ASHAs can only access mothers, alerts, visits, and follow-ups explicitly assigned to them in `asha_assignments`.
- ADMIN role is restricted to server-side operations and verified by `current_user_role() = 'ADMIN'`.
