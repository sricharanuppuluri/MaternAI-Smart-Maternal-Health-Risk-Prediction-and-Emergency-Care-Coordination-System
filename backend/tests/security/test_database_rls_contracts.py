"""Static analysis and contract tests for database migration and RLS policies.

Verifies:
- All 17 documented entities have Row Level Security enabled.
- Security Definer helper functions specify explicit SET search_path.
- Anti-escalation triggers are attached to profiles and mother_profiles.
- Server-controlled tables deny client direct INSERT.
- Immutable tables deny client direct UPDATE.
"""

from pathlib import Path
import re
import pytest

MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "supabase" / "migrations"
MIGRATION_FILE = MIGRATIONS_DIR / "20261003000001_initial_schema.sql"

DOCUMENTED_ENTITIES = [
    "profiles",
    "mother_profiles",
    "asha_profiles",
    "asha_assignments",
    "health_records",
    "symptoms",
    "model_versions",
    "predictions",
    "safety_events",
    "alerts",
    "visits",
    "follow_ups",
    "appointments",
    "medication_reminders",
    "chat_sessions",
    "chat_messages",
    "audit_logs",
]


def test_migration_file_exists():
    """Verify the Phase 2 baseline migration file exists."""
    assert MIGRATION_FILE.exists(), f"Migration file not found at {MIGRATION_FILE}"


def test_all_17_entities_have_rls_enabled():
    """Verify that all 17 documented entities explicitly enable Row Level Security."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    for entity in DOCUMENTED_ENTITIES:
        pattern = rf"ALTER\s+TABLE\s+public\.{entity}\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY;"
        assert re.search(pattern, content, re.IGNORECASE), f"RLS not enabled for entity '{entity}'"


def test_security_definer_functions_have_explicit_search_path():
    """Verify SECURITY DEFINER functions explicitly set search_path to prevent search-path injection."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    sec_definer_funcs = [
        "current_user_id",
        "current_user_role",
        "is_assigned_asha",
        "check_profile_role_update",
        "check_mother_profile_update",
    ]
    for func in sec_definer_funcs:
        pattern = rf"CREATE\s+OR\s+REPLACE\s+FUNCTION\s+public\.{func}\s*\([^)]*\).*?SECURITY\s+DEFINER.*?SET\s+search_path\s*=\s*public"
        assert re.search(pattern, content, re.IGNORECASE | re.DOTALL), f"Function {func} missing explicit search_path"


def test_anti_escalation_triggers_present():
    """Verify anti-escalation triggers for role and mother authoritative fields exist."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    assert "trg_prevent_role_escalation" in content
    assert "trg_prevent_mother_authoritative_update" in content
    assert "check_profile_role_update" in content
    assert "check_mother_profile_update" in content


def test_audit_logs_immutability_in_migration():
    """Verify audit_logs does not have client update or delete policies."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    # Verify no UPDATE policy for audit_logs
    assert not re.search(r"CREATE\s+POLICY\s+audit_logs_update", content, re.IGNORECASE)
    assert not re.search(r"CREATE\s+POLICY\s+audit_logs_delete", content, re.IGNORECASE)


# ------------------------------------------------------------------------------
# RLS Scenarios Static Analysis & Policy Invariant Tests (Part 2)
# ------------------------------------------------------------------------------
def test_scenario_1_mother_isolation_policy():
    """Scenario 1: Mother isolation - policies strictly enforce auth.uid() scoping."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    # Mother profiles SELECT must be restricted to user_id = auth.uid() or assigned ASHA/Admin
    assert re.search(r"user_id\s*=\s*auth\.uid\(\)", content)
    # Health records SELECT must be restricted to mother_id scoping or assigned ASHA/Admin
    assert re.search(r"mother_id\s*IN\s*\(SELECT\s+id\s+FROM\s+public\.mother_profiles\s+WHERE\s+user_id\s*=\s*auth\.uid\(\)\)", content)


def test_scenario_2_and_3_asha_assignment_and_isolation():
    """Scenarios 2 & 3: Assigned ASHA allowed, unassigned ASHA denied via is_assigned_asha()."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    # Must use is_assigned_asha(mother_id) or is_assigned_asha(id)
    assert re.search(r"public\.is_assigned_asha\(\s*(?:mother_id|id)\s*\)", content)


def test_scenario_4_role_escalation_trigger_logic():
    """Scenario 4: Role escalation blocked by check_profile_role_update trigger function."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    # Must check NEW.role != OLD.role and current_user_role() != 'ADMIN'
    assert "NEW.role IS DISTINCT FROM OLD.role" in content
    assert "public.current_user_role() != 'ADMIN'" in content
    assert "Unauthorized: Direct modification of user role is prohibited" in content


def test_scenario_5_and_6_mother_authoritative_fields_protection():
    """Scenarios 5 & 6: ASHA reassignment and risk level modification blocked by trigger."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    assert "NEW.assigned_asha_id IS DISTINCT FROM OLD.assigned_asha_id" in content
    assert "NEW.last_risk_level IS DISTINCT FROM OLD.last_risk_level" in content
    assert "Unauthorized: Mothers cannot reassign their assigned ASHA" in content
    assert "Unauthorized: last_risk_level is server-controlled" in content


def test_scenario_7_and_8_server_controlled_predictions_and_safety_events():
    """Scenarios 7 & 8: Predictions and safety_events insert policies restricted to ADMIN/service."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    # Predictions insert policy must restrict to ADMIN
    assert re.search(r"CREATE\s+POLICY\s+predictions_insert.*?WITH\s+CHECK\s*\(\s*public\.current_user_role\(\)\s*=\s*'ADMIN'\s*\);", content, re.DOTALL)
    # Safety events insert policy must restrict to ADMIN
    assert re.search(r"CREATE\s+POLICY\s+safety_events_insert.*?WITH\s+CHECK\s*\(\s*public\.current_user_role\(\)\s*=\s*'ADMIN'\s*\);", content, re.DOTALL)


def test_scenario_10_unauthenticated_access_denied():
    """Scenario 10: Unauthenticated access denied by requiring auth.uid() or current_user_role()."""
    content = MIGRATION_FILE.read_text(encoding="utf-8")
    # Helper functions check id = auth.uid() or auth.uid() IS NOT NULL
    assert "auth.uid()" in content
    assert "WHERE id = auth.uid()" in content

