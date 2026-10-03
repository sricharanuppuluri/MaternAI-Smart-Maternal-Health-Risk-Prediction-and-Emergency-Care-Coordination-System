"""Unit tests for configuration loading and validation."""

from backend.app.core.config import Settings


def test_default_settings():
    """Verify default configuration values."""
    settings = Settings()
    assert settings.PROJECT_NAME == "MaternAI"
    assert settings.VERSION == "0.1.0"
    assert settings.ENVIRONMENT == "development"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.MODEL_VERSION == "v0.1.0"
    assert settings.OLLAMA_BASE_URL == "http://localhost:11434"
    assert settings.OLLAMA_MODEL == "llama3"


def test_supabase_configured_property():
    """Verify is_supabase_configured logic."""
    unconfigured = Settings(SUPABASE_URL=None, SUPABASE_SERVICE_ROLE_KEY=None)
    assert unconfigured.is_supabase_configured is False

    partial = Settings(SUPABASE_URL="https://example.supabase.co", SUPABASE_SERVICE_ROLE_KEY=None)
    assert partial.is_supabase_configured is False

    configured = Settings(
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_SERVICE_ROLE_KEY="test-service-key",
    )
    assert configured.is_supabase_configured is True
