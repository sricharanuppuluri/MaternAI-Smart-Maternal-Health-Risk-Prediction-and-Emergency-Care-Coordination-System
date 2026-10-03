"""Database connection and ORM/client package.

Planned architecture:
Supabase PostgreSQL database with Row Level Security (RLS) policies.
Planned entities:
- profiles, mother_profiles, asha_profiles
- health_records, symptoms
- model_versions, predictions, safety_events
- asha_assignments, alerts, visits, follow_ups
- appointments, medication_reminders
- chat_sessions, chat_messages, audit_logs

Note: Database schema and client will be implemented in the Database/schema phase.
"""
