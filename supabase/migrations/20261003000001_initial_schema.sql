-- ==============================================================================
-- MaternAI Baseline Database Schema Migration
-- Migration: 20261003000001_initial_schema.sql
-- Architecture: PostgreSQL / Supabase with Row Level Security (RLS)
-- Roles: MOTHER, ASHA, ADMIN
-- ==============================================================================

-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. Profiles & Role Management
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('MOTHER', 'ASHA', 'ADMIN')),
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 2. ASHA Profiles
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.asha_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    worker_code VARCHAR(50) UNIQUE,
    assigned_village VARCHAR(100),
    phone VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 3. Mother Profiles
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.mother_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES public.profiles(id) ON DELETE CASCADE,
    date_of_birth DATE,
    age_years INT,
    gestational_age_weeks INT,
    expected_due_date DATE,
    assigned_asha_id UUID REFERENCES public.asha_profiles(id) ON DELETE SET NULL,
    last_risk_level VARCHAR(20) CHECK (last_risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 4. ASHA Assignments (Assignment-based authorization)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.asha_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asha_id UUID NOT NULL REFERENCES public.asha_profiles(id) ON DELETE CASCADE,
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_asha_mother_assignment UNIQUE (asha_id, mother_id)
);

-- ------------------------------------------------------------------------------
-- 5. Health Records (Maternal Vitals & Measurements)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.health_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    pregnancy_week INT,
    systolic_bp NUMERIC(5, 2),
    diastolic_bp NUMERIC(5, 2),
    blood_sugar NUMERIC(5, 2),
    hemoglobin NUMERIC(4, 2),
    weight_kg NUMERIC(5, 2),
    body_temperature NUMERIC(5, 2),
    heart_rate NUMERIC(5, 2),
    recorded_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 6. Symptoms
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.symptoms (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    health_record_id UUID REFERENCES public.health_records(id) ON DELETE SET NULL,
    symptom_code VARCHAR(100) NOT NULL,
    severity INT NOT NULL DEFAULT 1,
    notes TEXT,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 7. Model Versions
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.model_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_tag VARCHAR(50) NOT NULL UNIQUE,
    algorithm VARCHAR(100) NOT NULL,
    feature_schema_version VARCHAR(50) NOT NULL,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 8. Predictions (Structured Risk Screening Output - Server-Controlled)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    health_record_id UUID REFERENCES public.health_records(id) ON DELETE SET NULL,
    model_version_id UUID REFERENCES public.model_versions(id) ON DELETE SET NULL,
    risk_level VARCHAR(20) NOT NULL CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH')),
    model_score NUMERIC(5, 4),
    contributing_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 9. Safety Events (Deterministic Rule Escalation - Server-Controlled)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.safety_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    health_record_id UUID REFERENCES public.health_records(id) ON DELETE SET NULL,
    safety_status VARCHAR(20) NOT NULL CHECK (safety_status IN ('CLEAR', 'CONCERNING', 'EMERGENCY')),
    rule_code VARCHAR(100),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 10. Alerts (Workflow Cases for ASHAs - Generated by Decision Engine)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    asha_id UUID REFERENCES public.asha_profiles(id) ON DELETE SET NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status VARCHAR(30) NOT NULL DEFAULT 'NEW' CHECK (
        status IN ('NEW', 'ACKNOWLEDGED', 'CONTACTED', 'VISIT_SCHEDULED', 'FOLLOW_UP_PENDING', 'RESOLVED', 'ESCALATED')
    ),
    trigger_reason TEXT NOT NULL,
    safety_event_id UUID REFERENCES public.safety_events(id) ON DELETE SET NULL,
    prediction_id UUID REFERENCES public.predictions(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 11. Visits
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    asha_id UUID NOT NULL REFERENCES public.asha_profiles(id) ON DELETE CASCADE,
    alert_id UUID REFERENCES public.alerts(id) ON DELETE SET NULL,
    visit_date TIMESTAMPTZ NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED' CHECK (
        status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED', 'RESCHEDULED')
    ),
    notes TEXT,
    findings JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 12. Follow-ups
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.follow_ups (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    asha_id UUID NOT NULL REFERENCES public.asha_profiles(id) ON DELETE CASCADE,
    alert_id UUID REFERENCES public.alerts(id) ON DELETE SET NULL,
    visit_id UUID REFERENCES public.visits(id) ON DELETE SET NULL,
    due_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'PENDING' CHECK (
        status IN ('PENDING', 'COMPLETED', 'OVERDUE', 'CANCELLED')
    ),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 13. Appointments
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    facility_name VARCHAR(255),
    appointment_date TIMESTAMPTZ NOT NULL,
    purpose VARCHAR(255),
    status VARCHAR(30) NOT NULL DEFAULT 'SCHEDULED',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 14. Medication Reminders
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.medication_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    medication_name VARCHAR(255) NOT NULL,
    dosage VARCHAR(100),
    frequency VARCHAR(100),
    start_date DATE,
    end_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 15. Chat Sessions & Messages
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mother_id UUID NOT NULL REFERENCES public.mother_profiles(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
    sender_role VARCHAR(20) NOT NULL CHECK (sender_role IN ('USER', 'ASSISTANT', 'SYSTEM')),
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 16. Audit Logs (Immutable Security Audit Trail)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100) NOT NULL,
    resource_id VARCHAR(100),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- Indexes for Performance & Query Optimization
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_mother_profiles_user_id ON public.mother_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_mother_profiles_assigned_asha ON public.mother_profiles(assigned_asha_id);
CREATE INDEX IF NOT EXISTS idx_asha_profiles_user_id ON public.asha_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_asha_assignments_asha ON public.asha_assignments(asha_id);
CREATE INDEX IF NOT EXISTS idx_asha_assignments_mother ON public.asha_assignments(mother_id);
CREATE INDEX IF NOT EXISTS idx_health_records_mother_date ON public.health_records(mother_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_symptoms_mother ON public.symptoms(mother_id);
CREATE INDEX IF NOT EXISTS idx_predictions_mother_date ON public.predictions(mother_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_safety_events_mother ON public.safety_events(mother_id);
CREATE INDEX IF NOT EXISTS idx_alerts_asha_status ON public.alerts(asha_id, status);
CREATE INDEX IF NOT EXISTS idx_alerts_mother ON public.alerts(mother_id);
CREATE INDEX IF NOT EXISTS idx_visits_asha_date ON public.visits(asha_id, visit_date);
CREATE INDEX IF NOT EXISTS idx_follow_ups_asha_status ON public.follow_ups(asha_id, status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_date ON public.audit_logs(user_id, created_at DESC);

-- ------------------------------------------------------------------------------
-- 17. Hardened Row Level Security (RLS) Helper Functions (Explicit Search Path)
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.current_user_id()
RETURNS UUID AS $$
    SELECT auth.uid();
$$ LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, auth;

CREATE OR REPLACE FUNCTION public.current_user_role()
RETURNS VARCHAR AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid();
$$ LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, auth;

CREATE OR REPLACE FUNCTION public.is_assigned_asha(p_mother_id UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1
        FROM public.asha_assignments aa
        JOIN public.asha_profiles ap ON ap.id = aa.asha_id
        WHERE ap.user_id = auth.uid()
          AND aa.mother_id = p_mother_id
          AND aa.is_active = TRUE
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public, auth;

-- ------------------------------------------------------------------------------
-- 18. Database-Level Role Escalation & Authoritative Field Protection Triggers
-- ------------------------------------------------------------------------------

-- Prevent users from updating their own role column (MOTHER -> ASHA / ADMIN)
CREATE OR REPLACE FUNCTION public.check_profile_role_update()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.role IS DISTINCT FROM OLD.role THEN
        IF public.current_user_role() != 'ADMIN' THEN
            RAISE EXCEPTION 'Unauthorized: Direct modification of user role is prohibited';
        END IF;
    END IF;
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, auth;

DROP TRIGGER IF EXISTS trg_prevent_role_escalation ON public.profiles;
CREATE TRIGGER trg_prevent_role_escalation
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.check_profile_role_update();

-- Prevent mothers from updating last_risk_level (server-controlled) and assigned_asha_id
CREATE OR REPLACE FUNCTION public.check_mother_profile_update()
RETURNS TRIGGER AS $$
BEGIN
    -- Only server/admin can update last_risk_level directly
    IF NEW.last_risk_level IS DISTINCT FROM OLD.last_risk_level THEN
        IF public.current_user_role() != 'ADMIN' THEN
            RAISE EXCEPTION 'Unauthorized: last_risk_level is server-controlled and cannot be modified directly';
        END IF;
    END IF;

    -- assigned_asha_id can only be updated by ASHA or ADMIN, not self-assigned by Mother
    IF NEW.assigned_asha_id IS DISTINCT FROM OLD.assigned_asha_id THEN
        IF public.current_user_role() NOT IN ('ASHA', 'ADMIN') THEN
            RAISE EXCEPTION 'Unauthorized: Mothers cannot reassign their assigned ASHA';
        END IF;
    END IF;

    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, auth;

DROP TRIGGER IF EXISTS trg_prevent_mother_authoritative_update ON public.mother_profiles;
CREATE TRIGGER trg_prevent_mother_authoritative_update
    BEFORE UPDATE ON public.mother_profiles
    FOR EACH ROW EXECUTE FUNCTION public.check_mother_profile_update();

-- ------------------------------------------------------------------------------
-- 19. Enable Row Level Security (RLS) on All 17 Tables
-- ------------------------------------------------------------------------------
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.mother_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asha_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.asha_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.health_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.symptoms ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.safety_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.follow_ups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.medication_reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- 20. Comprehensive RLS Policies for All 17 Entities
-- ------------------------------------------------------------------------------

-- 1. PROFILES
CREATE POLICY profiles_select ON public.profiles
    FOR SELECT USING (
        id = auth.uid()
        OR id IN (SELECT mp.user_id FROM public.mother_profiles mp WHERE public.is_assigned_asha(mp.id))
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY profiles_insert ON public.profiles
    FOR INSERT WITH CHECK (id = auth.uid() OR public.current_user_role() = 'ADMIN');

CREATE POLICY profiles_update ON public.profiles
    FOR UPDATE USING (id = auth.uid() OR public.current_user_role() = 'ADMIN');

CREATE POLICY profiles_delete ON public.profiles
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 2. MOTHER PROFILES
CREATE POLICY mother_profiles_select ON public.mother_profiles
    FOR SELECT USING (
        user_id = auth.uid()
        OR public.is_assigned_asha(id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY mother_profiles_insert ON public.mother_profiles
    FOR INSERT WITH CHECK (
        user_id = auth.uid()
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY mother_profiles_update ON public.mother_profiles
    FOR UPDATE USING (
        user_id = auth.uid()
        OR public.is_assigned_asha(id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY mother_profiles_delete ON public.mother_profiles
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 3. ASHA PROFILES
CREATE POLICY asha_profiles_select ON public.asha_profiles
    FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY asha_profiles_insert ON public.asha_profiles
    FOR INSERT WITH CHECK (user_id = auth.uid() OR public.current_user_role() = 'ADMIN');

CREATE POLICY asha_profiles_update ON public.asha_profiles
    FOR UPDATE USING (user_id = auth.uid() OR public.current_user_role() = 'ADMIN');

CREATE POLICY asha_profiles_delete ON public.asha_profiles
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 4. ASHA ASSIGNMENTS
CREATE POLICY asha_assignments_select ON public.asha_assignments
    FOR SELECT USING (
        asha_id IN (SELECT id FROM public.asha_profiles WHERE user_id = auth.uid())
        OR mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY asha_assignments_insert ON public.asha_assignments
    FOR INSERT WITH CHECK (
        public.current_user_role() IN ('ASHA', 'ADMIN')
    );

CREATE POLICY asha_assignments_update ON public.asha_assignments
    FOR UPDATE USING (
        public.current_user_role() IN ('ASHA', 'ADMIN')
    );

CREATE POLICY asha_assignments_delete ON public.asha_assignments
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 5. HEALTH RECORDS (Measurements are immutable; UPDATE/DELETE restricted)
CREATE POLICY health_records_select ON public.health_records
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY health_records_insert ON public.health_records
    FOR INSERT WITH CHECK (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY health_records_update ON public.health_records
    FOR UPDATE USING (public.current_user_role() = 'ADMIN');

CREATE POLICY health_records_delete ON public.health_records
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 6. SYMPTOMS (Symptom reports are immutable; UPDATE/DELETE restricted)
CREATE POLICY symptoms_select ON public.symptoms
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY symptoms_insert ON public.symptoms
    FOR INSERT WITH CHECK (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY symptoms_update ON public.symptoms
    FOR UPDATE USING (public.current_user_role() = 'ADMIN');

CREATE POLICY symptoms_delete ON public.symptoms
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 7. MODEL VERSIONS (Registry is read-only for clients; managed by server/admin)
CREATE POLICY model_versions_select ON public.model_versions
    FOR SELECT USING (auth.uid() IS NOT NULL);

CREATE POLICY model_versions_insert ON public.model_versions
    FOR INSERT WITH CHECK (public.current_user_role() = 'ADMIN');

CREATE POLICY model_versions_update ON public.model_versions
    FOR UPDATE USING (public.current_user_role() = 'ADMIN');

CREATE POLICY model_versions_delete ON public.model_versions
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 8. PREDICTIONS (Authoritative output; direct client write strictly denied)
CREATE POLICY predictions_select ON public.predictions
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY predictions_insert ON public.predictions
    FOR INSERT WITH CHECK (public.current_user_role() = 'ADMIN');

CREATE POLICY predictions_update ON public.predictions
    FOR UPDATE USING (public.current_user_role() = 'ADMIN');

CREATE POLICY predictions_delete ON public.predictions
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 9. SAFETY EVENTS (Deterministic escalation output; direct client write strictly denied)
CREATE POLICY safety_events_select ON public.safety_events
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY safety_events_insert ON public.safety_events
    FOR INSERT WITH CHECK (public.current_user_role() = 'ADMIN');

CREATE POLICY safety_events_update ON public.safety_events
    FOR UPDATE USING (public.current_user_role() = 'ADMIN');

CREATE POLICY safety_events_delete ON public.safety_events
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 10. ALERTS (Workflow items; direct client INSERT denied; ASHA can update status)
CREATE POLICY alerts_select ON public.alerts
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY alerts_insert ON public.alerts
    FOR INSERT WITH CHECK (public.current_user_role() = 'ADMIN');

CREATE POLICY alerts_update ON public.alerts
    FOR UPDATE USING (
        public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY alerts_delete ON public.alerts
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 11. VISITS
CREATE POLICY visits_select ON public.visits
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY visits_insert ON public.visits
    FOR INSERT WITH CHECK (
        public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY visits_update ON public.visits
    FOR UPDATE USING (
        public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY visits_delete ON public.visits
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 12. FOLLOW-UPS
CREATE POLICY follow_ups_select ON public.follow_ups
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY follow_ups_insert ON public.follow_ups
    FOR INSERT WITH CHECK (
        public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY follow_ups_update ON public.follow_ups
    FOR UPDATE USING (
        public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY follow_ups_delete ON public.follow_ups
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 13. APPOINTMENTS
CREATE POLICY appointments_select ON public.appointments
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY appointments_insert ON public.appointments
    FOR INSERT WITH CHECK (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY appointments_update ON public.appointments
    FOR UPDATE USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY appointments_delete ON public.appointments
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 14. MEDICATION REMINDERS
CREATE POLICY medication_reminders_select ON public.medication_reminders
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY medication_reminders_insert ON public.medication_reminders
    FOR INSERT WITH CHECK (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY medication_reminders_update ON public.medication_reminders
    FOR UPDATE USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.is_assigned_asha(mother_id)
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY medication_reminders_delete ON public.medication_reminders
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 15. CHAT SESSIONS
CREATE POLICY chat_sessions_select ON public.chat_sessions
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY chat_sessions_insert ON public.chat_sessions
    FOR INSERT WITH CHECK (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY chat_sessions_update ON public.chat_sessions
    FOR UPDATE USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY chat_sessions_delete ON public.chat_sessions
    FOR DELETE USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR public.current_user_role() = 'ADMIN'
    );

-- 16. CHAT MESSAGES
CREATE POLICY chat_messages_select ON public.chat_messages
    FOR SELECT USING (
        session_id IN (
            SELECT id FROM public.chat_sessions
            WHERE mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        )
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY chat_messages_insert ON public.chat_messages
    FOR INSERT WITH CHECK (
        session_id IN (
            SELECT id FROM public.chat_sessions
            WHERE mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        )
        OR public.current_user_role() = 'ADMIN'
    );

CREATE POLICY chat_messages_update ON public.chat_messages
    FOR UPDATE USING (public.current_user_role() = 'ADMIN');

CREATE POLICY chat_messages_delete ON public.chat_messages
    FOR DELETE USING (public.current_user_role() = 'ADMIN');

-- 17. AUDIT LOGS (Immutable security logs; only ADMIN can view; clients cannot read or write)
CREATE POLICY audit_logs_select ON public.audit_logs
    FOR SELECT USING (public.current_user_role() = 'ADMIN');

CREATE POLICY audit_logs_insert ON public.audit_logs
    FOR INSERT WITH CHECK (public.current_user_role() = 'ADMIN');

-- Explicitly NO update or delete policies on audit_logs (Strictly DENIED / Immutable)
