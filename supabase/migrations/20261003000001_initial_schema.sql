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
-- 8. Predictions (Structured Risk Screening Output)
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
-- 9. Safety Events (Deterministic Rule Escalation)
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
-- 10. Alerts (Workflow Cases for ASHAs)
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
-- 16. Audit Logs
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
-- 17. Row Level Security (RLS) Helper Functions
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.current_user_id()
RETURNS UUID AS $$
    SELECT auth.uid();
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.current_user_role()
RETURNS VARCHAR AS $$
    SELECT role FROM public.profiles WHERE id = auth.uid();
$$ LANGUAGE sql STABLE SECURITY DEFINER;

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
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- ------------------------------------------------------------------------------
-- 18. Enable Row Level Security (RLS) on All Tables
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
-- 19. Core RLS Policies
-- ------------------------------------------------------------------------------

-- Profiles: Users can read and update their own profile; Admins full access
CREATE POLICY profiles_select_own ON public.profiles
    FOR SELECT USING (id = auth.uid() OR current_user_role() = 'ADMIN');

CREATE POLICY profiles_update_own ON public.profiles
    FOR UPDATE USING (id = auth.uid() OR current_user_role() = 'ADMIN');

-- Mother Profiles: Mother accesses own; Assigned ASHA accesses assigned mother; Admin
CREATE POLICY mother_profiles_select ON public.mother_profiles
    FOR SELECT USING (
        user_id = auth.uid()
        OR is_assigned_asha(id)
        OR current_user_role() = 'ADMIN'
    );

CREATE POLICY mother_profiles_update ON public.mother_profiles
    FOR UPDATE USING (
        user_id = auth.uid()
        OR current_user_role() = 'ADMIN'
    );

-- Health Records: Mother accesses own; Assigned ASHA accesses assigned; Admin
CREATE POLICY health_records_select ON public.health_records
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR is_assigned_asha(mother_id)
        OR current_user_role() = 'ADMIN'
    );

CREATE POLICY health_records_insert ON public.health_records
    FOR INSERT WITH CHECK (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR is_assigned_asha(mother_id)
        OR current_user_role() = 'ADMIN'
    );

-- Alerts: Mother views own; ASHA views assigned; Admin
CREATE POLICY alerts_select ON public.alerts
    FOR SELECT USING (
        mother_id IN (SELECT id FROM public.mother_profiles WHERE user_id = auth.uid())
        OR is_assigned_asha(mother_id)
        OR current_user_role() = 'ADMIN'
    );

CREATE POLICY alerts_update ON public.alerts
    FOR UPDATE USING (
        is_assigned_asha(mother_id)
        OR current_user_role() = 'ADMIN'
    );
