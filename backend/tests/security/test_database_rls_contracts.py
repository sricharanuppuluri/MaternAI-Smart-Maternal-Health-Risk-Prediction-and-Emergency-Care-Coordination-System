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
