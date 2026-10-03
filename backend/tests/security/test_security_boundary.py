"""Security boundary tests for Phase 0 foundation."""

from fastapi.testclient import TestClient
from backend.app.core.config import Settings


def test_no_hardcoded_secrets_in_settings():
    """Verify that default settings do not contain hardcoded secret values."""
    settings = Settings()
    # Keys should default to None in clean environment
    assert settings.SUPABASE_SERVICE_ROLE_KEY is None or settings.SUPABASE_SERVICE_ROLE_KEY == ""
    assert settings.SUPABASE_URL is None or settings.SUPABASE_URL == ""


def test_health_endpoints_do_not_leak_secrets(client: TestClient):
    """Verify health and root endpoints do not leak credentials or sensitive configurations."""
    for path in ["/", "/api/v1/health"]:
        response = client.get(path)
        assert response.status_code == 200
        text = response.text.lower()
        assert "service_role" not in text
        assert "secret" not in text
        assert "password" not in text
        assert "token" not in text
