# Supabase Database & Migrations

This directory contains Supabase PostgreSQL migrations and database scripts for MaternAI.

## Migrations

- `20261003000001_initial_schema.sql`: Baseline relational schema establishing all 17 documented entities, indexes, hardened security functions (`current_user_id()`, `current_user_role()`, `is_assigned_asha()`), anti-escalation triggers, and comprehensive Row Level Security (RLS) policies.

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

## Security Hardening Details

### 1. Hardened SECURITY DEFINER Helper Functions
All helper functions run with explicitly configured `search_path`:
```sql
CREATE OR REPLACE FUNCTION public.current_user_id() ...
SET search_path = public, auth;
```
This protects against search-path hijacking under Supabase / PostgreSQL execution.

### 2. Database Triggers Preventing Privilege & State Escalation
- `trg_prevent_role_escalation` on `public.profiles`: Aborts any `UPDATE` that attempts to change `role` unless `current_user_role() = 'ADMIN'`.
- `trg_prevent_mother_authoritative_update` on `public.mother_profiles`: Aborts any client-side `UPDATE` attempting to alter authoritative fields (`assigned_asha_id`, `last_risk_level`) unless executed by `ADMIN`.

### 3. Comprehensive 17-Entity RLS Policies
All 17 tables enforce Row Level Security (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`). Every table has explicit `SELECT`, `INSERT`, `UPDATE`, and `DELETE` policies:
- **Default Deny / Server-Controlled**: `model_versions`, `predictions`, `safety_events`, `audit_logs` prohibit direct client writes; inserts/updates are restricted to `ADMIN` or database service role.
- **Audit Logs Immutability**: `audit_logs` completely disallows `UPDATE` and `DELETE` for all roles (including ADMIN).
- **Patient Isolation**: Mothers have strictly scoped `SELECT`, `INSERT`, and `UPDATE` access to their own records only (`mother_id = auth.uid()`).
- **Assignment-Scoped Worker Access**: ASHAs can only query or update records for mothers explicitly assigned to them via active `asha_assignments` (`is_assigned_asha(mother_id)`).

## Verification & Testing Boundaries

- **Static Analysis & Contract Testing (PASSED)**: Executable via `pytest backend/tests/security/` (verifies SQL migration AST/regex invariants across all 17 tables, explicit `search_path = public, auth`, anti-escalation triggers, and audit log immutability).
- **Relational SQL Persistence (PASSED - Phase 4)**: Application data across all 17 schema entities persists relationally to disk via `RepositoryStore`, ensuring data survives backend restarts.
- **Live Supabase Container Integration Testing (DEFERRED)**: Runtime PostgreSQL execution of RLS policies and role-switching requires an active Supabase container or running PostgreSQL instance. When neither Docker, the Supabase CLI, nor local PostgreSQL (`psql`) are active on the host machine, live runtime execution is gracefully detected and skipped via `backend/tests/integration/test_supabase_rls_live.py`. Live DB RLS execution remains environment-dependent.

